package pryuan05.pysift.entity.ai;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftGeoEntity;

/**
 * 衝撞：前搖 {@code windUpTicks} tick（原地刨地、冒煙，鎖定方向），之後沿直線高速衝刺最多 {@code dashTicks} tick。
 * <ul>
 *   <li>衝刺途中撞到的第一個非敵對生物受 {@code damage} 傷害並被沿衝刺方向撞飛（{@code knockback}）。</li>
 *   <li>撞到牆會立刻停下並發出撞擊聲；撞到人或牆後還有一段收招時間，這段時間是反擊的破綻。</li>
 *   <li>方向在前搖結束時鎖定，所以目標可以在衝刺開始後側閃躲開。</li>
 * </ul>
 */
public class ChargeGoal extends TimedSkillGoal {
    private final int dashTicks;
    private final double speed;
    private final float damage;
    private final double knockback;
    private Vec3 direction;
    private boolean finished;

    public ChargeGoal(PysiftGeoEntity mob, String animation, int windUpTicks, int dashTicks, int recoverTicks, int cooldownTicks,
                      double minRange, double maxRange, double speed, float damage, double knockback) {
        super(mob, animation, windUpTicks, windUpTicks + dashTicks + recoverTicks, cooldownTicks, minRange, maxRange, true);
        this.dashTicks = dashTicks;
        this.speed = speed;
        this.damage = damage;
        this.knockback = knockback;
    }

    @Override
    protected void onStart() {
        direction = null;
        finished = false;
        mob.playSound(SoundEvents.RAVAGER_STEP, 1.5f, 0.6f);
    }

    @Override
    protected void onWindUp(ServerLevel level, int tick) {
        if (tick % 3 == 0) {   // 刨地揚起的塵土
            level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, mob.getX(), mob.getY() + 0.1, mob.getZ(),
                    2, mob.getBbWidth() * 0.4, 0.05, mob.getBbWidth() * 0.4, 0.01);
        }
    }

    @Override
    protected void perform(ServerLevel level, LivingEntity target) {
        Vec3 to = target != null ? target.position().subtract(mob.position()).multiply(1, 0, 1) : Vec3.ZERO;
        direction = to.lengthSqr() > 1.0E-4 ? to.normalize() : Vec3.directionFromRotation(0, mob.getYRot());
        mob.playSound(SoundEvents.RAVAGER_ROAR, 1.5f, 1.2f);
    }

    @Override
    protected void onAfterImpact(ServerLevel level, int ticks) {
        if (finished || direction == null) {
            return;
        }
        if (ticks > dashTicks) {
            finished = true;
            return;
        }
        float yaw = (float) (Mth.atan2(direction.z, direction.x) * Mth.RAD_TO_DEG) - 90.0f;
        mob.setYRot(yaw);
        mob.setYBodyRot(yaw);
        mob.setYHeadRot(yaw);
        mob.setDeltaMovement(direction.x * speed, mob.getDeltaMovement().y, direction.z * speed);
        mob.needsSync = true;
        if (ticks % 2 == 0) {
            level.sendParticles(ParticleTypes.CLOUD, mob.getX(), mob.getY() + 0.2, mob.getZ(), 1, 0.2, 0.05, 0.2, 0.0);
        }
        for (LivingEntity victim : level.getEntitiesOfClass(LivingEntity.class, mob.getBoundingBox().inflate(0.4),
                e -> e != mob && e.isAlive() && !(e instanceof Enemy))) {
            if (victim.hurtServer(level, mob.damageSources().mobAttack(mob), damage)) {
                victim.push(direction.x * knockback, 0.35 + knockback * 0.15, direction.z * knockback);
                victim.needsSync = true;
            }
            stop(level, SoundEvents.PLAYER_ATTACK_KNOCKBACK);
            return;
        }
        if (mob.horizontalCollision) {
            stop(level, SoundEvents.ANVIL_LAND);
            level.sendParticles(ParticleTypes.EXPLOSION, mob.getX() + direction.x * mob.getBbWidth() * 0.5,
                    mob.getY(0.5), mob.getZ() + direction.z * mob.getBbWidth() * 0.5, 1, 0, 0, 0, 0);
        }
    }

    private void stop(ServerLevel level, net.minecraft.sounds.SoundEvent sound) {
        finished = true;
        mob.setDeltaMovement(mob.getDeltaMovement().multiply(0.1, 1, 0.1));
        mob.playSound(sound, 1.5f, 0.8f);
    }
}
