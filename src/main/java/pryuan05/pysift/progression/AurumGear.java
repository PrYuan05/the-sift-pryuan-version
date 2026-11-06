package pryuan05.pysift.progression;

import net.minecraft.core.registries.Registries;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.item.component.Consumables;
import net.minecraft.world.item.consume_effects.ApplyStatusEffectsConsumeEffect;
import pryuan05.pysift.PySift;

import java.util.List;

/**
 * 金岩（Aurum）：搖籃曲山丘峽谷河床的金岩礦（氧化黃鐵礦）→ 粗金岩 → 熔煉成金岩錠，9 顆金岩粒 = 1 錠。
 * <ul>
 *   <li>工具：耐久 450、挖掘速度 10、攻擊 +2、附魔性 22（和金一樣好附魔，但耐用得多），可挖鐵等級的方塊。</li>
 *   <li>金岩蘋果（蘋果 + 8 金岩錠）：一律可吃；回復 II 5 秒、吸收 I 2 分鐘、靈魂守護 1 分鐘（不會被靈魂剝奪）。</li>
 *   <li>金岩胡蘿蔔（胡蘿蔔 + 8 金岩粒）：飽和度高；夜視與回音視界各 30 秒（32 格內的敵人發光）。</li>
 *   <li>金岩莓果（甜莓 + 4 金岩粒）：吃得快；速度 I 與挖掘加速 I 各 45 秒。</li>
 * </ul>
 * 資源（貼圖、模型、配方、掉落表、標籤、語系）由 tools/progression/build_aurum.py 產生。
 */
public final class AurumGear {
    public static final TagKey<Item> TOOL_MATERIALS = TagKey.create(Registries.ITEM, PySift.id("aurum_tool_materials"));

    public static final ToolMaterial TOOL = new ToolMaterial(BlockTags.INCORRECT_FOR_IRON_TOOL, 450, 10.0f, 2.0f, 22, TOOL_MATERIALS);

    // ===== 材料 =====
    public static final Item RAW_AURUM = ModProgression.registerItem("raw_aurum", Item::new);
    public static final Item AURUM_INGOT = ModProgression.registerItem("aurum_ingot", Item::new);
    public static final Item AURUM_NUGGET = ModProgression.registerItem("aurum_nugget", Item::new);

    // ===== 工具 =====
    public static final Item SWORD = ModProgression.registerItem("aurum_sword", Item::new, new Item.Properties().sword(TOOL, 3.0f, -2.4f));
    public static final Item PICKAXE = ModProgression.registerItem("aurum_pickaxe", Item::new, new Item.Properties().pickaxe(TOOL, 1.0f, -2.8f));
    public static final Item AXE = ModProgression.registerItem("aurum_axe", Item::new, new Item.Properties().axe(TOOL, 6.0f, -3.1f));
    public static final Item SHOVEL = ModProgression.registerItem("aurum_shovel", Item::new, new Item.Properties().shovel(TOOL, 1.5f, -3.0f));
    public static final Item HOE = ModProgression.registerItem("aurum_hoe", Item::new, new Item.Properties().hoe(TOOL, -2.0f, -1.0f));

    // ===== 食物 =====
    public static final Item AURUM_APPLE = ModProgression.registerItem("aurum_apple", Item::new,
            new Item.Properties().rarity(Rarity.RARE).food(new FoodProperties(4, 9.6f, true), Consumables.defaultFood().onConsume(
                    new ApplyStatusEffectsConsumeEffect(List.of(
                            new MobEffectInstance(MobEffects.REGENERATION, 100, 1),
                            new MobEffectInstance(MobEffects.ABSORPTION, 2400, 0),
                            new MobEffectInstance(SiftFarming.SOUL_WARD, 1200, 0)))).build()));
    public static final Item AURUM_CARROT = ModProgression.registerItem("aurum_carrot", Item::new,
            new Item.Properties().rarity(Rarity.UNCOMMON).food(new FoodProperties(6, 14.4f, false), Consumables.defaultFood().onConsume(
                    new ApplyStatusEffectsConsumeEffect(List.of(
                            new MobEffectInstance(MobEffects.NIGHT_VISION, 600, 0),
                            new MobEffectInstance(SiftFarming.ECHO_SIGHT, 600, 0)))).build()));
    public static final Item AURUM_BERRIES = ModProgression.registerItem("aurum_berries", Item::new,
            new Item.Properties().rarity(Rarity.UNCOMMON).food(new FoodProperties(4, 1.2f, false), Consumables.defaultFood()
                    .consumeSeconds(0.8f).onConsume(new ApplyStatusEffectsConsumeEffect(List.of(
                            new MobEffectInstance(MobEffects.SPEED, 900, 0),
                            new MobEffectInstance(MobEffects.HASTE, 900, 0)))).build()));

    private AurumGear() {
    }

    /** 觸發類別載入以完成註冊（由 ModProgression.register 呼叫）。 */
    static void load() {
    }
}
