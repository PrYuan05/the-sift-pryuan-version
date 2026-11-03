package pryuan05.pysift.progression;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUseAnimation;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Consumer;

/**
 * 音波法杖（調和者核心製成）：
 * <ul>
 *   <li>右鍵：舉起法杖詠唱 0.6 秒（音波往晶體匯聚、晶體越來越亮；中途放開就中斷），接著沿視線發射 15 格音爆，貫穿路上所有敵人造成 8 點傷害、冷卻 3 秒（覺醒：寬度加倍、12 點、冷卻 2 秒），遇到方塊停止。</li>
 *   <li>左鍵命中：連鎖攻擊目標附近 6 格內的 3 個敵人各 3 點（覺醒 5 個、各 4 點），連同主目標都附加靈魂剝奪。</li>
 * </ul>
 */
public class SonicStaffItem extends Item {
    private static final double RANGE = 15.0;
    private static final int COOLDOWN = 60;            // awakened: 40
    /** 詠唱多久才放出音爆（物品模型 sonic_staff_casting_* 依這段時間換階段，見 build_weapon_models.py）。 */
    public static final int CAST_TICKS = 12;

    public SonicStaffItem(Properties properties) {
        super(properties);
    }

    /** 不用原版姿勢：詠唱姿勢由客戶端的 WeaponPoses 畫（法杖舉向天空、另一隻手往前伸）。 */
    @Override
    public ItemUseAnimation getUseAnimation(ItemStack stack) {
        return ItemUseAnimation.NONE;
    }

    @Override
    public int getUseDuration(ItemStack stack, LivingEntity entity) {
        return CAST_TICKS;
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player.getCooldowns().isOnCooldown(stack)) {
            return InteractionResult.PASS;
        }
        player.startUsingItem(hand);
        return InteractionResult.CONSUME;
    }

    /** 詠唱中：音波粒子從四周往晶體匯聚，紫水晶的共鳴聲一階一階升高。 */
    @Override
    public void onUseTick(Level level, LivingEntity user, ItemStack stack, int remaining) {
        if (!(level instanceof ServerLevel server)) {
            return;
        }
        int t = CAST_TICKS - remaining;
        Vec3 tip = staffTip(user);
        double spread = 1.6 * remaining / CAST_TICKS + 0.3;
        for (int i = 0; i < 4; i++) {
            double a = server.getRandom().nextDouble() * Math.PI * 2, b = server.getRandom().nextDouble() * Math.PI - Math.PI / 2;
            Vec3 from = tip.add(Math.cos(a) * Math.cos(b) * spread, Math.sin(b) * spread, Math.sin(a) * Math.cos(b) * spread);
            Vec3 v = tip.subtract(from).scale(0.25);   // 往晶體飛
            server.sendParticles(ParticleTypes.ELECTRIC_SPARK, from.x, from.y, from.z, 0, v.x, v.y, v.z, 1.0);
        }
        server.sendParticles(ParticleTypes.END_ROD, tip.x, tip.y, tip.z, 1, 0.05, 0.05, 0.05, 0.0);
        if (t % 3 == 0) {
            server.playSound(null, user.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 0.8f, 0.8f + t * 0.08f);
        }
    }

    /** 詠唱完成：放出音爆。 */
    @Override
    public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity user) {
        if (level instanceof ServerLevel server && user instanceof Player player) {
            boolean awakened = BossWeapons.isAwakened(stack);
            Vec3 tip = staffTip(player);
            server.sendParticles(net.minecraft.core.particles.ColorParticleOption.create(ParticleTypes.FLASH, 0xFF9FF4FF), tip.x, tip.y, tip.z, 1, 0, 0, 0, 0);
            beam(server, player, awakened ? 1.6 : 0.9, awakened ? 12.0f : 8.0f);
            player.getCooldowns().addCooldown(stack, awakened ? 40 : COOLDOWN);
            stack.hurtAndBreak(1, player, player.getUsedItemHand() == InteractionHand.OFF_HAND ? EquipmentSlot.OFFHAND : EquipmentSlot.MAINHAND);
        }
        return stack;
    }

    /** 中途放開：咒語散掉（沒有冷卻）。 */
    @Override
    public boolean releaseUsing(ItemStack stack, Level level, LivingEntity user, int timeLeft) {
        if (level instanceof ServerLevel server) {
            Vec3 tip = staffTip(user);
            server.sendParticles(ParticleTypes.SMOKE, tip.x, tip.y, tip.z, 6, 0.1, 0.1, 0.1, 0.01);
            server.playSound(null, user.blockPosition(), SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.PLAYERS, 0.6f, 1.4f);
        }
        return false;
    }

    /** 法杖晶體大約在哪：眼睛前方 0.9 格、往持杖的那一側偏一點、往下一點。 */
    private static Vec3 staffTip(LivingEntity user) {
        Vec3 look = user.getLookAngle();
        Vec3 side = new Vec3(-look.z, 0, look.x).normalize().scale(user.getUsedItemHand() == InteractionHand.OFF_HAND ? -0.35 : 0.35);
        return user.getEyePosition().add(look.scale(0.9)).add(side).add(0, -0.25, 0);
    }

    private static void beam(ServerLevel level, Player player, double width, float damage) {
        Vec3 start = player.getEyePosition();
        Vec3 dir = player.getLookAngle();
        Set<LivingEntity> hit = new HashSet<>();
        for (double d = 1.0; d <= RANGE; d += 0.5) {
            Vec3 p = start.add(dir.scale(d));
            BlockPos bp = BlockPos.containing(p);
            if (!level.getBlockState(bp).getCollisionShape(level, bp).isEmpty()) {
                break;
            }
            if (((int) (d * 2)) % 3 == 0) {
                level.sendParticles(ParticleTypes.SONIC_BOOM, p.x, p.y, p.z, 1, 0, 0, 0, 0);
            }
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(p, p).inflate(width),
                    e -> BossWeapons.isFoe(player, e) && !hit.contains(e))) {
                hit.add(e);
                if (e.hurtServer(level, level.damageSources().sonicBoom(player), damage)) {
                    e.setDeltaMovement(e.getDeltaMovement().add(dir.x * 0.6, 0.2, dir.z * 0.6));   // pushed along the beam
                    e.needsSync = true;
                }
            }
        }
        level.playSound(null, player.blockPosition(), SoundEvents.WARDEN_SONIC_BOOM, SoundSource.PLAYERS, 1.5f, 1.2f);
    }

    @Override
    public void postHurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
        super.postHurtEnemy(stack, target, attacker);
        if (!(attacker.level() instanceof ServerLevel level)) {
            return;
        }
        BossWeapons.soulDeprive(target, attacker);
        boolean awakened = BossWeapons.isAwakened(stack);
        BossWeapons.chain(level, attacker, target, awakened ? 5 : 3, awakened ? 4.0f : 3.0f);
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        return BossWeapons.isAwakened(stack) || super.isFoil(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> out, TooltipFlag flag) {
        boolean awakened = BossWeapons.isAwakened(stack);
        out.accept(Component.translatable(awakened ? "tooltip.pysift.sonic_staff.use_awakened" : "tooltip.pysift.sonic_staff.use"));
        out.accept(Component.translatable(awakened ? "tooltip.pysift.sonic_staff.hit_awakened" : "tooltip.pysift.sonic_staff.hit"));
        if (awakened) {
            out.accept(Component.translatable("tooltip.pysift.awakened"));
        } else {
            out.accept(Component.translatable("tooltip.pysift.sonic_staff.how_to_awaken").withStyle(net.minecraft.ChatFormatting.DARK_GRAY));
        }
    }
}
