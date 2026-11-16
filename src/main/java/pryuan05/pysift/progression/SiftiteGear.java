package pryuan05.pysift.progression;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;
import pryuan05.pysift.PySift;

import java.util.Map;

/**
 * 隙浮金工具與盔甲：強度介於鐵與鑽石之間（鐵 250 耐久／鑽石 1561；盔甲鐵 15 點／鑽石 20 點）。
 * <ul>
 *   <li>工具：耐久 800、挖掘速度 7、攻擊 +2.5、附魔性 16，可挖鑽石等級以下的方塊（與鐵相同的 incorrect 標籤）。</li>
 *   <li>盔甲：2 / 7 / 5 / 2 共 16 點、韌性 1、附魔性 15。</li>
 *   <li>套裝效果（穿滿四件）：碰到靈液時血量只被抽到 0.5 倍，而不是 0.2 倍（{@link SoulWard#drainRatio}）。</li>
 * </ul>
 * 修理材料：隙浮金錠（#pysift:siftite_tool_materials / #pysift:repairs_siftite_armor）。
 */
public final class SiftiteGear {
    public static final TagKey<Item> TOOL_MATERIALS = TagKey.create(Registries.ITEM, PySift.id("siftite_tool_materials"));
    public static final TagKey<Item> REPAIRS_ARMOR = TagKey.create(Registries.ITEM, PySift.id("repairs_siftite_armor"));
    public static final ResourceKey<EquipmentAsset> ASSET = ResourceKey.create(EquipmentAssets.ROOT_ID, PySift.id("siftite"));

    public static final ToolMaterial TOOL = new ToolMaterial(BlockTags.INCORRECT_FOR_IRON_TOOL, 800, 7.0f, 2.5f, 16, TOOL_MATERIALS);
    public static final ArmorMaterial ARMOR = new ArmorMaterial(25, Map.of(
            ArmorType.HELMET, 2, ArmorType.CHESTPLATE, 7, ArmorType.LEGGINGS, 5, ArmorType.BOOTS, 2, ArmorType.BODY, 7),
            15, SoundEvents.ARMOR_EQUIP_IRON, 1.0f, 0.0f, REPAIRS_ARMOR, ASSET);

    public static final Item SWORD = ModProgression.registerItem("siftite_sword", Item::new, new Item.Properties().sword(TOOL, 3.0f, -2.4f));
    public static final Item PICKAXE = ModProgression.registerItem("siftite_pickaxe", Item::new, new Item.Properties().pickaxe(TOOL, 1.0f, -2.8f));
    public static final Item AXE = ModProgression.registerItem("siftite_axe", Item::new, new Item.Properties().axe(TOOL, 6.0f, -3.05f));
    public static final Item SHOVEL = ModProgression.registerItem("siftite_shovel", Item::new, new Item.Properties().shovel(TOOL, 1.5f, -3.0f));
    public static final Item HOE = ModProgression.registerItem("siftite_hoe", Item::new, new Item.Properties().hoe(TOOL, -2.5f, -0.5f));

    public static final Item HELMET = ModProgression.registerItem("siftite_helmet", Item::new, new Item.Properties().humanoidArmor(ARMOR, ArmorType.HELMET));
    public static final Item CHESTPLATE = ModProgression.registerItem("siftite_chestplate", Item::new, new Item.Properties().humanoidArmor(ARMOR, ArmorType.CHESTPLATE));
    public static final Item LEGGINGS = ModProgression.registerItem("siftite_leggings", Item::new, new Item.Properties().humanoidArmor(ARMOR, ArmorType.LEGGINGS));
    public static final Item BOOTS = ModProgression.registerItem("siftite_boots", Item::new, new Item.Properties().humanoidArmor(ARMOR, ArmorType.BOOTS));

    private SiftiteGear() {
    }

    /** 四件隙浮金盔甲都穿在身上。 */
    public static boolean wearsFullSet(Player player) {
        return player.getItemBySlot(EquipmentSlot.HEAD).is(HELMET) && player.getItemBySlot(EquipmentSlot.CHEST).is(CHESTPLATE)
                && player.getItemBySlot(EquipmentSlot.LEGS).is(LEGGINGS) && player.getItemBySlot(EquipmentSlot.FEET).is(BOOTS);
    }

    /** 觸發類別載入以完成註冊（由 ModProgression.register 呼叫）。 */
    static void load() {
    }
}
