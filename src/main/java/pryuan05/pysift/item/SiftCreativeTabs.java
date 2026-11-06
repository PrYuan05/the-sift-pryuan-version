package pryuan05.pysift.item;

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ItemLike;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.ModBlocks;
import pryuan05.pysift.block.SiftColors;
import pryuan05.pysift.block.SoulWillowWood;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.Set;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import java.util.function.Supplier;

/**
 * 隙浮的創造模式分頁，照原版的分法拆開：方塊（建築／自然／彩色／功能／未用於世界生成）與物品（工具／戰鬥／食物／材料／生怪蛋）
 * 分在不同分頁，物品不會混進方塊分頁。每樣東西同時加進對應的原版分頁（未用於世界生成的方塊依類別放進原版的建築或自然分頁）。
 * <p>
 * 各類別不直接寫分頁，而是用 {@link #source} 登記「來源」（方塊／未用方塊／物品，沿用 ModItems 的三個 key）；
 * 這裡把所有來源收集起來，再依 {@link CreativeLayout#section} 分到各分頁。分頁內的排序與排版仍由用戶端的
 * CreativeModeInventoryScreenMixin（CreativeLayout + CreativeTabRows）處理。
 */
public final class SiftCreativeTabs {
    public enum Tab {
        BUILDING("pysift_building", "building_blocks", () -> ModBlocks.ALL_BLOCKS.isEmpty() ? Items.STONE : ModBlocks.ALL_BLOCKS.get(0)),
        NATURAL("pysift_natural", "natural_blocks", () -> SoulWillowWood.ITEMS.isEmpty() ? Items.OAK_SAPLING : SoulWillowWood.ITEMS.get(0)),
        COLORED("pysift_colored", "colored_blocks", () -> SiftColors.DYES.get(SiftColors.SiftColor.TEAL)),
        FUNCTIONAL("pysift_functional", "functional_blocks", () -> SiftColors.CUSHIONS.get(SiftColors.SiftColor.ROSE)),
        UNUSED("pysift_unused_blocks", null, () -> Items.STRUCTURE_VOID),
        TOOLS("pysift_tools", "tools_and_utilities", () -> BuiltInRegistries.ITEM.getValue(PySift.id("siftite_pickaxe"))),
        COMBAT("pysift_combat", "combat", () -> BuiltInRegistries.ITEM.getValue(PySift.id("siftite_sword"))),
        FOOD("pysift_food", "food_and_drinks", () -> BuiltInRegistries.ITEM.getValue(PySift.id("soul_berries"))),
        INGREDIENTS("pysift_ingredients", "ingredients", () -> ModItems.SIFTITE_INGOT),
        SPAWN_EGGS("pysift_spawn_eggs", "spawn_eggs", () -> ModItems.BLUB_SPAWN_EGG);

        public final ResourceKey<CreativeModeTab> key;
        /** The vanilla tab the same items go into (null: decided per item, see {@link #vanillaTab}). */
        final ResourceKey<CreativeModeTab> vanilla;
        final Supplier<ItemLike> icon;
        CreativeModeTab tab;

        Tab(String id, String vanilla, Supplier<ItemLike> icon) {
            this.key = ResourceKey.create(Registries.CREATIVE_MODE_TAB, PySift.id(id));
            this.vanilla = vanilla == null ? null : ResourceKey.create(Registries.CREATIVE_MODE_TAB, Identifier.withDefaultNamespace(vanilla));
            this.icon = icon;
        }
    }

    private static final Map<ResourceKey<CreativeModeTab>, List<Consumer<CreativeModeTab.Output>>> SOURCES = new LinkedHashMap<>();
    private static final Map<CreativeModeTab, Tab> BY_TAB = new LinkedHashMap<>();

    private SiftCreativeTabs() {
    }

    /** Adds items to one of the sources (ModItems.BLOCKS_TAB_KEY, UNUSED_BLOCKS_TAB_KEY, ITEMS_TAB_KEY). */
    public static void source(ResourceKey<CreativeModeTab> source, Consumer<CreativeModeTab.Output> contents) {
        SOURCES.computeIfAbsent(source, k -> new ArrayList<>()).add(contents);
    }

    /** Is this one of our tabs (the client arranges their rows)? */
    public static boolean isOurs(CreativeModeTab tab) {
        return BY_TAB.containsKey(tab);
    }

