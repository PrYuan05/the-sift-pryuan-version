package pryuan05.pysift.item;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SpawnEggItem;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.ModBlocks;
import pryuan05.pysift.entity.ModEntities;

import java.util.function.Function;

public class ModItems {
    // Core Materials
    public static final Item CHAROITE = registerItem("charoite", Item::new);
    public static final Item SIFTITE_INGOT = registerItem("siftite_ingot", Item::new);

    // 24 Spawn Eggs
    public static final Item BLUB_SPAWN_EGG = registerSpawnEgg("blub_spawn_egg", ModEntities.BLUB);
    public static final Item ECHO_GOLEM_SPAWN_EGG = registerSpawnEgg("echo_golem_spawn_egg", ModEntities.ECHO_GOLEM);
    public static final Item SINGER_SPAWN_EGG = registerSpawnEgg("singer_spawn_egg", ModEntities.SINGER);
    public static final Item NUZZLE_SPAWN_EGG = registerSpawnEgg("nuzzle_spawn_egg", ModEntities.NUZZLE);
    public static final Item LOOTKIN_SPAWN_EGG = registerSpawnEgg("lootkin_spawn_egg", ModEntities.LOOTKIN);
    public static final Item FUSEFLY_SPAWN_EGG = registerSpawnEgg("fusefly_spawn_egg", ModEntities.FUSEFLY);
    public static final Item DARTBACK_SPAWN_EGG = registerSpawnEgg("dartback_spawn_egg", ModEntities.DARTBACK);
    public static final Item HURLER_SPAWN_EGG = registerSpawnEgg("hurler_spawn_egg", ModEntities.HURLER);
    public static final Item POLLINATOR_SPAWN_EGG = registerSpawnEgg("pollinator_spawn_egg", ModEntities.POLLINATOR);
    public static final Item NESTER_SPAWN_EGG = registerSpawnEgg("nester_spawn_egg", ModEntities.NESTER);
    public static final Item SEEDLING_SPAWN_EGG = registerSpawnEgg("seedling_spawn_egg", ModEntities.SEEDLING);
    public static final Item SPROUT_SPAWN_EGG = registerSpawnEgg("sprout_spawn_egg", ModEntities.SPROUT);
    public static final Item STALKER_SPAWN_EGG = registerSpawnEgg("stalker_spawn_egg", ModEntities.STALKER);
    public static final Item SCAVENGER_SPAWN_EGG = registerSpawnEgg("scavenger_spawn_egg", ModEntities.SCAVENGER);
    public static final Item SLABBER_SPAWN_EGG = registerSpawnEgg("slabber_spawn_egg", ModEntities.SLABBER);
    public static final Item PRICKLE_SPAWN_EGG = registerSpawnEgg("prickle_spawn_egg", ModEntities.PRICKLE);
    public static final Item SENTINEL_SPAWN_EGG = registerSpawnEgg("sentinel_spawn_egg", ModEntities.SENTINEL);
    public static final Item TUNER_SPAWN_EGG = registerSpawnEgg("tuner_spawn_egg", ModEntities.TUNER);
    public static final Item BLOOMBUD_SPAWN_EGG = registerSpawnEgg("bloombud_spawn_egg", ModEntities.BLOOMBUD);
    public static final Item ROAMROOT_SPAWN_EGG = registerSpawnEgg("roamroot_spawn_egg", ModEntities.ROAMROOT);
    public static final Item WOBBLE_SPAWN_EGG = registerSpawnEgg("wobble_spawn_egg", ModEntities.WOBBLE);
    public static final Item HARMONIZER_SPAWN_EGG = registerSpawnEgg("harmonizer_spawn_egg", ModEntities.HARMONIZER);
    public static final Item MONARCH_SPAWN_EGG = registerSpawnEgg("monarch_spawn_egg", ModEntities.MONARCH);
    public static final Item SCULK_MONSTROSITY_SPAWN_EGG = registerSpawnEgg("sculk_monstrosity_spawn_egg", ModEntities.SCULK_MONSTROSITY);

    public static final Item[] SPAWN_EGGS = new Item[] {
            BLUB_SPAWN_EGG, ECHO_GOLEM_SPAWN_EGG, SINGER_SPAWN_EGG, NUZZLE_SPAWN_EGG, LOOTKIN_SPAWN_EGG,
            FUSEFLY_SPAWN_EGG, DARTBACK_SPAWN_EGG, HURLER_SPAWN_EGG, POLLINATOR_SPAWN_EGG, NESTER_SPAWN_EGG,
            SEEDLING_SPAWN_EGG, SPROUT_SPAWN_EGG, STALKER_SPAWN_EGG, SCAVENGER_SPAWN_EGG, SLABBER_SPAWN_EGG,
            PRICKLE_SPAWN_EGG, SENTINEL_SPAWN_EGG, TUNER_SPAWN_EGG, BLOOMBUD_SPAWN_EGG, ROAMROOT_SPAWN_EGG,
            WOBBLE_SPAWN_EGG, HARMONIZER_SPAWN_EGG, MONARCH_SPAWN_EGG, SCULK_MONSTROSITY_SPAWN_EGG
    };

    // Creative Tabs
    public static final ResourceKey<CreativeModeTab> BLOCKS_TAB_KEY = ResourceKey.create(
            BuiltInRegistries.CREATIVE_MODE_TAB.key(),
            PySift.id("pysift_blocks")
    );

    public static final CreativeModeTab BLOCKS_TAB = FabricCreativeModeTab.builder()
            .icon(() -> new ItemStack(ModBlocks.ALL_BLOCKS.isEmpty() ? net.minecraft.world.item.Items.STONE : ModBlocks.ALL_BLOCKS.get(0)))
            .title(Component.translatable("itemGroup.pysift.pysift_blocks"))
            .displayItems((params, output) -> {
                for (net.minecraft.world.level.block.Block block : ModBlocks.ALL_BLOCKS) {
                    output.accept(block);
                    output.acceptAll(ModBlocks.stateVariantStacks(block));
                }
            })
            .build();

    public static final ResourceKey<CreativeModeTab> ITEMS_TAB_KEY = ResourceKey.create(
            BuiltInRegistries.CREATIVE_MODE_TAB.key(),
            PySift.id("pysift_items")
    );

    public static final CreativeModeTab ITEMS_TAB = FabricCreativeModeTab.builder()
            .icon(() -> new ItemStack(SIFTITE_INGOT))
            .title(Component.translatable("itemGroup.pysift.pysift_items"))
            .displayItems((params, output) -> {
                // Materials
                output.accept(CHAROITE);
                output.accept(SIFTITE_INGOT);
                // Spawn Eggs
                for (Item egg : SPAWN_EGGS) {
                    output.accept(egg);
                }
            })
            .build();

    public static Item registerItem(String name, Function<Item.Properties, Item> itemFactory) {
        ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Item item = itemFactory.apply(new Item.Properties().setId(key));
        return Registry.register(BuiltInRegistries.ITEM, key, item);
    }

    public static Item registerSpawnEgg(String name, EntityType<? extends Mob> entityType) {
        ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Item item = new SpawnEggItem(new Item.Properties().spawnEgg(entityType).setId(key));
        return Registry.register(BuiltInRegistries.ITEM, key, item);
    }

    public static void registerModItems() {
        PySift.LOGGER.info("Registering Items and Creative Tabs for {}", PySift.MOD_ID);
        Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, BLOCKS_TAB_KEY, BLOCKS_TAB);
        Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, ITEMS_TAB_KEY, ITEMS_TAB);
    }
}
