package pryuan05.pysift.worldgen;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockIgnoreProcessor;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import pryuan05.pysift.PySift;

import java.util.List;
import java.util.Optional;

/**
 * 迅從者荒原（Dungeons II 的 Humbler Huskland）沙地上到處插著的小化石：肋骨拱、一段脊椎、頭骨、爪子，
 * 隨機轉向、往沙裡埋 1～2 格。結構檔由 tools/worldgen/build_landmarks.py 產生（data/pysift/structure/fossil/）。
 * 只蓋骨頭本身，不清空周圍（模板裡的空氣不會挖掉沙子）。
 * 不懸空：先算出轉向後整個化石佔的每一欄地面高度，底部對齊其中最低的那一欄再往下埋，所以每根骨頭底下都是沙；
 * 佔地內高低差超過 {@link #MAX_SLOPE} 格（陡坡、懸崖邊）或原點有液體時不生成。
 */
public record SurfaceFossilFeature() implements Feature {
    public static final MapCodec<SurfaceFossilFeature> CODEC = MapCodec.unit(new SurfaceFossilFeature());
    public static final MapCodec<SurfaceFossilFeature> TYPE = Registry.register(BuiltInRegistries.FEATURE_TYPE, PySift.id("surface_fossil"), CODEC);
    private static final List<String> FOSSILS = List.of("fossil/rib_arch", "fossil/spine", "fossil/skull", "fossil/claw");
    private static final int MAX_SLOPE = 3;

    @Override
    public MapCodec<SurfaceFossilFeature> codec() {
        return CODEC;
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        Optional<StructureTemplate> template = level.getLevel().getStructureTemplateManager()
                .get(PySift.id(FOSSILS.get(random.nextInt(FOSSILS.size()))));
        if (template.isEmpty()) {
            return false;
        }
        Rotation rotation = Rotation.getRandom(random);
        StructurePlaceSettings settings = new StructurePlaceSettings().setRotation(rotation)
                .addProcessor(BlockIgnoreProcessor.STRUCTURE_AND_AIR).setIgnoreEntities(true);
        int y = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, origin.getX(), origin.getZ());
        if (!level.getFluidState(new BlockPos(origin.getX(), y - 1, origin.getZ())).isEmpty()) {
            return false;
        }
        // footprint of the rotated template: the lowest ground in it decides the height, so nothing hangs in the air
        BoundingBox box = template.get().getBoundingBox(settings, new BlockPos(origin.getX(), y, origin.getZ()));
        int lowest = Integer.MAX_VALUE, highest = Integer.MIN_VALUE;
        for (int x = box.minX(); x <= box.maxX(); x++) {
            for (int z = box.minZ(); z <= box.maxZ(); z++) {
                int h = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, x, z);
                lowest = Math.min(lowest, h);
                highest = Math.max(highest, h);
            }
        }
        if (highest - lowest > MAX_SLOPE) {
            return false;
        }
        BlockPos pos = new BlockPos(origin.getX(), lowest - 1 - random.nextInt(2), origin.getZ());
        template.get().placeInWorld(level, pos, pos, settings, random, Block.UPDATE_CLIENTS);
        return true;
    }

    public static void register() {
        PySift.LOGGER.debug("Registered feature {}", TYPE);
    }
}
