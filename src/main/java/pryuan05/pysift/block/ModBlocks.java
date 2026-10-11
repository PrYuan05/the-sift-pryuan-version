package pryuan05.pysift.block;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import pryuan05.pysift.PySift;

public class ModBlocks {
    // --- 核心基準方塊 ---
    public static final Block SIFTSLATE = registerBlock("siftslate",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.0f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.DEEPSLATE)
    );

    public static final Block RED_SCULK = registerBlock("red_sculk",
            BlockBehaviour.Properties.of()
                    .destroyTime(0.6f)
                    .explosionResistance(0.6f)
                    .sound(SoundType.SCULK)
    );

    public static final Block CHAROITE_ORE = registerBlock("charoite_ore",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.5f)
                    .explosionResistance(3.5f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.STONE)
    );

    public static final Block OVERGROWN_WILLOW_PLANKS = registerBlock("overgrown_willow_planks",
            BlockBehaviour.Properties.of()
                    .destroyTime(2.0f)
                    .explosionResistance(3.0f)
                    .sound(SoundType.WOOD)
    );

    // --- 擴展維度環境與建材方塊 ---
    public static final Block COBBLED_SIFTSLATE = registerBlock("cobbled_siftslate",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.5f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.DEEPSLATE)
    );

    public static final Block POLISHED_SIFTSLATE = registerBlock("polished_siftslate",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.5f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.DEEPSLATE)
    );

    public static final Block SIFTSLATE_BRICKS = registerBlock("siftslate_bricks",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.5f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.DEEPSLATE)
    );

    public static final Block CRACKED_SIFTSLATE_BRICKS = registerBlock("cracked_siftslate_bricks",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.5f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.DEEPSLATE)
    );

    public static final Block SIFTSLATE_TILES = registerBlock("siftslate_tiles",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.5f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.DEEPSLATE)
    );

    public static final Block CHISELED_SIFTSLATE = registerBlock("chiseled_siftslate",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.5f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.DEEPSLATE)
    );

    public static final Block MOSSY_SIFTSLATE = registerBlock("mossy_siftslate",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.5f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.DEEPSLATE)
    );

    public static final Block SIFTSLATE_PILLAR = registerBlock("siftslate_pillar",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.5f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.DEEPSLATE)
    );

    public static final Block RED_SCULK_CATALYST = registerBlock("red_sculk_catalyst",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.0f)
                    .explosionResistance(3.0f)
                    .sound(SoundType.SCULK_CATALYST)
                    .lightLevel(state -> 6)
    );

    public static final Block RED_SCULK_SENSOR = registerBlock("red_sculk_sensor",
            BlockBehaviour.Properties.of()
                    .destroyTime(1.5f)
                    .explosionResistance(1.5f)
                    .sound(SoundType.SCULK_SENSOR)
                    .lightLevel(state -> 4)
    );

    public static final Block RED_SCULK_SHRIEKER = registerBlock("red_sculk_shrieker",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.0f)
                    .explosionResistance(3.0f)
                    .sound(SoundType.SCULK_SHRIEKER)
    );

    public static final Block RED_SCULK_VEIN_BLOCK = registerBlock("red_sculk_vein_block",
            BlockBehaviour.Properties.of()
                    .destroyTime(0.8f)
                    .explosionResistance(0.8f)
                    .sound(SoundType.SCULK_VEIN)
                    .lightLevel(state -> 2)
    );

    public static final Block SCULK_TENDRIL_BLOCK = registerBlock("sculk_tendril_block",
            BlockBehaviour.Properties.of()
                    .destroyTime(0.6f)
                    .explosionResistance(0.6f)
                    .sound(SoundType.SCULK)
    );

    public static final Block CORRUPTED_SCULK_STONE = registerBlock("corrupted_sculk_stone",
            BlockBehaviour.Properties.of()
                    .destroyTime(2.0f)
                    .explosionResistance(3.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.SCULK)
    );

    public static final Block CHAROITE_BLOCK = registerBlock("charoite_block",
            BlockBehaviour.Properties.of()
                    .destroyTime(5.0f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.AMETHYST)
    );

    public static final Block RAW_CHAROITE_BLOCK = registerBlock("raw_charoite_block",
            BlockBehaviour.Properties.of()
                    .destroyTime(5.0f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.STONE)
    );

    public static final Block CHAROITE_BRICKS = registerBlock("charoite_bricks",
            BlockBehaviour.Properties.of()
                    .destroyTime(4.0f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.AMETHYST)
    );

    public static final Block CHISELED_CHAROITE = registerBlock("chiseled_charoite",
            BlockBehaviour.Properties.of()
                    .destroyTime(4.0f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.AMETHYST)
    );

    public static final Block POLISHED_CHAROITE = registerBlock("polished_charoite",
            BlockBehaviour.Properties.of()
                    .destroyTime(4.0f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.AMETHYST)
    );

    public static final Block GLOWING_CHAROITE = registerBlock("glowing_charoite",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.0f)
                    .explosionResistance(3.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.AMETHYST)
                    .lightLevel(state -> 12)
    );

    public static final Block OVERGROWN_WILLOW_LOG = registerBlock("overgrown_willow_log",
            BlockBehaviour.Properties.of()
                    .destroyTime(2.0f)
                    .explosionResistance(2.0f)
                    .sound(SoundType.WOOD)
    );

    public static final Block STRIPPED_OVERGROWN_WILLOW_LOG = registerBlock("stripped_overgrown_willow_log",
            BlockBehaviour.Properties.of()
                    .destroyTime(2.0f)
                    .explosionResistance(2.0f)
                    .sound(SoundType.WOOD)
    );

    public static final Block OVERGROWN_WILLOW_WOOD = registerBlock("overgrown_willow_wood",
            BlockBehaviour.Properties.of()
                    .destroyTime(2.0f)
                    .explosionResistance(2.0f)
                    .sound(SoundType.WOOD)
    );

    public static final Block STRIPPED_OVERGROWN_WILLOW_WOOD = registerBlock("stripped_overgrown_willow_wood",
            BlockBehaviour.Properties.of()
                    .destroyTime(2.0f)
                    .explosionResistance(2.0f)
                    .sound(SoundType.WOOD)
    );

    public static final Block OVERGROWN_WILLOW_MOSAIC = registerBlock("overgrown_willow_mosaic",
            BlockBehaviour.Properties.of()
                    .destroyTime(2.0f)
                    .explosionResistance(2.0f)
                    .sound(SoundType.WOOD)
    );

    public static final Block SIFT_SOIL = registerBlock("sift_soil",
            BlockBehaviour.Properties.of()
                    .destroyTime(0.6f)
                    .explosionResistance(0.6f)
                    .sound(SoundType.GRAVEL)
    );

    public static final Block SIFT_MUD = registerBlock("sift_mud",
            BlockBehaviour.Properties.of()
                    .destroyTime(0.5f)
                    .explosionResistance(0.5f)
                    .sound(SoundType.MUD)
    );

    public static final Block SIFT_MUD_BRICKS = registerBlock("sift_mud_bricks",
            BlockBehaviour.Properties.of()
                    .destroyTime(2.0f)
                    .explosionResistance(3.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.MUD_BRICKS)
    );

    public static final Block SIFT_SAND = registerBlock("sift_sand",
            BlockBehaviour.Properties.of()
                    .destroyTime(0.5f)
                    .explosionResistance(0.5f)
                    .sound(SoundType.SAND)
    );

    public static final Block SIFT_SANDSTONE = registerBlock("sift_sandstone",
            BlockBehaviour.Properties.of()
                    .destroyTime(0.8f)
                    .explosionResistance(0.8f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.STONE)
    );

    public static final Block SMOOTH_SIFT_SANDSTONE = registerBlock("smooth_sift_sandstone",
            BlockBehaviour.Properties.of()
                    .destroyTime(2.0f)
                    .explosionResistance(6.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.STONE)
    );

    public static final Block CUT_SIFT_SANDSTONE = registerBlock("cut_sift_sandstone",
            BlockBehaviour.Properties.of()
                    .destroyTime(0.8f)
                    .explosionResistance(0.8f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.STONE)
    );

    public static final Block CHISELED_SIFT_SANDSTONE = registerBlock("chiseled_sift_sandstone",
            BlockBehaviour.Properties.of()
                    .destroyTime(0.8f)
                    .explosionResistance(0.8f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.STONE)
    );

    public static final Block ANCIENT_RELIC_STONE = registerBlock("ancient_relic_stone",
            BlockBehaviour.Properties.of()
                    .destroyTime(4.0f)
                    .explosionResistance(8.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.STONE)
    );

    public static final Block CHISELED_RELIC_STONE = registerBlock("chiseled_relic_stone",
            BlockBehaviour.Properties.of()
                    .destroyTime(4.0f)
                    .explosionResistance(8.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.STONE)
    );

    public static final Block ANCIENT_RELIC_PILLAR = registerBlock("ancient_relic_pillar",
            BlockBehaviour.Properties.of()
                    .destroyTime(4.0f)
                    .explosionResistance(8.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.STONE)
    );

    public static final Block RUNIC_SIFTSLATE = registerBlock("runic_siftslate",
            BlockBehaviour.Properties.of()
                    .destroyTime(4.5f)
                    .explosionResistance(9.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.DEEPSLATE)
                    .lightLevel(state -> 7)
    );

    public static final Block ANCIENT_PLATING = registerBlock("ancient_plating",
            BlockBehaviour.Properties.of()
                    .destroyTime(5.0f)
                    .explosionResistance(12.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.METAL)
    );

    public static final Block RELIC_CORE_BLOCK = registerBlock("relic_core_block",
            BlockBehaviour.Properties.of()
                    .destroyTime(5.0f)
                    .explosionResistance(10.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.AMETHYST)
                    .lightLevel(state -> 15)
    );

    public static final Block SIFT_BONE_BLOCK = registerBlock("sift_bone_block",
            BlockBehaviour.Properties.of()
                    .destroyTime(2.0f)
                    .explosionResistance(2.0f)
                    .sound(SoundType.BONE_BLOCK)
    );

    public static final Block FOSSILIZED_SCULK_BONE = registerBlock("fossilized_sculk_bone",
            BlockBehaviour.Properties.of()
                    .destroyTime(3.0f)
                    .explosionResistance(4.0f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.BONE_BLOCK)
    );

    public static final Block SIFT_SPORE_GROWTH = registerBlock("sift_spore_growth",
            BlockBehaviour.Properties.of()
                    .destroyTime(1.0f)
                    .explosionResistance(1.0f)
                    .sound(SoundType.MOSS)
                    .lightLevel(state -> 5)
    );

    // 完整方塊列表（供創造模式分頁使用）
    public static final Block[] ALL_BLOCKS = new Block[] {
            SIFTSLATE, RED_SCULK, CHAROITE_ORE, OVERGROWN_WILLOW_PLANKS,
            COBBLED_SIFTSLATE, POLISHED_SIFTSLATE, SIFTSLATE_BRICKS, CRACKED_SIFTSLATE_BRICKS,
            SIFTSLATE_TILES, CHISELED_SIFTSLATE, MOSSY_SIFTSLATE, SIFTSLATE_PILLAR,
            RED_SCULK_CATALYST, RED_SCULK_SENSOR, RED_SCULK_SHRIEKER, RED_SCULK_VEIN_BLOCK,
            SCULK_TENDRIL_BLOCK, CORRUPTED_SCULK_STONE, CHAROITE_BLOCK, RAW_CHAROITE_BLOCK,
            CHAROITE_BRICKS, CHISELED_CHAROITE, POLISHED_CHAROITE, GLOWING_CHAROITE,
            OVERGROWN_WILLOW_LOG, STRIPPED_OVERGROWN_WILLOW_LOG, OVERGROWN_WILLOW_WOOD, STRIPPED_OVERGROWN_WILLOW_WOOD,
            OVERGROWN_WILLOW_MOSAIC, SIFT_SOIL, SIFT_MUD, SIFT_MUD_BRICKS,
            SIFT_SAND, SIFT_SANDSTONE, SMOOTH_SIFT_SANDSTONE, CUT_SIFT_SANDSTONE,
            CHISELED_SIFT_SANDSTONE, ANCIENT_RELIC_STONE, CHISELED_RELIC_STONE, ANCIENT_RELIC_PILLAR,
            RUNIC_SIFTSLATE, ANCIENT_PLATING, RELIC_CORE_BLOCK, SIFT_BONE_BLOCK,
            FOSSILIZED_SCULK_BONE, SIFT_SPORE_GROWTH
    };

    private static Block registerBlock(String name, BlockBehaviour.Properties properties) {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(name));

        Block block = new Block(properties.setId(blockKey));
        Registry.register(BuiltInRegistries.BLOCK, blockKey, block);

        BlockItem blockItem = new BlockItem(block, new Item.Properties().setId(itemKey));
        Registry.register(BuiltInRegistries.ITEM, itemKey, blockItem);

        return block;
    }

    public static void registerModBlocks() {
        PySift.LOGGER.info("Registering {} Blocks for {}", ALL_BLOCKS.length, PySift.MOD_ID);
    }
}
