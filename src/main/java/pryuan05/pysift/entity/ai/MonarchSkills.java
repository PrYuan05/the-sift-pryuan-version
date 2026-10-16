package pryuan05.pysift.entity.ai;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftGeoEntity;
import pryuan05.pysift.entity.projectile.MonarchFeatherEntity;

/**
 * Monarch 的移動型招式（它的模型沒有手臂骨骼，斬擊用身體、披風、頂冠的旋轉表現）：
 * <ul>
 *   <li>{@link DashStrike} 衝刺迴旋斬：後拉蓄力後沿直線迴旋衝刺，途中碰到的人受傷；衝刺路徑上留下羽毛，5 秒後射向玩家。</li>
 *   <li>{@link HoverLoop} 繞圈旋轉：朝目標高速旋轉撲過去，落點周圍的圓上留下 8 根羽毛，5 秒後射向玩家。</li>
 *   <li>{@link Calamity} 三段災厄連擊：前方斬擊 → 迴旋衝刺 → 再一次斬擊。</li>
 * </ul>
 * 共用 {@link #slash}（前方扇形斬擊）、{@link #contact}（迴旋衝刺的接觸傷害，每個目標每招只吃一次）。
 */
public final class MonarchSkills {
    /** 羽毛懸停多久才射出（5 秒）。 */
    public static final int FEATHER_ARM_TICKS = 100;

    private MonarchSkills() {
    }

    private static void face(PysiftGeoEntity mob, Vec3 dir) {
        float yaw = (float) (Mth.atan2(dir.z, dir.x) * Mth.RAD_TO_DEG) - 90.0f;
        mob.setYRot(yaw);
        mob.setYBodyRot(yaw);
        mob.setYHeadRot(yaw);
    }

    private static Vec3 lockDirection(PysiftGeoEntity mob, LivingEntity target) {
        Vec3 to = target != null ? target.position().subtract(mob.position()).multiply(1, 0, 1) : Vec3.ZERO;
        return to.lengthSqr() > 1.0E-4 ? to.normalize() : Vec3.directionFromRotation(0, mob.getYRot());
    }

