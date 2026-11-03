package pryuan05.pysift.progression;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
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
import net.minecraft.world.phys.Vec3;

import java.util.function.Consumer;

/**
 * 重錘（幽匿巨怪之心製成）：按住右鍵蓄力（至少 0.75 秒，最多 2 秒），放開後砸地：
 * 半徑 4 格（覺醒 6 格）內的敵人受到 8–12 點傷害並被擊飛，周圍長出 4 條（覺醒 7 條）幽匿藤蔓，
 * 2 秒後各自爆炸並造成靈魂剝奪（{@link BossWeapons#plantTendril}）。冷卻 3 秒。
 */
public class SculkHammerItem extends Item {
    /** 物品模型 sculk_hammer_charging_* 依同樣的時間換階段（build_weapon_models.py）。 */
    public static final int MIN_CHARGE = 15;
    public static final int FULL_CHARGE = 40;
    private static final int COOLDOWN = 60;

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
        boolean awakened = BossWeapons.isAwakened(stack);
        double radius = awakened ? 6.0 : 4.0;
        float power = Mth.clamp((float) charge / FULL_CHARGE, 0.0f, 1.0f);
        float damage = 8.0f + 4.0f * power;
        Vec3 c = user.position();
        for (LivingEntity e : server.getEntitiesOfClass(LivingEntity.class, user.getBoundingBox().inflate(radius, 2.0, radius),
                e -> BossWeapons.isFoe(user, e) && e.distanceToSqr(c) <= radius * radius)) {
            if (e.hurtServer(server, user instanceof Player p ? server.damageSources().playerAttack(p) : server.damageSources().mobAttack(user), damage)) {
                Vec3 away = e.position().subtract(c).multiply(1, 0, 1);
                Vec3 dir = away.lengthSqr() < 1.0E-4 ? Vec3.ZERO : away.normalize();
                e.setDeltaMovement(e.getDeltaMovement().add(dir.x * (1.0 + power), 0.5 + 0.3 * power, dir.z * (1.0 + power)));
                e.needsSync = true;
            }
        }
        int tendrils = awakened ? 7 : 4;
        for (int i = 0; i < tendrils; i++) {
            double a = Math.PI * 2 * i / tendrils + server.getRandom().nextDouble() * 0.5;
            double r = 2.0 + server.getRandom().nextDouble() * (radius - 2.0);
            BlockPos pos = BlockPos.containing(c.x + Math.cos(a) * r, c.y, c.z + Math.sin(a) * r);
            BossWeapons.plantTendril(server, pos, user, 40);
        }
        server.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.2, c.z, 3, radius * 0.4, 0.1, radius * 0.4, 0);
        server.sendParticles(ParticleTypes.SCULK_SOUL, c.x, c.y + 0.3, c.z, 30, radius * 0.5, 0.2, radius * 0.5, 0.05);
        server.playSound(null, user.blockPosition(), SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.PLAYERS, 1.5f, 0.7f);
        server.playSound(null, user.blockPosition(), SoundEvents.WARDEN_ATTACK_IMPACT, SoundSource.PLAYERS, 1.0f, 0.8f);
        if (user instanceof Player player) {
            player.getCooldowns().addCooldown(stack, COOLDOWN);
            stack.hurtAndBreak(1, player, player.getUsedItemHand() == InteractionHand.OFF_HAND ? EquipmentSlot.OFFHAND : EquipmentSlot.MAINHAND);
        }
        return true;
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
