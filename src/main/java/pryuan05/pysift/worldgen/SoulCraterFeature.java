package pryuan05.pysift.worldgen;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.densityfunction.DensityFunction;
import net.minecraft.world.level.levelgen.feature.Feature;
import pryuan05.pysift.PySift;

/**
 * 靈魂火山高原的火山口湖：火山是密度函數畫的圓錐（tools/worldgen/build_the_sift.py 的 SOUL_CONE），每個
 * CELL × CELL 格子最多一座，中心從格子中央隨機偏移（密度函數 volcano_jx／volcano_jz）。這裡直接計算同一組密度函數
 * 取得中心與是否有火山（soul_core），把火山口裡低於 LAKE_LEVEL 的空氣填成靈液，湖面一定是平的；
 * 火山口地板與內壁重鋪成焦紅的岩石（像 Terralith 的 crater_fixer）。
 */
public record SoulCraterFeature() implements Feature {
    public static final MapCodec<SoulCraterFeature> CODEC = MapCodec.unit(new SoulCraterFeature());
    public static final MapCodec<SoulCraterFeature> TYPE = Registry.register(BuiltInRegistries.FEATURE_TYPE, PySift.id("soul_crater"), CODEC);

    /** 與 build_the_sift.py 的 VOLCANO_CELL、CRATER_FLOOR、LAKE_LEVEL、LAKE_RADIUS、CRATER_RADIUS 相同。 */
    public static final int CELL = 256, FLOOR = 112, LAKE_LEVEL = 115, LAKE_RADIUS = 16, CRATER_RADIUS = 21;

    @Override
    public MapCodec<SoulCraterFeature> codec() {
        return CODEC;
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        int x0 = origin.getX() & ~15, z0 = origin.getZ() & ~15;
        RandomState state = level.getLevel().getChunkSource().randomState();
        if (state.sampleBlockValueUncached(function(level, "soul_core"), x0 + 8, 0, z0 + 8) < 0.99f) {
            return false;                                       // no volcano in this cell (or it would reach the biome's edge)
        }
        double cx = Math.floorDiv(x0 + 8, CELL) * CELL + CELL / 2 + state.sampleBlockValueUncached(function(level, "volcano_jx"), x0 + 8, 0, z0 + 8);
        double cz = Math.floorDiv(z0 + 8, CELL) * CELL + CELL / 2 + state.sampleBlockValueUncached(function(level, "volcano_jz"), x0 + 8, 0, z0 + 8);
        if (Math.abs(x0 + 7.5 - cx) > CRATER_RADIUS + 12 || Math.abs(z0 + 7.5 - cz) > CRATER_RADIUS + 12) {
            return false;
        }
        BlockState liquid = block("spirit_liquid");
        BlockState crimson = block("crimson_capped_void_stone");
        BlockState[] vein = new BlockState[4];
        BlockState slate = block("magma_vein_slate");
        IntegerProperty veinLevel = (IntegerProperty) slate.getBlock().getStateDefinition().getProperty("vein");
        for (int v = 0; v < 4; v++) {
            vein[v] = slate.setValue(veinLevel, v);
        }
        boolean placed = false;
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int x = x0; x < x0 + 16; x++) {
            for (int z = z0; z < z0 + 16; z++) {
                double r = Math.hypot(x - cx, z - cz);
                if (r > CRATER_RADIUS) {
                    continue;
                }
                int top = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, x, z) - 1;
                if (top < FLOOR - 6 || top > 150) {
                    continue;                                   // no volcano here (plateau far below the crater floor)
                }
                // repaint the crater floor and inner wall: magma veins grow inward, the rim vein 0, the centre a little vein 3
                double ring = r + random.nextDouble() * 3.0 - 1.5;       // ragged ring borders
                float roll = random.nextFloat();
                BlockState paint = ring > 18 ? (roll < 0.3f ? crimson : vein[0])
                        : ring > 15 ? vein[1]
                        : ring > 11 ? vein[2]
                        : roll < 0.25f ? vein[3] : vein[2];
                for (int y = top; y > top - 2; y--) {
                    pos.set(x, y, z);
                    if (!level.getBlockState(pos).isAir()) {
                        level.setBlock(pos, paint, Block.UPDATE_CLIENTS);
                    }
                }
                if (r <= LAKE_RADIUS && top < LAKE_LEVEL) {
                    for (int y = top + 1; y <= LAKE_LEVEL; y++) {
                        pos.set(x, y, z);
                        if (level.getBlockState(pos).isAir()) {
                            level.setBlock(pos, liquid, Block.UPDATE_CLIENTS);
                        }
                    }
                }
                placed = true;
            }
        }
        return placed;
    }

    private static DensityFunction function(WorldGenLevel level, String name) {
        return level.registryAccess().lookupOrThrow(Registries.DENSITY_FUNCTION).getValueOrThrow(
                ResourceKey.create(Registries.DENSITY_FUNCTION, PySift.id("the_sift/terrain/" + name)));
    }

    private static BlockState block(String name) {
        return BuiltInRegistries.BLOCK.getValue(PySift.id(name)).defaultBlockState();
    }

    public static void register() {
        PySift.LOGGER.debug("Registered feature {}", TYPE);
    }
}
