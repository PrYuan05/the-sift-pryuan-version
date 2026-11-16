package pryuan05.pysift.block;

import net.fabricmc.fabric.api.object.builder.v1.block.type.BlockSetTypeBuilder;
import net.fabricmc.fabric.api.object.builder.v1.block.type.WoodTypeBuilder;
import net.fabricmc.fabric.api.registry.FlammableBlockRegistry;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.vehicle.boat.Boat;
import net.minecraft.world.entity.vehicle.boat.ChestBoat;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.BoatItem;
import net.minecraft.world.item.DoubleHighBlockItem;
import net.minecraft.world.item.HangingSignItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.StandingAndWallBlockItem;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ButtonBlock;
import net.minecraft.world.level.block.CeilingHangingSignBlock;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.FenceBlock;
import net.minecraft.world.level.block.FenceGateBlock;
import net.minecraft.world.level.block.PressurePlateBlock;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.ShelfBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.StandingSignBlock;
import net.minecraft.world.level.block.TrapDoorBlock;
import net.minecraft.world.level.block.WallHangingSignBlock;
import net.minecraft.world.level.block.WallSignBlock;
import net.minecraft.world.level.block.entity.BlockEntityTypes;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.BlockSetType;
import net.minecraft.world.level.block.state.properties.WoodType;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.providers.number.ints.ContextIntProvider;
import net.minecraft.world.level.storage.loot.providers.number.ints.ContextIntProviders;
import pryuan05.pysift.PySift;
import pryuan05.pysift.item.ModItems;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

/**
 * 靈魂柳木的全套木製品（原木本身在 {@link ModVegetation#SOUL_WILLOW_LOG}）：
 * 木頭、去皮原木／木頭、木材、半磚、階梯、柵欄、柵欄門、門、活板門、壓力板、按鈕、告示牌、懸掛告示牌、層架、船、運輸船。
 * <ul>
 *   <li>方塊性質一律複製原版橡木的對應方塊；燃料時間沿用原版同類物品（26.3 由 Item.Properties#cookingFuel 指定）。</li>
 *   <li>斧頭去皮在 data/minecraft/block_transformer/axe.json（26.3 改成資料驅動），可燃性用 FlammableBlockRegistry。</li>
 *   <li>資源（模型、配方、掉落、標籤、改色貼圖）由 tools/worldgen/build_soul_willow_wood.py 從原版橡木複製改寫產生。</li>
 *   <li>船的渲染註冊在客戶端 SiftClientVisuals。</li>
 * </ul>
 */
public final class SoulWillowWood {
    public static final List<Item> ITEMS = new ArrayList<>();

    public static final BlockSetType SET_TYPE = BlockSetTypeBuilder.copyOf(BlockSetType.OAK).register(PySift.id("soul_willow"));
    public static final WoodType WOOD_TYPE = WoodTypeBuilder.copyOf(WoodType.OAK).register(PySift.id("soul_willow"), SET_TYPE);

    private static final ResourceKey<ContextIntProvider> FUEL_BLOCK = ContextIntProviders.COOKING_TIME_WOOD_BLOCKS;

    // ===== 引入 ModVegetation 中已註冊的樹幹、樹葉與樹苗，使木材套裝對外引用完整 =====
    public static final Block SOUL_WILLOW_LOG = ModVegetation.SOUL_WILLOW_LOG;
    public static final Block SOUL_WILLOW_LEAVES = ModVegetation.SOUL_WILLOW_LEAVES;
    public static final Block SOUL_WILLOW_LEAVES_PALE = ModVegetation.SOUL_WILLOW_LEAVES_PALE;
    public static final Block GLOWING_SOUL_WILLOW_LEAVES = ModVegetation.GLOWING_SOUL_WILLOW_LEAVES;
    public static final Block SOUL_WILLOW_SAPLING = ModVegetation.SOUL_WILLOW_SAPLING;

