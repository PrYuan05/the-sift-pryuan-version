package pryuan05.pysift.entity.mob;

import java.util.Comparator;
import java.util.EnumSet;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BonemealSource;
import net.minecraft.world.level.block.BonemealableBlock;
import net.minecraft.world.level.block.LevelEvent;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftGeoEntity;

/**
 * 傳粉蜂怪（地面輔助，中立，不會飛）。
 * <ul>
 *   <li>平時找 8 格內的作物或樹苗，走到旁邊彎腰施加骨粉效果（動畫 pollinate，每次最多 3 下，冷卻 20 秒）。</li>
 *   <li>被玩家攻擊時，周圍 8 格內的傳粉蜂全部被激怒，叮咬（動畫 sting）並施加 5 秒中毒。</li>
 * </ul>
 */
public class PollinatorEntity extends PysiftGeoEntity {
    private int pollinateCooldown = 100;

    public PollinatorEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PathfinderMob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.ATTACK_DAMAGE, 2.0)
                .add(Attributes.FOLLOW_RANGE, 16.0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new MeleeAttackGoal(this, 1.2, true));
        this.goalSelector.addGoal(4, new PollinateGoal());
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 6.0f));

        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("sting", "pollinate");
    }

    @Override
    protected String meleeAnimation() {
        return "sting";
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && source.getEntity() instanceof Player player && !player.isCreative()) {
            for (PollinatorEntity other : level.getEntitiesOfClass(PollinatorEntity.class, this.getBoundingBox().inflate(8.0))) {
                other.setTarget(player);
            }
        }
        return hurt;
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity living) {
            living.addEffect(new MobEffectInstance(MobEffects.POISON, 100, 0), this);
            this.playSound(SoundEvents.BEE_STING, 1.0f, 1.0f);
        }
        return hit;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (pollinateCooldown > 0) {
            pollinateCooldown--;
        }
    }

    private static boolean isPlant(BlockState state) {
        return state.is(BlockTags.CROPS) || state.is(BlockTags.SAPLINGS);
    }

    /** 走到作物旁邊，每 2 秒施一次骨粉，最多 3 次。 */
    private class PollinateGoal extends Goal {
        private BlockPos plant;
        private int ticks;
        private int pulses;

        PollinateGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (pollinateCooldown > 0 || getTarget() != null || !(level() instanceof ServerLevel level)) {
                return false;
            }
            pollinateCooldown = 100;   // 找不到時也不要每 tick 搜尋
            BlockPos c = blockPosition();
            plant = BlockPos.betweenClosedStream(c.offset(-8, -4, -8), c.offset(8, 2, 8))
                    .filter(p -> {
                        BlockState s = level.getBlockState(p);
                        return isPlant(s) && s.getBlock() instanceof BonemealableBlock b
                                && b.isValidBonemealTarget(level, p, s, BonemealSource.MOB);
                    })
                    .min(Comparator.comparingDouble(p -> p.distSqr(c)))
                    .map(BlockPos::immutable).orElse(null);
            return plant != null;
        }

        @Override
        public boolean canContinueToUse() {
            return plant != null && pulses < 3 && ticks < 400 && getTarget() == null && isPlant(level().getBlockState(plant));
        }

        @Override
        public void start() {
            ticks = 0;
            pulses = 0;
        }

        @Override
        public void tick() {
            ticks++;
            Vec3 spot = Vec3.atBottomCenterOf(plant);
            getLookControl().setLookAt(spot.x, spot.y, spot.z);
            if (distanceToSqr(spot) > 2.25 * 2.25) {
                if (getNavigation().isDone() || ticks % 20 == 0) {
                    getNavigation().moveTo(spot.x, spot.y, spot.z, 1.0);
                }
                return;
            }
            getNavigation().stop();
            if (ticks % 40 == 0 && level() instanceof ServerLevel level) {
                BlockState s = level.getBlockState(plant);
                if (s.getBlock() instanceof BonemealableBlock b && b.isValidBonemealTarget(level, plant, s, BonemealSource.MOB)) {
                    if (b.isBonemealSuccess(level, getRandom(), plant, s, BonemealSource.MOB)) {
                        b.performBonemeal(level, getRandom(), plant, s, BonemealSource.MOB);
                    }
                    level.levelEvent(LevelEvent.PARTICLES_AND_SOUND_PLANT_GROWTH, plant, 15);
                    triggerAnim("skill", "pollinate");
                }
                pulses++;
            }
        }

        @Override
        public void stop() {
            plant = null;
            pollinateCooldown = 400;
        }
    }
}
