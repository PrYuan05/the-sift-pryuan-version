package pryuan05.pysift.entity.mob;

import java.util.List;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftMonsterEntity;
import pryuan05.pysift.entity.ai.SkillGoal;

/**
 * 冠羽哨兵（遺跡武士，手持重刃）。
 * <ul>
 *   <li>重劈：目標在 3 格內時蓄力 0.8 秒（動畫 slash），12 點傷害並強力擊退；若目標正在舉盾，盾牌被粉碎（進入 3 秒冷卻）。冷卻 3 秒。</li>
 *   <li>其餘時間一般近戰（動畫 attack）。</li>
 * </ul>
 */
public class SentinelEntity extends PysiftMonsterEntity {
    /** 體型倍率（原版 SCALE 屬性）：模型本身約 0.89 格高，放大到約 1.8 格。 */
    private static final double SCALE = 1.8 / (14.25 / 16.0);
    public SentinelEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 50.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.75)
                .add(Attributes.ATTACK_DAMAGE, 7.0)
                .add(Attributes.ARMOR, 6.0)
                .add(Attributes.SCALE, SCALE);          // 模型 0.89 格高 → 約 1.8 格
    }

    @Override
    protected void registerGoals() {
        super.registerGoals();
        this.goalSelector.addGoal(1, new SkillGoal(this, "slash", 16, 26, 60, 0.0, 3.0, false, this::heavySlash));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("slash", "attack");
    }

    @Override
    protected String meleeAnimation() {
        return "attack";
    }

    private void heavySlash(ServerLevel level, LivingEntity target) {
        this.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 1.5f, 0.6f);
        Vec3 forward = Vec3.directionFromRotation(0.0f, this.getYRot());
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, this.getX() + forward.x * 1.5, this.getY(0.6), this.getZ() + forward.z * 1.5,
                1, 0, 0, 0, 0);
        if (target == null || !target.isAlive() || this.distanceTo(target) > 3.5 + target.getBbWidth() / 2) {
            return;
        }
        if (target instanceof Player player && player.isBlocking()) {
            ItemStack shield = player.getItemBlockingWith();
            if (shield != null) {
                player.getCooldowns().addCooldown(shield, 60);
            }
            player.stopUsingItem();
            this.playSound(SoundEvents.SHIELD_BREAK.value(), 1.0f, 0.8f);
        }
        if (target.hurtServer(level, this.damageSources().mobAttack(this), 12.0f)) {
            Vec3 away = target.position().subtract(this.position()).multiply(1, 0, 1);
            Vec3 dir = away.lengthSqr() < 1.0E-4 ? forward : away.normalize();
            target.setDeltaMovement(target.getDeltaMovement().add(dir.x * 1.2, 0.4, dir.z * 1.2));
            target.needsSync = true;
        }
    }
}
