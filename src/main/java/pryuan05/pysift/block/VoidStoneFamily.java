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
 * 虛黑岩（玄武岩）的其他建材，比照原版深板岩的磨製／磚瓦／裂紋形式與平滑石：
 * 磨製虛黑岩、虛黑岩磚瓦（各含半磚／階梯／牆）、裂紋虛黑岩磚、裂紋虛黑岩磚瓦、平滑虛黑岩與其半磚。
 * 虛黑岩本體、石磚、浮雕石磚與柱在 {@link ModBlocks}。
 * <ul>
 *   <li>方塊性質複製原版石頭系的對應方塊（虛黑岩是 Mat.STONE，硬度與原版石頭相同）。</li>
 *   <li>資源（模型、配方、掉落、標籤）由 tools/worldgen/build_void_stone_family.py 從原版深板岩／平滑石複製改寫產生，
 *       貼圖由 tools/worldgen/paint_void_stone.py 手繪。</li>
 * </ul>
 */
public final class VoidStoneFamily {
    private static final List<Item> ITEMS = new ArrayList<>();

    public static final Block POLISHED_VOID_STONE = block("polished_void_stone", Block::new, Blocks.POLISHED_ANDESITE);
    public static final Block POLISHED_VOID_STONE_SLAB = block("polished_void_stone_slab", SlabBlock::new, Blocks.POLISHED_ANDESITE_SLAB);
    public static final Block POLISHED_VOID_STONE_STAIRS = block("polished_void_stone_stairs",
            p -> new StairBlock(POLISHED_VOID_STONE.defaultBlockState(), p), Blocks.POLISHED_ANDESITE_STAIRS);
    public static final Block POLISHED_VOID_STONE_WALL = block("polished_void_stone_wall", WallBlock::new, Blocks.ANDESITE_WALL);

    public static final Block VOID_STONE_TILES = block("void_stone_tiles", Block::new, Blocks.STONE_BRICKS);
    public static final Block VOID_STONE_TILE_SLAB = block("void_stone_tile_slab", SlabBlock::new, Blocks.STONE_BRICK_SLAB);
    public static final Block VOID_STONE_TILE_STAIRS = block("void_stone_tile_stairs",
            p -> new StairBlock(VOID_STONE_TILES.defaultBlockState(), p), Blocks.STONE_BRICK_STAIRS);
    public static final Block VOID_STONE_TILE_WALL = block("void_stone_tile_wall", WallBlock::new, Blocks.STONE_BRICK_WALL);

    // 原版沒有的衍生（每種方塊都要有半磚／階梯／牆）：資源由 build_void_stone_family.py 從磨製深板岩的形式改寫
    public static final Block CRACKED_VOID_STONE_BRICKS = block("cracked_void_stone_bricks", Block::new, Blocks.CRACKED_STONE_BRICKS);
    public static final Block CRACKED_VOID_STONE_BRICK_SLAB = block("cracked_void_stone_brick_slab", SlabBlock::new, Blocks.STONE_BRICK_SLAB);
    public static final Block CRACKED_VOID_STONE_BRICK_STAIRS = block("cracked_void_stone_brick_stairs",
            p -> new StairBlock(CRACKED_VOID_STONE_BRICKS.defaultBlockState(), p), Blocks.STONE_BRICK_STAIRS);
    public static final Block CRACKED_VOID_STONE_BRICK_WALL = block("cracked_void_stone_brick_wall", WallBlock::new, Blocks.STONE_BRICK_WALL);

    public static final Block CRACKED_VOID_STONE_TILES = block("cracked_void_stone_tiles", Block::new, Blocks.CRACKED_STONE_BRICKS);
    public static final Block CRACKED_VOID_STONE_TILE_SLAB = block("cracked_void_stone_tile_slab", SlabBlock::new, Blocks.STONE_BRICK_SLAB);
    public static final Block CRACKED_VOID_STONE_TILE_STAIRS = block("cracked_void_stone_tile_stairs",
            p -> new StairBlock(CRACKED_VOID_STONE_TILES.defaultBlockState(), p), Blocks.STONE_BRICK_STAIRS);
    public static final Block CRACKED_VOID_STONE_TILE_WALL = block("cracked_void_stone_tile_wall", WallBlock::new, Blocks.STONE_BRICK_WALL);

    public static final Block SMOOTH_VOID_STONE = block("smooth_void_stone", Block::new, Blocks.SMOOTH_STONE);
    public static final Block SMOOTH_VOID_STONE_SLAB = block("smooth_void_stone_slab", SlabBlock::new, Blocks.SMOOTH_STONE_SLAB);
    public static final Block SMOOTH_VOID_STONE_STAIRS = block("smooth_void_stone_stairs",
            p -> new StairBlock(SMOOTH_VOID_STONE.defaultBlockState(), p), Blocks.STONE_STAIRS);
    public static final Block SMOOTH_VOID_STONE_WALL = block("smooth_void_stone_wall", WallBlock::new, Blocks.STONE_BRICK_WALL);

    private VoidStoneFamily() {
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
        PySift.LOGGER.info("Registered void stone family ({} blocks)", ITEMS.size());
    }
}
