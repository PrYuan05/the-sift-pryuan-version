package pryuan05.pysift.progression;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.tag.convention.v2.ConventionalBlockTags;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;
import net.minecraft.world.level.block.Block;
import pryuan05.pysift.PySift;
import pryuan05.pysift.fluid.ModFluids;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * 靈髓（Soulite）：比獄髓更強的材料，結合三隻 Boss 的能力。
 * <ul>
 *   <li>靈髓錠 = 獄髓錠 + 共鳴音晶 + 君王羽刃 + 幽匿鱗片 + 4 紫龍晶；鍛造台用靈髓升級模板 + 靈髓錠把獄髓裝備升級（保留附魔）。</li>
 *   <li>工具：耐久 2600、速度 10、攻擊 +5、附魔性 18；盔甲 4/9/7/4、韌性 4、擊退抗性 0.15；不會被岩漿燒毀。</li>
 *   <li>靈髓劍：每第 3 下命中放出小音波，連鎖 2 個敵人並附加靈魂剝奪（調和者）。</li>
 *   <li>靈髓斧：蓄滿力的攻擊在目標腳下長出幽匿藤蔓，2 秒後爆炸（幽匿巨怪）。</li>
 *   <li>靈髓鎬／鏟／鋤：挖到礦石時 15% 額外掉落靈魂精華。</li>
 *   <li>頭盔：16 格內的敵人發光（調和者）。胸甲：血量低於 30% 時留下分身並獲得速度 II，冷卻 60 秒（君王）。
 *       護腿：擊退抗性 +0.35，近戰攻擊你的敵人受到 3 點幽匿荊棘傷害（幽匿巨怪）。靴子：免疫摔落傷害、可在靈液上行走（君王）。</li>
 *   <li>四件套裝：自己免疫靈魂剝奪（{@link SoulWard#isImmune}）。</li>
 * </ul>
 */
public final class SouliteGear {
    public static final TagKey<Item> TOOL_MATERIALS = TagKey.create(Registries.ITEM, PySift.id("soulite_tool_materials"));
    public static final TagKey<Item> REPAIRS_ARMOR = TagKey.create(Registries.ITEM, PySift.id("repairs_soulite_armor"));
    public static final ResourceKey<EquipmentAsset> ASSET = ResourceKey.create(EquipmentAssets.ROOT_ID, PySift.id("soulite"));

    public static final ToolMaterial TOOL = new ToolMaterial(BlockTags.INCORRECT_FOR_NETHERITE_TOOL, 2600, 10.0f, 5.0f, 18, TOOL_MATERIALS);
    public static final ArmorMaterial ARMOR = new ArmorMaterial(42, Map.of(
            ArmorType.HELMET, 4, ArmorType.CHESTPLATE, 9, ArmorType.LEGGINGS, 7, ArmorType.BOOTS, 4, ArmorType.BODY, 12),
            18, SoundEvents.ARMOR_EQUIP_NETHERITE, 4.0f, 0.15f, REPAIRS_ARMOR, ASSET);

    public static final Item INGOT = ModProgression.registerItem("soulite_ingot", Item::new,
            new Item.Properties().rarity(Rarity.EPIC).fireResistant());
    public static final Item UPGRADE_TEMPLATE = ModProgression.registerItem("soulite_upgrade_smithing_template",
            p -> new HintItem(p, "tooltip.pysift.soulite_upgrade.0", "tooltip.pysift.soulite_upgrade.1"),
            new Item.Properties().rarity(Rarity.EPIC).fireResistant());

    public static final Item SWORD = ModProgression.registerItem("soulite_sword",
            p -> new HintItem(p, "tooltip.pysift.soulite_sword"), props().sword(TOOL, 3.0f, -2.4f));
    public static final Item AXE = ModProgression.registerItem("soulite_axe",
            p -> new HintItem(p, "tooltip.pysift.soulite_axe"), props().axe(TOOL, 5.0f, -3.0f));
    public static final Item PICKAXE = ModProgression.registerItem("soulite_pickaxe",
            p -> new HintItem(p, "tooltip.pysift.soulite_digger"), props().pickaxe(TOOL, 1.0f, -2.8f));
    public static final Item SHOVEL = ModProgression.registerItem("soulite_shovel",
            p -> new HintItem(p, "tooltip.pysift.soulite_digger"), props().shovel(TOOL, 1.5f, -3.0f));
    public static final Item HOE = ModProgression.registerItem("soulite_hoe",
            p -> new HintItem(p, "tooltip.pysift.soulite_digger"), props().hoe(TOOL, -4.0f, 0.0f));

    public static final Item HELMET = ModProgression.registerItem("soulite_helmet",
            p -> new HintItem(p, "tooltip.pysift.soulite_helmet", "tooltip.pysift.soulite_set"), props().humanoidArmor(ARMOR, ArmorType.HELMET));
    public static final Item CHESTPLATE = ModProgression.registerItem("soulite_chestplate",
            p -> new HintItem(p, "tooltip.pysift.soulite_chestplate", "tooltip.pysift.soulite_set"), props().humanoidArmor(ARMOR, ArmorType.CHESTPLATE));
    public static final Item LEGGINGS = ModProgression.registerItem("soulite_leggings",
            p -> new HintItem(p, "tooltip.pysift.soulite_leggings", "tooltip.pysift.soulite_set"),
            props().humanoidArmor(ARMOR, ArmorType.LEGGINGS).attributes(ARMOR.createAttributes(ArmorType.LEGGINGS).withModifierAdded(
                    Attributes.KNOCKBACK_RESISTANCE, new AttributeModifier(PySift.id("soulite_leggings_knockback"), 0.35,
                            AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.LEGS)));
    public static final Item BOOTS = ModProgression.registerItem("soulite_boots",
            p -> new HintItem(p, "tooltip.pysift.soulite_boots", "tooltip.pysift.soulite_set"), props().humanoidArmor(ARMOR, ArmorType.BOOTS));

    private static final Set<Item> DIGGERS = Set.of(PICKAXE, SHOVEL, HOE);
    private static final int CHEST_COOLDOWN = 1200;
    private static final Map<UUID, Integer> SWORD_HITS = new HashMap<>();
    private static final Map<UUID, Boolean> AXE_FULL_SWING = new HashMap<>();
    private static final Map<UUID, Long> CHEST_READY_AT = new HashMap<>();

    private SouliteGear() {
    }

    private static Item.Properties props() {
        return new Item.Properties().fireResistant();
    }

    private static boolean wears(LivingEntity e, EquipmentSlot slot, Item item) {
        return e.getItemBySlot(slot).is(item);
    }

    public static boolean wearsFullSet(Player player) {
        return wears(player, EquipmentSlot.HEAD, HELMET) && wears(player, EquipmentSlot.CHEST, CHESTPLATE)
                && wears(player, EquipmentSlot.LEGS, LEGGINGS) && wears(player, EquipmentSlot.FEET, BOOTS);
    }

    /**
     * 靈髓靴子：站在靈液表面（SouliteFluidWalkMixin）。只在還沒泡進靈液時生效（靈液在 #water 標籤裡，所以用 isInWater）：
     * 一旦掉進去就和平常一樣游泳、跳躍；蹲下會沉下去。
     */
    public static boolean standsOnLiquid(LivingEntity e) {
        return wears(e, EquipmentSlot.FEET, BOOTS) && !e.isShiftKeyDown() && !e.isInWater();
    }

    public static boolean walksOnSpirit(LivingEntity e, net.minecraft.world.level.material.FluidState fluid) {
        return standsOnLiquid(e) && (fluid.is(ModFluids.SPIRIT_LIQUID) || fluid.is(ModFluids.FLOWING_SPIRIT_LIQUID));
    }

    /** 踩在液體上的碰撞形狀：15/16 格高，比靈液表面（約 0.89 格）高一點，站著時腳不會泡在靈液裡。 */
    public static final net.minecraft.world.phys.shapes.VoxelShape LIQUID_FLOOR = Block.box(0.0, 0.0, 0.0, 16.0, 15.0, 16.0);

    static void load() {
        // 靈髓劍：每第 3 下命中連鎖
        // 靈髓斧：在攻擊前（攻擊冷卻還沒重置時）記下這一下是不是蓄滿力
        AttackEntityCallback.EVENT.register((player, level, hand, entity, hit) -> {
            if (!level.isClientSide() && player.getMainHandItem().is(AXE)) {
                AXE_FULL_SWING.put(player.getUUID(), player.getAttackStrengthScale(0.5f) > 0.9f);
            }
            return InteractionResult.PASS;
        });
        ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, baseDamage, damageTaken, blocked) -> {
            if (!(entity.level() instanceof ServerLevel level) || damageTaken <= 0) {
                return;
            }
            // 武器命中
            if (source.getEntity() instanceof Player player && source.getDirectEntity() == player && entity != player) {
                ItemStack weapon = player.getMainHandItem();
                if (weapon.is(SWORD)) {
                    int hits = SWORD_HITS.merge(player.getUUID(), 1, Integer::sum);
                    if (hits % 3 == 0) {
                        BossWeapons.soulDeprive(entity, player);
                        BossWeapons.chain(level, player, entity, 2, 4.0f);
                        level.sendParticles(ParticleTypes.SONIC_BOOM, entity.getX(), entity.getY(0.5), entity.getZ(), 1, 0, 0, 0, 0);
                    }
                } else if (weapon.is(AXE) && AXE_FULL_SWING.getOrDefault(player.getUUID(), false)) {
                    AXE_FULL_SWING.put(player.getUUID(), false);
                    BossWeapons.plantTendril(level, entity.blockPosition(), player, 40);
                }
            }
            // 靈髓護腿：幽匿荊棘
            if (entity instanceof Player wearer && wears(wearer, EquipmentSlot.LEGS, LEGGINGS)
                    && source.getEntity() instanceof LivingEntity attacker && source.getDirectEntity() == attacker && attacker != wearer) {
                attacker.hurtServer(level, level.damageSources().thorns(wearer), 3.0f);
                level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, attacker.getX(), attacker.getY(0.5), attacker.getZ(), 6, 0.3, 0.3, 0.3, 0.02);
            }
            // 靈髓胸甲：瀕死時留下分身並加速
            if (entity instanceof ServerPlayer wearer && wears(wearer, EquipmentSlot.CHEST, CHESTPLATE)
                    && wearer.getHealth() < wearer.getMaxHealth() * 0.3f && wearer.isAlive()) {
                long now = level.getGameTime();
                if (now >= CHEST_READY_AT.getOrDefault(wearer.getUUID(), 0L)) {
                    CHEST_READY_AT.put(wearer.getUUID(), now + CHEST_COOLDOWN);
                    BossWeapons.spawnDecoy(level, wearer, 200);
                    wearer.addEffect(new MobEffectInstance(MobEffects.SPEED, 100, 1));
                    level.playSound(null, wearer.blockPosition(), SoundEvents.ILLUSIONER_MIRROR_MOVE, SoundSource.PLAYERS, 1.0f, 0.9f);
                }
            }
        });
        // 靈髓靴子：免疫摔落傷害
        ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) ->
                !(source.is(DamageTypeTags.IS_FALL) && wears(entity, EquipmentSlot.FEET, BOOTS)));
        // 靈髓鎬／鏟／鋤：挖礦石時額外掉靈魂精華
        PlayerBlockBreakEvents.AFTER.register((level, player, pos, state, blockEntity) -> {
            if (!level.isClientSide() && DIGGERS.contains(player.getMainHandItem().getItem())
                    && state.is(ConventionalBlockTags.ORES) && level.getRandom().nextFloat() < 0.15f) {
                Block.popResource(level, pos, new ItemStack(ModProgression.SOUL_ESSENCE));
            }
        });
        // 靈髓頭盔：每秒讓 16 格內的敵人發光 1.5 秒
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            if (server.getTickCount() % 20 != 0) {
                return;
            }
            for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                if (wears(player, EquipmentSlot.HEAD, HELMET) && player.level() instanceof ServerLevel level) {
                    for (net.minecraft.world.entity.Mob e : level.getEntitiesOfClass(net.minecraft.world.entity.Mob.class,
                            player.getBoundingBox().inflate(16.0), e -> SiftFarming.isHostile(e, player))) {
                        e.addEffect(new MobEffectInstance(MobEffects.GLOWING, 30, 0, false, false));
                    }
                }
            }
        });
    }
}
