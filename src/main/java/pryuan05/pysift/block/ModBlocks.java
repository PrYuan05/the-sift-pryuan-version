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
        PySift.LOGGER.info("Registering Blocks for {}", PySift.MOD_ID);
    }
}
