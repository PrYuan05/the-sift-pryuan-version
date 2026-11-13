package pryuan05.pysift.progression;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUseAnimation;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.function.Consumer;

/**
 * 重錘（幽匿巨怪之心製成）：按住右鍵蓄力，放開後砸地，從落點擴散出一圈震波。蓄力分兩段，和物品模型的階段一致
 * （sculk_hammer_charging_*，build_weapon_models.py）：
 * <ul>
 *   <li>未滿 0.75 秒（{@link #MIN_CHARGE}）：放開沒有效果。</li>
 *   <li>蓄力（0.75–2 秒）：震波半徑 3 → 4.5 格、傷害 6 → 9、2 → 4 條幽匿藤蔓，越久越強；冷卻 2 秒。</li>
 *   <li>蓄滿（2 秒，{@link #FULL_CHARGE}）：半徑 6 格、傷害 14、6 條藤蔓、把敵人高高震起並緩速；
 *       中心多一聲音爆，冷卻 3 秒。</li>
 * </ul>
 * 覺醒後半徑 ×4/3、多 3 條藤蔓。蓄力時地上會畫出目前的震波範圍（蓄力：靈魂粒子圈；蓄滿：藍色靈魂火圈），
 * 放開後震波由內往外擴散，波前掃到敵人時才結算傷害。藤蔓 2 秒後各自爆炸並造成靈魂剝奪（{@link BossWeapons#plantTendril}）。
 */
public class SculkHammerItem extends Item {
    /** 物品模型 sculk_hammer_charging_* 依同樣的時間換階段（build_weapon_models.py）。 */
    public static final int MIN_CHARGE = 15;
    public static final int FULL_CHARGE = 40;
    private static final int COOLDOWN = 40;
    private static final int FULL_COOLDOWN = 60;
    /** 震波每 tick 往外推進的格數。 */
    private static final double WAVE_SPEED = 0.6;

    /** 某段蓄力的砸地效果。 */
    private record Slam(boolean full, double radius, float damage, int tendrils, double push, double lift, int cooldown) {
        static Slam of(int charge, boolean awakened) {
            double scale = awakened ? 4.0 / 3.0 : 1.0;
            int bonus = awakened ? 3 : 0;
            if (charge >= FULL_CHARGE) {
                return new Slam(true, 6.0 * scale, 14.0f, 6 + bonus, 1.8, 0.85, FULL_COOLDOWN);
            }
            float t = Mth.clamp((float) (charge - MIN_CHARGE) / (FULL_CHARGE - MIN_CHARGE), 0.0f, 1.0f);
            return new Slam(false, (3.0 + 1.5 * t) * scale, 6.0f + 3.0f * t, 2 + Math.round(2 * t) + bonus,
                    0.6 + 0.6 * t, 0.35 + 0.15 * t, COOLDOWN);
        }
    }

    public SculkHammerItem(Properties properties) {
        super(properties);
    }

    @Override
    public ItemUseAnimation getUseAnimation(ItemStack stack) {
        return ItemUseAnimation.NONE;   // 不用原版姿勢：雙手舉過頭頂蓄力的姿勢由客戶端的 WeaponPoses 畫
    }

    @Override
    public int getUseDuration(ItemStack stack, LivingEntity entity) {
        return 72000;
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (player.getCooldowns().isOnCooldown(player.getItemInHand(hand))) {
            return InteractionResult.PASS;
        }
        player.startUsingItem(hand);
        return InteractionResult.CONSUME;
    }

