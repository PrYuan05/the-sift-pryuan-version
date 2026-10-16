package pryuan05.pysift.entity.mob;

import java.util.List;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LeapAtTargetGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.PysiftMonsterEntity;

/**
 * 蟲群幼體（Seedling、Sprout 共用）：HP 8、速度 0.34。
 * <ul>
 *   <li>跳躍撲咬目標（動畫 attack）。</li>
 *   <li>群體圍攻：任何一隻鎖定目標時，12 格內還沒有目標的同伴會一起鎖定同一個目標。</li>
 *   <li>極度脆弱：火焰與摔落傷害變成 3 倍。</li>
 * </ul>
 */
public abstract class PysiftSwarmEntity extends PysiftMonsterEntity {
    private boolean propagating;

    protected PysiftSwarmEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createSwarmAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 8.0)
                .add(Attributes.MOVEMENT_SPEED, 0.34)
                .add(Attributes.ATTACK_DAMAGE, 2.0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new LeapAtTargetGoal(this, 0.4f));
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.2, false));
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

    @Override
    public void setTarget(LivingEntity target) {
        super.setTarget(target);
        if (target == null || propagating || !(this.level() instanceof ServerLevel level)) {
            return;
        }
        for (PysiftSwarmEntity kin : level.getEntitiesOfClass(PysiftSwarmEntity.class, this.getBoundingBox().inflate(12.0),
                k -> k != this && k.getTarget() == null && k.isAlive())) {
            kin.propagating = true;
            kin.setTarget(target);
            kin.propagating = false;
        }
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (source.is(DamageTypeTags.IS_FIRE) || source.is(DamageTypeTags.IS_FALL)) {
            amount *= 3.0f;
        }
        return super.hurtServer(level, source, amount);
    }
}
