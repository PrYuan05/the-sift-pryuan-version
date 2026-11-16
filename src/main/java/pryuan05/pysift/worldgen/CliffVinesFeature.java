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
import pryuan05.pysift.block.ModVegetation;
import pryuan05.pysift.block.SoulWillowVineBlock;

/**
 * 懸崖與岩壁垂藤特徵（Cliff & Wall Vines）：
 * 在 The Sift 維度的懸崖邊緣、峽谷峭壁側面、桌山斷崖與湖畔岩壁自然生成垂掛的靈魂柳藤蔓與微量發光垂藤。
 */
public record CliffVinesFeature(
        int tries,
        int minLength,
        int maxLength,
        float glowChance,
        int xzSpread,
        int ySpread
) implements Feature {

    public static final MapCodec<CliffVinesFeature> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            Codec.intRange(1, 256).fieldOf("tries").forGetter(CliffVinesFeature::tries),
            Codec.intRange(1, 32).fieldOf("min_length").forGetter(CliffVinesFeature::minLength),
            Codec.intRange(1, 64).fieldOf("max_length").forGetter(CliffVinesFeature::maxLength),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("glow_chance", 0.15F).forGetter(CliffVinesFeature::glowChance),
            Codec.intRange(1, 32).optionalFieldOf("xz_spread", 8).forGetter(CliffVinesFeature::xzSpread),
            Codec.intRange(1, 64).optionalFieldOf("y_spread", 16).forGetter(CliffVinesFeature::ySpread)
    ).apply(instance, CliffVinesFeature::new));

    public static final MapCodec<CliffVinesFeature> TYPE = Registry.register(
            BuiltInRegistries.FEATURE_TYPE, PySift.id("cliff_vines"), CODEC);

    @Override
    public MapCodec<CliffVinesFeature> codec() {
        return CODEC;
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        boolean placedAny = false;
        BlockPos.MutableBlockPos testPos = new BlockPos.MutableBlockPos();
        BlockPos.MutableBlockPos vinePos = new BlockPos.MutableBlockPos();

        for (int i = 0; i < tries; i++) {
            int rx = origin.getX() + random.nextInt(xzSpread * 2 + 1) - xzSpread;
            int rz = origin.getZ() + random.nextInt(xzSpread * 2 + 1) - xzSpread;
            int ry = origin.getY() + random.nextInt(ySpread * 2 + 1) - ySpread;
            testPos.set(rx, ry, rz);

            if (!level.getBlockState(testPos).isAir()) {
                continue;
            }

            // 必須是懸崖或峭壁：下方至少有一格空氣，且水平方向至少有一面是實心岩壁，或上方是實心天花板
            if (!level.getBlockState(testPos.below()).isAir()) {
                continue;
            }

            boolean hasSturdyWall = false;
            boolean northWall = false;
            boolean eastWall = false;
            boolean southWall = false;
            boolean westWall = false;

            for (Direction dir : Direction.Plane.HORIZONTAL) {
                BlockPos neighbor = testPos.relative(dir);
                if (level.getBlockState(neighbor).isFaceSturdy(level, neighbor, dir.getOpposite())) {
                    hasSturdyWall = true;
                    if (dir == Direction.NORTH) northWall = true;
                    if (dir == Direction.EAST) eastWall = true;
                    if (dir == Direction.SOUTH) southWall = true;
                    if (dir == Direction.WEST) westWall = true;
                }
            }

            boolean hasCeiling = level.getBlockState(testPos.above()).isFaceSturdy(level, testPos.above(), Direction.DOWN)
                    || level.getBlockState(testPos.above()).is(SoulWillowVineBlock.SUPPORTS);

            if (!hasSturdyWall && !hasCeiling) {
                continue;
            }

            // 垂掛藤蔓長度
            int length = minLength + (maxLength > minLength ? random.nextInt(maxLength - minLength + 1) : 0);
            Block vineBlock = random.nextFloat() < glowChance ? ModVegetation.GLOWING_SOUL_WILLOW_VINE : ModVegetation.SOUL_WILLOW_VINE;

            // 若有天花板但沒有側牆，則預設兩面或四面開啟
            if (!hasSturdyWall) {
                if (random.nextBoolean()) {
                    northWall = true;
                    southWall = true;
                } else {
                    eastWall = true;
                    westWall = true;
                }
            }

            for (int step = 0; step < length; step++) {
                vinePos.set(testPos.getX(), testPos.getY() - step, testPos.getZ());
                if (!level.getBlockState(vinePos).isAir()) {
                    break;
                }

                // 動態檢查當前格的岩壁支撐（若岩壁向下延續則貼著）
                boolean curNorth = northWall && (step == 0 || level.getBlockState(vinePos.north()).isFaceSturdy(level, vinePos.north(), Direction.SOUTH) || hasCeiling);
                boolean curEast = eastWall && (step == 0 || level.getBlockState(vinePos.east()).isFaceSturdy(level, vinePos.east(), Direction.WEST) || hasCeiling);
                boolean curSouth = southWall && (step == 0 || level.getBlockState(vinePos.south()).isFaceSturdy(level, vinePos.south(), Direction.NORTH) || hasCeiling);
                boolean curWest = westWall && (step == 0 || level.getBlockState(vinePos.west()).isFaceSturdy(level, vinePos.west(), Direction.EAST) || hasCeiling);

                // 至少保留前一段開啟的面，使整串垂簾垂下時不中斷
                if (!curNorth && !curEast && !curSouth && !curWest) {
                    curNorth = northWall;
                    curEast = eastWall;
                    curSouth = southWall;
                    curWest = westWall;
                }

                boolean tip = (step == length - 1) || !level.getBlockState(vinePos.below()).isAir();
                int shade = step == 0 ? 0 : (tip || step >= length - 2 ? 2 : 1);

                BlockState state = vineBlock.defaultBlockState()
                        .setValue(SoulWillowVineBlock.TIP, tip)
                        .setValue(SoulWillowVineBlock.SHADE, shade)
                        .setValue(SoulWillowVineBlock.NORTH, curNorth)
                        .setValue(SoulWillowVineBlock.EAST, curEast)
                        .setValue(SoulWillowVineBlock.SOUTH, curSouth)
                        .setValue(SoulWillowVineBlock.WEST, curWest);

                level.setBlock(vinePos, state, 2);
                placedAny = true;

                if (tip) {
                    break;
                }
            }
        }
        return placedAny;
    }

    public static void register() {
        PySift.LOGGER.info("Registered feature type {}", BuiltInRegistries.FEATURE_TYPE.getKey(TYPE));
    }
}
