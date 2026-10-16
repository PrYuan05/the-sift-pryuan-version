package pryuan05.pysift.entity.ai;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftGeoEntity;

/**
 * 遠程音波（仿 Warden 的 sonic boom）：蓄力期間播放 {@code chargeAnimation}，命中時切換成 {@code releaseAnimation}，
 * 沿視線畫出音波粒子，對目標造成無視護甲的 sonicBoom 傷害並擊退。需要視線，且目標必須在射程內。
 */
public class SonicBeamGoal extends TimedSkillGoal {
    private final String releaseAnimation;
    private final double range;
    private final float damage;

    public SonicBeamGoal(PysiftGeoEntity mob, String chargeAnimation, String releaseAnimation, int impactTick, int totalTicks,
                         int cooldownTicks, double minRange, double range, float damage) {
        super(mob, chargeAnimation, impactTick, totalTicks, cooldownTicks, minRange, range, true);
        this.releaseAnimation = releaseAnimation;
        this.range = range;
        this.damage = damage;
    }

    @Override
    protected void onStart() {
        mob.playSound(SoundEvents.WARDEN_SONIC_CHARGE, 3.0f, 1.0f);
    }

    @Override
    protected void perform(ServerLevel level, LivingEntity t) {
        mob.triggerAnim("skill", releaseAnimation);
        if (t == null || !t.isAlive() || mob.distanceTo(t) > range + 2 || !mob.hasLineOfSight(t)) {
            return;   // 目標在蓄力時躲開了
        }
        Vec3 from = mob.position().add(0, mob.getBbHeight() * 0.75, 0);
        Vec3 to = t.getEyePosition();
        Vec3 step = to.subtract(from);
        Vec3 dir = step.normalize();
        int n = Math.max(1, (int) Math.ceil(step.length()));
        for (int i = 1; i <= n; i++) {
            Vec3 p = from.add(dir.scale(i));
            level.sendParticles(ParticleTypes.SONIC_BOOM, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
        mob.playSound(SoundEvents.WARDEN_SONIC_BOOM, 3.0f, 1.0f);
        if (t.hurtServer(level, mob.damageSources().sonicBoom(mob), damage)) {
            t.setDeltaMovement(t.getDeltaMovement().add(dir.x * 1.6, 0.4, dir.z * 1.6));
            t.needsSync = true;
        }
    }
}