    public static final Block SOUL_WILLOW_WOOD = block("soul_willow_wood", RotatedPillarBlock::new, Blocks.OAK_WOOD, FUEL_BLOCK);
    public static final Block STRIPPED_SOUL_WILLOW_LOG = block("stripped_soul_willow_log", RotatedPillarBlock::new, Blocks.STRIPPED_OAK_LOG, FUEL_BLOCK);
    public static final Block STRIPPED_SOUL_WILLOW_WOOD = block("stripped_soul_willow_wood", RotatedPillarBlock::new, Blocks.STRIPPED_OAK_WOOD, FUEL_BLOCK);
    public static final Block SOUL_WILLOW_PLANKS = block("soul_willow_planks", Block::new, Blocks.OAK_PLANKS, FUEL_BLOCK);
    public static final Block SOUL_WILLOW_SLAB = block("soul_willow_slab", SlabBlock::new, Blocks.OAK_SLAB, ContextIntProviders.COOKING_TIME_WOOD_SLABS);
    public static final Block SOUL_WILLOW_STAIRS = block("soul_willow_stairs",
            p -> new StairBlock(SOUL_WILLOW_PLANKS.defaultBlockState(), p), Blocks.OAK_STAIRS, FUEL_BLOCK);
    public static final Block SOUL_WILLOW_FENCE = block("soul_willow_fence", FenceBlock::new, Blocks.OAK_FENCE, FUEL_BLOCK);
    public static final Block SOUL_WILLOW_FENCE_GATE = block("soul_willow_fence_gate",
            p -> new FenceGateBlock(WOOD_TYPE, p), Blocks.OAK_FENCE_GATE, FUEL_BLOCK);
    public static final Block SOUL_WILLOW_TRAPDOOR = block("soul_willow_trapdoor",
            p -> new TrapDoorBlock(SET_TYPE, p), Blocks.OAK_TRAPDOOR, FUEL_BLOCK);
    public static final Block SOUL_WILLOW_PRESSURE_PLATE = block("soul_willow_pressure_plate",
            p -> new PressurePlateBlock(SET_TYPE, p), Blocks.OAK_PRESSURE_PLATE, FUEL_BLOCK);
    public static final Block SOUL_WILLOW_BUTTON = block("soul_willow_button",
            p -> new ButtonBlock(SET_TYPE, 30, p), Blocks.OAK_BUTTON, ContextIntProviders.COOKING_TIME_WOOD_ITEMS_SMALL);
    public static final Block SOUL_WILLOW_SHELF = block("soul_willow_shelf", ShelfBlock::new, Blocks.OAK_SHELF, FUEL_BLOCK);

    public static final Block SOUL_WILLOW_DOOR = blockOnly("soul_willow_door", p -> new DoorBlock(SET_TYPE, p), Blocks.OAK_DOOR);
    public static final Block SOUL_WILLOW_SIGN = blockOnly("soul_willow_sign", p -> new StandingSignBlock(WOOD_TYPE, p), Blocks.OAK_SIGN);
    public static final Block SOUL_WILLOW_WALL_SIGN = blockOnly("soul_willow_wall_sign",
            p -> new WallSignBlock(WOOD_TYPE, wallVariantOf(p, SOUL_WILLOW_SIGN)), Blocks.OAK_WALL_SIGN);
    public static final Block SOUL_WILLOW_HANGING_SIGN = blockOnly("soul_willow_hanging_sign",
            p -> new CeilingHangingSignBlock(WOOD_TYPE, p), Blocks.OAK_HANGING_SIGN);
    public static final Block SOUL_WILLOW_WALL_HANGING_SIGN = blockOnly("soul_willow_wall_hanging_sign",
            p -> new WallHangingSignBlock(WOOD_TYPE, wallVariantOf(p, SOUL_WILLOW_HANGING_SIGN)), Blocks.OAK_WALL_HANGING_SIGN);

    public static final Item SOUL_WILLOW_DOOR_ITEM = item("soul_willow_door",
            p -> new DoubleHighBlockItem(SOUL_WILLOW_DOOR, p), new Item.Properties().cookingFuel(ContextIntProviders.COOKING_TIME_WOOD_ITEMS_LARGE));
    public static final Item SOUL_WILLOW_SIGN_ITEM = item("soul_willow_sign",
            p -> new StandingAndWallBlockItem(SOUL_WILLOW_SIGN, SOUL_WILLOW_WALL_SIGN, Direction.DOWN, p),
            new Item.Properties().cookingFuel(ContextIntProviders.COOKING_TIME_WOOD_ITEMS_LARGE).stacksTo(16).signText());
    public static final Item SOUL_WILLOW_HANGING_SIGN_ITEM = item("soul_willow_hanging_sign",
            p -> new HangingSignItem(SOUL_WILLOW_HANGING_SIGN, SOUL_WILLOW_WALL_HANGING_SIGN, p),
            new Item.Properties().cookingFuel(ContextIntProviders.COOKING_TIME_HANGING_SIGNS).stacksTo(16).signText());

