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
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ItemLike;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.ModBlocks;
import pryuan05.pysift.block.SiftColors;
import pryuan05.pysift.block.SoulWillowWood;

import java.util.ArrayList;
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
        // the same items in vanilla's tabs, after vanilla's own (block_state variants only in ours)
        Map<ResourceKey<CreativeModeTab>, List<ItemStack>> vanilla = new LinkedHashMap<>();
        for (Tab t : Tab.values()) {
            ResourceKey<CreativeModeTab> key = t.vanilla != null ? t.vanilla : Tab.BUILDING.vanilla;
            vanilla.computeIfAbsent(key, k -> new ArrayList<>());
        }
        vanilla.computeIfAbsent(Tab.NATURAL.vanilla, k -> new ArrayList<>());
        for (ResourceKey<CreativeModeTab> key : vanilla.keySet()) {
            CreativeModeTabEvents.modifyOutputEvent(key).register(output -> collect().forEach((t, stacks) -> {
                for (ItemStack stack : stacks) {
                    if (!stack.has(DataComponents.BLOCK_STATE) && vanillaTab(t, stack).equals(key)) {
                        output.accept(stack);
                    }
                }
            }));
        }
    }
}
