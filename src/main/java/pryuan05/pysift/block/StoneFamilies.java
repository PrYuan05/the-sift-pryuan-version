package pryuan05.pysift.block;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.WallBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import pryuan05.pysift.PySift;
import pryuan05.pysift.item.ModItems;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

/**
 * 升級後石材的額外建材形式（依現實參照挑選的 polished／smooth／tiles），每個方塊都附半磚／階梯／牆。
 * <ul>
 *   <li>平滑灰大理石：無外框的鋸切大理石面（smooth_basalt 式），灰大理石燒製而成。</li>
 *   <li>資源由 tools/worldgen/build_stone_families.py 從原版磨製深板岩的形式改寫，貼圖由 paint_marble_mudstone.py 手繪。</li>
 * </ul>
 */
public final class StoneFamilies {
    private static final List<Item> ITEMS = new ArrayList<>();

    public static final Block SMOOTH_ASH_MARBLE = block("smooth_ash_marble", Block::new, Blocks.SMOOTH_STONE);
    public static final Block SMOOTH_ASH_MARBLE_SLAB = block("smooth_ash_marble_slab", SlabBlock::new, Blocks.SMOOTH_STONE_SLAB);
    public static final Block SMOOTH_ASH_MARBLE_STAIRS = block("smooth_ash_marble_stairs",
            p -> new StairBlock(SMOOTH_ASH_MARBLE.defaultBlockState(), p), Blocks.STONE_STAIRS);
    public static final Block SMOOTH_ASH_MARBLE_WALL = block("smooth_ash_marble_wall", WallBlock::new, Blocks.STONE_BRICK_WALL);

    private StoneFamilies() {
    }

    private static Block block(String name, Function<BlockBehaviour.Properties, Block> factory, Block copyFrom) {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Block block = Registry.register(BuiltInRegistries.BLOCK, blockKey, factory.apply(BlockBehaviour.Properties.ofFullCopy(copyFrom).setId(blockKey)));
        ITEMS.add(Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().setId(itemKey))));
        return block;
    }

    public static void register() {
        pryuan05.pysift.item.SiftCreativeTabs.source(ModItems.BLOCKS_TAB_KEY, output -> ITEMS.forEach(output::accept));
        PySift.LOGGER.info("Registered stone families ({} blocks)", ITEMS.size());
    }
}
