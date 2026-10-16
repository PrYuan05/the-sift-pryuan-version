package pryuan05.pysift.entity.ai;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import pryuan05.pysift.entity.PysiftGeoEntity;

import java.util.EnumSet;

/**
 * 有前搖、命中時間點與冷卻的技能。
 * <p>
 * 流程：開始時停止移動並觸發 {@code animation}（GeckoLib 的 "skill" 控制器，伺服器端觸發會自動同步到客戶端）；
 * 第 {@code impactTick} tick 呼叫 {@link #perform}；第 {@code totalTicks} tick 結束並進入冷卻。
 * 同一隻生物同時只會執行一個技能（{@link PysiftGeoEntity#isUsingSkill()}）。
 */
public abstract class TimedSkillGoal extends Goal {
    protected final PysiftGeoEntity mob;
    private final String animation;
    private final int impactTick;
    private final int totalTicks;
    private final int cooldownTicks;
    private final double minRange;
    private final double maxRange;
    private final boolean needsLineOfSight;
    private int tick;
    private long nextUseTick;
    protected LivingEntity target;

    protected TimedSkillGoal(PysiftGeoEntity mob, String animation, int impactTick, int totalTicks, int cooldownTicks,
                             double minRange, double maxRange, boolean needsLineOfSight) {
        this.mob = mob;
        this.animation = animation;
        this.impactTick = impactTick;
        this.totalTicks = totalTicks;
        this.cooldownTicks = cooldownTicks;
        this.minRange = minRange;
        this.maxRange = maxRange;
        this.needsLineOfSight = needsLineOfSight;
        this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        LivingEntity t = mob.getTarget();
        if (t == null || !t.isAlive() || mob.isUsingSkill() || mob.tickCount < nextUseTick) {
            return false;
        }
        double d = mob.distanceTo(t);
        return d >= minRange && d <= maxRange && (!needsLineOfSight || mob.hasLineOfSight(t));
    }

    @Override
    public boolean canContinueToUse() {
        return tick < totalTicks && mob.isAlive();
    }

    @Override
    public void start() {
        target = mob.getTarget();
        tick = 0;
        mob.setUsingSkill(true);
        mob.getNavigation().stop();
        mob.triggerAnim("skill", animation);
        onStart();
    }

    @Override
    public void tick() {
        tick++;
        if (target != null && target.isAlive()) {
            mob.getLookControl().setLookAt(target, 30.0f, 30.0f);
        }
        if (mob.level() instanceof ServerLevel level) {
            if (tick < impactTick) {
                onWindUp(level, tick);
            } else if (tick == impactTick) {
                perform(level, target);
            } else {
                onAfterImpact(level, tick - impactTick);
            }
        }
    }

    @Override
    public void stop() {
        mob.setUsingSkill(false);
        nextUseTick = mob.tickCount + Math.round(cooldownTicks * mob.skillCooldownScale());
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    /** 技能開始的那一刻（音效等）。 */
    protected void onStart() {
    }

    /** 前搖期間每 tick 呼叫（例如蓄力粒子）。 */
    protected void onWindUp(ServerLevel level, int tick) {
    }

    /** 命中之後到技能結束前每 tick 呼叫（例如持續擴散的音波環）；ticksSinceImpact 從 1 開始。 */
    protected void onAfterImpact(ServerLevel level, int ticksSinceImpact) {
    }

    /** 命中時間點：實際造成效果。target 可能已經死亡或離開。 */
    protected abstract void perform(ServerLevel level, LivingEntity target);
}
