package pryuan05.pysift.entity.ai;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftGeoEntity;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

/**
 * 共鳴環：命中時從自身放出一圈音波，在 {@code expandTicks} tick 內從 startRadius 擴散到 endRadius。
 * 環經過的非敵對生物各受一次傷害並被往外推；站在環內側或外側都不會被打到，可以跳過或躲開。
 */
public class ResonanceRingGoal extends TimedSkillGoal {
    private final double startRadius;
    private final double endRadius;
    private final int expandTicks;
    private final float damage;
    private final Set<UUID> hit = new HashSet<>();
    private Vec3 centre = Vec3.ZERO;

    public ResonanceRingGoal(PysiftGeoEntity mob, String animation, int impactTick, int cooldownTicks, double triggerRange,
                             double startRadius, double endRadius, int expandTicks, float damage) {
        super(mob, animation, impactTick, impactTick + expandTicks, cooldownTicks, 0.0, triggerRange, false);
        this.startRadius = startRadius;
        this.endRadius = endRadius;
        this.expandTicks = expandTicks;
        this.damage = damage;
    }

    @Override
    protected void perform(ServerLevel level, LivingEntity t) {
        hit.clear();
        centre = mob.position();
        mob.playSound(SoundEvents.WARDEN_SONIC_BOOM, 3.0f, 0.7f);
        ring(level, startRadius);
    }

    @Override
    protected void onAfterImpact(ServerLevel level, int ticksSinceImpact) {
        double r = startRadius + (endRadius - startRadius) * Math.min(1.0, ticksSinceImpact / (double) expandTicks);
        ring(level, r);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class,
                new AABB(centre.x - r - 1, centre.y - 1, centre.z - r - 1, centre.x + r + 1, centre.y + 3, centre.z + r + 1),
                e -> e != mob && e.isAlive() && !(e instanceof Enemy) && !hit.contains(e.getUUID()))) {
            double d = Math.sqrt(e.distanceToSqr(centre.x, e.getY(), centre.z));
            if (Math.abs(d - r) > 0.9 || e.getY() > centre.y + 1.6) {
                continue;   // not on the ring, or jumped over it
            }
            hit.add(e.getUUID());
            if (e.hurtServer(level, mob.damageSources().sonicBoom(mob), damage)) {
                Vec3 out = e.position().subtract(centre).multiply(1, 0, 1).normalize();
                e.setDeltaMovement(e.getDeltaMovement().add(out.x * 0.8, 0.3, out.z * 0.8));
                e.needsSync = true;
            }
        }
    }

    private void ring(ServerLevel level, double r) {
        int n = Math.max(12, (int) (r * 8));
        for (int i = 0; i < n; i++) {
            double a = i * Math.PI * 2 / n;
            level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, centre.x + Math.cos(a) * r, centre.y + 0.3, centre.z + Math.sin(a) * r,
                    1, 0, 0.05, 0, 0.0);
        }
    }
}
