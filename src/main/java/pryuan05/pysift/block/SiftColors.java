package pryuan05.pysift.block;

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CarpetBlock;
import net.minecraft.world.level.block.ConcretePowderBlock;
import net.minecraft.world.level.block.GlazedTerracottaBlock;
import net.minecraft.world.level.block.IronBarsBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import pryuan05.pysift.PySift;
import pryuan05.pysift.item.ModItems;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

/**
 * 篩靈界的 9 種新顏色（原版 16 色寫死在 DyeColor，不能擴充，所以每個顏色有自己的一整套方塊）：
 * 染料（由同色的篩靈界植物合成，也能染皮甲：{@link SiftDyeRecipe}）＋羊毛（含半磚、階梯）、地毯、混凝土（含半磚、階梯）、
 * 混凝土粉末、陶土、彩繪陶瓦、染色玻璃、玻璃片。
 * 所有方塊和物品都沿用原版白色版本的貼圖，再由客戶端依 {@link SiftColor#rgb} 著色（模型的面有 tintindex 0），
 * 不複製任何原版貼圖。資源（模型、blockstate、配方、掉落物、標籤、語系）由 tools/progression/build_sift_colors.py 產生。
 */
public final class SiftColors {
    public enum SiftColor {
        TEAL("teal", 0x2EB8A6),
        MINT("mint", 0x8FE3C0),
        CORAL("coral", 0xF08A6C),
        AMBER("amber", 0xE8A33A),
        LAVENDER("lavender", 0xB39DDB),
        ROSE("rose", 0xD9536E),
        SOUL_BLUE("soul_blue", 0x8EC5F0),
        VOID("void", 0x3A2E48),
        DUSK_GOLD("dusk_gold", 0xF2CF6B);

        public final String id;
        /** 0xRRGGBB。 */
        public final int rgb;

        SiftColor(String id, int rgb) {
            this.id = id;
            this.rgb = rgb;
        }
    }

    /** 每個顏色的染料。 */
    public static final Map<SiftColor, SiftDyeItem> DYES = new LinkedHashMap<>();
    /** 方塊 → 著色用的 0xRRGGBB（客戶端讀這張表）。 */
    public static final Map<Block, Integer> TINTS = new LinkedHashMap<>();
    /** 物品欄的排列順序。 */
    private static final List<Item> ORDER = new ArrayList<>();

    private SiftColors() {
    }

    public static void register() {
        for (SiftColor c : SiftColor.values()) {
            ResourceKey<Item> dyeKey = ResourceKey.create(Registries.ITEM, PySift.id(c.id + "_dye"));
            SiftDyeItem dye = Registry.register(BuiltInRegistries.ITEM, dyeKey, new SiftDyeItem(c, new Item.Properties().setId(dyeKey)));
            DYES.put(c, dye);
            ORDER.add(dye);
            Block wool = block(c, "wool", Block::new, Blocks.WOOL.white());
            block(c, "wool_slab", SlabBlock::new, Blocks.WOOL_SLAB.white());
            block(c, "wool_stairs", p -> new StairBlock(wool.defaultBlockState(), p), Blocks.WOOL_STAIRS.white());
            block(c, "carpet", CarpetBlock::new, Blocks.CARPET.white());
            Block concrete = block(c, "concrete", Block::new, Blocks.CONCRETE.white());
            block(c, "concrete_slab", SlabBlock::new, Blocks.CONCRETE_SLAB.white());
            block(c, "concrete_stairs", p -> new StairBlock(concrete.defaultBlockState(), p), Blocks.CONCRETE_STAIRS.white());
            block(c, "concrete_powder", p -> new ConcretePowderBlock(concrete, p), Blocks.CONCRETE_POWDER.white());
            block(c, "terracotta", Block::new, Blocks.DYED_TERRACOTTA.white());
            block(c, "glazed_terracotta", GlazedTerracottaBlock::new, Blocks.GLAZED_TERRACOTTA.white());
            block(c, "stained_glass", SiftGlassBlock::new, Blocks.STAINED_GLASS.white());
            block(c, "stained_glass_pane", SiftGlassPaneBlock::new, Blocks.STAINED_GLASS_PANE.white());
        }
        Registry.register(BuiltInRegistries.RECIPE_SERIALIZER, PySift.id("crafting_sift_dye"), SiftDyeRecipe.SERIALIZER);
        CreativeModeTabEvents.modifyOutputEvent(ModItems.BLOCKS_TAB_KEY).register(output -> ORDER.forEach(output::accept));
    }

    private static Block block(SiftColor c, String kind, Function<BlockBehaviour.Properties, Block> factory, Block like) {
        String name = c.id + "_" + kind;
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        Block block = Registry.register(BuiltInRegistries.BLOCK, blockKey,
                factory.apply(BlockBehaviour.Properties.ofFullCopy(like).setId(blockKey)));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Item item = Registry.register(BuiltInRegistries.ITEM, itemKey,
                new BlockItem(block, new Item.Properties().setId(itemKey)));
        TINTS.put(block, c.rgb);
        ORDER.add(item);
        return block;
    }

    /** 新顏色的染料：記住自己的顏色，給染皮甲的配方用。 */
    public static final class SiftDyeItem extends Item {
        public final SiftColor color;

        public SiftDyeItem(SiftColor color, Properties properties) {
            super(properties);
            this.color = color;
        }
    }

    /** 染色玻璃（原版 StainedGlassBlock 需要 DyeColor，這裡用沒有顏色的透明方塊，顏色由著色決定）。 */
    public static final class SiftGlassBlock extends TransparentBlock {
        public SiftGlassBlock(Properties properties) {
            super(properties);
        }
    }

    /** 玻璃片（同上，原版 StainedGlassPaneBlock 需要 DyeColor）。 */
    public static final class SiftGlassPaneBlock extends IronBarsBlock {
        public SiftGlassPaneBlock(Properties properties) {
            super(properties);
        }
    }
}
