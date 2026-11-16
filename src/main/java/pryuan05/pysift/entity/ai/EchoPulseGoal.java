package pryuan05.pysift.entity.ai;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftGeoEntity;

/**
 * 回音脈衝：單一目標的短程音波。命中時造成少量 sonicBoom 傷害並施加緩慢，沿線畫出聲波粒子。需要視線。
 */
public class EchoPulseGoal extends TimedSkillGoal {
    private final double range;
    private final float damage;
    private final int slowTicks;
    private final int slowAmplifier;

    public EchoPulseGoal(PysiftGeoEntity mob, String animation, int impactTick, int totalTicks, int cooldownTicks,
                         double minRange, double range, float damage, int slowTicks, int slowAmplifier) {
        super(mob, animation, impactTick, totalTicks, cooldownTicks, minRange, range, true);
        this.range = range;
        this.damage = damage;
        this.slowTicks = slowTicks;
        this.slowAmplifier = slowAmplifier;
    }

    @Override
    protected void onWindUp(ServerLevel level, int tick) {
        if (tick % 4 == 0) {
            Vec3 p = mob.position().add(0, mob.getBbHeight() * 0.6, 0);
            level.sendParticles(ParticleTypes.SCULK_SOUL, p.x, p.y, p.z, 2, 0.4, 0.3, 0.4, 0.01);
        }
    }

    @Override
    protected void perform(ServerLevel level, LivingEntity t) {
        if (t == null || !t.isAlive() || mob.distanceTo(t) > range + 2 || !mob.hasLineOfSight(t)) {
            return;
        }
        Vec3 from = mob.position().add(0, mob.getBbHeight() * 0.6, 0);
        Vec3 to = t.position().add(0, t.getBbHeight() * 0.5, 0);
        Vec3 dir = to.subtract(from).normalize();
        int n = Math.max(1, (int) Math.ceil(from.distanceTo(to) / 1.5));
        for (int i = 1; i <= n; i++) {
            Vec3 p = from.add(dir.scale(i * 1.5));
            level.sendParticles(ParticleTypes.SONIC_BOOM, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
        mob.playSound(SoundEvents.WARDEN_SONIC_BOOM, 1.5f, 1.6f);
        if (t.hurtServer(level, mob.damageSources().sonicBoom(mob), damage)) {
            t.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, slowTicks, slowAmplifier), mob);
        }
    }
}
