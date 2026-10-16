package pryuan05.pysift.entity.ai;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftGeoEntity;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

/**
 * 地面衝擊波：命中時朝目標方向沿地面送出一道音波，每 tick 前進 {@code speed} 格、共 {@code length} 格；
 * 波頭附近（寬度 halfWidth）的非敵對生物各受一次傷害並被掀起。可以往側面閃避或跳過。
 */
public class GroundShockwaveGoal extends TimedSkillGoal {
    private final double length;
    private final double speed;
    private final double halfWidth;
    private final float damage;
    private final Set<UUID> hit = new HashSet<>();
    private Vec3 start = Vec3.ZERO;
    private Vec3 dir = Vec3.ZERO;

    public GroundShockwaveGoal(PysiftGeoEntity mob, String animation, int impactTick, int cooldownTicks, double minRange, double maxRange,
                               double length, double speed, double halfWidth, float damage) {
        super(mob, animation, impactTick, impactTick + (int) Math.ceil(length / speed), cooldownTicks, minRange, maxRange, true);
        this.length = length;
        this.speed = speed;
        this.halfWidth = halfWidth;
        this.damage = damage;
    }

    @Override
    protected void perform(ServerLevel level, LivingEntity t) {
        hit.clear();
        start = mob.position();
        Vec3 aim = t != null ? t.position().subtract(start) : mob.getLookAngle();
        dir = aim.multiply(1, 0, 1).normalize();
        mob.playSound(SoundEvents.WARDEN_SONIC_BOOM, 2.5f, 0.6f);
    }

    @Override
    protected void onAfterImpact(ServerLevel level, int ticksSinceImpact) {
        double d = Math.min(length, ticksSinceImpact * speed);
        Vec3 head = start.add(dir.scale(d));
        BlockState ground = level.getBlockState(BlockPos.containing(head.x, head.y - 0.5, head.z));
        if (!ground.isAir()) {
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), head.x, head.y + 0.2, head.z, 12, halfWidth * 0.6, 0.2, halfWidth * 0.6, 0.2);
        }
        level.sendParticles(ParticleTypes.SONIC_BOOM, head.x, head.y + 0.6, head.z, 1, 0, 0, 0, 0);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(head, head).inflate(halfWidth, 1.5, halfWidth),
                e -> e != mob && e.isAlive() && !(e instanceof Enemy) && !hit.contains(e.getUUID()))) {
            if (e.getY() > head.y + 1.2) {
                continue;   // jumped over the wave
            }
            hit.add(e.getUUID());
            if (e.hurtServer(level, mob.damageSources().sonicBoom(mob), damage)) {
                e.setDeltaMovement(e.getDeltaMovement().add(dir.x * 0.5, 0.6, dir.z * 0.5));
                e.needsSync = true;
            }
        }
    }
}