    // ===== 船：每種木頭一個實體類型（26.3 的做法，同原版 EntityTypes.OAK_BOAT） =====
    public static final EntityType<Boat> SOUL_WILLOW_BOAT_TYPE = boatType("soul_willow_boat",
            EntityType.Builder.of((type, level) -> new Boat(type, level, () -> SoulWillowWood.SOUL_WILLOW_BOAT), MobCategory.MISC));
    public static final EntityType<ChestBoat> SOUL_WILLOW_CHEST_BOAT_TYPE = boatType("soul_willow_chest_boat",
            EntityType.Builder.of((type, level) -> new ChestBoat(type, level, () -> SoulWillowWood.SOUL_WILLOW_CHEST_BOAT), MobCategory.MISC));
    public static final Item SOUL_WILLOW_BOAT = item("soul_willow_boat", p -> new BoatItem(SOUL_WILLOW_BOAT_TYPE, p),
            new Item.Properties().cookingFuel(ContextIntProviders.COOKING_TIME_BOATS).stacksTo(1));
    public static final Item SOUL_WILLOW_CHEST_BOAT = item("soul_willow_chest_boat", p -> new BoatItem(SOUL_WILLOW_CHEST_BOAT_TYPE, p),
            new Item.Properties().cookingFuel(ContextIntProviders.COOKING_TIME_BOATS).stacksTo(1));

    private SoulWillowWood() {
    }

    /** 方塊 + 一般方塊物品（含燃料時間）。 */
    private static Block block(String name, Function<BlockBehaviour.Properties, Block> factory, Block copyFrom,
                               ResourceKey<ContextIntProvider> fuel) {
        Block block = blockOnly(name, factory, copyFrom);
        item(name, p -> new BlockItem(block, p), new Item.Properties().cookingFuel(fuel));
        return block;
    }

    /** 只註冊方塊（門、告示牌另外配特殊物品；牆上告示牌沒有物品）。 */
    private static Block blockOnly(String name, Function<BlockBehaviour.Properties, Block> factory, Block copyFrom) {
        ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        Block block = factory.apply(BlockBehaviour.Properties.ofFullCopy(copyFrom).setId(key));
        return Registry.register(BuiltInRegistries.BLOCK, key, block);
    }

    private static Item item(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
        ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Item item = Registry.register(BuiltInRegistries.ITEM, key, factory.apply(properties.setId(key)));
        ITEMS.add(item);
        return item;
    }

    /** 牆上的告示牌：掉落與名稱沿用立式告示牌（同原版 wallVariant）。 */
    private static BlockBehaviour.Properties wallVariantOf(BlockBehaviour.Properties properties, Block standing) {
        java.util.Optional<ResourceKey<LootTable>> loot = standing.getLootTable();
        return properties.overrideLootTable(loot).overrideDescription(standing.getDescriptionId());
    }

    private static <T extends net.minecraft.world.entity.Entity> EntityType<T> boatType(String name, EntityType.Builder<T> builder) {
        ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, PySift.id(name));
        return Registry.register(BuiltInRegistries.ENTITY_TYPE, key,
                builder.noLootTable().sized(1.375F, 0.5625F).eyeHeight(0.5625F).clientTrackingRange(10).build(key));
    }

    public static void register() {
        // 告示牌、懸掛告示牌、層架的方塊實體要認得新方塊（Fabric 注入的 FabricBlockEntityType#addValidBlock）
        BlockEntityTypes.SIGN.addValidBlock(SOUL_WILLOW_SIGN);
        BlockEntityTypes.SIGN.addValidBlock(SOUL_WILLOW_WALL_SIGN);
        BlockEntityTypes.HANGING_SIGN.addValidBlock(SOUL_WILLOW_HANGING_SIGN);
        BlockEntityTypes.HANGING_SIGN.addValidBlock(SOUL_WILLOW_WALL_HANGING_SIGN);
        BlockEntityTypes.SHELF.addValidBlock(SOUL_WILLOW_SHELF);

        // 可燃性：與原版橡木相同（原木類 5/5，木材類 5/20）
        FlammableBlockRegistry flammable = FlammableBlockRegistry.getDefaultInstance();
        for (Block log : List.of(ModVegetation.SOUL_WILLOW_LOG, SOUL_WILLOW_WOOD, STRIPPED_SOUL_WILLOW_LOG, STRIPPED_SOUL_WILLOW_WOOD)) {
            flammable.add(log, 5, 5);
        }
        for (Block wood : List.of(SOUL_WILLOW_PLANKS, SOUL_WILLOW_SLAB, SOUL_WILLOW_STAIRS, SOUL_WILLOW_FENCE, SOUL_WILLOW_FENCE_GATE)) {
            flammable.add(wood, 5, 20);
        }
        flammable.add(SOUL_WILLOW_SHELF, 30, 20);

        pryuan05.pysift.item.SiftCreativeTabs.source(ModItems.BLOCKS_TAB_KEY, output -> ITEMS.forEach(output::accept));
        PySift.LOGGER.info("Registered soul willow wood set ({} items)", ITEMS.size());
    }
}
