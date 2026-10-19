package pryuan05.pysift.entity.mob;

import java.util.List;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftGeoEntity;
import pryuan05.pysift.entity.PysiftMonsterEntity;
import pryuan05.pysift.entity.ai.KeepDistanceGoal;
import pryuan05.pysift.entity.ai.SkillGoal;
import pryuan05.pysift.entity.projectile.HunterJavelinEntity;

/**
 * 獵人（Monarch 麾下的遠程標槍手）。
 * <ul>
 *   <li>走位：和目標保持 8~14 格；被貼到 4 格內時往後跳開（動畫 leap，冷卻 5 秒），躲不掉才用標槍近戰（動畫 attack）。</li>
 *   <li>標槍：5~18 格且看得到目標時投出靈魂標槍（{@link HunterJavelinEntity}，約 6 點，不能撿；動畫 throw，冷卻 3 秒）。</li>
 *   <li>標記：指向目標 8 秒發光，24 格內沒有目標的篩靈界怪物全部改追這個目標（動畫 mark，冷卻 15 秒）。</li>
 * </ul>
 */
public class HunterEntity extends PysiftMonsterEntity {
    public HunterEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 26.0)
                .add(Attributes.MOVEMENT_SPEED, 0.28)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.FOLLOW_RANGE, 32.0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new SkillGoal(this, "leap", 4, 14, 100, 0.0, 4.0, false, this::leapAway));
        this.goalSelector.addGoal(2, new SkillGoal(this, "mark", 10, 20, 300, 4.0, 20.0, true, this::mark));
        this.goalSelector.addGoal(2, new SkillGoal(this, "throw", 11, 20, 60, 5.0, 18.0, true, this::throwJavelin));
        this.goalSelector.addGoal(3, new KeepDistanceGoal(this, 8.0, 14.0, 3.0, 1.0));
        this.goalSelector.addGoal(4, new MeleeAttackGoal(this, 1.1, false));
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8.0f));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));

        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("attack", "throw", "mark", "leap");
    }

    @Override
    protected String meleeAnimation() {
        return "attack";
    }

    private void throwJavelin(ServerLevel level, LivingEntity target) {
        if (target == null || !target.isAlive()) {
            return;
        }
        HunterJavelinEntity javelin = HunterJavelinEntity.create(level, this);
        double dx = target.getX() - this.getX();
        double dz = target.getZ() - this.getZ();
        double dy = target.getY(0.4) - javelin.getY() + Math.sqrt(dx * dx + dz * dz) * 0.12;
        javelin.shoot(dx, dy, dz, 1.7f, 4.0f);
        level.addFreshEntity(javelin);
        this.playSound(SoundEvents.TRIDENT_THROW.value(), 1.0f, 1.1f);
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, javelin.getX(), javelin.getY(), javelin.getZ(), 4, 0.1, 0.1, 0.1, 0.02);
    }

    private void mark(ServerLevel level, LivingEntity target) {
        if (target == null || !target.isAlive()) {
            return;
        }
        target.addEffect(new MobEffectInstance(MobEffects.GLOWING, 160, 0), this);
        this.playSound(SoundEvents.ILLUSIONER_CAST_SPELL, 1.5f, 1.2f);
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, target.getX(), target.getY() + target.getBbHeight() + 0.3, target.getZ(),
                12, 0.3, 0.2, 0.3, 0.02);
        for (Mob ally : level.getEntitiesOfClass(Mob.class, this.getBoundingBox().inflate(24),
                m -> m != this && m.isAlive() && m instanceof Enemy && m instanceof PysiftGeoEntity && m.getTarget() == null)) {
            ally.setTarget(target);
        }
    }

    /** 被貼身：往遠離目標的方向後跳。 */
    private void leapAway(ServerLevel level, LivingEntity target) {
        Vec3 away = target != null ? this.position().subtract(target.position()).multiply(1, 0, 1) : Vec3.ZERO;
        away = away.lengthSqr() > 1.0E-4 ? away.normalize() : Vec3.directionFromRotation(0, this.getYRot() + 180);
        this.setDeltaMovement(away.x * 0.95, 0.45, away.z * 0.95);
        this.needsSync = true;
        this.playSound(SoundEvents.GOAT_LONG_JUMP, 1.0f, 1.2f);
        level.sendParticles(ParticleTypes.CLOUD, this.getX(), this.getY() + 0.1, this.getZ(), 6, 0.3, 0.05, 0.3, 0.02);
    }
}
