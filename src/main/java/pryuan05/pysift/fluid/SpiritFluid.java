package pryuan05.pysift.fluid;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.InsideBlockEffectApplier;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.material.FlowingFluid;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.FluidState;
import pryuan05.pysift.effect.ModEffects;
import pryuan05.pysift.effect.SoulBurn;
import net.minecraft.server.level.ServerPlayer;
import pryuan05.pysift.particle.ModParticles;
import net.minecraft.util.RandomSource;

import java.util.Optional;

/**
 * 靈液：The Sift 地表與含水層的流體。流動方式與水相同（屬於 #minecraft:water，可游泳），
 * 會發光，浸泡其中的生物會獲得靈魂剝奪。
 */
public abstract class SpiritFluid extends FlowingFluid {
    @Override
    public Fluid getFlowing() {
        return ModFluids.FLOWING_SPIRIT_LIQUID;
    }

    @Override
    public Fluid getSource() {
        return ModFluids.SPIRIT_LIQUID;
    }

    @Override
    public Item getBucket() {
        return ModFluids.SPIRIT_LIQUID_BUCKET;
    }

    @Override
    public boolean isSame(Fluid fluid) {
        return fluid == ModFluids.SPIRIT_LIQUID || fluid == ModFluids.FLOWING_SPIRIT_LIQUID;
    }

    @Override
    protected boolean canConvertToSource(ServerLevel level) {
        return true;
    }

    @Override
    protected void beforeDestroyingBlock(LevelAccessor level, BlockPos pos, BlockState state) {
        BlockEntity blockEntity = state.hasBlockEntity() ? level.getBlockEntity(pos) : null;
        Block.dropResources(state, level, pos, blockEntity);
    }

    @Override
    protected void entityInside(Level level, BlockPos pos, Entity entity, InsideBlockEffectApplier effectApplier) {
        super.entityInside(level, pos, entity, effectApplier);
        if (!level.isClientSide() && entity instanceof LivingEntity living) {
            if (living instanceof ServerPlayer player) {
                SoulBurn.ignite(player);          // 靈魂剝奪：伏聆視野＋靈魂火＋血量抽到 0.2 倍（只在還沒中時觸發）
            } else {
                living.addEffect(new MobEffectInstance(ModEffects.SOUL_DEPRIVATION, 60, 0, true, true));
            }
        }
    }

    /** 平均每次 animateTick 冒出靈魂的機率是 1 / WISP_CHANCE；其中 1 / BURST_CHANCE 會一次冒出一小群。 */
    private static final int WISP_CHANCE = 70;
    private static final int BURST_CHANCE = 6;

    /** 客戶端：靈魂出竅，從水面上方是空氣的靈液源頭冒出 soul_wisp（外觀與光尾見 client/particle/SoulWispParticle）。 */
    @Override
    protected void animateTick(Level level, BlockPos pos, FluidState state, RandomSource random) {
        if (!state.isSource() || random.nextInt(WISP_CHANCE) != 0 || !level.getBlockState(pos.above()).isAir()) {
            return;
        }
        int count = random.nextInt(BURST_CHANCE) == 0 ? 3 + random.nextInt(3) : 1;
        for (int i = 0; i < count; i++) {
            level.addParticle(ModParticles.SOUL_WISP, pos.getX() + random.nextDouble(), pos.getY() + 0.9,
                    pos.getZ() + random.nextDouble(), 0, 0.02 + random.nextDouble() * 0.03, 0);
        }
    }

    @Override
    protected int getSlopeFindDistance(LevelReader level) {
        return 4;
    }

    @Override
    protected int getDropOff(LevelReader level) {
        return 1;
    }

    @Override
    public int getTickDelay(LevelReader level) {
        return 5;
    }

    @Override
    protected boolean canBeReplacedWith(FluidState state, BlockGetter level, BlockPos pos, Fluid fluid, Direction direction) {
        return direction == Direction.DOWN && !isSame(fluid);
    }

    @Override
    protected float getExplosionResistance() {
        return 100.0F;
    }

    @Override
    protected BlockState createLegacyBlock(FluidState state) {
        return ModFluids.SPIRIT_LIQUID_BLOCK.defaultBlockState().setValue(LiquidBlock.LEVEL, getLegacyLevel(state));
    }

    @Override
    public Optional<SoundEvent> getPickupSound() {
        return Optional.of(SoundEvents.BUCKET_FILL);
    }

    public static class Source extends SpiritFluid {
        @Override
        public int getAmount(FluidState state) {
            return 8;
        }

        @Override
        public boolean isSource(FluidState state) {
            return true;
        }
    }

    public static class Flowing extends SpiritFluid {
        @Override
        protected void createFluidStateDefinition(StateDefinition.Builder<Fluid, FluidState> builder) {
            super.createFluidStateDefinition(builder);
            builder.add(LEVEL);
        }

        @Override
        public int getAmount(FluidState state) {
            return state.getValue(LEVEL);
        }

        @Override
        public boolean isSource(FluidState state) {
            return false;
        }
    }
}
