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

import java.util.function.Predicate;
import pryuan05.pysift.entity.PysiftGeoEntity;

/**
 * 近戰砸地：以自身為中心的圓形範圍傷害，把範圍內的目標往外、往上擊飛，並噴出地面方塊的碎屑粒子。
 * 誰會受傷由 {@code victims} 決定；預設（敵對生物用）是「不是 Enemy 的生物」，中立守衛則改成只打 Enemy。
 */
public class GroundSlamGoal extends TimedSkillGoal {
    private final double radius;
    private final float damage;
    private final double launch;
    private final Predicate<LivingEntity> victims;

    public GroundSlamGoal(PysiftGeoEntity mob, String animation, int impactTick, int totalTicks, int cooldownTicks,
                          double triggerRange, double radius, float damage, double launch) {
        this(mob, animation, impactTick, totalTicks, cooldownTicks, triggerRange, radius, damage, launch, e -> !(e instanceof Enemy));
    }

    public GroundSlamGoal(PysiftGeoEntity mob, String animation, int impactTick, int totalTicks, int cooldownTicks,
                          double triggerRange, double radius, float damage, double launch, Predicate<LivingEntity> victims) {
        super(mob, animation, impactTick, totalTicks, cooldownTicks, 0.0, triggerRange, false);
        this.radius = radius;
        this.damage = damage;
        this.launch = launch;
        this.victims = victims;
    }

    @Override
    protected void perform(ServerLevel level, LivingEntity ignored) {
        slamAt(level, mob, mob.position(), radius, damage, launch, victims);
    }

    /**
     * 以 centre 為中心的砸地效果（也給跳躍砸地使用）：範圍內符合 victims（或是 mob 的目標）的生物受傷，往外、往上擊飛，
     * 並噴出地面方塊碎屑與爆炸粒子。
     */
    public static void slamAt(ServerLevel level, PysiftGeoEntity mob, Vec3 c, double radius, float damage, double launch,
                              Predicate<LivingEntity> victims) {
        AABB box = new AABB(c.x - radius, c.y - 1, c.z - radius, c.x + radius, c.y + 3, c.z + radius);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box,
                e -> e != mob && e.isAlive() && (victims.test(e) || e == mob.getTarget()) && e.distanceToSqr(c) <= radius * radius)) {
            if (e.hurtServer(level, mob.damageSources().mobAttack(mob), damage)) {
                Vec3 away = e.position().subtract(c).multiply(1, 0, 1);
                Vec3 dir = away.lengthSqr() < 1.0E-4 ? Vec3.ZERO : away.normalize();
                e.setDeltaMovement(e.getDeltaMovement().add(dir.x * 0.6, launch, dir.z * 0.6));
                e.needsSync = true;
            }
        }
        mob.playSound(SoundEvents.WARDEN_ATTACK_IMPACT, 2.0f, 0.6f);
        BlockState ground = level.getBlockState(BlockPos.containing(c.x, c.y - 0.5, c.z));
        for (int i = 0; i < 48; i++) {
            double a = i * (Math.PI * 2 / 48);
            double r = radius * (0.4 + 0.6 * level.getRandom().nextDouble());
            if (!ground.isAir()) {
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground),
                        c.x + Math.cos(a) * r, c.y + 0.1, c.z + Math.sin(a) * r, 2, 0.2, 0.1, 0.2, 0.15);
            }
        }
        level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.2, c.z, 3, radius * 0.3, 0.1, radius * 0.3, 0.0);
    }
}
