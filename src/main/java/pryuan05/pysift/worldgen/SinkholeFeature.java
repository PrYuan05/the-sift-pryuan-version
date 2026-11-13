package pryuan05.pysift.worldgen;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import pryuan05.pysift.PySift;

/**
 * 天坑（v2.1.0 地底分層）：連接表層與地底的洞口。隙浮的「血管」在這裡裂到地表：
 * 漏斗形的洞口往下收成豎井，最底下接一個鐘形的小洞室，剛好落在乾涸淺層（地表下 26 格以上）的深度，
 * 所以不論下面有沒有天然洞穴，天坑本身都有底；碰到天然洞穴就自然接通。
 * 約三分之一的天坑在井壁上有一個靈液泉眼，靈液沿豎井流成一道細瀑布，落進洞底嵌在地面的小水池（池邊有地層石圍住，不會漫開，洞室保持乾燥）。洞室裡長赤紅幽匿與 charoite。
 * 只動以區塊中心為圓心、半徑 {@link #MAX_RADIUS} 的範圍（不跨出本區塊，避免被鄰近區塊截斷）。
 * 由 tools/worldgen/build_the_sift.py 在各地表生態域的 local_modifications 階段放置。
 */
public record SinkholeFeature() implements Feature {
    public static final MapCodec<SinkholeFeature> CODEC = MapCodec.unit(new SinkholeFeature());
    public static final MapCodec<SinkholeFeature> TYPE = Registry.register(BuiltInRegistries.FEATURE_TYPE, PySift.id("sinkhole"), CODEC);

    /** 洞口最大半徑（漏斗頂）；加上起伏後不超過 8，剛好留在放置的區塊內。 */
    public static final int MAX_RADIUS = 7;
    /** 豎井半徑、洞室半徑、從中心地表算起的總深度、豎井結束（洞室開始擴張）的深度。 */
    public static final double SHAFT_RADIUS = 2.4, CHAMBER_RADIUS = 6.0;
    public static final int DEPTH = 34, FUNNEL_DEPTH = 14, CHAMBER_START = 28;
    /** 地表太低（水邊、池子）或太陡就不挖。 */
    public static final int MIN_SURFACE = 66, MAX_SLOPE = 7;