    /** Every stack of every source, in source order, with the tab it belongs to. */
    private static Map<Tab, List<ItemStack>> collect() {
        Map<Tab, List<ItemStack>> out = new EnumMap<>(Tab.class);
        for (Tab t : Tab.values()) {
            out.put(t, new ArrayList<>());
        }
        for (ResourceKey<CreativeModeTab> source : List.of(ModItems.BLOCKS_TAB_KEY, ModItems.UNUSED_BLOCKS_TAB_KEY, ModItems.ITEMS_TAB_KEY)) {
            boolean unused = source == ModItems.UNUSED_BLOCKS_TAB_KEY;
            CreativeModeTab.Output collector = (stack, visibility) -> out.get(tabOf(stack, unused)).add(stack);
            SOURCES.getOrDefault(source, List.of()).forEach(c -> c.accept(collector));
        }
        return out;
    }

    static Tab tabOf(ItemStack stack, boolean unused) {
        CreativeLayout.Section section = CreativeLayout.section(stack);
        return switch (section) {
            case STONE, CAPPED, EARTH, SAND, WOOD, DECOR -> unused ? Tab.UNUSED : Tab.BUILDING;
            case ORE, PLANT, TREE -> unused ? Tab.UNUSED : Tab.NATURAL;
            case COLORED -> Tab.COLORED;
            case SPECIAL -> unused ? Tab.UNUSED : Tab.FUNCTIONAL;
            case TOOL -> Tab.TOOLS;
            case COMBAT -> Tab.COMBAT;
            case CONSUMABLE -> Tab.FOOD;
            case MATERIAL -> Tab.INGREDIENTS;
            case SPAWN_EGG -> Tab.SPAWN_EGGS;
        };
    }

    /** The vanilla tab of a stack in our tab t (unused blocks: building or natural by their category). */
    private static ResourceKey<CreativeModeTab> vanillaTab(Tab t, ItemStack stack) {
        if (t.vanilla != null) {
            return t.vanilla;
        }
        return tabOf(stack, false).vanilla;
    }

