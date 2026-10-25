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
 * 每種沙（{@link ModBlocks} 的 amber_sand、pale_sand）各一套和原版砂岩相同的建材：
 * 砂岩、雕紋砂岩、切製砂岩、平滑砂岩，砂岩的半磚／階梯／牆，切製砂岩半磚，平滑砂岩的半磚／階梯。
 * <ul>
 *   <li>方塊性質一律複製原版砂岩的對應方塊（砂岩本身不受重力影響，和原版一樣；會掉落的是沙）。</li>
 *   <li>資源（模型、配方、掉落、標籤、改色貼圖）由 tools/worldgen/build_sandstone.py 從原版砂岩複製改寫產生，
 *       貼圖依該種沙的顏色重新上色。</li>
 * </ul>
 */
public final class SandstoneFamily {
    private static final List<Item> ITEMS = new ArrayList<>();

    // ===== 琥珀沙 → 琥珀砂岩 =====
    public static final Block AMBER_SANDSTONE = block("amber_sandstone", Block::new, Blocks.SANDSTONE);
    public static final Block CHISELED_AMBER_SANDSTONE = block("chiseled_amber_sandstone", Block::new, Blocks.CHISELED_SANDSTONE);
    public static final Block CUT_AMBER_SANDSTONE = block("cut_amber_sandstone", Block::new, Blocks.CUT_SANDSTONE);
    public static final Block SMOOTH_AMBER_SANDSTONE = block("smooth_amber_sandstone", Block::new, Blocks.SMOOTH_SANDSTONE);
    public static final Block AMBER_SANDSTONE_SLAB = block("amber_sandstone_slab", SlabBlock::new, Blocks.SANDSTONE_SLAB);
    public static final Block AMBER_SANDSTONE_STAIRS = block("amber_sandstone_stairs",
            p -> new StairBlock(AMBER_SANDSTONE.defaultBlockState(), p), Blocks.SANDSTONE_STAIRS);
    public static final Block AMBER_SANDSTONE_WALL = block("amber_sandstone_wall", WallBlock::new, Blocks.SANDSTONE_WALL);
    public static final Block CUT_AMBER_SANDSTONE_SLAB = block("cut_amber_sandstone_slab", SlabBlock::new, Blocks.CUT_SANDSTONE_SLAB);
    public static final Block SMOOTH_AMBER_SANDSTONE_SLAB = block("smooth_amber_sandstone_slab", SlabBlock::new, Blocks.SMOOTH_SANDSTONE_SLAB);
    public static final Block SMOOTH_AMBER_SANDSTONE_STAIRS = block("smooth_amber_sandstone_stairs",
            p -> new StairBlock(SMOOTH_AMBER_SANDSTONE.defaultBlockState(), p), Blocks.SMOOTH_SANDSTONE_STAIRS);

    // ===== 淺沙 → 淺砂岩 =====
    public static final Block PALE_SANDSTONE = block("pale_sandstone", Block::new, Blocks.SANDSTONE);
    public static final Block CHISELED_PALE_SANDSTONE = block("chiseled_pale_sandstone", Block::new, Blocks.CHISELED_SANDSTONE);
    public static final Block CUT_PALE_SANDSTONE = block("cut_pale_sandstone", Block::new, Blocks.CUT_SANDSTONE);
    public static final Block SMOOTH_PALE_SANDSTONE = block("smooth_pale_sandstone", Block::new, Blocks.SMOOTH_SANDSTONE);
    public static final Block PALE_SANDSTONE_SLAB = block("pale_sandstone_slab", SlabBlock::new, Blocks.SANDSTONE_SLAB);
    public static final Block PALE_SANDSTONE_STAIRS = block("pale_sandstone_stairs",
            p -> new StairBlock(PALE_SANDSTONE.defaultBlockState(), p), Blocks.SANDSTONE_STAIRS);
    public static final Block PALE_SANDSTONE_WALL = block("pale_sandstone_wall", WallBlock::new, Blocks.SANDSTONE_WALL);
    public static final Block CUT_PALE_SANDSTONE_SLAB = block("cut_pale_sandstone_slab", SlabBlock::new, Blocks.CUT_SANDSTONE_SLAB);
    public static final Block SMOOTH_PALE_SANDSTONE_SLAB = block("smooth_pale_sandstone_slab", SlabBlock::new, Blocks.SMOOTH_SANDSTONE_SLAB);
    public static final Block SMOOTH_PALE_SANDSTONE_STAIRS = block("smooth_pale_sandstone_stairs",
            p -> new StairBlock(SMOOTH_PALE_SANDSTONE.defaultBlockState(), p), Blocks.SMOOTH_SANDSTONE_STAIRS);

    private SandstoneFamily() {
    }

    private static Block block(String name, Function<BlockBehaviour.Properties, Block> factory, Block copyFrom) {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Block block = Registry.register(BuiltInRegistries.BLOCK, blockKey, factory.apply(BlockBehaviour.Properties.ofFullCopy(copyFrom).setId(blockKey)));
        ITEMS.add(Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().setId(itemKey))));
        return block;
    }

    public static void register() {
        CreativeModeTabEvents.modifyOutputEvent(ModItems.BLOCKS_TAB_KEY).register(output -> ITEMS.forEach(output::accept));
        PySift.LOGGER.info("Registered sandstone families ({} blocks)", ITEMS.size());
    }
}
