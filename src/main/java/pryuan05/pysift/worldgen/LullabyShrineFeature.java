package pryuan05.pysift.worldgen;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.Vec3i;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.ModBlocks;

import java.util.Optional;

/**
 * 搖籃曲山丘神殿（Dungeons II 的 Lullaby Hilltop）：只蓋在山頂上（比周圍一圈平均高 4 格以上，一圈 12 點裡最多 2 點跟它一樣高，
 * 允許台地的邊緣），
 * 圓形石台、六根柱子、中央唱片機和一圈音符盒，兩隻迴音傀儡在這裡哼搖籃曲。
 * 結構檔 data/pysift/structure/lullaby_shrine.nbt（tools/worldgen/build_landmarks.py；最底層是地台）。
 * 地台懸空的部分往下補到地面。
 */
public record LullabyShrineFeature() implements Feature {
    public static final MapCodec<LullabyShrineFeature> CODEC = MapCodec.unit(new LullabyShrineFeature());
    public static final MapCodec<LullabyShrineFeature> TYPE = Registry.register(BuiltInRegistries.FEATURE_TYPE, PySift.id("lullaby_shrine"), CODEC);
    private static final int RING = 12;
    private static final int MIN_PROMINENCE = 4;
    private static final int MAX_HIGHER = 2;

    @Override
    public MapCodec<LullabyShrineFeature> codec() {
        return CODEC;
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        // 這個區塊裡最高的一點（4 x 4 取樣）
        int baseX = origin.getX() & ~15, baseZ = origin.getZ() & ~15;
        BlockPos peak = null;
        for (int dx = 2; dx < 16; dx += 4) {
            for (int dz = 2; dz < 16; dz += 4) {
                int y = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, baseX + dx, baseZ + dz);
                if (peak == null || y > peak.getY()) {
                    peak = new BlockPos(baseX + dx, y, baseZ + dz);
                }
            }
        }
        if (peak == null || !level.getFluidState(peak.below()).isEmpty()) {
            return false;
        }
        // 山頂：周圍一圈幾乎都比它低（最多 MAX_HIGHER 點不低），平均低 MIN_PROMINENCE 格以上
        int sum = 0, higher = 0;
        for (int i = 0; i < 12; i++) {
            double a = i * Math.PI / 6;
            int y = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, peak.getX() + (int) Math.round(RING * Math.cos(a)),
                    peak.getZ() + (int) Math.round(RING * Math.sin(a)));
            if (y >= peak.getY() && ++higher > MAX_HIGHER) {
                return false;
            }
            sum += y;
        }
        if (peak.getY() - sum / 12.0 < MIN_PROMINENCE) {
            return false;
        }
        Optional<StructureTemplate> template = level.getLevel().getStructureTemplateManager().get(PySift.id("lullaby_shrine"));
        if (template.isEmpty()) {
            return false;
        }
        Rotation rotation = Rotation.getRandom(random);
        StructurePlaceSettings settings = new StructurePlaceSettings().setRotation(rotation).setFinalizeEntities(true);
        Vec3i size = template.get().getSize();
        BlockPos centre = new BlockPos(size.getX() / 2, 0, size.getZ() / 2);
        BlockPos corner = peak.below().subtract(StructureTemplate.calculateRelativePosition(settings, centre));
        template.get().placeInWorld(level, corner, corner, settings, random, Block.UPDATE_CLIENTS);
        // 地台（最底層）懸空的地方往下補到地面
        BlockState fill = ModBlocks.BY_NAME.getOrDefault("dark_slate", net.minecraft.world.level.block.Blocks.DEEPSLATE).defaultBlockState();
        BoundingBox box = template.get().getBoundingBox(settings, corner);
        for (int x = box.minX(); x <= box.maxX(); x++) {
            for (int z = box.minZ(); z <= box.maxZ(); z++) {
                BlockPos floor = new BlockPos(x, corner.getY(), z);
                if (level.getBlockState(floor).isAir()) {
                    continue;
                }
                for (int d = 1; d <= 12 && level.getBlockState(floor.below(d)).canBeReplaced(); d++) {
                    level.setBlock(floor.below(d), fill, Block.UPDATE_CLIENTS);
                }
            }
        }
        return true;
    }

    public static void register() {
        PySift.LOGGER.debug("Registered feature {}", TYPE);
    }
}
