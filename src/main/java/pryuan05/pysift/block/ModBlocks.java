package pryuan05.pysift.block;

import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.BlockItemStateProperties;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.block.state.properties.Property;
import pryuan05.pysift.PySift;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * The Sift 方塊註冊。方塊定義來自 blockstate_restructure 的 REGISTRY.md（layered_strata 已拆成 18 個獨立方塊）。
 * 狀態屬性的名稱與取值範圍必須與 assets/pysift/blockstates/*.json 一致；挖掘工具由 mineable 標籤決定。
 */
public class ModBlocks {
    public static final List<Block> ALL_BLOCKS = new ArrayList<>();
    public static final Map<String, Block> BY_NAME = new LinkedHashMap<>();

    /** 沿用原 295 款方塊的六種材質組合；各方塊的材質依其貼圖對應的舊方塊多數決而來。 */
    enum Mat {
        STONE(1.5f, 6.0f, SoundType.STONE),
        DEEPSLATE(3.0f, 6.0f, SoundType.DEEPSLATE),
        WOOD(2.0f, 3.0f, SoundType.WOOD),
        GRAVEL(0.5f, 0.5f, SoundType.GRAVEL),
        SAND(0.5f, 0.5f, SoundType.SAND),
        GRASS(0.6f, 0.6f, SoundType.GRASS);

        private final float destroyTime;
        private final float explosionResistance;
        private final SoundType sound;

        Mat(float destroyTime, float explosionResistance, SoundType sound) {
            this.destroyTime = destroyTime;
            this.explosionResistance = explosionResistance;
            this.sound = sound;
        }

        BlockBehaviour.Properties properties() {
            return BlockBehaviour.Properties.of().destroyTime(destroyTime).explosionResistance(explosionResistance).sound(sound);
        }
    }

    record Def(String name, Mat mat, SiftStateBlock.Shape shape, List<Property<?>> properties) {
        Def intProp(String property, int min, int max) {
            return with(IntegerProperty.create(property, min, max));
        }

        <T extends Enum<T> & StringRepresentable> Def enumProp(String property, Class<T> type) {
            return with(EnumProperty.create(property, type));
        }

        /** 色調標籤：tone 屬性只開放列出的值，順序即 blockstate 與創造模式分頁的順序，第一個為預設。 */
        Def tones(String... names) {
            return with(EnumProperty.create("tone", SiftStateProperties.Tone.class,
                    Arrays.stream(names).map(n -> SiftStateProperties.Tone.valueOf(n.toUpperCase(Locale.ROOT))).toList()));
        }

        private Def with(Property<?> property) {
            List<Property<?>> list = new ArrayList<>(properties);
            list.add(property);
            return new Def(name, mat, shape, List.copyOf(list));
        }
    }

    private static Def block(String name, Mat mat) {
        return new Def(name, mat, SiftStateBlock.Shape.CUBE, List.of());
    }

    /** 柱狀方塊：RotatedPillarBlock，具 axis=x|y|z。 */
    private static Def pillar(String name, Mat mat) {
        return new Def(name, mat, SiftStateBlock.Shape.PILLAR, List.of());
    }

    /** 六向可旋轉的複合面方塊（草方塊型），具 facing，頂面朝向 facing。 */
    private static Def facing(String name, Mat mat) {
        return new Def(name, mat, SiftStateBlock.Shape.FACING, List.of());
    }

