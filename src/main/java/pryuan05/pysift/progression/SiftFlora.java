package pryuan05.pysift.progression;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.VegetationBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import pryuan05.pysift.block.SiftDayPhase;

/**
 * 夜光植物（參考影片中夜裡會發出青藍光點的草地與灌木）：
 * <ul>
 *   <li>夜光短草（貼圖沿用幽匿草）、夜光草叢：青綠色草葉，葉尖有一層自發光的光點（模型的 light_emission 層），白天看起來像普通的草。</li>
 *   <li>星光灌木：深色小灌木，掛滿發藍光的小點。</li>
 * </ul>
 * 一直帶著微弱亮度；入夜後（{@link SiftDayPhase}）會飄出小小的發光粒子。
 * 資源由 tools/progression/build_progression.py 產生，世界生成在 tools/worldgen/build_the_sift.py 的 GLOW_FEATURES。
 */
public final class SiftFlora {
    public static final Block GLOWSHADE_SHORT_GRASS = ModProgression.registerBlock("glowshade_short_grass",
            p -> new NightGlowPlant(p.lightLevel(state -> 3), Block.box(2.0, 0.0, 2.0, 14.0, 10.0, 14.0), 40), Blocks.SHORT_GRASS);
    public static final Block GLOWSHADE_TUFT = ModProgression.registerBlock("glowshade_tuft",
            p -> new NightGlowPlant(p.lightLevel(state -> 4), Block.box(1.0, 0.0, 1.0, 15.0, 15.0, 15.0), 25), Blocks.SHORT_GRASS);
    public static final Block STARLIT_SHRUB = ModProgression.registerBlock("starlit_shrub",
            p -> new NightGlowPlant(p.lightLevel(state -> 5), Block.box(1.0, 0.0, 1.0, 15.0, 13.0, 15.0), 15), Blocks.FERN);

    private SiftFlora() {
    }

    static void load() {
    }

    /** 一般的地被植物；chance：夜裡每 tick 有 1/chance 的機率冒出一顆發光粒子。 */
    public static class NightGlowPlant extends VegetationBlock {
        private final VoxelShape shape;
        private final int chance;

        public NightGlowPlant(Properties properties, VoxelShape shape, int chance) {
            super(properties);
            this.shape = shape;
            this.chance = chance;
        }

        @Override
        protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
            return shape;
        }

        @Override
        protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
            return state.is(BlockTags.DIRT) || state.isFaceSturdy(level, pos, Direction.UP);
        }

        @Override
        public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
            float night = SiftDayPhase.night(level);
            if (night > 0.2f && random.nextInt(chance) < Math.max(1, (int) (night * 3))) {
                level.addParticle(ParticleTypes.GLOW, pos.getX() + random.nextDouble(), pos.getY() + 0.3 + random.nextDouble() * 0.6,
                        pos.getZ() + random.nextDouble(), (random.nextDouble() - 0.5) * 0.02, 0.015, (random.nextDouble() - 0.5) * 0.02);
            }
        }
    }
}
