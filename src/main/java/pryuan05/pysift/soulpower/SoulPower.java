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

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

/**
 * 靈魂動力（第一階段）：以「靈壓（SP）」計的轉動動力，靈液引擎產生、傳動軸或靈魂振波傳送、靈魂研磨機使用。
 * 網路的計算見 {@link SoulNetwork}；資源由 tools/progression/build_soul_power.py 產生。
 */
public final class SoulPower {
    /** 所有靈魂動力方塊（創造模式分頁、CreativeLayout 用）。 */
    public static final List<Block> BLOCKS = new ArrayList<>();

    public static final Block SPIRIT_ENGINE = register("spirit_engine", SpiritEngineBlock::new, 3.5f);
    public static final Block SOUL_SHAFT = register("soul_shaft", SoulShaftBlock::new, 2.0f);
    public static final Block SOUL_WAVE_EMITTER = register("soul_wave_emitter", p -> new SoulWaveBlock(true, p), 3.0f);
    public static final Block SOUL_WAVE_RECEIVER = register("soul_wave_receiver", p -> new SoulWaveBlock(false, p), 3.0f);
    public static final Block SOUL_GRINDER = register("soul_grinder", SoulGrinderBlock::new, 3.5f);

    public static final BlockEntityType<SpiritEngineBlockEntity> SPIRIT_ENGINE_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("spirit_engine"),
            FabricBlockEntityTypeBuilder.create(SpiritEngineBlockEntity::new, SPIRIT_ENGINE).build());
    public static final BlockEntityType<SoulWaveBlockEntity> SOUL_WAVE_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("soul_wave"),
            FabricBlockEntityTypeBuilder.create(SoulWaveBlockEntity::new, SOUL_WAVE_EMITTER, SOUL_WAVE_RECEIVER).build());
    public static final BlockEntityType<SoulGrinderBlockEntity> SOUL_GRINDER_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("soul_grinder"),
            FabricBlockEntityTypeBuilder.create(SoulGrinderBlockEntity::new, SOUL_GRINDER).build());

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

    public static void register() {
        Registry.register(BuiltInRegistries.RECIPE_SERIALIZER, PySift.id("soul_grinding"), SoulGrindingRecipe.SERIALIZER);
        SiftCreativeTabs.source(ModItems.BLOCKS_TAB_KEY, output -> BLOCKS.forEach(output::accept));
        PySift.LOGGER.info("Registered {} soul power blocks", BLOCKS.size());
    }
}
