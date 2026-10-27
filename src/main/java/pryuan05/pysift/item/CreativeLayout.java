package pryuan05.pysift.item;

import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.VegetationBlock;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.ModBlocks;
import pryuan05.pysift.block.ModVegetation;
import pryuan05.pysift.block.SiftColors;
import pryuan05.pysift.block.SiftPortalBlock;
import net.minecraft.world.item.BucketItem;
import net.minecraft.world.item.SmithingTemplateItem;
import pryuan05.pysift.block.SoulWillowWood;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 創造模式分頁的分類與排序（pysift 的分頁共用，SiftCreativeTabs 也用 {@link #section} 決定東西放哪一頁；用戶端的 CreativeModeInventoryScreenMixin 在顯示前套用）。
 * <ol>
 *   <li>每個物品先歸到一個「族」（{@link #group}）：方塊與它的 block_state 變體、建材組（石磚／半磚／階梯／牆）、
 *       靈柳木整組、同一種沙的砂岩家族各算一族，族內順序不變。</li>
 *   <li>族依「類別」（{@link Section}，見 {@link #section}）排序；同一類別內，族裡有任何成員在
 *       {@link #IN_WORLDGEN}（生態域或結構會生成的方塊、會自然生成的生物的生怪蛋）的族排前面。</li>
 *   <li>CreativeTabRows.layout 再排版：每個類別從新的一列開始；5 個以上的大族獨佔整列，小族接在同一列，
 *       避免一個物品佔一整列。</li>
 * </ol>
 * IN_WORLDGEN 物品標籤由 tools/worldgen/unused_blocks.py 產生（與方塊標籤 not_in_worldgen 一起），改了世界生成後重跑。
 */
public final class CreativeLayout {
    public static final TagKey<Item> IN_WORLDGEN = TagKey.create(Registries.ITEM, PySift.id("in_worldgen"));

    /** 類別，宣告順序就是分頁裡的順序。 */
    public enum Section {
        STONE, CAPPED, EARTH, SAND, ORE, PLANT, TREE, WOOD, DECOR, COLORED, SPECIAL,   // 方塊（SPECIAL = 功能方塊）
        MATERIAL, TOOL, COMBAT, CONSUMABLE, SPAWN_EGG                                 // 物品
    }

    /** 戰鬥用的物品（其餘有 TOOL 元件或有特殊功能的物品算工具）。 */
    private static final String[] COMBAT_WORDS = {"_sword", "_helmet", "_chestplate", "_leggings", "_boots", "staff", "charm", "hammer"};
    private static final String[] PLANT_WORDS = {"grass", "fern", "flower", "vine", "leaf_litter", "agave", "canopy",
            "stalk", "tuft", "bloom", "plant", "gloomcap"};
    private static final String[] EARTH_WORDS = {"dirt", "moss", "forest_floor", "grass_block", "foliage", "earth", "wilting"};
    private static final String[] DECOR_WORDS = {"labyrinth", "spiral", "concentric", "frame", "meander", "glyph", "rune",
            "circle", "edged", "grooved", "pillar", "sculk", "water_block", "sky_block", "panel", "carved"};

    private CreativeLayout() {
    }

    /** 依類別與「是否在生態域中使用」排序，族保持連續、族內順序不變。 */
    public static List<ItemStack> arrange(List<ItemStack> items) {
        Map<Object, List<ItemStack>> groups = new LinkedHashMap<>();
        for (ItemStack stack : items) {
            if (!stack.isEmpty()) {
                groups.computeIfAbsent(group(stack), k -> new ArrayList<>()).add(stack);
            }
        }
        List<List<ItemStack>> ordered = new ArrayList<>(groups.values());
        ordered.sort(Comparator.<List<ItemStack>>comparingInt(g -> section(g.get(0)).ordinal())
                .thenComparing(g -> g.stream().anyMatch(s -> s.is(IN_WORLDGEN)) ? 0 : 1));   // List.sort 是穩定排序
        List<ItemStack> out = new ArrayList<>(items.size());
        ordered.forEach(out::addAll);
        return out;
    }

    /** 族：同一族的物品排在一起。 */
    public static Object group(ItemStack stack) {
        Item item = stack.getItem();
        Block block = Block.byItem(item);
        if (block != Blocks.AIR) {
            Block base = ModBlocks.SET_BASE.get(block);
            if (base != null) {
                return base;
            }
            if (SoulWillowWood.ITEMS.contains(item)) {
                return "soul_willow_wood";
            }
            String path = path(item);
            if (path.contains("amber_sandstone")) {
                return "amber_sandstone";
            }
            if (path.contains("pale_sandstone")) {
                return "pale_sandstone";
            }
        }
        return item;
    }

    public static Section section(ItemStack stack) {
        Item item = stack.getItem();
        if (item instanceof SpawnEggItem) {
            return Section.SPAWN_EGG;
        }
        Block block = Block.byItem(item);
        if (block == Blocks.AIR) {
            String id = path(item);
            if (SiftColors.CUSHIONS.containsValue(item)) {
                return Section.SPECIAL;                       // cushions sit with the beds and banners' functional blocks
            }
            if (containsAny(id, COMBAT_WORDS) || stack.has(DataComponents.EQUIPPABLE)) {
                return Section.COMBAT;
            }
            if (stack.has(DataComponents.FOOD) || stack.has(DataComponents.CONSUMABLE) || id.contains("antidote")) {
                return Section.CONSUMABLE;
            }
            if (stack.has(DataComponents.TOOL) || item instanceof BucketItem) {
                return Section.TOOL;
            }
            // plain materials (ingots, shards, dyes, templates) vs items with their own behaviour (compass, homeward stone)
            if (item.getClass() == Item.class || item instanceof SiftColors.SiftDyeItem || item instanceof SmithingTemplateItem) {
                return Section.MATERIAL;
            }
            return Section.TOOL;
        }
        if (SiftColors.TINTS.containsKey(block)) {
            return Section.COLORED;                           // the 9 Sift colours: wool ... candles, beds, banners
        }
        Block base = ModBlocks.SET_BASE.getOrDefault(block, block);       // 建材組跟著石頭分類
        String id = path(base.asItem());
        if (base instanceof SiftPortalBlock || id.contains("altar") || id.contains("portal") || id.contains("axle")) {
            return Section.SPECIAL;
        }
        if (id.contains("soul_willow") || SoulWillowWood.ITEMS.contains(base.asItem())) {
            return Section.TREE;
        }
        if (id.endsWith("_ore") || id.contains("crystal") || id.endsWith("_cluster")) {
            return Section.ORE;
        }
        if (ModVegetation.ALL.contains(base) || base instanceof VegetationBlock || containsAny(id, PLANT_WORDS)
                && !base.defaultBlockState().isSolid()) {
            return Section.PLANT;
        }
        if (id.contains("sand")) {
            return Section.SAND;
        }
        if (id.contains("_log") || id.contains("planks") || id.endsWith("_wood")) {
            return Section.WOOD;
        }
        if (id.contains("capped")) {
            return Section.CAPPED;
        }
        if (containsAny(id, EARTH_WORDS)) {
            return Section.EARTH;
        }
        if (containsAny(id, DECOR_WORDS)) {
            return Section.DECOR;
        }
        return Section.STONE;
    }

    private static String path(Item item) {
        return BuiltInRegistries.ITEM.getKey(item).getPath();
    }

    private static boolean containsAny(String id, String[] words) {
        for (String w : words) {
            if (id.contains(w)) {
                return true;
            }
        }
        return false;
    }
}