    private static final List<Def> DEFS = List.of(
            // ===== 遞增／複合方塊 =====
            block("rune_slate", Mat.DEEPSLATE).intProp("charge", 0, 2),
            block("aurum_ore", Mat.STONE).intProp("richness", 0, 1),
            block("patina_ore", Mat.STONE).intProp("oxidation", 0, 1),
            block("crimson_vein_stone", Mat.STONE).intProp("crimson_spread", 0, 4),
            block("amber_vein_stone", Mat.STONE).intProp("amber_spread", 0, 3),
            block("ember_stone", Mat.STONE).intProp("heat", 0, 4),
            block("abyssal_strata", Mat.STONE).intProp("depth", 0, 2),
            block("silted_strata", Mat.STONE).intProp("silt", 0, 2),
            block("lichen_stone", Mat.DEEPSLATE).intProp("lichen", 0, 4),
            block("bleached_sandstone", Mat.STONE).intProp("bleach", 0, 4),
            block("banded_mudstone", Mat.STONE).intProp("banding", 0, 3),
            block("cracked_sandstone", Mat.SAND).intProp("crack", 0, 3),
            block("bleached_clay", Mat.STONE).intProp("bleach", 0, 2),
            block("ash_marble", Mat.STONE).intProp("veining", 0, 3),
            block("emerald_ore", Mat.STONE).intProp("density", 0, 1).enumProp("host", SiftStateProperties.Host.class),
            block("glyph_block", Mat.STONE).intProp("corruption", 0, 3),
            block("sky_block", Mat.STONE).intProp("cloud", 0, 2),
            block("wilting_foliage", Mat.GRAVEL).intProp("wither", 0, 3),
            block("teal_deep_block", Mat.STONE).intProp("depth", 0, 2),
            block("rusted_dark_cobble", Mat.STONE).intProp("rust", 0, 3),
            block("corrupted_slate", Mat.DEEPSLATE).intProp("corruption", 0, 3),
            block("corrupted_slate_bricks", Mat.DEEPSLATE).intProp("corruption", 0, 2),
            block("magma_vein_slate", Mat.STONE).intProp("vein", 0, 2),
            block("frost_veined_stone", Mat.STONE).enumProp("tint", SiftStateProperties.Tint.class).intProp("veins", 0, 2), // TODO: verify — 未繪製的 4 種 tint/veins 組合暫借 tint=none,veins=0 的模型
            block("cobbled_dirt", Mat.GRAVEL).intProp("stone", 0, 5),
            block("mossy_cobblestone", Mat.STONE).intProp("moss", 0, 2),
            block("mossy_carved_bricks", Mat.STONE).intProp("moss", 0, 1),
            block("mossy_smooth_stone", Mat.STONE).intProp("moss", 0, 1),
            block("mossy_olive_earth", Mat.STONE).intProp("moss", 0, 3),
            block("forest_floor", Mat.GRAVEL).intProp("moss", 0, 3),
            block("meadow_grass_block", Mat.GRASS).intProp("grass_cover", 0, 3), // TODO: verify texture pairing — grass_cover=1、2 的側面為推測配對

            // ===== 原木與柱狀 =====
            pillar("amber_log", Mat.WOOD),
            pillar("umber_log", Mat.WOOD),
            pillar("peeling_log", Mat.WOOD).intProp("peel", 0, 2), // TODO: verify texture pairing — 三階共用的頂面為推測配對
            pillar("grooved_stone_pillar", Mat.STONE),

            // ===== 覆蓋石（由 layered_strata 拆分，cube_bottom_top） =====
            block("amber_capped_stone_01", Mat.STONE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("amber_capped_stone_02", Mat.STONE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("amber_capped_stone_03", Mat.STONE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("ash_capped_crimson_01", Mat.STONE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("ash_capped_dark_slate_01", Mat.DEEPSLATE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("ash_capped_dark_slate_02", Mat.DEEPSLATE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("ash_capped_violet_01", Mat.STONE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("crimson_capped_void_01", Mat.STONE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("dark_slate_capped_ash_01", Mat.DEEPSLATE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("dark_slate_capped_rose_01", Mat.DEEPSLATE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("rose_capped_dark_slate_01", Mat.DEEPSLATE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("rose_capped_stone_01", Mat.STONE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("stone_capped_amber_01", Mat.STONE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("stone_capped_amber_02", Mat.STONE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("stone_capped_amber_03", Mat.STONE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("stone_capped_rose_01", Mat.STONE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("stone_capped_violet_01", Mat.STONE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測
            block("void_capped_crimson_01", Mat.STONE), // TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測

            // ===== 帶狀貼圖抽出的複合面方塊（facing 六向可旋轉；柱狀為 axis） =====
            facing("teal_capped_abyssal_strata", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 abyssal_strata_depth0_b）
            facing("crimson_capped_crimson_strata", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 crimson_strata_b）
            facing("crimson_capped_crimson_strata_2", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 crimson_strata_c）
            facing("rose_capped_crimson_strata", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 crimson_strata_e）
            facing("rose_capped_crimson_strata_2", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 crimson_strata_f）
            facing("teal_capped_crimson_strata", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 crimson_strata_h）
            facing("violet_capped_crimson_strata", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 crimson_strata_l）
            facing("teal_capped_dark_slate", Mat.DEEPSLATE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 dark_slate_b）
            facing("teal_capped_dark_slate_2", Mat.DEEPSLATE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 dark_slate_c）
            facing("olive_capped_dark_slate", Mat.DEEPSLATE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 dark_slate_f）
            pillar("dark_slate_pillar", Mat.DEEPSLATE), // TODO: verify texture pairing — 端面為色彩相近的推測配對（來源 dark_slate_l）
            facing("gray_capped_dark_slate", Mat.DEEPSLATE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 dark_slate_m）
            facing("violet_capped_dark_slate", Mat.DEEPSLATE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 dark_slate_q）
            facing("crimson_capped_ember_stone", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 ember_stone_heat3_b）
            facing("warm_capped_ember_stone", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 ember_stone_heat3_c）
            facing("olive_capped_forest_floor", Mat.GRAVEL), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 forest_floor_moss1）
            facing("crimson_capped_gray_strata", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 gray_strata_a）
            facing("teal_capped_gray_strata", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 gray_strata_h）
            facing("teal_capped_gray_strata_2", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 gray_strata_i）
            facing("olive_capped_mossy_olive_earth", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 mossy_olive_earth_moss2）
            facing("gray_capped_sky_block", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 sky_block_cloud2）
            facing("teal_capped_teal_strata", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 teal_strata_c）
            facing("crimson_capped_violet_strata", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 violet_strata_b）
            facing("crimson_capped_violet_strata_2", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 violet_strata_c）

            // ===== 隨機池回饋第二輪：新方塊 =====
            block("varied_dark_slate", Mat.DEEPSLATE).tones("gray", "mottled", "violet"),
            block("framed_dark_slate", Mat.DEEPSLATE),
            block("blotched_dark_slate", Mat.DEEPSLATE),
            block("umber_void_stone", Mat.STONE),
            block("void_stone_bricks", Mat.STONE),
            block("speckled_void_stone", Mat.STONE),
            facing("crimson_capped_crimson_strata_3", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 crimson_strata_i，rot90）
            facing("teal_capped_teal_strata_2", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 teal_strata_g，rot90）
            facing("gray_capped_void_stone", Mat.STONE), // TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 void_stone_i，none）
            pillar("void_stone_pillar", Mat.STONE), // TODO: verify texture pairing — 端面為色彩相近的推測配對（來源 void_stone_h，側面上下翻轉）

            // ===== 連接紋理邊框（非遞增） =====
            block("teal_framed_panel", Mat.STONE).intProp("frame", 0, 6),

            // ===== 隨機變體池（weighted 多模型，無狀態屬性） =====
            block("dark_slate", Mat.DEEPSLATE).intProp("fade", 0, 3), // k → o,p → r,s → t,u：紫色漸少、灰綠漸多
            block("crimson_strata", Mat.STONE).tones("rose", "mottled", "crimson", "plum"),
            block("gray_strata", Mat.STONE).tones("teal", "lavender", "violet", "warm"),
            block("void_stone", Mat.STONE).tones("dark", "rusty", "olive"),
            block("teal_strata", Mat.STONE).tones("pale", "cyan"),
            block("violet_strata", Mat.STONE).tones("dusk", "violet", "slate"),
            facing("edged_stone", Mat.STONE).tones("olive", "warm").intProp("edge", 0, 3), // TODO: warm 的 edge=1~3 尚無專屬貼圖，暫用 e
            block("smooth_stone", Mat.STONE).tones("light", "warm", "blue"),
            block("stone_bricks", Mat.STONE).tones("smooth", "rough", "paneled", "dark"),
            block("ridge_stone", Mat.STONE),
            block("rich_dirt", Mat.GRAVEL),
            block("rose_strata", Mat.STONE).tones("violet", "rose"),
            block("veined_crimson_stone", Mat.STONE),
            block("veined_teal_stone", Mat.STONE).tones("teal", "mottled"),
            block("violet_marble", Mat.STONE),
            block("argent_ore", Mat.STONE),
            block("aurum_lapis_ore", Mat.STONE),
            block("circle_slate", Mat.DEEPSLATE),
            block("framed_slate", Mat.DEEPSLATE),
            block("labyrinth_marble", Mat.STONE),
            block("labyrinth_marble_core", Mat.STONE),
            block("red_sculk_vein_bottom", Mat.STONE),
            block("rose_quartz_ore", Mat.STONE),
            block("spiral_carved_stone", Mat.STONE),
            block("teal_water_block", Mat.STONE),
            block("violet_solid_block", Mat.STONE),
            block("void_obsidian", Mat.STONE),
            block("amber_sand", Mat.SAND),
            block("chiseled_stone_frame", Mat.STONE),
            block("cinnabar_planks", Mat.WOOD),
            block("concentric_stone", Mat.STONE),
            block("dark_stone", Mat.STONE),
            block("dense_foliage_block", Mat.GRASS),
            block("honey_planks", Mat.WOOD),
            block("meander_stone_bricks", Mat.STONE),
            block("pale_sand", Mat.SAND),
            block("rosewood_planks", Mat.WOOD),
            block("stone_variant", Mat.STONE),
            block("walnut_planks", Mat.WOOD)
    );

    static {
        for (Def def : DEFS) {
            register(def);
        }
    }

    private static Block register(Def def) {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(def.name()));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(def.name()));
        Block block = SiftStateBlock.create(def.mat().properties().setId(blockKey), def.shape(), def.properties());
        Registry.register(BuiltInRegistries.BLOCK, blockKey, block);
        Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().setId(itemKey)));
        ALL_BLOCKS.add(block);
        BY_NAME.put(def.name(), block);
        return block;
    }

    /**
     * 創造模式分頁用：預設狀態以外的每個狀態（不含 axis、facing 這類朝向屬性）各一個物品，以 block_state 元件區分。
     * 放置時 BlockItem 會套用該元件；掉落表以 copy_state 保留當下階段。
     */
    public static List<ItemStack> stateVariantStacks(Block block) {
        List<ItemStack> stacks = new ArrayList<>();
        BlockState defaultState = block.defaultBlockState();
        for (BlockState state : block.getStateDefinition().getPossibleStates()) {
            if (state == defaultState) {
                continue;
            }
            if (state.hasProperty(RotatedPillarBlock.AXIS) && state.getValue(RotatedPillarBlock.AXIS) != Direction.Axis.Y) {
                continue;
            }
            if (state.hasProperty(SiftStateBlock.Facing.FACING) && state.getValue(SiftStateBlock.Facing.FACING) != Direction.UP) {
                continue;
            }
            BlockItemStateProperties stateProperties = BlockItemStateProperties.EMPTY;
            for (Property<?> property : state.getProperties()) {
                if (property != RotatedPillarBlock.AXIS && property != SiftStateBlock.Facing.FACING) {
                    stateProperties = withValue(stateProperties, property, state);
                }
            }
            ItemStack stack = new ItemStack(block);
            stack.set(DataComponents.BLOCK_STATE, stateProperties);
            stacks.add(stack);
        }
        return stacks;
    }

    private static <T extends Comparable<T>> BlockItemStateProperties withValue(BlockItemStateProperties stateProperties, Property<T> property, BlockState state) {
        return stateProperties.with(property, state);
    }

    public static void registerModBlocks() {
        PySift.LOGGER.info("Successfully registered {} Sift Blocks for {}", ALL_BLOCKS.size(), PySift.MOD_ID);
    }
}
