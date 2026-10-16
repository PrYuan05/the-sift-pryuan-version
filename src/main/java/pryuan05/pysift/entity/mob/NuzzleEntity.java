package pryuan05.pysift.entity.mob;

import java.util.EnumSet;
import java.util.List;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.PysiftAnimalEntity;

/**
 * 親暱獸（溫馴，被動）。
 * <ul>
 *   <li>會主動走向 10 格內的玩家蹭臉（動畫 nuzzle），給予 10 秒發光與生命恢復 I；冷卻 60 秒。</li>
 *   <li>被攻擊時尖叫，並以 1.5 倍速度逃離攻擊者 10 秒。</li>
 * </ul>
 */
public class NuzzleEntity extends PysiftAnimalEntity {
    private int nuzzleCooldown = 100;

    public NuzzleEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftAnimalEntity.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.30);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new AvoidEntityGoal<>(this, LivingEntity.class, 12.0f, 1.5, 1.5, this::isRecentAttacker));
        this.goalSelector.addGoal(3, new NuzzlePlayerGoal());
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 6.0f));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
    }

    private boolean isRecentAttacker(LivingEntity e) {
        return e == this.getLastHurtByMob() && this.tickCount - this.getLastHurtByMobTimestamp() < 200;
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("nuzzle");
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt) {
            this.playSound(SoundEvents.FOX_SCREECH, 1.2f, 1.4f);
        }
        return hurt;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (nuzzleCooldown > 0) {
            nuzzleCooldown--;
        }
    }

    /** 走向最近的玩家，貼近後蹭一下。 */
    private class NuzzlePlayerGoal extends Goal {
        private Player player;

        NuzzlePlayerGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (nuzzleCooldown > 0 || tickCount - getLastHurtByMobTimestamp() < 200) {
                return false;
            }
            player = level().getNearestPlayer(NuzzleEntity.this, 10.0);
            return player != null && !player.isSpectator();
        }

        @Override
        public boolean canContinueToUse() {
            return player != null && player.isAlive() && nuzzleCooldown <= 0 && distanceToSqr(player) < 14 * 14;
        }

        @Override
        public void tick() {
            getLookControl().setLookAt(player, 30.0f, 30.0f);
            if (distanceToSqr(player) > 2.25) {
                if (tickCount % 10 == 0) {
                    getNavigation().moveTo(player, 1.0);
                }
                return;
            }
            getNavigation().stop();
            nuzzleCooldown = 1200;
            triggerAnim("skill", "nuzzle");
            playSound(SoundEvents.FOX_SNIFF, 1.0f, 1.3f);
            player.addEffect(new MobEffectInstance(MobEffects.GLOWING, 200, 0), NuzzleEntity.this);
            player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 200, 0), NuzzleEntity.this);
            if (level() instanceof ServerLevel level) {
                level.sendParticles(ParticleTypes.HEART, getX(), getY() + getBbHeight(), getZ(), 5, 0.4, 0.3, 0.4, 0.0);
            }
        }

        @Override
        public void stop() {
            player = null;
        }
    }
}
