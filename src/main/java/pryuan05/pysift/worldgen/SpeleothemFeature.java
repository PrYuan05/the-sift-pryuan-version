package pryuan05.pysift.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SpeleothemBlock;
import net.minecraft.world.level.block.state.properties.SpeleothemThickness;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.feature.Feature;
import pryuan05.pysift.PySift;

/**
 * 鐘乳石與石筍（v2.1.0 地底裝飾）：用隙浮自己的石材疊出的錐形岩柱，不用原版的棕色滴水石。
 * 起點是緊貼天花板（hanging）或地面的空氣格；柱子從那裡往外長 {@code min_height}–{@code max_height} 格：
 * 下三分之一是十字形的粗根，中段單格，最後約三分之一換成該層的尖石（block/PointedStones，像滴水石一樣由粗到尖）。{@code alt_block} 以約三成混進柱身，
 * 顏色和該層的地面同一組，不會突兀。起點對面沒有實心面（懸空）就不放。
 */
public record SpeleothemFeature(Block block, Block altBlock, Block tipBlock, int minHeight, int maxHeight,
                                boolean hanging) implements Feature {
    public static final MapCodec<SpeleothemFeature> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            BuiltInRegistries.BLOCK.byNameCodec().fieldOf("block").forGetter(SpeleothemFeature::block),
            BuiltInRegistries.BLOCK.byNameCodec().fieldOf("alt_block").forGetter(SpeleothemFeature::altBlock),
            BuiltInRegistries.BLOCK.byNameCodec().fieldOf("tip_block").forGetter(SpeleothemFeature::tipBlock),
            Codec.intRange(2, 24).fieldOf("min_height").forGetter(SpeleothemFeature::minHeight),
            Codec.intRange(2, 24).fieldOf("max_height").forGetter(SpeleothemFeature::maxHeight),
            Codec.BOOL.fieldOf("hanging").forGetter(SpeleothemFeature::hanging)
    ).apply(instance, SpeleothemFeature::new));
    public static final MapCodec<SpeleothemFeature> TYPE = Registry.register(BuiltInRegistries.FEATURE_TYPE, PySift.id("speleothem"), CODEC);

    @Override
    public MapCodec<SpeleothemFeature> codec() {
        return CODEC;
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        Direction grow = hanging ? Direction.DOWN : Direction.UP;
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        pos.set(origin);
        if (!level.getBlockState(pos).isAir() || !level.getBlockState(pos.relative(grow.getOpposite())).isSolid()) {
            return false;                                       // must start in air right against the ceiling / floor
        }
        int height = minHeight + (maxHeight > minHeight ? random.nextInt(maxHeight - minHeight + 1) : 0);
        // how far the free air goes in the growth direction: the column may not be taller than the room
        int room = 0;
        while (room < height && level.getBlockState(pos.set(origin).move(grow, room)).isAir()) {
            room++;
        }
        if (room < 2) {
            return false;
        }
        height = Math.min(height, room);
        boolean wide = height >= 4;
        boolean placed = false;
        // the last blocks are the layer's own pointed stone (block/PointedStones), thinning out to a tip like dripstone
        int pointed = tipBlock instanceof SpeleothemBlock ? Math.min(4, Math.max(1, height / 3)) : (height >= 3 ? 1 : 0);
        for (int t = 0; t < height; t++) {
            boolean tip = t >= height - pointed;
            BlockState body = tip ? pointedState(grow, t - (height - pointed), pointed)
                    : (random.nextFloat() < 0.3f ? altBlock : block).defaultBlockState();
            BlockPos center = origin.relative(grow, t);
            if (!level.getBlockState(center).isAir()) {
                break;
            }
            level.setBlock(center, body, Block.UPDATE_CLIENTS);
            placed = true;
            if (wide && t < Math.max(1, height / 3)) {          // the thick root: a plus shape around the centre
                for (Direction side : Direction.Plane.HORIZONTAL) {
                    BlockPos arm = center.relative(side);
                    if (level.getBlockState(arm).isAir() && (t > 0 || level.getBlockState(arm.relative(grow.getOpposite())).isSolid())) {
                        level.setBlock(arm, (random.nextFloat() < 0.3f ? altBlock : block).defaultBlockState(), Block.UPDATE_CLIENTS);
                    }
                }
            }
        }
        return placed;
    }

    /** The pointed stone at position i (0 = next to the column) of a run of n: base, middle..., frustum, tip. */
    private BlockState pointedState(Direction grow, int i, int n) {
        BlockState state = tipBlock.defaultBlockState();
        if (!(tipBlock instanceof SpeleothemBlock)) {
            return state;
        }
        SpeleothemThickness thickness = i == n - 1 ? SpeleothemThickness.TIP
                : i == n - 2 ? SpeleothemThickness.FRUSTUM
                : i == 0 ? SpeleothemThickness.BASE : SpeleothemThickness.MIDDLE;
        return state.setValue(SpeleothemBlock.TIP_DIRECTION, grow).setValue(SpeleothemBlock.THICKNESS, thickness);
    }

    public static void register() {
        PySift.LOGGER.debug("Registered feature {}", TYPE);
    }
}
