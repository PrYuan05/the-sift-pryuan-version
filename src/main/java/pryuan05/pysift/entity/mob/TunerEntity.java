package pryuan05.pysift.entity.mob;

import java.util.List;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.PysiftMonsterEntity;

/**
 * 音律使（戰術光環怪）。自己不攻擊，會和玩家保持 6 格以上距離；
 * 每 3 秒釋放音律光環（動畫 aura），給 12 格內所有敵對怪物 4 秒速度 I 與力量 I（附近沒有其他敵對怪物時不釋放）。
 */
public class TunerEntity extends PysiftMonsterEntity {
    private static final double AURA_RANGE = 12.0;
    private int auraTimer = 60;

    public TunerEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 25.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.SCALE, 0.56); // 模型約 1.79 格高，縮小後約 1 格高
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new AvoidEntityGoal<>(this, Player.class, 6.0f, 1.0, 1.2,
                p -> !((Player) p).isCreative() && !p.isSpectator()));
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 10.0f));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("aura");
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (--auraTimer > 0) {
            return;
        }
        auraTimer = 60;
        List<LivingEntity> allies = level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(AURA_RANGE),
                e -> e != this && e.isAlive() && e instanceof Enemy && e.distanceToSqr(this) <= AURA_RANGE * AURA_RANGE);
        if (allies.isEmpty()) {
            return;
        }
        this.triggerAnim("skill", "aura");
        this.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 1.5f, 1.5f);
        for (int i = 0; i < 24; i++) {
            double a = i * Math.PI * 2 / 24;
            level.sendParticles(ParticleTypes.NOTE, this.getX() + Math.cos(a) * 2.5, this.getY() + 0.5, this.getZ() + Math.sin(a) * 2.5,
                    1, 0, 0, 0, i / 24.0);
        }
        for (LivingEntity ally : allies) {
            ally.addEffect(new MobEffectInstance(MobEffects.SPEED, 80, 0), this);
            ally.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 80, 0), this);
        }
    }
}
