package pryuan05.pysift.progression;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Position;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.entity.projectile.arrow.Arrow;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.ArrowItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.Consumables;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.consume_effects.ApplyStatusEffectsConsumeEffect;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import pryuan05.pysift.effect.ModEffects;
import pryuan05.pysift.entity.projectile.HunterJavelinEntity;

import java.util.function.BiFunction;

/**
 * 生物掉落物（v2.2）：每種有血肉的隙浮生物都有自己的食材（生的能煮熟），每種戰鬥型生物都有一樣對應牠技能的材料。
 * 掉落表在 tools/progression/build_progression.py 的 MOB_DROPS；配方、模型、名稱在 tools/progression/build_mob_drops.py。
 * 歌者、迴音傀儡、哀悼者、隙浮守衛是隙浮的人與家人，不掉食材。
 */
public final class MobDrops {
    // ---------------------------------------------------------------- 食物
    /** 布魯布凝膠：可以直接吃，也能做成黏液球。 */
    public static final Item BLUB_GEL = food("blub_gel", 2, 0.3f);
    /** 布魯布果凍：3 凝膠＋糖。吃了身體變輕（緩降 10 秒）。 */
    public static final Item BLUB_JELLY = food("blub_jelly", 6, 0.6f, new MobEffectInstance(MobEffects.SLOW_FALLING, 200));
    public static final Item RAW_SLABBER_STEAK = food("raw_slabber_steak", 3, 0.3f);
    public static final Item COOKED_SLABBER_STEAK = food("cooked_slabber_steak", 8, 0.8f);
    public static final Item RAW_DARTBACK_MEAT = food("raw_dartback_meat", 2, 0.3f);
    /** 熟殼肉：殼下的肉很結實，吃了抗性 I 5 秒。 */
    public static final Item COOKED_DARTBACK_MEAT = food("cooked_dartback_meat", 6, 0.6f, new MobEffectInstance(MobEffects.RESISTANCE, 100));
    /** 築巢者蛋：不能生吃，可以煎，也算原版的蛋（#minecraft:eggs，做蛋糕）。 */
    public static final Item NESTER_EGG = ModProgression.registerItem("nester_egg", Item::new, new Item.Properties().stacksTo(16));
    public static final Item FRIED_NESTER_EGG = food("fried_nester_egg", 5, 0.6f);
    public static final Item ROAMROOT_TUBER = food("roamroot_tuber", 1, 0.3f);
    public static final Item BAKED_ROAMROOT_TUBER = food("baked_roamroot_tuber", 5, 0.6f);
    /** 靈魂花蜜：授粉者採的蜜，喝了靈魂守護 10 秒，留下玻璃瓶。 */
    public static final Item SOUL_NECTAR = ModProgression.registerItem("soul_nectar", Item::new,
            new Item.Properties().stacksTo(16).usingConvertsTo(Items.GLASS_BOTTLE).food(new FoodProperties(4, 0.4f, true),
                    Consumables.defaultDrink().onConsume(new ApplyStatusEffectsConsumeEffect(new MobEffectInstance(SiftFarming.SOUL_WARD, 200))).build()));
    /** 搖晃凍：能吃，但 3 成機率頭暈 8 秒。 */
    public static final Item WOBBLE_JELLY = ModProgression.registerItem("wobble_jelly", Item::new,
            new Item.Properties().food(new FoodProperties(4, 0.3f, false), Consumables.defaultFood().onConsume(
                    new ApplyStatusEffectsConsumeEffect(new MobEffectInstance(MobEffects.NAUSEA, 160), 0.3f)).build()));
    /** 隙浮燉菜：熟泥板獸排＋烤塊莖＋幽光菇＋碗，最飽的一道菜，附回音視界 1 分鐘。 */
    public static final Item SIFT_STEW = ModProgression.registerItem("sift_stew", Item::new,
            new Item.Properties().stacksTo(1).usingConvertsTo(Items.BOWL).food(new FoodProperties(10, 0.8f, false),
                    Consumables.defaultFood().onConsume(new ApplyStatusEffectsConsumeEffect(new MobEffectInstance(SiftFarming.ECHO_SIGHT, 1200))).build()));

