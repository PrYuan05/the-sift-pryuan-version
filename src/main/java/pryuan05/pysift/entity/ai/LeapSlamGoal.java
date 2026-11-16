package pryuan05.pysift.entity.ai;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftGeoEntity;

/**
 * 跳躍砸地：蹲低 {@code launchTick} tick 後朝目標躍起（依距離計算初速，約 {@code flightTicks} tick 落地），
 * 落地時在落點造成範圍傷害並擊飛（效果同 {@link GroundSlamGoal#slamAt}）。目標需在 minRange ~ maxRange 之間。
 */
public class LeapSlamGoal extends TimedSkillGoal {
    private final int launchTick;
    private final int flightTicks;
    private final double radius;
    private final float damage;

    public LeapSlamGoal(PysiftGeoEntity mob, String animation, int launchTick, int flightTicks, int recoverTicks, int cooldownTicks,
                        double minRange, double maxRange, double radius, float damage) {
        super(mob, animation, launchTick + flightTicks, launchTick + flightTicks + recoverTicks, cooldownTicks, minRange, maxRange, true);
        this.launchTick = launchTick;
        this.flightTicks = flightTicks;
        this.radius = radius;
        this.damage = damage;
    }

    @Override
    protected void onWindUp(ServerLevel level, int tick) {
        if (tick != launchTick || target == null) {
            return;
        }
        Vec3 to = target.position().subtract(mob.position());
        double gravity = 0.08, drag = 0.91;
        // horizontal: sum of v*drag^k over the flight ~= distance; vertical: rise and fall within the flight time
        double dragSum = (1 - Math.pow(drag, flightTicks)) / (1 - drag);
        Vec3 horizontal = to.multiply(1, 0, 1).scale(1.0 / dragSum);
        double vy = gravity * flightTicks / 2.0 + Math.max(0, to.y) / flightTicks;
        mob.setDeltaMovement(horizontal.x, vy, horizontal.z);
        mob.needsSync = true;
        mob.playSound(SoundEvents.RAVAGER_ROAR, 1.5f, 1.3f);
    }

    @Override
    protected void perform(ServerLevel level, LivingEntity t) {
        GroundSlamGoal.slamAt(level, mob, mob.position(), radius, damage, 0.7, e -> !(e instanceof Enemy));
    }
}
