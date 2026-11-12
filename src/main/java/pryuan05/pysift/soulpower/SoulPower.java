package pryuan05.pysift.soulpower;

import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.flag.FeatureFlags;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import pryuan05.pysift.PySift;
import pryuan05.pysift.item.ModItems;
import pryuan05.pysift.item.SiftCreativeTabs;
import pryuan05.pysift.soulpower.kinetic.KineticAddon;
import pryuan05.pysift.soulpower.kinetic.SoulCogBlock;
import pryuan05.pysift.soulpower.kinetic.SoulGearboxBlock;
import pryuan05.pysift.soulpower.kinetic.SoulHandCrankBlock;
import pryuan05.pysift.soulpower.kinetic.SoulShaftBlock;
import pryuan05.pysift.soulpower.kinetic.SoulShiftBlock;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

/**
 * 靈魂動力：以「靈壓（SP）」計的轉動動力（Create 式），靈液引擎產生，傳動軸、齒輪（可以變速、反轉）或靈魂振波傳送，
 * 靈魂研磨機等機器使用，靈壓計讀出負載。
 * 迴路的計算見 {@link SoulCircuit}；資源由 tools/progression/build_soul_power.py 產生。
 */
public final class SoulPower {
    /** 所有靈魂動力方塊（創造模式分頁、CreativeLayout 用）。 */
    public static final List<Block> BLOCKS = new ArrayList<>();

    public static final Block SPIRIT_ENGINE = register("spirit_engine", SpiritEngineBlock::new, 3.5f);
    /** 靈魂導線：靈魂紅石的線（{@link SoulConduitBlock}）。 */
    public static final Block SOUL_CONDUIT = registerConduit("soul_conduit");
    /** 串在導線上的元件與靈魂音符盒（靈魂紅石第二階段）。 */
    public static final Block SOUL_REPEATER = register("soul_repeater", SoulRepeaterBlock::new, 2.0f);
    public static final Block SOUL_FILTER = register("soul_filter", SoulFilterBlock::new, 2.0f);
    public static final Block SOUL_NOTE_BLOCK = register("soul_note_block", SoulNoteBlock::new, 1.5f);
    // 機械擴充（{@link KineticAddon}）：沒啟用時這七個是 null，完全不註冊
    public static final Block SOUL_SHAFT = kinetic("soul_shaft", SoulShaftBlock::new, 2.0f);
    public static final Block SOUL_COGWHEEL = kinetic("soul_cogwheel", p -> new SoulCogBlock(false, p), 2.0f);
    public static final Block LARGE_SOUL_COGWHEEL = kinetic("large_soul_cogwheel", p -> new SoulCogBlock(true, p), 2.0f);
    public static final Block SOUL_GAUGE = register("soul_gauge", SoulGaugeBlock::new, 2.5f);
    public static final Block SOUL_GEARBOX = kinetic("soul_gearbox", SoulGearboxBlock::new, 2.5f);
    public static final Block SOUL_GRINDER = register("soul_grinder", SoulGrinderBlock::new, 3.5f);
    public static final Block SOUL_SIFTER = register("soul_sifter", SoulSifterBlock::new, 3.0f);
    public static final Block CHAROITE_BEAM_EMITTER = register("charoite_beam_emitter", p -> new CharoiteBeamBlock(true, p), 3.0f);
    public static final Block CHAROITE_BEAM_RECEIVER = register("charoite_beam_receiver", p -> new CharoiteBeamBlock(false, p), 3.0f);
    public static final Block CHAROITE_PRISM = register("charoite_prism", CharoitePrismBlock::new, 1.5f);
    public static final Block SPIRIT_PUMP = register("spirit_pump", SpiritPumpBlock::new, 3.0f);
    public static final Block SPIRIT_PIPE = register("spirit_pipe", SpiritPipeBlock::new, 1.5f);
    public static final Block SOUL_HAND_CRANK = kinetic("soul_hand_crank", SoulHandCrankBlock::new, 1.5f);
    public static final Block SOUL_CLUTCH = kinetic("soul_clutch", p -> new SoulShiftBlock(false, p), 2.5f);
    public static final Block SOUL_GEARSHIFT = kinetic("soul_gearshift", p -> new SoulShiftBlock(true, p), 2.5f);
    public static final Block SOUL_FAN = register("soul_fan", SoulFanBlock::new, 2.5f);
    public static final Block SOUL_DRILL = register("soul_drill", SoulDrillBlock::new, 3.0f);
    public static final Block RESONANCE_CORE = register("resonance_core", ResonanceCoreBlock::new, 3.5f);
    public static final Block RESONANCE_PEDESTAL = register("resonance_pedestal", ResonancePedestalBlock::new, 2.0f);
    /** 靈脈石：發光的裝飾石頭（原本是靈脈節點之間長出來的；節點已於 2026-11-13 移除）。 */
    public static final Block SOUL_VEINED_STONE = registerStone("soul_veined_stone");

