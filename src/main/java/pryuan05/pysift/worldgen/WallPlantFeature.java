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
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.feature.Feature;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.SiftWallPlantBlock;

/**
 * 貼牆植物特徵：在岩壁、峭壁側面找空氣格，貼著旁邊的實心面放一株 {@link SiftWallPlantBlock}，
 * 再沿著同一面牆往下延伸（藤蔓）最多 max_length 格。
 */
public record WallPlantFeature(Block block, int tries, int minLength, int maxLength, int xzSpread, int ySpread) implements Feature {

    public static final MapCodec<WallPlantFeature> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            BuiltInRegistries.BLOCK.byNameCodec().fieldOf("block").forGetter(WallPlantFeature::block),
            Codec.intRange(1, 256).fieldOf("tries").forGetter(WallPlantFeature::tries),
            Codec.intRange(1, 32).optionalFieldOf("min_length", 1).forGetter(WallPlantFeature::minLength),
            Codec.intRange(1, 32).optionalFieldOf("max_length", 1).forGetter(WallPlantFeature::maxLength),
            Codec.intRange(1, 32).optionalFieldOf("xz_spread", 8).forGetter(WallPlantFeature::xzSpread),
            Codec.intRange(1, 64).optionalFieldOf("y_spread", 16).forGetter(WallPlantFeature::ySpread)
    ).apply(instance, WallPlantFeature::new));

    public static final MapCodec<WallPlantFeature> TYPE = Registry.register(
            BuiltInRegistries.FEATURE_TYPE, PySift.id("wall_plant"), CODEC);

    @Override
    public MapCodec<WallPlantFeature> codec() {
        return CODEC;
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        if (!(block instanceof SiftWallPlantBlock)) {
            return false;
        }
        boolean placedAny = false;
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int i = 0; i < tries; i++) {
            pos.set(origin.getX() + random.nextInt(xzSpread * 2 + 1) - xzSpread,
                    origin.getY() + random.nextInt(ySpread * 2 + 1) - ySpread,
                    origin.getZ() + random.nextInt(xzSpread * 2 + 1) - xzSpread);
            if (!level.getBlockState(pos).isAir()) {
                continue;
            }
            // 隨機挑一個有實心牆的水平方向；植物朝外（facing = 牆的反方向）
            BlockState state = null;
            int start = random.nextInt(4);
            for (int k = 0; k < 4 && state == null; k++) {
                Direction wall = Direction.from2DDataValue((start + k) % 4);
                BlockState candidate = block.defaultBlockState().setValue(SiftWallPlantBlock.FACING, wall.getOpposite());
                if (candidate.canSurvive(level, pos)) {
                    state = candidate;
                }
            }
            if (state == null) {
                continue;
            }
            int length = minLength + (maxLength > minLength ? random.nextInt(maxLength - minLength + 1) : 0);
            for (int step = 0; step < length; step++) {
                if (step > 0 && (!level.getBlockState(pos).isAir() || !state.canSurvive(level, pos))) {
                    break;
                }
                level.setBlock(pos, state, 2);
                placedAny = true;
                pos.move(Direction.DOWN);
            }
        }
        return placedAny;
    }

    public static void register() {
        PySift.LOGGER.info("Registered feature type {}", BuiltInRegistries.FEATURE_TYPE.getKey(TYPE));
    }
}
