package pryuan05.pysift.entity.ai;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftGeoEntity;

/**
 * 音波錐：朝目標方向放出扇形音波，範圍內（距離 ≤ range、與朝向夾角 ≤ halfAngle）的非敵對生物受到 sonicBoom 傷害並被往外推。
 */
public class SonicConeGoal extends TimedSkillGoal {
    private final double range;
    private final double halfAngleCos;
    private final float damage;
    private final double push;

    public SonicConeGoal(PysiftGeoEntity mob, String animation, int impactTick, int totalTicks, int cooldownTicks,
                         double range, double halfAngleDegrees, float damage, double push) {
        super(mob, animation, impactTick, totalTicks, cooldownTicks, 0.0, range, true);
        this.range = range;
        this.halfAngleCos = Math.cos(Math.toRadians(halfAngleDegrees));
        this.damage = damage;
        this.push = push;
    }

    @Override
    protected void perform(ServerLevel level, LivingEntity t) {
        Vec3 origin = mob.position().add(0, mob.getBbHeight() * 0.6, 0);
        Vec3 aim = (t != null && t.isAlive() ? t.position().add(0, t.getBbHeight() * 0.5, 0).subtract(origin) : mob.getLookAngle());
        Vec3 dir = aim.multiply(1, 0.3, 1).normalize();
        for (double a = -1; a <= 1.001; a += 0.5) {                     // five rays of particles across the cone
            double yaw = Math.acos(halfAngleCos) * a;
            Vec3 ray = new Vec3(dir.x * Math.cos(yaw) - dir.z * Math.sin(yaw), dir.y, dir.x * Math.sin(yaw) + dir.z * Math.cos(yaw));
            for (int i = 1; i <= (int) range; i += 2) {
                Vec3 p = origin.add(ray.scale(i));
                level.sendParticles(ParticleTypes.SONIC_BOOM, p.x, p.y, p.z, 1, 0, 0, 0, 0);
            }
        }
        mob.playSound(SoundEvents.WARDEN_SONIC_BOOM, 3.0f, 1.3f);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(mob.blockPosition()).inflate(range),
                e -> e != mob && e.isAlive() && !(e instanceof Enemy))) {
            Vec3 to = e.position().add(0, e.getBbHeight() * 0.5, 0).subtract(origin);
            double dist = to.length();
            if (dist > range || dist < 1.0E-3 || to.normalize().dot(dir) < halfAngleCos) {
                continue;
            }
            if (e.hurtServer(level, mob.damageSources().sonicBoom(mob), damage)) {
                Vec3 out = to.multiply(1, 0, 1).normalize();
                e.setDeltaMovement(e.getDeltaMovement().add(out.x * push, 0.35, out.z * push));
                e.needsSync = true;
            }
        }
    }
}
