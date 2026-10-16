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
import net.minecraft.world.level.block.state.BlockBehaviour;
import pryuan05.pysift.PySift;
import pryuan05.pysift.item.ModItems;

/**
 * 靈魂晶塊：迴音傀儡頭頂慢慢凝結的淡藍色發光方塊（貼圖取自傀儡模型頭頂那顆方塊）。
 * 傀儡會把它送給歌者，玩家也能右鍵傀儡取下；泥板厚甲怪用它繁殖。資源由 tools/worldgen/build_soul_crystal.py 產生。
 */
public final class SoulCrystal {
    public static final Block SOUL_CRYSTAL_BLOCK;
    public static final Item SOUL_CRYSTAL_BLOCK_ITEM;

    static {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id("soul_crystal_block"));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id("soul_crystal_block"));
        SOUL_CRYSTAL_BLOCK = Registry.register(BuiltInRegistries.BLOCK, blockKey, new Block(
                BlockBehaviour.Properties.ofFullCopy(Blocks.AMETHYST_BLOCK).lightLevel(state -> 10).setId(blockKey)));
        SOUL_CRYSTAL_BLOCK_ITEM = Registry.register(BuiltInRegistries.ITEM, itemKey,
                new BlockItem(SOUL_CRYSTAL_BLOCK, new Item.Properties().setId(itemKey)));
    }

    private SoulCrystal() {
    }

    public static void register() {
        CreativeModeTabEvents.modifyOutputEvent(ModItems.BLOCKS_TAB_KEY).register(output -> output.accept(SOUL_CRYSTAL_BLOCK_ITEM));
        PySift.LOGGER.info("Registered soul crystal block");
    }
}
