package pryuan05.pysift.block;

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.DoubleHighBlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.BonemealSource;
import net.minecraft.world.level.block.BushBlock;
import net.minecraft.world.level.block.DoublePlantBlock;
import net.minecraft.world.level.block.FlowerBedBlock;
import net.minecraft.world.level.block.FlowerBlock;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SaplingBlock;
import net.minecraft.world.level.block.grower.TreeGrower;
import net.minecraft.util.random.WeightedList;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.block.TallGrassBlock;
import net.minecraft.world.level.block.TintedParticleLeavesBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import pryuan05.pysift.PySift;
import pryuan05.pysift.fluid.ModFluids;
import pryuan05.pysift.item.ModItems;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

/**
 * The Sift 的柳樹與自然植被。暫時重用原版灰階貼圖，顏色由 {@link #TINTS} 決定
 * （tools/worldgen/build_vegetation.py 也從這張表產生物品的 tints，改顏色只改這裡）。
 */
public final class ModVegetation {
    public static final List<Block> ALL = new ArrayList<>();
    /** 方塊 → 染色（ARGB）。不在表中的方塊不染色。 */
    public static final Map<Block, Integer> TINTS = new LinkedHashMap<>();
    /**
     * 依腳下地板染色的植物 → 預設顏色（物品圖示、查不到地板時用）。實際顏色由 client 的 FloorTint 依植物下方那格方塊
     * 查 FloorTints 色表（tools/worldgen/make_floor_tints.py 產生）。
     */
    public static final Map<Block, Integer> FLOOR_TINTS = new LinkedHashMap<>();

    // ===== 靈魂柳 =====
    /** 樹幹。貼圖來自使用者的 soul_willow_sheet.png（tools/worldgen/make_soul_willow_textures.py），本身已上色，不染色。 */
    public static final Block SOUL_WILLOW_LOG = register("soul_willow_log", RotatedPillarBlock::new, Blocks.DARK_OAK_LOG, false);
    /** 樹冠三種葉子：貼圖本身已上色（不受生態域影響、不染色），由 configured feature 的 weighted foliage_provider 混合。 */
    public static final Block SOUL_WILLOW_LEAVES = register("soul_willow_leaves",
            p -> new TintedParticleLeavesBlock(0.01F, p), Blocks.OAK_LEAVES, false);
    public static final Block SOUL_WILLOW_LEAVES_PALE = register("soul_willow_leaves_pale",
            p -> new TintedParticleLeavesBlock(0.01F, p), Blocks.OAK_LEAVES, false);
    public static final Block GLOWING_SOUL_WILLOW_LEAVES = register("glowing_soul_willow_leaves",
            p -> new TintedParticleLeavesBlock(0.01F, p.lightLevel(state -> 12)), Blocks.OAK_LEAVES, false);
    /** 垂藤：四面藤蔓、無碰撞、可攀爬、剪刀採集；每個 shade 有自己的貼圖（顏色漸層）。 */
    public static final Block SOUL_WILLOW_VINE = register("soul_willow_vine",
            p -> new SoulWillowVineBlock(p.noOcclusion()), Blocks.VINE, false);
    public static final Block GLOWING_SOUL_WILLOW_VINE = register("glowing_soul_willow_vine",
            p -> new SoulWillowVineBlock(p.noOcclusion().lightLevel(state -> 11)), Blocks.VINE, false);
    /** 樹苗：單株長成一般靈魂柳（2×2 樹幹、高 8–10）；2×2 擺放的樹苗長成巨型靈魂柳。 */
    public static final ResourceKey<Feature> SOUL_WILLOW = ResourceKey.create(Registries.FEATURE, PySift.id("soul_willow"));
    public static final ResourceKey<Feature> SOUL_WILLOW_GIANT = ResourceKey.create(Registries.FEATURE, PySift.id("soul_willow_giant"));
    public static final TreeGrower SOUL_WILLOW_GROWER = new TreeGrower("pysift_soul_willow",   // trees, megaTrees, flowerTrees, shortest
            WeightedList.of(SOUL_WILLOW), WeightedList.of(SOUL_WILLOW_GIANT), WeightedList.of(SOUL_WILLOW), SOUL_WILLOW);
    public static final Block SOUL_WILLOW_SAPLING = tint(register("soul_willow_sapling",
            p -> new SaplingBlock(SOUL_WILLOW_GROWER, p), Blocks.OAK_SAPLING, false), 0xFF7FD6C8);