    /** 前方扇形斬擊：半徑 radius、夾角 cos ≥ minDot 內的非敵對生物受傷並被往外擊退。 */
    public static void slash(ServerLevel level, PysiftGeoEntity mob, double radius, float damage, double minDot) {
        Vec3 fwd = Vec3.directionFromRotation(0, mob.getYRot());
        mob.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 2.0f, 0.6f);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, mob.getX() + fwd.x * radius * 0.6, mob.getY(0.45), mob.getZ() + fwd.z * radius * 0.6,
                2, radius * 0.25, 0.2, radius * 0.25, 0);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, mob.getBoundingBox().inflate(radius),
                e -> e != mob && e.isAlive() && !(e instanceof Enemy))) {
            Vec3 to = e.position().subtract(mob.position()).multiply(1, 0, 1);
            if (to.length() > radius + mob.getBbWidth() * 0.5 || (to.lengthSqr() > 1.0E-4 && fwd.dot(to.normalize()) < minDot)) {
                continue;
            }
            if (e.hurtServer(level, mob.damageSources().mobAttack(mob), damage)) {
                Vec3 out = to.lengthSqr() < 1.0E-4 ? fwd : to.normalize();
                e.setDeltaMovement(e.getDeltaMovement().add(out.x * 1.0, 0.35, out.z * 1.0));
                e.needsSync = true;
            }
        }
    }

    /** 迴旋衝刺中的接觸傷害：碰到的非敵對生物各受一次傷害。 */
    public static void contact(ServerLevel level, PysiftGeoEntity mob, Set<UUID> hit, float damage) {
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, mob.getX(), mob.getY(0.45), mob.getZ(), 1, 0.3, 0.1, 0.3, 0);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, mob.getBoundingBox().inflate(0.6),
                e -> e != mob && e.isAlive() && !(e instanceof Enemy) && !hit.contains(e.getUUID()))) {
            hit.add(e.getUUID());
            if (e.hurtServer(level, mob.damageSources().mobAttack(mob), damage)) {
                Vec3 out = e.position().subtract(mob.position()).multiply(1, 0, 1);
                out = out.lengthSqr() < 1.0E-4 ? Vec3.ZERO : out.normalize();
                e.setDeltaMovement(e.getDeltaMovement().add(out.x * 0.9, 0.4, out.z * 0.9));
                e.needsSync = true;
            }
        }
    }

    public static void feather(ServerLevel level, PysiftGeoEntity mob, Vec3 at) {
        level.addFreshEntity(new MonarchFeatherEntity(level, mob, at, FEATHER_ARM_TICKS));
        level.sendParticles(ParticleTypes.END_ROD, at.x, at.y, at.z, 3, 0.1, 0.1, 0.1, 0.02);
    }

    // ------------------------------------------------------------------ dash strike
    public static class DashStrike extends TimedSkillGoal {
        private final int dashTicks;
        private final double speed;
        private final float damage;
        private final Set<UUID> hit = new HashSet<>();
        private final List<Vec3> path = new ArrayList<>();
        private Vec3 dir = Vec3.ZERO;

        public DashStrike(PysiftGeoEntity mob, String animation, int windUp, int dashTicks, int recover, int cooldown,
                          double minRange, double maxRange, double speed, float damage) {
            super(mob, animation, windUp, windUp + dashTicks + recover, cooldown, minRange, maxRange, true);
            this.dashTicks = dashTicks;
            this.speed = speed;
            this.damage = damage;
        }

        @Override
        protected void perform(ServerLevel level, LivingEntity t) {
            hit.clear();
            path.clear();
            dir = lockDirection(mob, t);
            mob.playSound(SoundEvents.PHANTOM_SWOOP, 2.0f, 0.7f);
        }

        @Override
        protected void onAfterImpact(ServerLevel level, int ticks) {
            if (ticks <= dashTicks) {
                face(mob, dir);
                mob.setDeltaMovement(dir.x * speed, mob.getDeltaMovement().y, dir.z * speed);
                mob.needsSync = true;
                contact(level, mob, hit, damage);
                if (ticks % 2 == 0) {
                    path.add(mob.position().add(0, mob.getBbHeight() * 0.4, 0));
                }
            } else if (ticks == dashTicks + 1) {
                mob.setDeltaMovement(mob.getDeltaMovement().multiply(0.1, 1, 0.1));
                for (Vec3 p : path) {
                    feather(level, mob, p);
                }
            }
        }
    }

    // ------------------------------------------------------------------ hover loop
    public static class HoverLoop extends TimedSkillGoal {
        private final int spinTicks;
        private final double speed;
        private final float damage;
        private final double ringRadius;
        private final Set<UUID> hit = new HashSet<>();
        private Vec3 goal = Vec3.ZERO;

        public HoverLoop(PysiftGeoEntity mob, String animation, int windUp, int spinTicks, int recover, int cooldown,
                         double minRange, double maxRange, double speed, float damage, double ringRadius) {
            super(mob, animation, windUp, windUp + spinTicks + recover, cooldown, minRange, maxRange, true);
            this.spinTicks = spinTicks;
            this.speed = speed;
            this.damage = damage;
            this.ringRadius = ringRadius;
        }

        @Override
        protected void perform(ServerLevel level, LivingEntity t) {
            hit.clear();
            goal = t != null ? t.position() : mob.position();
            mob.playSound(SoundEvents.PHANTOM_FLAP, 2.0f, 0.5f);
        }

        @Override
        protected void onAfterImpact(ServerLevel level, int ticks) {
            if (ticks <= spinTicks) {
                Vec3 to = goal.subtract(mob.position()).multiply(1, 0, 1);
                if (to.length() > 1.0) {
                    Vec3 dir = to.normalize();
                    mob.setDeltaMovement(dir.x * speed, mob.getDeltaMovement().y, dir.z * speed);
                    mob.needsSync = true;
                } else {
                    mob.setDeltaMovement(mob.getDeltaMovement().multiply(0.3, 1, 0.3));
                }
                contact(level, mob, hit, damage);
                level.sendParticles(ParticleTypes.CLOUD, mob.getX(), mob.getY() + 0.2, mob.getZ(), 2, 0.6, 0.05, 0.6, 0.01);
            } else if (ticks == spinTicks + 1) {
                mob.setDeltaMovement(mob.getDeltaMovement().multiply(0.1, 1, 0.1));
                Vec3 c = mob.position().add(0, mob.getBbHeight() * 0.4, 0);
                for (int i = 0; i < 8; i++) {
                    double a = Math.PI * 2 * i / 8;
                    feather(level, mob, c.add(Math.cos(a) * ringRadius, 0, Math.sin(a) * ringRadius));
                }
            }
        }
    }

    // ------------------------------------------------------------------ calamity combo
    public static class Calamity extends TimedSkillGoal {
        private static final int DASH_FROM = 6, DASH_TO = 16, SECOND_SLASH = 28;
        private final double radius;
        private final float slashDamage;
        private final float dashDamage;
        private final double speed;
        private final Set<UUID> hit = new HashSet<>();
        private Vec3 dir = Vec3.ZERO;

        /** 第一斬在 impactTick，迴旋衝刺在其後 6~16 tick，第二斬在其後 28 tick；總長 impactTick + 46。 */
        public Calamity(PysiftGeoEntity mob, String animation, int impactTick, int cooldown, double maxRange,
                        double radius, float slashDamage, float dashDamage, double speed) {
            super(mob, animation, impactTick, impactTick + 46, cooldown, 0.0, maxRange, false);
            this.radius = radius;
            this.slashDamage = slashDamage;
            this.dashDamage = dashDamage;
            this.speed = speed;
        }

        @Override
        protected void perform(ServerLevel level, LivingEntity t) {
            hit.clear();
            slash(level, mob, radius, slashDamage, 0.5);
            dir = lockDirection(mob, t);
        }

        @Override
        protected void onAfterImpact(ServerLevel level, int ticks) {
            if (ticks >= DASH_FROM && ticks <= DASH_TO) {
                if (ticks == DASH_FROM && target != null && target.isAlive()) {
                    dir = lockDirection(mob, target);
                }
                face(mob, dir);
                mob.setDeltaMovement(dir.x * speed, mob.getDeltaMovement().y, dir.z * speed);
                mob.needsSync = true;
                contact(level, mob, hit, dashDamage);
            } else if (ticks == DASH_TO + 1) {
                mob.setDeltaMovement(mob.getDeltaMovement().multiply(0.1, 1, 0.1));
            } else if (ticks == SECOND_SLASH) {
                if (target != null && target.isAlive()) {
                    face(mob, lockDirection(mob, target));
                }
                slash(level, mob, radius, slashDamage, 0.5);
            }
        }
    }
}