    /**
     * 蓄力中：幽匿的靈魂從地面盤旋著被吸進錘頭（越蓄越快、越多），每 10 tick 一聲越來越急的心跳；
     * 蓄到可以砸（MIN_CHARGE）和蓄滿（FULL_CHARGE）時各有一個提示。
     */
    @Override
    public void onUseTick(Level level, LivingEntity user, ItemStack stack, int remaining) {
        if (!(level instanceof ServerLevel server)) {
            return;
        }
        int charge = getUseDuration(stack, user) - remaining;
        float power = Mth.clamp((float) charge / FULL_CHARGE, 0.0f, 1.0f);
        Vec3 head = user.getEyePosition().add(0, 0.45, 0).add(user.getLookAngle().multiply(1, 0, 1).scale(-0.2));
        double r = 2.2 - 1.6 * power;
        for (int i = 0, n = 1 + (int) (power * 3); i < n; i++) {
            double a = charge * 0.45 + i * Math.PI * 2 / n;      // 盤旋往上
            double y = user.getY() + 0.1 + power * 0.8;
            Vec3 from = new Vec3(user.getX() + Math.cos(a) * r, y, user.getZ() + Math.sin(a) * r);
            Vec3 v = head.subtract(from).scale(0.18);
            server.sendParticles(ParticleTypes.SCULK_SOUL, from.x, from.y, from.z, 0, v.x, v.y, v.z, 1.0);
        }
        if (charge >= MIN_CHARGE && charge % 4 == 0) {           // 地上畫出放開時的震波範圍
            Slam slam = Slam.of(charge, BossWeapons.isAwakened(stack));
            ring(server, user.position(), slam.radius(), slam.full() ? ParticleTypes.SOUL_FIRE_FLAME : ParticleTypes.SOUL, 0.0, charge * 0.07);
        }
        if (charge % Math.max(4, 10 - (int) (power * 6)) == 0) {
            server.playSound(null, user.blockPosition(), SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 0.9f, 0.8f + power * 0.6f);
        }
        if (charge == MIN_CHARGE) {
            server.playSound(null, user.blockPosition(), SoundEvents.SCULK_CLICKING, SoundSource.PLAYERS, 1.0f, 1.0f);
        }
        if (charge == FULL_CHARGE) {
            server.playSound(null, user.blockPosition(), SoundEvents.SCULK_SHRIEKER_SHRIEK, SoundSource.PLAYERS, 0.8f, 1.3f);
            server.sendParticles(new net.minecraft.core.particles.ShriekParticleOption(0), head.x, head.y, head.z, 1, 0, 0, 0, 0);
            server.sendParticles(ParticleTypes.SCULK_CHARGE_POP, head.x, head.y, head.z, 12, 0.3, 0.3, 0.3, 0.05);
        }
    }

