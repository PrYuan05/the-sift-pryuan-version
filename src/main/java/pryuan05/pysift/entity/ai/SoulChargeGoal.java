package pryuan05.pysift.entity.ai;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.effect.ModEffects;
import pryuan05.pysift.entity.PysiftGeoEntity;

/**
 * 靈魂火衝撞＋重拳（Sculk Monstrosity）：{@link ChargeGoal} 的衝刺途中全身冒出靈魂火；
 * 衝刺停下後右拳點燃（動畫 {@code punchAnimation}），{@link #PUNCH_WINDUP} tick 後揮出重拳——
 * 前方 {@code punchRange} 格內的非敵對生物受 {@code punchDamage} 傷害、被擊飛，並附上靈魂剝奪與 4 秒火焰。
 */
public class SoulChargeGoal extends ChargeGoal {
    private static final int PUNCH_WINDUP = 14;
    private final String punchAnimation;
    private final double punchRange;
    private final float punchDamage;
    private boolean punchStarted;
    private boolean punched;

    public SoulChargeGoal(PysiftGeoEntity mob, String animation, String punchAnimation, int windUpTicks, int dashTicks, int recoverTicks,
                          int cooldownTicks, double minRange, double maxRange, double speed, float damage, double knockback,
                          double punchRange, float punchDamage) {
        super(mob, animation, windUpTicks, dashTicks, recoverTicks, cooldownTicks, minRange, maxRange, speed, damage, knockback);
        this.punchAnimation = punchAnimation;
        this.punchRange = punchRange;
        this.punchDamage = punchDamage;
    }

    @Override
    protected void onStart() {
        super.onStart();
        punchStarted = false;
        punched = false;
    }

    @Override
    protected void onAfterImpact(ServerLevel level, int ticks) {
        super.onAfterImpact(level, ticks);
        if (!finished) {
            // 衝刺中：全身靈魂火
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, mob.getX(), mob.getY(0.5), mob.getZ(), 6,
                    mob.getBbWidth() * 0.4, mob.getBbHeight() * 0.3, mob.getBbWidth() * 0.4, 0.02);
            return;
        }
        int since = ticks - stoppedAt;
        if (!punchStarted && since >= 2) {
            punchStarted = true;
            mob.triggerAnim("skill", punchAnimation);
            mob.playSound(SoundEvents.BLAZE_SHOOT, 1.5f, 0.6f);
        }
        if (punchStarted && !punched) {
            Vec3 fist = fistPosition();
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, fist.x, fist.y, fist.z, 4, 0.3, 0.3, 0.3, 0.02);
            if (since >= 2 + PUNCH_WINDUP) {
                punched = true;
                punch(level);
            }
        }
    }

    private Vec3 fistPosition() {
        Vec3 fwd = Vec3.directionFromRotation(0, mob.getYRot());
        return mob.position().add(fwd.scale(mob.getBbWidth() * 0.6)).add(0, mob.getBbHeight() * 0.45, 0);
    }

    private void punch(ServerLevel level) {
        Vec3 fwd = Vec3.directionFromRotation(0, mob.getYRot());
        Vec3 c = mob.position();
        mob.playSound(SoundEvents.WARDEN_ATTACK_IMPACT, 2.5f, 0.5f);
        Vec3 fist = fistPosition();
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, fist.x, fist.y, fist.z, 40, 0.8, 0.8, 0.8, 0.15);
        level.sendParticles(ParticleTypes.EXPLOSION, fist.x, fist.y, fist.z, 1, 0, 0, 0, 0);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, mob.getBoundingBox().inflate(punchRange),
                e -> e != mob && e.isAlive() && !(e instanceof Enemy))) {
            Vec3 to = e.position().subtract(c).multiply(1, 0, 1);
            if (to.length() > punchRange + mob.getBbWidth() * 0.5 || (to.lengthSqr() > 1.0E-4 && fwd.dot(to.normalize()) < 0.3)) {
                continue;   // 只打前方
            }
            if (e.hurtServer(level, mob.damageSources().mobAttack(mob), punchDamage)) {
                e.setDeltaMovement(e.getDeltaMovement().add(fwd.x * 1.6, 0.6, fwd.z * 1.6));
                e.needsSync = true;
                e.addEffect(new MobEffectInstance(ModEffects.SOUL_DEPRIVATION, 160, 0), mob);
                e.igniteForSeconds(4.0f);
            }
        }
    }
}
