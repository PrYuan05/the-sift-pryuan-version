package pryuan05.pysift.item;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import pryuan05.pysift.TheSiftPrYuanSVersion;

import java.util.function.Function;

public class ModItems {
    // Creative Mode Tab Key
    public static final ResourceKey<CreativeModeTab> SIFT_TAB_KEY = ResourceKey.create(
            BuiltInRegistries.CREATIVE_MODE_TAB.key(),
            TheSiftPrYuanSVersion.id("pysift")
    );

    // 24 Mod Items
    public static final Item BLUB = registerItem("blub", Item::new);
    public static final Item ECHO_GOLEM = registerItem("echo_golem", Item::new);
    public static final Item SINGER = registerItem("singer", Item::new);
    public static final Item HARMONIZER_BODY = registerItem("harmonizer_body", Item::new);
    public static final Item HARMONIZER_HEAD = registerItem("harmonizer_head", Item::new);
    public static final Item MONARCH_BODY = registerItem("monarch_body", Item::new);
    public static final Item MONARCH_HEAD = registerItem("monarch_head", Item::new);
    public static final Item NESTER = registerItem("nester", Item::new);
    public static final Item SEEDLING = registerItem("seedling", Item::new);
    public static final Item SENTINEL = registerItem("sentinel", Item::new);
    public static final Item SPROUT = registerItem("sprout", Item::new);
    public static final Item STALKER = registerItem("stalker", Item::new);
    public static final Item SCAVENGER = registerItem("scavenger", Item::new);
    public static final Item FUSEFLY = registerItem("fusefly", Item::new);
    public static final Item DARTBACK = registerItem("dartback", Item::new);
    public static final Item HURLER = registerItem("hurler", Item::new);
    public static final Item LOOTKIN = registerItem("lootkin", Item::new);
    public static final Item NUZZLE = registerItem("nuzzle", Item::new);
    public static final Item PRICKLE = registerItem("prickle", Item::new);
    public static final Item ROAMROOT = registerItem("roamroot", Item::new);
    public static final Item SLABBER = registerItem("slabber", Item::new);
    public static final Item TUNER = registerItem("tuner", Item::new);
    public static final Item WOBBLE = registerItem("wobble", Item::new);
    public static final Item BLOOMBUD = registerItem("bloombud", Item::new);

    public static final Item[] ALL_ITEMS = new Item[] {
            BLUB,
            ECHO_GOLEM,
            SINGER,
            HARMONIZER_BODY,
            HARMONIZER_HEAD,
            MONARCH_BODY,
            MONARCH_HEAD,
            NESTER,
            SEEDLING,
            SENTINEL,
            SPROUT,
            STALKER,
            SCAVENGER,
            FUSEFLY,
            DARTBACK,
            HURLER,
            LOOTKIN,
            NUZZLE,
            PRICKLE,
            ROAMROOT,
            SLABBER,
            TUNER,
            WOBBLE,
            BLOOMBUD
    };

    // Dedicated Creative Mode Tab for The Sift
    public static final CreativeModeTab SIFT_TAB = FabricCreativeModeTab.builder()
            .icon(() -> new ItemStack(BLUB))
            .title(Component.translatable("itemGroup.the_sift"))
            .displayItems((params, output) -> {
                for (Item item : ALL_ITEMS) {
                    output.accept(item);
                }
            })
            .build();

    public static Item registerItem(String name, Function<Item.Properties, Item> itemFactory) {
        ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, TheSiftPrYuanSVersion.id(name));
        Item item = itemFactory.apply(new Item.Properties().setId(key));
        return Registry.register(BuiltInRegistries.ITEM, key, item);
    }

    public static Item registerItem(String name) {
        return registerItem(name, Item::new);
    }

    public static void registerModItems() {
        TheSiftPrYuanSVersion.LOGGER.info("Registering Mod Items and Creative Tab for {}", TheSiftPrYuanSVersion.MOD_ID);
        Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, SIFT_TAB_KEY, SIFT_TAB);
    }
}
