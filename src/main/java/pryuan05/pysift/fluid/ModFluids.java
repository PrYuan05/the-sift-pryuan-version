package pryuan05.pysift.fluid;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BucketItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.DispenserBlock;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.FlowingFluid;
import pryuan05.pysift.PySift;

public final class ModFluids {
    public static final FlowingFluid SPIRIT_LIQUID =
            Registry.register(BuiltInRegistries.FLUID, PySift.id("spirit_liquid"), new SpiritFluid.Source());
    public static final FlowingFluid FLOWING_SPIRIT_LIQUID =
            Registry.register(BuiltInRegistries.FLUID, PySift.id("flowing_spirit_liquid"), new SpiritFluid.Flowing());

    /** 靈液方塊：亮度 10，其餘屬性與水相同。 */
    public static final Block SPIRIT_LIQUID_BLOCK = registerBlock("spirit_liquid",
            BlockBehaviour.Properties.ofFullCopy(Blocks.WATER).lightLevel(state -> 10));

    public static final Item SPIRIT_LIQUID_BUCKET = registerBucket("spirit_liquid_bucket");

    private ModFluids() {
    }

    private static Block registerBlock(String name, BlockBehaviour.Properties properties) {
        ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        return Registry.register(BuiltInRegistries.BLOCK, key, new LiquidBlock(SPIRIT_LIQUID, properties.setId(key)));
    }

    private static Item registerBucket(String name) {
        ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, PySift.id(name));
        return Registry.register(BuiltInRegistries.ITEM, key, new BucketItem(SPIRIT_LIQUID,
                new Item.Properties().craftRemainder(Items.BUCKET).stacksTo(1).setId(key)));
    }

    public static void registerModFluids() {
        PySift.LOGGER.info("Registering Fluids for {}", PySift.MOD_ID);
        // 發射器：和水桶同一套行為（倒出、倒進可含水／含靈液的方塊）；不註冊的話發射器只會把桶子當物品吐出去
        DispenserBlock.registerBehavior(SPIRIT_LIQUID_BUCKET, DispenserBlock.DISPENSER_REGISTRY.get(Items.WATER_BUCKET));
    }
}
