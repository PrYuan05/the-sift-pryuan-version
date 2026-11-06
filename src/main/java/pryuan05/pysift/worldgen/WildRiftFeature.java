package pryuan05.pysift.worldgen;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.MultifaceBlock;
import net.minecraft.world.level.block.state.BlockState;
import pryuan05.pysift.block.ModVegetation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.SiftPortalBlock;

/**
 * 野外的小裂隙門：極少數生成在隙浮的平地上，可以傳回主世界，夜晚特別亮（SiftPortalBlockEntityRenderer）。
 * 地面高低差超過 1 格、或有液體時不生成。
 * <p>
 * 世界觀 4.7：主世界沒有靈魂的空氣從裂縫倒灌進隙浮，讓附近的赤紅幽匿腐爛成藍色。所以每道裂隙門周圍都有一圈腐爛帶：
 * 門邊是原版的藍色幽匿，往外藍紅交錯，最外圈是還活著的赤紅幽匿，再往外漸漸變回原本的地面（{@link #rotHalo}）。
 */
public record WildRiftFeature() implements Feature {
    public static final MapCodec<WildRiftFeature> CODEC = MapCodec.unit(new WildRiftFeature());
    public static final MapCodec<WildRiftFeature> TYPE = Registry.register(BuiltInRegistries.FEATURE_TYPE, PySift.id("wild_rift"), CODEC);

    @Override
    public MapCodec<WildRiftFeature> codec() {
        return CODEC;
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        Direction.Axis axis = random.nextBoolean() ? Direction.Axis.X : Direction.Axis.Z;
        Direction along = axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
        int y0 = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, origin.getX(), origin.getZ());
        for (int u = -4; u <= 4; u++) {
            BlockPos column = origin.relative(along, u);
            int y = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, column.getX(), column.getZ());
            if (Math.abs(y - y0) > 1 || !level.getFluidState(new BlockPos(column.getX(), y - 1, column.getZ())).isEmpty()) {
                return false;
            }
        }
        SiftPortalBlock.buildRiftPortal(level, new BlockPos(origin.getX(), y0, origin.getZ()), axis);
        rotHalo(level, origin, random);
        return true;
    }

    private static final int HALO = 8;
    private static final TagKey<Block> REPLACEABLE = TagKey.create(Registries.BLOCK, PySift.id("red_sculk_replaceable"));

    /**
     * 裂隙門周圍半徑 {@link #HALO} 格的腐爛帶：3 格內幾乎都是藍色幽匿，3～5.5 格藍色越來越少、換成赤紅幽匿，
     * 5.5～8 格只剩零星的赤紅幽匿。地面上再長一點同色的脈絡。只換地表那一格，而且只換 #pysift:red_sculk_replaceable 的方塊。
     */
    public static void rotHalo(net.minecraft.world.level.LevelAccessor level, BlockPos centre, RandomSource random) {
        // during worldgen only the _WG heightmaps exist; on a running world (a portal opened by a player) use the live one
        Heightmap.Types surface = level instanceof net.minecraft.server.level.ServerLevel ? Heightmap.Types.WORLD_SURFACE : Heightmap.Types.WORLD_SURFACE_WG;
        BlockState blue = Blocks.SCULK.defaultBlockState();
        BlockState red = ModVegetation.RED_SCULK.defaultBlockState();
        BlockState blueVein = Blocks.SCULK_VEIN.defaultBlockState().setValue(MultifaceBlock.getFaceProperty(Direction.DOWN), true);
        BlockState redVein = ModVegetation.RED_SCULK_VEIN.defaultBlockState().setValue(MultifaceBlock.getFaceProperty(Direction.DOWN), true);
        for (int dx = -HALO; dx <= HALO; dx++) {
            for (int dz = -HALO; dz <= HALO; dz++) {
                double d = Math.sqrt(dx * dx + dz * dz) + (random.nextDouble() - 0.5);   // ragged rings
                if (d > HALO) {
                    continue;
                }
                boolean rotten;
                if (d < 3.0) {
                    rotten = random.nextFloat() < 0.9f;
                    if (!rotten && random.nextFloat() < 0.5f) {
                        continue;
                    }
                } else if (d < 5.5) {
                    rotten = random.nextDouble() < (5.5 - d) / 2.5;
                } else if (random.nextDouble() < (HALO - d) / (HALO - 5.5) * 0.7) {
                    rotten = false;
                } else {
                    continue;
                }
                int x = centre.getX() + dx, z = centre.getZ() + dz;
                BlockPos top = new BlockPos(x, level.getHeight(surface, x, z) - 1, z);
                for (int i = 0; i < 4 && level.getBlockState(top).canBeReplaced() && level.getFluidState(top).isEmpty(); i++) {
                    top = top.below();   // under the grass and plants
                }
                if (!level.getBlockState(top).is(REPLACEABLE) || !level.getFluidState(top.above()).isEmpty()) {
                    continue;
                }
                if (!level.getBlockState(top.above()).canBeReplaced()) {
                    continue;   // the portal itself, or anything solid standing on this block
                }
                for (int up = 1; up <= 2 && !level.getBlockState(top.above(up)).isAir() && level.getBlockState(top.above(up)).canBeReplaced(); up++) {
                    level.setBlock(top.above(up), Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);   // the rot kills the plants
                }
                level.setBlock(top, rotten ? blue : red, Block.UPDATE_CLIENTS);
                if (level.getBlockState(top.above()).isAir() && random.nextFloat() < 0.2f) {
                    level.setBlock(top.above(), rotten ? blueVein : redVein, Block.UPDATE_CLIENTS);
                }
            }
        }
    }

    public static void register() {
        PySift.LOGGER.debug("Registered feature {}", TYPE);
    }
}