    public static void register() {
        // the three sources ModItems always had
        source(ModItems.BLOCKS_TAB_KEY, output -> ModItems.acceptBlocks(output, false));
        source(ModItems.UNUSED_BLOCKS_TAB_KEY, output -> ModItems.acceptBlocks(output, true));
        source(ModItems.ITEMS_TAB_KEY, ModItems::acceptItems);
        for (Tab t : Tab.values()) {
            t.tab = FabricCreativeModeTab.builder()
                    .icon(() -> new ItemStack(t.icon.get()))
                    .title(Component.translatable("itemGroup.pysift." + t.key.identifier().getPath()))
                    .displayItems((params, output) -> output.acceptAll(collect().get(t)))
                    .build();
            Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, t.key, t.tab);
            BY_TAB.put(t.tab, t);
        }
        // the same items in vanilla's tabs, right after the vanilla item of the same kind (block_state variants only in ours)
        for (ResourceKey<CreativeModeTab> key : List.of(Tab.BUILDING.vanilla, Tab.NATURAL.vanilla, Tab.COLORED.vanilla,
                Tab.FUNCTIONAL.vanilla, Tab.TOOLS.vanilla, Tab.COMBAT.vanilla, Tab.FOOD.vanilla, Tab.INGREDIENTS.vanilla,
                Tab.SPAWN_EGGS.vanilla)) {
            CreativeModeTabEvents.modifyOutputEvent(key).register(output -> {
                Set<Item> shown = new HashSet<>();
                output.getDisplayStacks().forEach(s -> shown.add(s.getItem()));
                Map<Item, List<ItemStack>> groups = new LinkedHashMap<>();   // vanilla anchor -> our stacks after it
                List<ItemStack> rest = new ArrayList<>();
                Map<Item, Tab> ours = new LinkedHashMap<>();
                Map<Item, ItemStack> stackOf = new LinkedHashMap<>();
                collect().forEach((t, stacks) -> stacks.forEach(stack -> {
                    if (!stack.has(DataComponents.BLOCK_STATE) && !ours.containsKey(stack.getItem())) {
                        ours.put(stack.getItem(), t);
                        stackOf.put(stack.getItem(), stack);
                    }
                }));
                for (ItemStack stack : CreativeLayout.arrange(new ArrayList<>(stackOf.values()))) {
                    List<String> kin = VanillaKin.of(stack);
                    if (kin.isEmpty()) {
                        // no vanilla item of the same kind: the tab of its category, after that category's anchor
                        if (!vanillaTab(ours.get(stack.getItem()), stack).equals(key)) {
                            continue;
                        }
                        Item anchor = SECTION_ANCHORS.get(CreativeLayout.section(stack));
                        if (anchor != null && shown.contains(anchor)) {
                            groups.computeIfAbsent(anchor, a -> new ArrayList<>()).add(stack);
                        } else {
                            rest.add(stack);
                        }
                        continue;
                    }
                    // the first kin that is in this tab; a stack whose kin is in no tab here is not shown here
                    String only = VanillaKin.ONLY_IN.get(BuiltInRegistries.ITEM.getKey(stack.getItem()).getPath());
                    if (only != null && !key.identifier().getPath().equals(only)) {
                        continue;
                    }
                    for (String id : kin) {
                        Item anchor = BuiltInRegistries.ITEM.getValue(Identifier.withDefaultNamespace(id));
                        if (shown.contains(anchor)) {
                            groups.computeIfAbsent(anchor, a -> new ArrayList<>()).add(stack);
                            break;
                        }
                    }
                }
                groups.forEach((anchor, stacks) -> {
                    stacks.sort(Comparator.comparingInt(VanillaKin::order));   // stable: tiers and armour pieces in vanilla order
                    output.insertAfter(anchor, stacks);
                });
                rest.forEach(output::accept);
            });
        }
    }

    /** Vanilla's last colour in its colour order: our 9 colours go right after it. */
    private static final String LAST_VANILLA_COLOUR = "pink_";
    /** Where each kind of our items without a vanilla kin sits in vanilla's tabs (after this vanilla item). */
    private static final Map<CreativeLayout.Section, Item> SECTION_ANCHORS = Map.ofEntries(
            Map.entry(CreativeLayout.Section.WOOD, Items.WARPED_BUTTON),           // after the last wood family
            Map.entry(CreativeLayout.Section.STONE, Items.PURPUR_SLAB),            // after the stone families, before the metal blocks
            Map.entry(CreativeLayout.Section.CAPPED, Items.PURPUR_SLAB),
            Map.entry(CreativeLayout.Section.DECOR, Items.PURPUR_SLAB),
            Map.entry(CreativeLayout.Section.EARTH, Items.MUD_BRICK_WALL),
            Map.entry(CreativeLayout.Section.SAND, Items.CUT_RED_SANDSTONE_SLAB),
            Map.entry(CreativeLayout.Section.ORE, Items.ANCIENT_DEBRIS),
            Map.entry(CreativeLayout.Section.TREE, Items.WARPED_STEM),
            Map.entry(CreativeLayout.Section.PLANT, Items.WARPED_FUNGUS),
            Map.entry(CreativeLayout.Section.SPECIAL, Items.LODESTONE),
            Map.entry(CreativeLayout.Section.TOOL, Items.ENDER_EYE),
            Map.entry(CreativeLayout.Section.COMBAT, Items.MACE),
            Map.entry(CreativeLayout.Section.CONSUMABLE, Items.ENCHANTED_GOLDEN_APPLE),
            Map.entry(CreativeLayout.Section.MATERIAL, Items.NETHER_STAR));

    /**
     * The vanilla items our item is "the same kind" as, in order of preference: the item goes into every vanilla tab that
     * holds the first of them it finds there, right after it (so soul willow logs sit in both the building and the natural
     * tab, like vanilla logs, and our wools continue vanilla's wool row). Empty: no kin, use the category's anchor.
     */
    static final class VanillaKin {
        private static final List<String> TIERS = List.of("siftite", "aurum", "soulite");
        private static final List<String> TOOLS = List.of("shovel", "pickaxe", "axe", "hoe");
        private static final List<String> ARMOUR = List.of("helmet", "chestplate", "leggings", "boots");
        /** The soul willow pieces vanilla keeps in one wood run in the building tab (soul_willow_ / _soul_willow removed). */
        private static final Set<String> WOOD_RUN = Set.of("log", "wood", "stripped_log", "stripped_wood", "planks", "stairs",
                "slab", "fence", "fence_gate", "door", "trapdoor", "pressure_plate", "button");
        private static final Map<String, List<String>> EXACT = Map.ofEntries(
                // natural ground and sand live in the natural tab
                Map.entry("amber_sand", List.of("red_sand")), Map.entry("pale_sand", List.of("red_sand")),
                Map.entry("cobbled_dirt", List.of("rooted_dirt")), Map.entry("rich_dirt", List.of("rooted_dirt")),
                Map.entry("meadow_grass_block", List.of("rooted_dirt")), Map.entry("forest_floor", List.of("rooted_dirt")),
                Map.entry("wilting_foliage", List.of("pale_hanging_moss")), Map.entry("dense_foliage_block", List.of("pale_hanging_moss")),
                // metal and raw metal blocks
                Map.entry("siftite_block", List.of("netherite_block")), Map.entry("patina_block", List.of("netherite_block")),
                Map.entry("raw_siftite_block", List.of("raw_gold_block")), Map.entry("raw_patina_block", List.of("raw_gold_block")),
                Map.entry("red_sculk", List.of("sculk_sensor")), Map.entry("red_sculk_vein", List.of("sculk_sensor")),
                Map.entry("soul_berries", List.of("sweet_berries")),
                // soul willow pieces outside the building run
                Map.entry("soul_willow_leaves", List.of("flowering_azalea_leaves")),
                Map.entry("soul_willow_leaves_pale", List.of("flowering_azalea_leaves")),
                Map.entry("glowing_soul_willow_leaves", List.of("flowering_azalea_leaves")),
                Map.entry("soul_willow_sapling", List.of("poplar_sapling")),
                Map.entry("soul_willow_vine", List.of("twisting_vines")), Map.entry("glowing_soul_willow_vine", List.of("twisting_vines")),
                Map.entry("soul_willow_sign", List.of("warped_hanging_sign")),
                Map.entry("soul_willow_hanging_sign", List.of("warped_hanging_sign")),
                Map.entry("soul_willow_shelf", List.of("warped_shelf")),
                Map.entry("soul_willow_boat", List.of("poplar_chest_boat")), Map.entry("soul_willow_chest_boat", List.of("poplar_chest_boat")),
                // tools & utilities
                Map.entry("spirit_liquid_bucket", List.of("milk_bucket")),
                Map.entry("soul_compass", List.of("recovery_compass")), Map.entry("homeward_stone", List.of("recovery_compass")),
                Map.entry("summoning_sigil", List.of("recovery_compass")),
                Map.entry("rift_seal", List.of("recovery_compass")), Map.entry("mourning_horn", List.of("goat_horn")),
                Map.entry("lullaby_censer", List.of("soul_lantern")), Map.entry("sift_heart", List.of("nether_star")),
                Map.entry("ancient_chronicle", List.of("writable_book")),
                // combat: the boss weapons after the mace
                Map.entry("sonic_staff", List.of("mace")), Map.entry("dash_charm", List.of("mace")), Map.entry("sculk_hammer", List.of("mace")),
                // food
                Map.entry("aurum_apple", List.of("enchanted_golden_apple")), Map.entry("aurum_carrot", List.of("golden_carrot")),
                Map.entry("aurum_berries", List.of("glow_berries")), Map.entry("gloomcap_stew", List.of("rabbit_stew")),
                Map.entry("soul_antidote", List.of("milk_bucket")),
                // ingredients
                Map.entry("raw_siftite", List.of("raw_gold")), Map.entry("raw_aurum", List.of("raw_gold")), Map.entry("raw_patina", List.of("raw_gold")),
                Map.entry("aurum_nugget", List.of("gold_nugget")),
                Map.entry("siftite_ingot", List.of("netherite_ingot")), Map.entry("patina_ingot", List.of("netherite_ingot")),
                Map.entry("aurum_ingot", List.of("netherite_ingot")), Map.entry("soulite_ingot", List.of("netherite_ingot")),
                Map.entry("charoite", List.of("amethyst_shard")), Map.entry("fuse_powder", List.of("gunpowder")),
                Map.entry("soul_essence", List.of("echo_shard")),
                Map.entry("harmonizer_core", List.of("nether_star")), Map.entry("monarch_crown", List.of("nether_star")),
                Map.entry("sculk_monstrosity_heart", List.of("nether_star")), Map.entry("resonant_crystal", List.of("nether_star")),
                Map.entry("monarch_feather", List.of("nether_star")), Map.entry("sculk_scale", List.of("nether_star")),
                Map.entry("sift_beacon_gem", List.of("nether_star")),
                Map.entry("soulite_upgrade_smithing_template", List.of("netherite_upgrade_smithing_template")));
        /** Items whose vanilla kin is in several tabs (milk bucket, glow berries...) but which belong in one. */
        static final Map<String, String> ONLY_IN = Map.of(
                "spirit_liquid_bucket", "tools_and_utilities", "summoning_sigil", "tools_and_utilities",
                "soul_antidote", "food_and_drinks", "aurum_berries", "food_and_drinks", "aurum_carrot", "food_and_drinks");
        /** Order inside one anchor for items vanilla lists in a fixed sequence (ingots, boss drops). */
        private static final List<String> SEQUENCE = List.of("raw_siftite", "raw_patina", "raw_aurum",
                "siftite_ingot", "patina_ingot", "aurum_ingot", "soulite_ingot",
                "harmonizer_core", "resonant_crystal", "monarch_crown", "monarch_feather", "sculk_monstrosity_heart", "sculk_scale", "sift_heart",
                "sift_beacon_gem", "siftite_block", "patina_block", "raw_siftite_block", "raw_patina_block",
                "soul_compass", "homeward_stone", "summoning_sigil", "soul_willow_boat", "soul_willow_chest_boat",
                "soul_willow_log", "soul_willow_wood", "stripped_soul_willow_log", "stripped_soul_willow_wood", "soul_willow_planks",
                "soul_willow_stairs", "soul_willow_slab", "soul_willow_fence", "soul_willow_fence_gate", "soul_willow_door",
                "soul_willow_trapdoor", "soul_willow_pressure_plate", "soul_willow_button",
                "soul_willow_sign", "soul_willow_hanging_sign");

        private VanillaKin() {
        }

        static List<String> of(ItemStack stack) {
            String path = BuiltInRegistries.ITEM.getKey(stack.getItem()).getPath();
            List<String> exact = EXACT.get(path);
            if (exact != null) {
                return exact;
            }
            if (path.startsWith("ancient_page_")) {
                return List.of("writable_book");
            }
            if (path.endsWith("_pottery_sherd")) {
                return List.of("snort_pottery_sherd");          // vanilla's last sherd
            }
            if (path.endsWith("_spawn_egg")) {
                return List.of("shulker_spawn_egg");            // all of ours as one run after vanilla's last egg
            }
            if (path.contains("soul_willow") && WOOD_RUN.contains(path.replace("soul_willow_", "").replace("_soul_willow", ""))) {
                return path.equals("soul_willow_log") ? List.of("warped_button", "warped_stem") : List.of("warped_button");
            }
            for (SiftColors.SiftColor c : SiftColors.SiftColor.values()) {
                // <colour>_<kind> right after vanilla's pink_<kind> (wool, wool slab and wool stairs each in their own row)
                if (path.startsWith(c.id + "_")) {
                    String kind = path.substring(c.id.length() + 1);
                    if (BuiltInRegistries.ITEM.containsKey(Identifier.withDefaultNamespace(LAST_VANILLA_COLOUR + kind))) {
                        return List.of(LAST_VANILLA_COLOUR + kind);
                    }
                }
            }
            String tier = tier(path);
            if (tier != null) {
                String kind = path.substring(tier.length() + 1);
                if (TOOLS.contains(kind)) {
                    return kind.equals("axe") ? List.of("netherite_hoe", "netherite_axe") : List.of("netherite_hoe");
                }
                if (ARMOUR.contains(kind)) {
                    return List.of("netherite_boots");
                }
                if (kind.equals("sword")) {
                    return List.of("netherite_sword");
                }
            }
            return List.of();
        }

        /** Sort key inside one anchor (stable): tools and armour tier by tier in vanilla's piece order, then SEQUENCE, else 0. */
        static int order(ItemStack stack) {
            String path = BuiltInRegistries.ITEM.getKey(stack.getItem()).getPath();
            String tier = tier(path);
            if (tier != null) {
                String kind = path.substring(tier.length() + 1);
                int piece = TOOLS.contains(kind) ? TOOLS.indexOf(kind) : Math.max(0, ARMOUR.indexOf(kind));
                return TIERS.indexOf(tier) * 10 + piece;
            }
            int i = SEQUENCE.indexOf(path);
            return i < 0 ? 1000 : i;                     // listed items first, the rest keep their order
        }

        private static String tier(String path) {
            for (String t : TIERS) {
                if (path.startsWith(t + "_")) {
                    return t;
                }
            }
            return null;
        }
    }
}