    @Override
    public MapCodec<SinkholeFeature> codec() {
        return CODEC;
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        int cx = (origin.getX() & ~15) + 8, cz = (origin.getZ() & ~15) + 8;
        int top = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, cx, cz) - 1;
        int bottom = top - DEPTH;
        if (top < MIN_SURFACE || bottom < level.getMinY() + 12) {
            return false;
        }
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        // the centre must be dry solid ground and the surroundings reasonably flat
        pos.set(cx, top, cz);
        if (level.getBlockState(pos).isAir() || !level.getBlockState(pos).getFluidState().isEmpty()) {
            return false;
        }
        for (int[] d : new int[][]{{6, 0}, {-6, 0}, {0, 6}, {0, -6}}) {
            int h = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, cx + d[0], cz + d[1]) - 1;
            if (Math.abs(h - top) > MAX_SLOPE) {
                return false;
            }
        }
        double phase1 = random.nextDouble() * Math.PI * 2, phase2 = random.nextDouble() * Math.PI * 2;
        boolean spirit = random.nextInt(3) == 0;
        BlockState air = Blocks.AIR.defaultBlockState();
        BlockState redSculk = block("red_sculk");
        BlockState floorStone = block("varied_dark_slate");

        // carve: column by column, from the highest surface in the footprint down to the chamber floor
        for (int x = cx - MAX_RADIUS - 1; x <= cx + MAX_RADIUS + 1; x++) {
            for (int z = cz - MAX_RADIUS - 1; z <= cz + MAX_RADIUS + 1; z++) {
                double dx = x - cx, dz = z - cz, r = Math.hypot(dx, dz);
                double angle = Math.atan2(dz, dx);
                double wobble = 1.0 + 0.16 * Math.sin(3 * angle + phase1) + 0.10 * Math.sin(5 * angle + phase2);
                int colTop = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, x, z);
                for (int y = Math.max(colTop, top + 1); y >= bottom; y--) {
                    int d = top - y;                          // depth below the centre surface (negative = above it)
                    double limit = radiusAt(Math.max(d, 0)) * wobble;
                    if (r > limit) {
                        continue;
                    }
                    pos.set(x, y, z);
                    BlockState current = level.getBlockState(pos);
                    if (current.isAir() || current.is(Blocks.BEDROCK)) {
                        continue;
                    }
                    level.setBlock(pos, y == bottom ? floorStone : air, Block.UPDATE_CLIENTS);
                }
            }
        }
        // floor of the chamber: silted strata, red sculk patches (the vein is alive: spirit liquid reaches here)
        for (int x = cx - 7; x <= cx + 7; x++) {
            for (int z = cz - 7; z <= cz + 7; z++) {
                double r = Math.hypot(x - cx, z - cz);
                if (r > CHAMBER_RADIUS * 1.15) {
                    continue;
                }
                pos.set(x, bottom, z);
                if (level.getBlockState(pos).isAir()) {
                    continue;
                }
                if (r <= CHAMBER_RADIUS * 0.9) {
                    level.setBlock(pos, random.nextFloat() < 0.55f ? redSculk : floorStone, Block.UPDATE_CLIENTS);
                }
                pos.set(x, bottom + 1, z);
                if (random.nextInt(26) == 0 && level.getBlockState(pos).isAir()) {
                    level.setBlock(pos, block("charoite_cluster"), Block.UPDATE_CLIENTS);
                }
            }
        }
        if (spirit) {
            spiritFall(level, cx, cz, top, bottom, random);
        }
        // vines hanging down the funnel and shaft walls (the same wall-plant placement the cliffs use)
        net.minecraft.world.level.block.Block vine = BuiltInRegistries.BLOCK.getValue(PySift.id("green_sift_vine"));
        new WallPlantFeature(vine, 36, 2, 6, 6, 9).place(level, generator, random, new BlockPos(cx, top - 8, cz));
        return true;
    }


    /**
     * A small spirit spring instead of a flood: a single source is set into the shaft wall a little below the funnel, so it
     * runs out into the shaft and falls straight down; the stream lands on a small basin of sources sunk into the chamber
     * floor (a source level with the floor, boxed in by floor stone), where it merges instead of spreading, so the chamber
     * stays dry apart from the basin. Nothing is placed if no wall is found.
     */
    private static void spiritFall(WorldGenLevel level, int cx, int cz, int top, int bottom, RandomSource random) {
        BlockState liquid = block("spirit_liquid");
        BlockState floorStone = block("varied_dark_slate");
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        int y = top - FUNNEL_DEPTH - 3;                          // in the straight part of the shaft
        int wallX = Integer.MIN_VALUE;
        for (int x = cx + 1; x <= cx + 6; x++) {                // walk out from the shaft axis to the first wall
            pos.set(x, y, cz);
            if (!level.getBlockState(pos).isAir()) {
                wallX = x;
                break;
            }
        }
        if (wallX == Integer.MIN_VALUE) {
            return;
        }
        int streamX = wallX - 1;                                // the shaft cell the spring runs into
        // the stream must fall all the way to the chamber floor: the column has to be open
        for (int yy = y; yy > bottom; yy--) {
            pos.set(streamX, yy, cz);
            if (!level.getBlockState(pos).isAir()) {
                return;
            }
        }
        pos.set(wallX, y, cz);
        level.setBlock(pos, liquid, Block.UPDATE_CLIENTS);
        level.scheduleTick(pos, liquid.getFluidState().getType(), 0);
        // the basin: sources level with the floor around the landing point, floor stone all around it
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                pos.set(streamX + dx, bottom, cz + dz);
                if (level.getBlockState(pos).isAir()) {
                    continue;
                }
                boolean inside = dx * dx + dz * dz <= 2;
                level.setBlock(pos, inside ? liquid : floorStone, Block.UPDATE_CLIENTS);
                if (!inside) {
                    pos.set(streamX + dx, bottom + 1, cz + dz);
                    if (level.getBlockState(pos).is(block("charoite_cluster").getBlock())) {
                        level.setBlock(pos, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
                    }
                }
            }
        }
    }

    /** Radius of the hole at the given depth below the centre surface: funnel, shaft, then the bell-shaped chamber. */
    static double radiusAt(int d) {
        if (d <= FUNNEL_DEPTH) {
            double t = 1.0 - (double) d / FUNNEL_DEPTH;                 // 1 at the rim, 0 where the shaft starts
            return SHAFT_RADIUS + (MAX_RADIUS - 1 - SHAFT_RADIUS) * t * t;
        }
        if (d < CHAMBER_START) {
            return SHAFT_RADIUS;
        }
        double t = (double) (d - CHAMBER_START) / (DEPTH - CHAMBER_START);   // 0 .. 1 over the chamber's height
        return SHAFT_RADIUS + (CHAMBER_RADIUS - SHAFT_RADIUS) * Math.sin(t * Math.PI / 2);
    }

    private static BlockState block(String name) {
        return BuiltInRegistries.BLOCK.getValue(PySift.id(name)).defaultBlockState();
    }

    public static void register() {
        PySift.LOGGER.debug("Registered feature {}", TYPE);
    }
}
