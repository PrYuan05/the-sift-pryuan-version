package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.WallBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import org.jspecify.annotations.Nullable;
import pryuan05.pysift.PySift;
import pryuan05.pysift.item.ModItems;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

/**
 * 魂頁岩：原版深板岩整個家族的形式，配色取自使用者給的雕紋魂頁岩貼圖（6 色色票）。
 * 魂頁岩、磨製、磚、裂紋磚、磚瓦、裂紋磚瓦都有半磚／階梯／牆，雕紋魂頁岩沒有。
 * <ul>
 *   <li>取得：8 個深淵地層圍住 1 個靈魂沙或靈魂土，合成 8 個魂頁岩；其餘照原版深板岩的合成、切石與燒製。</li>
 *   <li>方塊性質複製原版深板岩的對應方塊（硬度、聲音）。</li>
 *   <li>雕紋魂頁岩放下時，會響起八音儀式 8 個音的其中一個（和共鳴唱片盒同一組聲音與音高，{@link RitualDiscs}）。</li>
 *   <li>資源與貼圖由 tools/worldgen/build_soulshale_family.py 產生。</li>
 * </ul>
 */
public final class SoulshaleFamily {
    private static final List<Item> ITEMS = new ArrayList<>();

    public static final Block SOULSHALE = block("soulshale", RotatedPillarBlock::new, Blocks.DEEPSLATE);
    public static final Block SOULSHALE_SLAB = block("soulshale_slab", SlabBlock::new, Blocks.COBBLED_DEEPSLATE_SLAB);
    public static final Block SOULSHALE_STAIRS = block("soulshale_stairs",
            p -> new StairBlock(SOULSHALE.defaultBlockState(), p), Blocks.COBBLED_DEEPSLATE_STAIRS);
    public static final Block SOULSHALE_WALL = block("soulshale_wall", WallBlock::new, Blocks.COBBLED_DEEPSLATE_WALL);

    public static final Block POLISHED_SOULSHALE = block("polished_soulshale", Block::new, Blocks.POLISHED_DEEPSLATE);
    public static final Block POLISHED_SOULSHALE_SLAB = block("polished_soulshale_slab", SlabBlock::new, Blocks.POLISHED_DEEPSLATE_SLAB);
    public static final Block POLISHED_SOULSHALE_STAIRS = block("polished_soulshale_stairs",
            p -> new StairBlock(POLISHED_SOULSHALE.defaultBlockState(), p), Blocks.POLISHED_DEEPSLATE_STAIRS);
    public static final Block POLISHED_SOULSHALE_WALL = block("polished_soulshale_wall", WallBlock::new, Blocks.POLISHED_DEEPSLATE_WALL);

    public static final Block SOULSHALE_BRICKS = block("soulshale_bricks", Block::new, Blocks.DEEPSLATE_BRICKS);
    public static final Block SOULSHALE_BRICK_SLAB = block("soulshale_brick_slab", SlabBlock::new, Blocks.DEEPSLATE_BRICK_SLAB);
    public static final Block SOULSHALE_BRICK_STAIRS = block("soulshale_brick_stairs",
            p -> new StairBlock(SOULSHALE_BRICKS.defaultBlockState(), p), Blocks.DEEPSLATE_BRICK_STAIRS);
    public static final Block SOULSHALE_BRICK_WALL = block("soulshale_brick_wall", WallBlock::new, Blocks.DEEPSLATE_BRICK_WALL);

    public static final Block CRACKED_SOULSHALE_BRICKS = block("cracked_soulshale_bricks", Block::new, Blocks.CRACKED_DEEPSLATE_BRICKS);
    public static final Block CRACKED_SOULSHALE_BRICK_SLAB = block("cracked_soulshale_brick_slab", SlabBlock::new, Blocks.DEEPSLATE_BRICK_SLAB);
    public static final Block CRACKED_SOULSHALE_BRICK_STAIRS = block("cracked_soulshale_brick_stairs",
            p -> new StairBlock(CRACKED_SOULSHALE_BRICKS.defaultBlockState(), p), Blocks.DEEPSLATE_BRICK_STAIRS);
    public static final Block CRACKED_SOULSHALE_BRICK_WALL = block("cracked_soulshale_brick_wall", WallBlock::new, Blocks.DEEPSLATE_BRICK_WALL);

    public static final Block SOULSHALE_TILES = block("soulshale_tiles", Block::new, Blocks.DEEPSLATE_TILES);
    public static final Block SOULSHALE_TILE_SLAB = block("soulshale_tile_slab", SlabBlock::new, Blocks.DEEPSLATE_TILE_SLAB);
    public static final Block SOULSHALE_TILE_STAIRS = block("soulshale_tile_stairs",
            p -> new StairBlock(SOULSHALE_TILES.defaultBlockState(), p), Blocks.DEEPSLATE_TILE_STAIRS);
    public static final Block SOULSHALE_TILE_WALL = block("soulshale_tile_wall", WallBlock::new, Blocks.DEEPSLATE_TILE_WALL);

    public static final Block CRACKED_SOULSHALE_TILES = block("cracked_soulshale_tiles", Block::new, Blocks.CRACKED_DEEPSLATE_TILES);
    public static final Block CRACKED_SOULSHALE_TILE_SLAB = block("cracked_soulshale_tile_slab", SlabBlock::new, Blocks.DEEPSLATE_TILE_SLAB);
    public static final Block CRACKED_SOULSHALE_TILE_STAIRS = block("cracked_soulshale_tile_stairs",
            p -> new StairBlock(CRACKED_SOULSHALE_TILES.defaultBlockState(), p), Blocks.DEEPSLATE_TILE_STAIRS);
    public static final Block CRACKED_SOULSHALE_TILE_WALL = block("cracked_soulshale_tile_wall", WallBlock::new, Blocks.DEEPSLATE_TILE_WALL);

    public static final Block CHISELED_SOULSHALE = block("chiseled_soulshale", ChiseledSoulshaleBlock::new, Blocks.CHISELED_DEEPSLATE);

    private SoulshaleFamily() {
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
        PySift.LOGGER.info("Registered soulshale family ({} blocks)", ITEMS.size());
    }

    /** 雕紋魂頁岩：放下時隨機響起八音裡的一個音（共鳴唱片盒的 chime＋harp，同樣的音高）。 */
    public static class ChiseledSoulshaleBlock extends Block {
        public ChiseledSoulshaleBlock(Properties properties) {
            super(properties);
        }

        @Override
        public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity by, ItemStack stack) {
            super.setPlacedBy(level, pos, state, by, stack);
            if (!level.isClientSide()) {
                float pitch = RitualDiscs.DISCS.get(level.getRandom().nextInt(RitualDiscs.DISCS.size())).pitch();
                level.playSound(null, pos, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.BLOCKS, 1.0f, pitch);
                level.playSound(null, pos, SoundEvents.NOTE_BLOCK_HARP.value(), SoundSource.BLOCKS, 0.7f, pitch);
            }
        }
    }
}
