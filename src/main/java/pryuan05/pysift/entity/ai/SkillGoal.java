package pryuan05.pysift.entity.ai;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import pryuan05.pysift.entity.PysiftGeoEntity;

import java.util.function.BiConsumer;

/**
 * 只需要「命中時做一件事」的簡單計時技能：效果由 lambda 提供，其餘（前搖、動畫、冷卻、距離判定）同 {@link TimedSkillGoal}。
 */
public class SkillGoal extends TimedSkillGoal {
    private final BiConsumer<ServerLevel, LivingEntity> effect;

    public SkillGoal(PysiftGeoEntity mob, String animation, int impactTick, int totalTicks, int cooldownTicks,
                     double minRange, double maxRange, boolean needsLineOfSight, BiConsumer<ServerLevel, LivingEntity> effect) {
        super(mob, animation, impactTick, totalTicks, cooldownTicks, minRange, maxRange, needsLineOfSight);
        this.effect = effect;
    }

    @Override
    protected void perform(ServerLevel level, LivingEntity target) {
        effect.accept(level, target);
    }
}
