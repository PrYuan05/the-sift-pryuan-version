package pryuan05.pysift.progression;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.util.valueproviders.UniformInt;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.AmethystClusterBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.DropExperienceBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import pryuan05.pysift.PySift;
import pryuan05.pysift.item.ModItems;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

/**
 * 第 1 階段「進度循環」的方塊與物品（規格見 MODDING_ROADMAP_AND_SPECS.md）：
 * <ul>
 *   <li>礦石：隙浮金礦（所有生態域地下的虛黑岩，y -40～40）→ 粗隙浮金 → 熔煉成隙浮金錠；
 *       紫龍晶簇（紫晶深板岩區地表與洞穴）→ 紫龍晶。生成設定在 tools/worldgen/build_the_sift.py 的 PROGRESSION_ORES。</li>
 *   <li>一般生物掉落的材料：引信粉（引信蠅）、靈魂精華（隙浮的敵對生物，召喚印記的材料）。</li>
 * </ul>
 * 資源（模型、貼圖、掉落表、配方、標籤、語系）由 tools/progression/build_progression.py 產生。
 */
public final class ModProgression {
    public static final List<Item> CREATIVE_ORDER = new ArrayList<>();

    // ===== 礦石 =====
    public static final Block SIFTITE_ORE = registerBlock("siftite_ore",
            p -> new DropExperienceBlock(UniformInt.of(1, 3), p), Blocks.DEEPSLATE_IRON_ORE);
    public static final Block CHAROITE_CLUSTER = registerBlock("charoite_cluster",
            p -> new AmethystClusterBlock(7.0f, 3.0f, p.lightLevel(state -> 6)), Blocks.AMETHYST_CLUSTER);

    // ===== 材料 =====
    public static final Item RAW_SIFTITE = registerItem("raw_siftite", Item::new);
    public static final Item FUSE_POWDER = registerItem("fuse_powder", Item::new);
    public static final Item SOUL_ESSENCE = registerItem("soul_essence", Item::new);

    private ModProgression() {
    }

    static Block registerBlock(String name, Function<BlockBehaviour.Properties, Block> factory, Block copyFrom) {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Block block = factory.apply(BlockBehaviour.Properties.ofFullCopy(copyFrom).setId(blockKey));
        Registry.register(BuiltInRegistries.BLOCK, blockKey, block);
        Item item = Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().setId(itemKey)));
        CREATIVE_ORDER.add(item);
        return block;
    }

    static Item registerItem(String name, Function<Item.Properties, Item> factory) {
        return registerItem(name, factory, new Item.Properties());
    }

    static Item registerItem(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
        ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Item item = Registry.register(BuiltInRegistries.ITEM, key, factory.apply(properties.setId(key)));
        CREATIVE_ORDER.add(item);
        return item;
    }

    public static void register() {
        SiftiteGear.load();
        BossRewards.load();
        BossWeapons.load();
        SiftBeacon.load();
        SouliteGear.load();
        SiftGuidance.load();
        SiftFarming.load();
        SiftFlora.load();
        // 進度相關的物品排在「物品」分頁；方塊（礦石、祭壇、作物、草叢）由 ModItems 放進方塊分頁
        pryuan05.pysift.item.SiftCreativeTabs.source(ModItems.ITEMS_TAB_KEY, output ->
                CREATIVE_ORDER.stream().filter(item -> !(item instanceof BlockItem)).forEach(output::accept));
        PySift.LOGGER.info("Registered {} progression blocks / items", CREATIVE_ORDER.size());
    }
}
