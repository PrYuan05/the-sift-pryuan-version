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
 * 紫色漩渦球＋砸地（Harmonizer）：在自己前方、朝目標方向召出一顆紫色漩渦球，前搖期間把 {@code pullRadius} 格內
 * 站在地上的非敵對生物往球心吸（一直跳就不會被吸走）；時間到時整個身體砸在球的位置上，半徑 {@code slamRadius}
 * 格 {@code damage} 點傷害並擊飛。
 */
public class VortexGoal extends TimedSkillGoal {
    private final double orbDistance;
    private final double pullRadius;
    private final double slamRadius;
    private final float damage;
    private Vec3 orb = Vec3.ZERO;

    public VortexGoal(PysiftGeoEntity mob, String animation, int impactTick, int totalTicks, int cooldownTicks, double maxRange,
                      double orbDistance, double pullRadius, double slamRadius, float damage) {
        super(mob, animation, impactTick, totalTicks, cooldownTicks, 0.0, maxRange, true);
        this.orbDistance = orbDistance;
        this.pullRadius = pullRadius;
        this.slamRadius = slamRadius;
        this.damage = damage;
    }

    @Override
    protected void onStart() {
        Vec3 dir = target != null ? target.position().subtract(mob.position()).multiply(1, 0, 1) : Vec3.ZERO;
        dir = dir.lengthSqr() > 1.0E-4 ? dir.normalize() : Vec3.directionFromRotation(0, mob.getYRot());
        orb = mob.position().add(dir.scale(orbDistance)).add(0, 1.2, 0);
        mob.playSound(SoundEvents.PORTAL_TRIGGER, 2.0f, 1.4f);
    }

    @Override
    protected void onWindUp(ServerLevel level, int tick) {
        // 漩渦球：一圈旋轉的紫色粒子
        double a = tick * 0.6;
        for (int i = 0; i < 6; i++) {
            double ang = a + i * Math.PI / 3;
            double r = 1.2 + 0.3 * Math.sin(tick * 0.3 + i);
            level.sendParticles(ParticleTypes.PORTAL, orb.x + Math.cos(ang) * r, orb.y + Math.sin(ang * 0.7) * 0.4, orb.z + Math.sin(ang) * r,
                    1, 0, 0, 0, 0);
        }
        level.sendParticles(ParticleTypes.WITCH, orb.x, orb.y, orb.z, 3, 0.3, 0.3, 0.3, 0.0);
        if (tick % 20 == 0) {
            mob.playSound(SoundEvents.BEACON_AMBIENT, 1.5f, 0.6f);
        }
        AABB box = new AABB(orb, orb).inflate(pullRadius);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box,
                e -> e != mob && e.isAlive() && !(e instanceof Enemy) && e.onGround())) {
            Vec3 to = orb.subtract(e.position()).multiply(1, 0, 1);
            double d = to.length();
            if (d > pullRadius || d < 0.6) {
                continue;
            }
            Vec3 pull = to.normalize().scale(0.09 + 0.05 * (1 - d / pullRadius));
            e.setDeltaMovement(e.getDeltaMovement().add(pull));
            e.needsSync = true;
        }
    }

    @Override
    protected void perform(ServerLevel level, LivingEntity ignored) {
        Vec3 ground = new Vec3(orb.x, mob.getY(), orb.z);
        GroundSlamGoal.slamAt(level, mob, ground, slamRadius, damage, 0.8, e -> !(e instanceof Enemy));
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, orb.x, orb.y, orb.z, 60, 1.5, 0.5, 1.5, 0.3);
    }
}
