package pryuan05.pysift.worldgen;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.SiftPortalBlock;

/**
 * 野外的小裂隙門：極少數生成在篩靈界的平地上，可以傳回主世界，夜晚特別亮（SiftPortalBlockEntityRenderer）。
 * 地面高低差超過 1 格、或有液體時不生成。
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
        return true;
    }

    public static void register() {
        PySift.LOGGER.debug("Registered feature {}", TYPE);
    }
}
