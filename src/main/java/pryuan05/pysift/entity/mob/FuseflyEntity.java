package pryuan05.pysift.entity.mob;

import java.util.List;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomFlyingGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftMonsterEntity;

/**
 * 引信飛蟲（飛行）。活著時飛著追咬目標（動畫 attack，2 點傷害）；
 * 死亡時身體膨脹成約 0.9 格的方塊（動畫 death，約 1 秒），在死亡第 18 tick 爆開：半徑 4 格 12 點魔法傷害並強力擊退，
 * 不破壞方塊。致命一擊不會把它打飛，死亡期間停在原地懸空，所以近身打死它一定會被炸到，最好從遠處解決。
 */
public class FuseflyEntity extends PysiftMonsterEntity {
    private static final double BLAST_RADIUS = 4.0;
    private static final float BLAST_DAMAGE = 12.0f;
    private static final int BLAST_DEATH_TICK = 18;   // 原版在 deathTime 20 時移除屍體

    public FuseflyEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
        this.moveControl = new FlyingMoveControl<>(this, 20, true);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FLYING_SPEED, 0.6)
                .add(Attributes.ATTACK_DAMAGE, 2.0)
                .add(Attributes.FALL_DAMAGE_MULTIPLIER, 0.0);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new FlyingPathNavigation(this, level);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.0, true));
        this.goalSelector.addGoal(7, new WaterAvoidingRandomFlyingGoal(this, 1.0));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8.0f));

        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("attack");
    }

    @Override
    protected String meleeAnimation() {
        return "attack";
    }

    @Override
    protected boolean hasDeathAnimation() {
        return true;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        if (this.isDeadOrDying()) {
            // 致命一擊不擊退：留在原地爆炸
            this.setDeltaMovement(Vec3.ZERO);
            this.needsSync = true;
        }
        return hurt;
    }

    @Override
    protected void tickDeath() {
        // 死亡期間懸停在原地（不掉落、不被推走）
        this.setNoGravity(true);
        this.setDeltaMovement(Vec3.ZERO);
        super.tickDeath();
        if (this.level() instanceof ServerLevel level) {
            if (this.deathTime == 1) {
                this.playSound(SoundEvents.CREEPER_PRIMED, 1.0f, 1.6f);
            } else if (this.deathTime < BLAST_DEATH_TICK) {
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, this.getX(), this.getY(0.5), this.getZ(), 3, 0.2, 0.2, 0.2, 0.05);
            } else if (this.deathTime == BLAST_DEATH_TICK) {
                blast(level);
            }
        }
    }

    private void blast(ServerLevel level) {
        Vec3 c = this.position().add(0, this.getBbHeight() / 2, 0);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(BLAST_RADIUS),
                e -> e != this && e.isAlive() && !(e instanceof Enemy) && e.distanceToSqr(c) <= BLAST_RADIUS * BLAST_RADIUS)) {
            if (e.hurtServer(level, this.damageSources().indirectMagic(this, this), BLAST_DAMAGE)) {
                Vec3 away = e.position().subtract(c).multiply(1, 0, 1);
                Vec3 dir = away.lengthSqr() < 1.0E-4 ? Vec3.ZERO : away.normalize();
                e.setDeltaMovement(e.getDeltaMovement().add(dir.x * 1.4, 0.6, dir.z * 1.4));
                e.needsSync = true;
            }
        }
        level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, c.x, c.y, c.z, 1, 0, 0, 0, 0.0);
        level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y, c.z, 8, 1.2, 1.0, 1.2, 0.0);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, c.x, c.y, c.z, 40, BLAST_RADIUS * 0.5, 0.6, BLAST_RADIUS * 0.5, 0.4);
        this.playSound(SoundEvents.GENERIC_EXPLODE.value(), 2.0f, 1.3f);
    }
}
