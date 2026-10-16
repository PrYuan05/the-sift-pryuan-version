package pryuan05.pysift.entity.ai;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftGeoEntity;

import java.util.EnumSet;

/**
 * 遠程型的走位：和目標保持在 minRange ~ maxRange 之間。太近就往遠離目標的方向退，太遠就靠近，在範圍內就停下面向目標。
 */
public class KeepRangeGoal extends Goal {
    private final PysiftGeoEntity mob;
    private final double minRange;
    private final double maxRange;
    private final double speed;
    private int repathDelay;

    public KeepRangeGoal(PysiftGeoEntity mob, double minRange, double maxRange, double speed) {
        this.mob = mob;
        this.minRange = minRange;
        this.maxRange = maxRange;
        this.speed = speed;
        this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        LivingEntity t = mob.getTarget();
        return t != null && t.isAlive() && !mob.isUsingSkill();
    }

    @Override
    public void tick() {
        LivingEntity t = mob.getTarget();
        if (t == null) {
            return;
        }
        mob.getLookControl().setLookAt(t, 30.0f, 30.0f);
        if (--repathDelay > 0) {
            return;
        }
        repathDelay = 10;
        double d = mob.distanceTo(t);
        if (d < minRange) {
            Vec3 away = DefaultRandomPos.getPosAway(mob, 8, 4, t.position());
            if (away != null) {
                mob.getNavigation().moveTo(away.x, away.y, away.z, speed * 1.2);
            }
        } else if (d > maxRange || !mob.hasLineOfSight(t)) {
            mob.getNavigation().moveTo(t, speed);
        } else {
            mob.getNavigation().stop();
        }
    }

    @Override
    public void stop() {
        mob.getNavigation().stop();
    }
}
