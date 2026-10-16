package pryuan05.pysift.entity.mob;

import java.util.EnumSet;
import java.util.List;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.PySift;
import pryuan05.pysift.entity.PysiftMonsterEntity;

/**
 * 潛伏獵手（暗影刺客）。
 * <ul>
 *   <li>所在位置光照低於 7 時保持隱形（無粒子），亮處自動現形。</li>
 *   <li>繞後：鎖定目標後先繞到目標背後；從背後打出的第一刀造成 200% 傷害（動畫 attack，暴擊粒子）。</li>
 *   <li>受到攻擊後往反方向後撤約 5 格（2 秒），撤退結束後背刺重新就緒。</li>
 * </ul>
 */
public class StalkerEntity extends PysiftMonsterEntity {
    private static final AttributeModifier BACKSTAB = new AttributeModifier(PySift.id("stalker_backstab"), 1.0,
            AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
    private boolean backstabReady = true;
    private int retreatTicks;
    private LivingEntity retreatFrom;

    public StalkerEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 28.0)
                .add(Attributes.MOVEMENT_SPEED, 0.32)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.SCALE, 1.89); // 模型約 1.22 格高，放大後約 2.3 格高
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new RetreatGoal());
        this.goalSelector.addGoal(2, new FlankGoal());
        this.goalSelector.addGoal(3, new MeleeAttackGoal(this, 1.2, false));
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8.0f));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));

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

    /** 自己是否在 target 視線方向的背後（夾角大於約 120°）。 */
    private boolean isBehind(LivingEntity target) {
        Vec3 look = target.getViewVector(1.0f).multiply(1, 0, 1);
        Vec3 toMe = this.position().subtract(target.position()).multiply(1, 0, 1);
        if (look.lengthSqr() < 1.0E-4 || toMe.lengthSqr() < 1.0E-4) {
            return false;
        }
        return look.normalize().dot(toMe.normalize()) < -0.5;
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean backstab = backstabReady && target instanceof LivingEntity living && isBehind(living);
        AttributeInstance damage = this.getAttribute(Attributes.ATTACK_DAMAGE);
        if (backstab && damage != null) {
            damage.addTransientModifier(BACKSTAB);
        }
        boolean hit;
        try {
            hit = super.doHurtTarget(level, target);
        } finally {
            if (backstab && damage != null) {
                damage.removeModifier(BACKSTAB.id());
            }
        }
        if (hit && backstab) {
            backstabReady = false;
            this.playSound(SoundEvents.PLAYER_ATTACK_CRIT, 1.0f, 0.8f);
            level.sendParticles(ParticleTypes.CRIT, target.getX(), target.getY(0.6), target.getZ(), 15, 0.3, 0.3, 0.3, 0.2);
        }
        return hit;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && source.getEntity() instanceof LivingEntity attacker && attacker != this) {
            retreatTicks = 40;
            retreatFrom = attacker;
        }
        return hurt;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (this.tickCount % 20 != 0) {
            return;
        }
        if (level.getMaxLocalRawBrightness(this.blockPosition()) < 7) {
            this.addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 40, 0, false, false));
        } else if (this.hasEffect(MobEffects.INVISIBILITY)) {
            this.removeEffect(MobEffects.INVISIBILITY);
        }
    }

    /** 受擊後往攻擊者的反方向跑約 5 格。 */
    private class RetreatGoal extends Goal {
        RetreatGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            return retreatTicks > 0 && retreatFrom != null;
        }

        @Override
        public boolean canContinueToUse() {
            return retreatTicks > 0;
        }

        @Override
        public void start() {
            Vec3 away = position().subtract(retreatFrom.position()).multiply(1, 0, 1);
            Vec3 dir = away.lengthSqr() < 1.0E-4 ? Vec3.directionFromRotation(0, getYRot() + 180) : away.normalize();
            Vec3 dest = position().add(dir.scale(5.0));
            getNavigation().moveTo(dest.x, dest.y, dest.z, 1.4);
        }

        @Override
        public void tick() {
            retreatTicks--;
        }

        @Override
        public void stop() {
            retreatTicks = 0;
            retreatFrom = null;
            backstabReady = true;
        }
    }

    /** 背刺就緒時，繞到目標背後 2.5 格的位置；到位後交給近戰。 */
    private class FlankGoal extends Goal {
        private int ticks;

        FlankGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = getTarget();
            return backstabReady && t != null && t.isAlive() && distanceToSqr(t) < 16 * 16 && !isBehind(t);
        }

        @Override
        public boolean canContinueToUse() {
            LivingEntity t = getTarget();
            return backstabReady && t != null && t.isAlive() && ticks < 200 && distanceToSqr(t) < 20 * 20 && !isBehind(t);
        }

        @Override
        public void start() {
            ticks = 0;
        }

        @Override
        public void tick() {
            LivingEntity t = getTarget();
            ticks++;
            getLookControl().setLookAt(t, 30.0f, 30.0f);
            if (ticks % 10 == 1) {
                Vec3 look = t.getViewVector(1.0f).multiply(1, 0, 1);
                Vec3 back = look.lengthSqr() < 1.0E-4 ? Vec3.ZERO : look.normalize().scale(-2.5);
                Vec3 dest = t.position().add(back);
                getNavigation().moveTo(dest.x, dest.y, dest.z, 1.2);
            }
        }
    }
}