    // ---------------------------------------------------------------- 材料
    /** 蹭蹭軟毛：4 個做成白色羊毛；粗製藥水＋軟毛 = 再生藥水。 */
    public static final Item NUZZLE_FLUFF = ModProgression.registerItem("nuzzle_fluff", Item::new);
    /** 花苞花瓣：做成黃色染料。 */
    public static final Item BLOOMBUD_PETAL = ModProgression.registerItem("bloombud_petal", Item::new);
    /** 飛鏢背棘刺、刺球棘：當箭頭做棘刺箭。 */
    public static final Item DARTBACK_SPINE = ModProgression.registerItem("dartback_spine", Item::new);
    public static final Item PRICKLE_QUILL = ModProgression.registerItem("prickle_quill", Item::new);
    /** 清道夫獠牙：和箭做成放血箭。 */
    public static final Item SCAVENGER_FANG = ModProgression.registerItem("scavenger_fang", Item::new);
    /** 暗影皮（追蹤者）：粗製藥水＋暗影皮 = 隱形藥水；4 張拼成皮革。 */
    public static final Item SHADOW_HIDE = ModProgression.registerItem("shadow_hide", Item::new);
    /** 標槍頭（獵人）：接上兩根木棍就是靈魂標槍。 */
    public static final Item HUNTER_SPEARHEAD = ModProgression.registerItem("hunter_spearhead", Item::new);

    // ---------------------------------------------------------------- 武器與工具
    /** 棘刺箭：比一般箭多 1 點基礎傷害。 */
    public static final Item SPINE_ARROW = ModProgression.registerItem("spine_arrow", p -> new SpecialArrowItem(p, false));
    /** 放血箭：命中後流血 5 秒（{@link ModEffects#BLEEDING}）。 */
    public static final Item BLEEDING_ARROW = ModProgression.registerItem("bleeding_arrow", p -> new SpecialArrowItem(p, true));
    public static final Item SOUL_JAVELIN = ModProgression.registerItem("soul_javelin", SoulJavelinItem::new,
            new Item.Properties().stacksTo(16));
    public static final Item TUNING_FORK = ModProgression.registerItem("tuning_fork", TuningForkItem::new,
            new Item.Properties().stacksTo(1));

    private MobDrops() {
    }

    private static Item food(String name, int nutrition, float saturation) {
        return ModProgression.registerItem(name, Item::new, new Item.Properties().food(new FoodProperties(nutrition, saturation, false)));
    }

    private static Item food(String name, int nutrition, float saturation, MobEffectInstance effect) {
        return ModProgression.registerItem(name, Item::new, new Item.Properties().food(new FoodProperties(nutrition, saturation, false),
                Consumables.defaultFood().onConsume(new ApplyStatusEffectsConsumeEffect(effect)).build()));
    }

    static void load() {
        // 類別載入時已經註冊完；放在 ModProgression.register() 呼叫，確保物品排進物品分頁
    }

    /** 棘刺箭與放血箭：射出的仍是原版的箭（外觀、撿回來還是同一種箭），只多了傷害或流血。 */
    public static class SpecialArrowItem extends ArrowItem {
        private final boolean bleeding;

        public SpecialArrowItem(Item.Properties properties, boolean bleeding) {
            super(properties);
            this.bleeding = bleeding;
        }

        private AbstractArrow tune(AbstractArrow arrow) {
            if (!bleeding) {
                arrow.setBaseDamage(3.0);   // 原版箭的基礎傷害是 2
            }
            return arrow;
        }

        @Override
        public AbstractArrow createArrow(Level level, ItemStack ammo, LivingEntity shooter, ItemStack weapon) {
            return tune(bleeding ? new BleedingArrow(level, shooter, ammo.copyWithCount(1), weapon)
                    : new Arrow(level, shooter, ammo.copyWithCount(1), weapon));
        }

        @Override
        public Projectile asProjectile(Level level, Position pos, ItemStack stack, Direction direction) {
            AbstractArrow arrow = tune(bleeding ? new BleedingArrow(level, pos, stack.copyWithCount(1))
                    : new Arrow(level, pos.x(), pos.y(), pos.z(), stack.copyWithCount(1), null));
            arrow.pickup = AbstractArrow.Pickup.ALLOWED;
            return arrow;
        }
    }

    /** 放血箭射出的箭（實體類型仍是原版的箭，用戶端照原版畫）。 */
    private static class BleedingArrow extends Arrow {
        BleedingArrow(Level level, LivingEntity shooter, ItemStack pickup, ItemStack weapon) {
            super(level, shooter, pickup, weapon);
        }