    /** 傳動軸與齒輪：只記轉速，讓用戶端畫出轉動。 */
    /** 隙浮金齒輪：靈魂動力機器會動的零件（4 隙浮金錠＋靈魂精華 → 2 個），和齒輪、飛輪一樣是隙浮金做的。 */
    private static final ResourceKey<Item> SIFTITE_GEAR_KEY = ResourceKey.create(Registries.ITEM, PySift.id("siftite_gear"));
    public static final Item SIFTITE_GEAR = Registry.register(BuiltInRegistries.ITEM, SIFTITE_GEAR_KEY,
            new Item(new Item.Properties().setId(SIFTITE_GEAR_KEY)));

    public static final BlockEntityType<KineticBlockEntity> SOUL_KINETIC_ENTITY = !KineticAddon.enabled() ? null : Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("soul_kinetic"),
            FabricBlockEntityTypeBuilder.<KineticBlockEntity>create(KineticBlockEntity::new, SOUL_SHAFT, SOUL_COGWHEEL, LARGE_SOUL_COGWHEEL,
                    SOUL_CLUTCH, SOUL_GEARSHIFT, SOUL_GEARBOX).build());
    public static final BlockEntityType<SoulConduitBlock.Entity> SOUL_CONDUIT_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("soul_conduit"),
            FabricBlockEntityTypeBuilder.create(SoulConduitBlock.Entity::new, SOUL_CONDUIT).build());
    public static final BlockEntityType<SoulGaugeBlock.Entity> SOUL_GAUGE_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("soul_gauge"),
            FabricBlockEntityTypeBuilder.create(SoulGaugeBlock.Entity::new, SOUL_GAUGE).build());
    public static final BlockEntityType<SpiritEngineBlockEntity> SPIRIT_ENGINE_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("spirit_engine"),
            FabricBlockEntityTypeBuilder.create(SpiritEngineBlockEntity::new, SPIRIT_ENGINE).build());
    public static final BlockEntityType<SoulGrinderBlockEntity> SOUL_GRINDER_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("soul_grinder"),
            FabricBlockEntityTypeBuilder.create(SoulGrinderBlockEntity::new, SOUL_GRINDER).build());

    public static final BlockEntityType<SoulSifterBlockEntity> SOUL_SIFTER_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("soul_sifter"),
            FabricBlockEntityTypeBuilder.create(SoulSifterBlockEntity::new, SOUL_SIFTER).build());

    public static final BlockEntityType<CharoiteBeamBlockEntity> CHAROITE_BEAM_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("charoite_beam"),
            FabricBlockEntityTypeBuilder.create(CharoiteBeamBlockEntity::new, CHAROITE_BEAM_EMITTER, CHAROITE_BEAM_RECEIVER).build());

    public static final BlockEntityType<SpiritPumpBlockEntity> SPIRIT_PUMP_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("spirit_pump"),
            FabricBlockEntityTypeBuilder.create(SpiritPumpBlockEntity::new, SPIRIT_PUMP).build());

    public static final BlockEntityType<SoulHandCrankBlock.Entity> SOUL_HAND_CRANK_ENTITY = !KineticAddon.enabled() ? null : Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("soul_hand_crank"),
            FabricBlockEntityTypeBuilder.create(SoulHandCrankBlock.Entity::new, SOUL_HAND_CRANK).build());
    public static final BlockEntityType<SoulFanBlockEntity> SOUL_FAN_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("soul_fan"),
            FabricBlockEntityTypeBuilder.create(SoulFanBlockEntity::new, SOUL_FAN).build());

    public static final BlockEntityType<ResonanceCoreBlockEntity> RESONANCE_CORE_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("resonance_core"),
            FabricBlockEntityTypeBuilder.create(ResonanceCoreBlockEntity::new, RESONANCE_CORE).build());
    public static final BlockEntityType<ResonancePedestalBlock.Entity> RESONANCE_PEDESTAL_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("resonance_pedestal"),
            FabricBlockEntityTypeBuilder.create(ResonancePedestalBlock.Entity::new, RESONANCE_PEDESTAL).build());

    public static final BlockEntityType<SoulDrillBlock.Entity> SOUL_DRILL_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("soul_drill"),
            FabricBlockEntityTypeBuilder.create(SoulDrillBlock.Entity::new, SOUL_DRILL).build());

    public static final MenuType<SpiritEngineMenu> SPIRIT_ENGINE_MENU = Registry.register(BuiltInRegistries.MENU,
            PySift.id("spirit_engine"), new MenuType<>(SpiritEngineMenu::new, FeatureFlags.VANILLA_SET));
    public static final MenuType<SoulGrinderMenu> SOUL_GRINDER_MENU = Registry.register(BuiltInRegistries.MENU,
            PySift.id("soul_grinder"), new MenuType<>(SoulGrinderMenu::new, FeatureFlags.VANILLA_SET));

    public static final RecipeType<SoulGrindingRecipe> SOUL_GRINDING = Registry.register(BuiltInRegistries.RECIPE_TYPE,
            PySift.id("soul_grinding"), new RecipeType<>() {
                @Override
                public String toString() {
                    return "pysift:soul_grinding";
                }
            });

    public static final RecipeType<SoulSiftingRecipe> SOUL_SIFTING = Registry.register(BuiltInRegistries.RECIPE_TYPE,
            PySift.id("soul_sifting"), new RecipeType<>() {
                @Override
                public String toString() {
                    return "pysift:soul_sifting";
                }
            });

    public static final RecipeType<SoulHauntingRecipe> SOUL_HAUNTING = Registry.register(BuiltInRegistries.RECIPE_TYPE,
            PySift.id("soul_haunting"), new RecipeType<>() {
                @Override
                public String toString() {
                    return "pysift:soul_haunting";
                }
            });

    private SoulPower() {
    }

    private static Block register(String name, Function<BlockBehaviour.Properties, Block> factory, float strength) {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        Block block = Registry.register(BuiltInRegistries.BLOCK, blockKey, factory.apply(BlockBehaviour.Properties.of()
                .mapColor(MapColor.COLOR_CYAN).strength(strength).requiresCorrectToolForDrops()
                .sound(SoundType.POLISHED_DEEPSLATE).noOcclusion().setId(blockKey)));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().useBlockDescriptionPrefix().setId(itemKey)));
        BLOCKS.add(block);
        return block;
    }

    /** 機械擴充的方塊：沒啟用就不註冊（回傳 null）。 */
    private static Block kinetic(String name, Function<BlockBehaviour.Properties, Block> factory, float strength) {
        return KineticAddon.enabled() ? register(name, factory, strength) : null;
    }

    /** 靈魂導線：徒手就拆得掉；有靈魂訊號時發光最亮，只有原版訊號時微亮。 */
    private static Block registerConduit(String name) {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        Block block = Registry.register(BuiltInRegistries.BLOCK, blockKey, new SoulConduitBlock(BlockBehaviour.Properties.of()
                .mapColor(MapColor.COLOR_RED).strength(0.4f).sound(SoundType.SCULK_VEIN).noOcclusion()
                .lightLevel(st -> switch (st.getValue(SoulConduitBlock.LOOK)) {
                    case SOUL -> 7;
                    case PLAIN -> 3;
                    case OFF -> 0;
                })
                .setId(blockKey)));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().useBlockDescriptionPrefix().setId(itemKey)));
        BLOCKS.add(block);
        return block;
    }

    private static Block registerStone(String name) {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        Block block = Registry.register(BuiltInRegistries.BLOCK, blockKey, new Block(BlockBehaviour.Properties.of()
                .mapColor(MapColor.DEEPSLATE).strength(3.0f, 6.0f).requiresCorrectToolForDrops().lightLevel(s -> 5)
                .sound(SoundType.DEEPSLATE).setId(blockKey)));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().useBlockDescriptionPrefix().setId(itemKey)));
        BLOCKS.add(block);
        return block;
    }

    public static void register() {
        SoulParts.init();
        Registry.register(BuiltInRegistries.RECIPE_SERIALIZER, PySift.id("soul_grinding"), SoulGrindingRecipe.SERIALIZER);
        Registry.register(BuiltInRegistries.RECIPE_SERIALIZER, PySift.id("soul_sifting"), SoulSiftingRecipe.SERIALIZER);
        Registry.register(BuiltInRegistries.RECIPE_SERIALIZER, PySift.id("soul_haunting"), SoulHauntingRecipe.SERIALIZER);
        SiftCreativeTabs.source(ModItems.BLOCKS_TAB_KEY, output -> BLOCKS.forEach(output::accept));
        SiftCreativeTabs.source(ModItems.ITEMS_TAB_KEY, output -> output.accept(SIFTITE_GEAR));
        PySift.LOGGER.info("Registered {} soul power blocks", BLOCKS.size());
    }
}
