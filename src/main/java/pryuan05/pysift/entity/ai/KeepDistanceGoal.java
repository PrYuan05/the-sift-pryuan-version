package pryuan05.pysift.entity.ai;

import java.util.EnumSet;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftGeoEntity;

/**
 * 遠程／中距離生物的走位：和目標保持在 {@code min}~{@code max} 格之間。太近就往反方向退，太遠就靠近，
 * 在範圍內就停下來面對目標（讓技能有機會出手）。距離小於 {@code cornered} 時不接手，讓近戰目標去處理。
 */
public class KeepDistanceGoal extends Goal {
    private final PysiftGeoEntity mob;
    private final double min;
    private final double max;
    private final double cornered;
    private final double speed;
    private int repath;

    public KeepDistanceGoal(PysiftGeoEntity mob, double min, double max, double cornered, double speed) {
        this.mob = mob;
        this.min = min;
        this.max = max;
        this.cornered = cornered;
        this.speed = speed;
        this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        LivingEntity t = mob.getTarget();
        return t != null && t.isAlive() && !mob.isUsingSkill() && mob.distanceTo(t) >= cornered;
    }

    @Override
    public boolean canContinueToUse() {
        return canUse();
    }

    @Override
    public void start() {
        repath = 0;
    }

    @Override
    public void stop() {
        mob.getNavigation().stop();
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        LivingEntity t = mob.getTarget();
        if (t == null) {
            return;
        }
        mob.getLookControl().setLookAt(t, 30.0f, 30.0f);
        if (--repath > 0) {
            return;
        }
        repath = 10;
        double d = mob.distanceTo(t);
        if (d < min) {
            Vec3 away = DefaultRandomPos.getPosAway(mob, 8, 4, t.position());
            if (away != null) {
                mob.getNavigation().moveTo(away.x, away.y, away.z, speed * 1.2);
            }
        } else if (d > max || !mob.hasLineOfSight(t)) {
            mob.getNavigation().moveTo(t, speed);
        } else {
            mob.getNavigation().stop();
        }
    }
}
