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
 *   <li>右鍵：沿視線發射 15 格音爆，貫穿路上所有敵人造成 8 點傷害、冷卻 3 秒（覺醒：寬度加倍、12 點、冷卻 2 秒），遇到方塊停止。</li>
 *   <li>左鍵命中：連鎖攻擊目標附近 6 格內的 3 個敵人各 3 點（覺醒 5 個、各 4 點），連同主目標都附加靈魂剝奪。</li>
 * </ul>
 */
public class SonicStaffItem extends Item {
    private static final double RANGE = 15.0;
    private static final int COOLDOWN = 60;            // awakened: 40

    public SonicStaffItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player.getCooldowns().isOnCooldown(stack)) {
            return InteractionResult.PASS;
        }
        if (level instanceof ServerLevel server) {
            boolean awakened = BossWeapons.isAwakened(stack);
            beam(server, player, awakened ? 1.6 : 0.9, awakened ? 12.0f : 8.0f);
            player.getCooldowns().addCooldown(stack, awakened ? 40 : COOLDOWN);
            stack.hurtAndBreak(1, player, hand == InteractionHand.MAIN_HAND ? EquipmentSlot.MAINHAND : EquipmentSlot.OFFHAND);
        }
        return InteractionResult.SUCCESS;
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