    // ===== 赤紅沉積地層區 =====
    public static final Block EMBER_GRASS = floorTint(register("ember_grass", SiftGrassBlock::new, Blocks.SHORT_GRASS, false), 0xFFF8B0A4);
    public static final Block TALL_EMBER_GRASS = floorTint(register("tall_ember_grass", DoublePlantBlock::new, Blocks.TALL_GRASS, true), 0xFFF8B0A4);

    // ===== 林地腐殖帶 =====
    public static final Block HUMUS_GRASS = tint(register("humus_grass", SiftGrassBlock::new, Blocks.SHORT_GRASS, false), 0xFF7CC79A);
    public static final Block TALL_HUMUS_GRASS = tint(register("tall_humus_grass", DoublePlantBlock::new, Blocks.TALL_GRASS, true), 0xFF7CC79A);
    public static final Block HUMUS_FERN = tint(register("humus_fern", SiftGrassBlock::new, Blocks.FERN, false), 0xFF5DAE8C);
    public static final Block HUMUS_BUSH = tint(register("humus_bush", BushBlock::new, Blocks.BUSH, false), 0xFFC7A8E0);

    // ===== 紫晶深板岩區 =====
    /** 深淵草：與餘燼草同樣的線條狀草叢（原 abyss_fern 深淵蕨改名）。 */
    public static final Block ABYSS_GRASS = floorTint(register("abyss_grass", SiftGrassBlock::new, Blocks.SHORT_GRASS, false), 0xFF7BE0D0);