    @Override
    public boolean releaseUsing(ItemStack stack, Level level, LivingEntity user, int timeLeft) {
        int charge = getUseDuration(stack, user) - timeLeft;
        if (charge < MIN_CHARGE || !(level instanceof ServerLevel server)) {
            return false;
        }
        Slam slam = Slam.of(charge, BossWeapons.isAwakened(stack));
        Vec3 c = user.position();
        wave(server, user, c, slam);
        for (int i = 0; i < slam.tendrils(); i++) {
            double a = Math.PI * 2 * i / slam.tendrils() + server.getRandom().nextDouble() * 0.5;
            double r = 1.5 + server.getRandom().nextDouble() * (slam.radius() - 1.5);
            BlockPos pos = BlockPos.containing(c.x + Math.cos(a) * r, c.y, c.z + Math.sin(a) * r);
            BossWeapons.plantTendril(server, pos, user, 40);
        }
        server.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.2, c.z, slam.full() ? 3 : 1, 0.6, 0.1, 0.6, 0);
        server.playSound(null, user.blockPosition(), slam.full() ? SoundEvents.MACE_SMASH_GROUND_HEAVY : SoundEvents.MACE_SMASH_GROUND,
                SoundSource.PLAYERS, slam.full() ? 1.6f : 1.1f, slam.full() ? 0.7f : 0.9f);
        server.playSound(null, user.blockPosition(), SoundEvents.WARDEN_ATTACK_IMPACT, SoundSource.PLAYERS, slam.full() ? 1.2f : 0.7f, 0.8f);
        if (slam.full()) {                                         // 蓄滿：中心一聲音爆
            server.sendParticles(ParticleTypes.SONIC_BOOM, c.x, c.y + 0.6, c.z, 1, 0, 0, 0, 0);
            server.playSound(null, user.blockPosition(), SoundEvents.WARDEN_SONIC_BOOM, SoundSource.PLAYERS, 0.8f, 1.1f);
        }
        if (user instanceof Player player) {
            player.getCooldowns().addCooldown(stack, slam.cooldown());
            stack.hurtAndBreak(1, player, player.getUsedItemHand() == InteractionHand.OFF_HAND ? EquipmentSlot.OFFHAND : EquipmentSlot.MAINHAND);
        }
        return true;
    }

    /**
     * 震波：每 tick 往外推進 {@link #WAVE_SPEED} 格，地面上畫出波前（幽匿靈魂＋地面碎屑，蓄滿多一圈靈魂火），
     * 波前掃過的敵人受傷並被往外推（每隻只會被打一次）。
     */
    private static void wave(ServerLevel server, LivingEntity user, Vec3 c, Slam slam) {
        java.util.Set<LivingEntity> hit = new java.util.HashSet<>();
        var source = user instanceof Player p ? server.damageSources().playerAttack(p) : server.damageSources().mobAttack(user);
        double[] front = {0.0};
        BossWeapons.schedule(now -> {
            if (user.isRemoved() || user.level() != server) {
                return true;
            }
            double r1 = Math.min(slam.radius(), front[0] + WAVE_SPEED);
            front[0] = r1;
            ring(server, c, r1, ParticleTypes.SCULK_SOUL, 0.04, 0.0);
            if (slam.full()) {
                ring(server, c, r1, ParticleTypes.SOUL_FIRE_FLAME, 0.0, 0.5);
            }
            dust(server, c, r1);
            for (LivingEntity e : server.getEntitiesOfClass(LivingEntity.class, new AABB(c, c).inflate(r1 + 0.5, 2.5, r1 + 0.5),
                    e -> !hit.contains(e) && BossWeapons.isFoe(user, e))) {
                double dx = e.getX() - c.x, dz = e.getZ() - c.z;
                if (dx * dx + dz * dz > (r1 + 0.5) * (r1 + 0.5)) {
                    continue;
                }
                hit.add(e);
                if (e.hurtServer(server, source, slam.damage())) {
                    double len = Math.sqrt(dx * dx + dz * dz);
                    double nx = len < 1.0E-2 ? 0 : dx / len, nz = len < 1.0E-2 ? 0 : dz / len;
                    e.setDeltaMovement(e.getDeltaMovement().add(nx * slam.push(), slam.lift(), nz * slam.push()));
                    e.needsSync = true;
                    if (slam.full()) {
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1));
                    }
                }
            }
            return r1 >= slam.radius();
        });
    }

    /** 地面上一圈粒子：每 0.5 格一顆；speed 為往外飄的速度。 */
    private static void ring(ServerLevel server, Vec3 c, double radius, ParticleOptions particle, double speed, double phase) {
        int n = Math.max(8, (int) (radius * Math.PI * 2 / 0.5));
        for (int i = 0; i < n; i++) {
            double a = phase + Math.PI * 2 * i / n;
            double cos = Math.cos(a), sin = Math.sin(a);
            server.sendParticles(particle, c.x + cos * radius, c.y + 0.1, c.z + sin * radius, 0, cos, 0.15, sin, speed);
        }
    }

    /** 波前上被震起的地面碎屑（取波前底下的方塊）。 */
    private static void dust(ServerLevel server, Vec3 c, double radius) {
        int n = Math.max(4, (int) (radius * 2));
        for (int i = 0; i < n; i++) {
            double a = server.getRandom().nextDouble() * Math.PI * 2;
            double x = c.x + Math.cos(a) * radius, z = c.z + Math.sin(a) * radius;
            BlockState state = server.getBlockState(BlockPos.containing(x, c.y - 0.5, z));
            if (!state.isAir()) {
                server.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state), x, c.y + 0.1, z, 3, 0.15, 0.05, 0.15, 0.15);
            }
        }
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        return BossWeapons.isAwakened(stack) || super.isFoil(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> out, TooltipFlag flag) {
        boolean awakened = BossWeapons.isAwakened(stack);
        out.accept(Component.translatable(awakened ? "tooltip.pysift.sculk_hammer.use_awakened" : "tooltip.pysift.sculk_hammer.use"));
        out.accept(Component.translatable("tooltip.pysift.sculk_hammer.tendrils"));
        if (awakened) {
            out.accept(Component.translatable("tooltip.pysift.awakened"));
        } else {
            out.accept(Component.translatable("tooltip.pysift.sculk_hammer.how_to_awaken").withStyle(net.minecraft.ChatFormatting.DARK_GRAY));
        }
    }
}