        BleedingArrow(Level level, Position pos, ItemStack pickup) {
            super(level, pos.x(), pos.y(), pos.z(), pickup, null);
        }

        @Override
        protected void doPostHurtEffects(LivingEntity target) {
            super.doPostHurtEffects(target);
            target.addEffect(new MobEffectInstance(ModEffects.BLEEDING, 100, 0), this.getEffectSource());
        }
    }

    /** 可以丟出去的掉落物（投石、陷阱師的網）：像雪球一樣右鍵丟出。 */
    public static class ThrowableDropItem extends Item {
        private final BiFunction<Level, Player, Projectile> factory;

        public ThrowableDropItem(Item.Properties properties, BiFunction<Level, Player, Projectile> factory) {
            super(properties);
            this.factory = factory;
        }

        @Override
        public InteractionResult use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.SNOWBALL_THROW, SoundSource.PLAYERS,
                    0.5f, 0.4f / (level.getRandom().nextFloat() * 0.4f + 0.8f));
            if (level instanceof ServerLevel) {
                Projectile projectile = factory.apply(level, player);
                projectile.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0f, 1.3f, 1.0f);
                level.addFreshEntity(projectile);
            }
            player.getCooldowns().addCooldown(stack, 10);
            stack.consume(1, player);
            return InteractionResult.SUCCESS;
        }
    }

    /** 靈魂標槍：右鍵擲出（約 7 點傷害，拖著靈魂火），插在地上可以撿回來。 */
    public static class SoulJavelinItem extends HintItem {
        public SoulJavelinItem(Item.Properties properties) {
            super(properties, "tooltip.pysift.soul_javelin");
        }

        @Override
        public InteractionResult use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.TRIDENT_THROW.value(), SoundSource.PLAYERS, 1.0f, 1.2f);
            if (level instanceof ServerLevel) {
                HunterJavelinEntity javelin = HunterJavelinEntity.thrown(level, player, stack);
                javelin.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0f, 2.0f, 1.0f);
                level.addFreshEntity(javelin);
            }
            player.getCooldowns().addCooldown(stack, 15);
            stack.consume(1, player);
            return InteractionResult.SUCCESS;
        }
    }

    /** 調音叉：潛行右鍵音符盒記住它的音高，右鍵別的音符盒直接調成同一個音。 */
    public static class TuningForkItem extends HintItem {
        private static final String NOTE = "note";

        public TuningForkItem(Item.Properties properties) {
            super(properties, "tooltip.pysift.tuning_fork");
        }

        @Override
        public InteractionResult useOn(UseOnContext context) {
            Level level = context.getLevel();
            BlockPos pos = context.getClickedPos();
            BlockState state = level.getBlockState(pos);
            if (!state.hasProperty(BlockStateProperties.NOTE)) {
                return InteractionResult.PASS;
            }
            Player player = context.getPlayer();
            ItemStack stack = context.getItemInHand();
            if (level.isClientSide()) {
                return InteractionResult.SUCCESS;
            }
            if (player != null && player.isSecondaryUseActive()) {
                CompoundTag tag = new CompoundTag();
                tag.putInt(NOTE, state.getValue(BlockStateProperties.NOTE));
                stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
                player.sendOverlayMessage(Component.translatable("message.pysift.tuning_fork.stored",
                        state.getValue(BlockStateProperties.NOTE)).withStyle(ChatFormatting.AQUA));
                level.blockEvent(pos, state.getBlock(), 0, 0);
                return InteractionResult.SUCCESS;
            }
            int note = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag().getIntOr(NOTE, -1);
            if (note < 0) {
                if (player != null) {
                    player.sendOverlayMessage(Component.translatable("message.pysift.tuning_fork.empty").withStyle(ChatFormatting.GRAY));
                }
                return InteractionResult.SUCCESS;
            }
            BlockState tuned = state.setValue(BlockStateProperties.NOTE, note);
            level.setBlock(pos, tuned, 3);
            level.blockEvent(pos, tuned.getBlock(), 0, 0);
            if (player != null) {
                player.sendOverlayMessage(Component.translatable("message.pysift.tuning_fork.tuned", note).withStyle(ChatFormatting.AQUA));
            }
            return InteractionResult.SUCCESS;
        }
    }
}