    // ===== 影片風格的裝飾 =====
    /** 青色發光小蘑菇（紫區、柳林）。 */
    public static final Block GLOWCAP = register("glowcap",
            p -> new SiftGrassBlock(p.lightLevel(state -> 7)), Blocks.SHORT_GRASS, false);
    /** 白色骨珊瑚狀尖刺（紫區）。 */
    public static final Block BONE_SPIRE = register("bone_spire", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    /** 蓬鬆草團：兩格高，顏色依地板（粉壤上粉紅、紫地層上偏青）。 */
    public static final Block PUFF_GRASS = floorTint(register("puff_grass", DoublePlantBlock::new, Blocks.TALL_GRASS, true), 0xFFF08AB0);

    // ===== 共用 =====
    public static final Block GOLDEN_BLOOM = register("golden_bloom",
            p -> new FlowerBlock(MobEffects.NIGHT_VISION, 5.0F, p), Blocks.DANDELION, false);

    // ===== 地表 =====
    /** 柳絮林地的鮭魚粉地表（貼圖由 tools/worldgen/make_pink_loam.py 產生）。 */
    public static final Block SIFT_PINK_LOAM = register("sift_pink_loam", Block::new, Blocks.COARSE_DIRT, false);

    // ===== 大型平展花（一格寬的水平花瓣 + 低矮葉片；染色只作用在葉片） =====
    public static final Block SUN_BLOOM = register("sun_bloom",
            p -> new FlowerBlock(MobEffects.NIGHT_VISION, 5.0F, p), Blocks.DANDELION, false);
    public static final Block ROSE_BLOOM = register("rose_bloom",
            p -> new FlowerBlock(MobEffects.REGENERATION, 5.0F, p), Blocks.DANDELION, false);
    public static final Block DUSK_BLOOM = register("dusk_bloom",
            p -> new FlowerBlock(MobEffects.NIGHT_VISION, 5.0F, p), Blocks.DANDELION, false);

    // ===== 裂隙植被（使用者提供的 rift_dimension_flora_assets；資源由 tools/worldgen/install_rift_flora.py 安裝，尚未加入世界生成） =====
    public static final Block CRIMSON_SHORT_SPROUTS = register("crimson_short_sprouts", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    public static final Block CURLED_FERN_BLUE = register("curled_fern_blue", SiftGrassBlock::new, Blocks.FERN, false);
    public static final Block CURLED_FERN_PINK = register("curled_fern_pink", SiftGrassBlock::new, Blocks.FERN, false);
    public static final Block CURLED_FERN_WHITE = register("curled_fern_white", SiftGrassBlock::new, Blocks.FERN, false);
    public static final Block MINT_RIFT_GRASS = register("mint_rift_grass", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    public static final Block ORANGE_RIFT_GRASS = register("orange_rift_grass", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    public static final Block YELLOW_SHORT_GRASS = register("yellow_short_grass", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    public static final Block OLIVE_FORKED_STALK = register("olive_forked_stalk", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    public static final Block ORANGE_TALL_RIFT_GRASS = register("orange_tall_rift_grass", DoublePlantBlock::new, Blocks.TALL_GRASS, true);
    /** 立體植物：黃龍舌蘭、三色巨傘草（直接掉落自己）。 */
    public static final Block AGAVE_ROSETTE = register("agave_rosette", BushBlock::new, Blocks.BUSH, false);
    public static final Block GIANT_CANOPY_GREEN = register("giant_canopy_green", BushBlock::new, Blocks.BUSH, false);
    public static final Block GIANT_CANOPY_BLUE = register("giant_canopy_blue", BushBlock::new, Blocks.BUSH, false);
    public static final Block GIANT_CANOPY_WHITE = register("giant_canopy_white", BushBlock::new, Blocks.BUSH, false);
    public static final Block CLUSTERED_YELLOW_FLOWERS = register("clustered_yellow_flowers",
            p -> new FlowerBlock(MobEffects.SPEED, 5.0F, p), Blocks.DANDELION, false);

    // ===== 影片 The Sift 章節補上的植物（資源由 tools/models/gen_batch3.py 產生） =====
    /** 高發光草：兩格高的青色粗葉草，葉間有發光黃點；顏色依地板，本身微微發光。 */
    public static final Block TALL_GLOW_GRASS = floorTint(register("tall_glow_grass",
            p -> new DoublePlantBlock(p.lightLevel(state -> 5)), Blocks.TALL_GRASS, true), 0xFF7BE0D0);
    /** 珊瑚落葉地毯：像粉紅花瓣，可疊 1~4 層。 */
    public static final Block CORAL_LEAF_CARPET = register("coral_leaf_carpet", p -> new FlowerBedBlock(p, 3), Blocks.PINK_PETALS, false);

    // ===== 影片風格柔和草地與短草／高草（額外方塊） =====
    public static final Block CRIMSON_SHORT_GRASS = register("crimson_short_grass", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    public static final Block CRIMSON_TALL_GRASS = register("crimson_tall_grass", DoublePlantBlock::new, Blocks.TALL_GRASS, true);

    private ModVegetation() {
    }

    private static Block register(String name, Function<BlockBehaviour.Properties, Block> factory, Block copyFrom, boolean doubleHigh) {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Block block = factory.apply(BlockBehaviour.Properties.ofFullCopy(copyFrom).setId(blockKey));
        Registry.register(BuiltInRegistries.BLOCK, blockKey, block);
        Item.Properties itemProperties = new Item.Properties().setId(itemKey);
        if (copyFrom == Blocks.DARK_OAK_LOG) {   // 靈魂柳原木：和原版原木一樣可以當燃料（其餘木製品見 SoulWillowWood）
            itemProperties.cookingFuel(net.minecraft.world.level.storage.loot.providers.number.ints.ContextIntProviders.COOKING_TIME_WOOD_BLOCKS);
        }
        Registry.register(BuiltInRegistries.ITEM, itemKey,
                doubleHigh ? new DoubleHighBlockItem(block, itemProperties) : new BlockItem(block, itemProperties));
        ALL.add(block);
        return block;
    }

    private static Block floorTint(Block block, int defaultArgb) {
        FLOOR_TINTS.put(block, defaultArgb);
        return block;
    }

    private static Block tint(Block block, int argb) {
        TINTS.put(block, argb);
        return block;
    }

    /** 草叢與蕨：不會被骨粉催成原版的高草。 */
    public static class SiftGrassBlock extends TallGrassBlock {
        public SiftGrassBlock(BlockBehaviour.Properties properties) {
            super(properties);
        }

        @Override
        public boolean isValidBonemealTarget(LevelReader level, BlockPos pos, BlockState state, BonemealSource source) {
            return false;
        }
    }

    public static void registerModVegetation() {
        // 世界生成用到的植被放主方塊分頁，沒用到的（ModItems.NOT_IN_WORLDGEN）放「未使用方塊」分頁
        CreativeModeTabEvents.modifyOutputEvent(ModItems.BLOCKS_TAB_KEY).register(output -> {
            ALL.stream().filter(b -> !b.defaultBlockState().is(ModItems.NOT_IN_WORLDGEN)).forEach(output::accept);
            output.accept(ModFluids.SPIRIT_LIQUID_BUCKET);
        });
        CreativeModeTabEvents.modifyOutputEvent(ModItems.UNUSED_BLOCKS_TAB_KEY).register(output ->
                ALL.stream().filter(b -> b.defaultBlockState().is(ModItems.NOT_IN_WORLDGEN)).forEach(output::accept));
        PySift.LOGGER.info("Registered {} Sift vegetation blocks", ALL.size());
    }
}
