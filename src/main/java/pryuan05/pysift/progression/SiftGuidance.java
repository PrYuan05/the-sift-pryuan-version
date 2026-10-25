package pryuan05.pysift.progression;

import com.mojang.serialization.Codec;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.Filterable;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUseAnimation;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.LodestoneTracker;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.item.component.WrittenBookContent;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.portal.TeleportTransition;
import pryuan05.pysift.PySift;
import pryuan05.pysift.worldgen.BossArenaSavedData;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.function.Consumer;

/**
 * 上手輔助（A）：
 * <ul>
 *   <li><b>靈魂羅盤</b>：在隙浮右鍵，指針指向目前模式的目標（調和者／君王／幽匿巨怪的競技場，或最近的遺跡結構）；
 *       蹲下右鍵切換模式。還沒生成的競技場會改指向該 Boss 所在的生態域。</li>
 *   <li><b>回程符石</b>：在隙浮按住右鍵 3 秒，傳送回你在主世界的重生點（床／重生錨，沒有就世界重生點）。</li>
 *   <li><b>隙浮指南書</b>：第一次進入隙浮時自動獲得（也能用書＋紫龍晶合成），介紹靈液、解藥、礦石、Boss、祭壇、覺醒、信標與靈髓。</li>
 * </ul>
 */
public final class SiftGuidance {
    public static final ResourceKey<Level> THE_SIFT = ResourceKey.create(Registries.DIMENSION, PySift.id("the_sift"));
    public static final TagKey<Structure> COMPASS_STRUCTURES = TagKey.create(Registries.STRUCTURE, PySift.id("soul_compass_targets"));
    public static final int GUIDE_PAGES = 12;

    public static final DataComponentType<Integer> COMPASS_MODE = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
            PySift.id("compass_mode"), DataComponentType.<Integer>builder().persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());

    public static final AttachmentType<Boolean> RECEIVED_GUIDE = AttachmentRegistry.create(PySift.id("received_guide"),
            builder -> builder.persistent(Codec.BOOL).initializer(() -> false).copyOnDeath());

    /** 羅盤模式：Boss 鍵（與 BossArenaSavedData 的 bossKey 相同）、競技場所在的生態域。最後一個模式是遺跡結構。 */
    private record Target(String bossKey, String biome, String lang) {
    }

    private static final List<Target> BOSSES = List.of(
            new Target("pysift:harmonizer", "willow_grove", "entity.pysift.harmonizer"),
            new Target("pysift:monarch", "amber_dunes", "entity.pysift.monarch"),
            new Target("pysift:sculk_monstrosity", "violet_slate_abyss", "entity.pysift.sculk_monstrosity"));
    private static final int MODES = BOSSES.size() + 1;

    public static final Item SOUL_COMPASS = ModProgression.registerItem("soul_compass", SoulCompassItem::new,
            new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON));
    public static final Item HOMEWARD_STONE = ModProgression.registerItem("homeward_stone", HomewardStoneItem::new,
            new Item.Properties().stacksTo(16).rarity(Rarity.UNCOMMON));

    private SiftGuidance() {
    }

    // ------------------------------------------------------------ guide book
    public static ItemStack guideBook() {
        List<Filterable<Component>> pages = new ArrayList<>();
        for (int i = 1; i <= GUIDE_PAGES; i++) {
            pages.add(Filterable.passThrough(Component.translatable("book.pysift.guide.page" + i)));
        }
        ItemStack book = new ItemStack(Items.WRITTEN_BOOK);
        book.set(DataComponents.WRITTEN_BOOK_CONTENT, new WrittenBookContent(Filterable.passThrough("Sift Guide"), "PrYuan05", 0, pages, true));
        book.set(DataComponents.CUSTOM_NAME, Component.translatable("book.pysift.guide.title").withStyle(ChatFormatting.LIGHT_PURPLE));
        return book;
    }

    // ------------------------------------------------------------ soul compass
    public static class SoulCompassItem extends Item {
        public SoulCompassItem(Properties properties) {
            super(properties);
        }

        @Override
        public InteractionResult use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            if (!(level instanceof ServerLevel server) || !(player instanceof ServerPlayer sp)) {
                return InteractionResult.SUCCESS;
            }
            int mode = stack.getOrDefault(COMPASS_MODE, 0);
            if (player.isShiftKeyDown()) {
                // 蹲下右鍵：切換到下一個目標，並且立刻鎖定（不用再右鍵一次）
                mode = (mode + 1) % MODES;
                stack.set(COMPASS_MODE, mode);
                stack.remove(DataComponents.LODESTONE_TRACKER);
                if (!level.dimension().equals(THE_SIFT)) {
                    sp.sendOverlayMessage(Component.translatable("message.pysift.compass.mode", modeName(mode)));
                    return InteractionResult.SUCCESS_SERVER;
                }
            }
            if (!level.dimension().equals(THE_SIFT)) {
                sp.sendOverlayMessage(Component.translatable("message.pysift.compass.wrong_dimension"));
                return InteractionResult.FAIL;
            }
            BlockPos here = player.blockPosition();
            BlockPos target = null;
            boolean biomeOnly = false;
            if (mode < BOSSES.size()) {
                Target t = BOSSES.get(mode);
                Optional<BossArenaSavedData.ArenaRecord> arena = BossArenaSavedData.get(server).getArenas().stream()
                        .filter(a -> a.bossKey().equals(t.bossKey()))
                        .min(Comparator.comparingDouble(a -> a.pos().distSqr(here)));
                if (arena.isPresent()) {
                    target = arena.get().pos();
                } else {
                    ResourceKey<Biome> biome = ResourceKey.create(Registries.BIOME, PySift.id(t.biome()));
                    var found = server.findClosestBiome3d((Holder<Biome> h) -> h.is(biome), here, 6400, 32, 64);
                    if (found != null) {
                        target = found.getFirst();
                        biomeOnly = true;
                    }
                }
            } else {
                target = server.findNearestMapStructure(COMPASS_STRUCTURES, here, 100, false);
            }
            if (target == null) {
                sp.sendOverlayMessage(Component.translatable("message.pysift.compass.not_found", modeName(mode)));
                return InteractionResult.FAIL;
            }
            stack.set(DataComponents.LODESTONE_TRACKER, new LodestoneTracker(Optional.of(GlobalPos.of(level.dimension(), target)), false));
            int distance = (int) Math.sqrt(target.distSqr(here));
            sp.sendOverlayMessage(Component.translatable(biomeOnly ? "message.pysift.compass.biome" : "message.pysift.compass.found",
                    modeName(mode), distance));
            server.playSound(null, here, SoundEvents.LODESTONE_COMPASS_LOCK, SoundSource.PLAYERS, 1.0f, 1.2f);
            player.getCooldowns().addCooldown(stack, 40);
            return InteractionResult.SUCCESS_SERVER;
        }

        private static Component modeName(int mode) {
            return mode < BOSSES.size() ? Component.translatable(BOSSES.get(mode).lang()) : Component.translatable("message.pysift.compass.ruins");
        }

        @Override
        public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> out, TooltipFlag flag) {
            out.accept(Component.translatable("message.pysift.compass.mode", modeName(stack.getOrDefault(COMPASS_MODE, 0)))
                    .withStyle(ChatFormatting.AQUA));
            out.accept(Component.translatable("tooltip.pysift.soul_compass.0").withStyle(ChatFormatting.GRAY));
            out.accept(Component.translatable("tooltip.pysift.soul_compass.1").withStyle(ChatFormatting.GRAY));
        }
    }

    // ------------------------------------------------------------ homeward stone
    public static class HomewardStoneItem extends Item {
        private static final int CHANNEL = 60;

        public HomewardStoneItem(Properties properties) {
            super(properties);
        }

        @Override
        public ItemUseAnimation getUseAnimation(ItemStack stack) {
            return ItemUseAnimation.BOW;
        }

        @Override
        public int getUseDuration(ItemStack stack, LivingEntity entity) {
            return CHANNEL;
        }

        @Override
        public InteractionResult use(Level level, Player player, InteractionHand hand) {
            if (!level.dimension().equals(THE_SIFT)) {
                if (player instanceof ServerPlayer sp) {
                    sp.sendOverlayMessage(Component.translatable("message.pysift.homeward.wrong_dimension"));
                }
                return InteractionResult.FAIL;
            }
            player.startUsingItem(hand);
            return InteractionResult.CONSUME;
        }

        @Override
        public void onUseTick(Level level, LivingEntity user, ItemStack stack, int remaining) {
            if (level instanceof ServerLevel server && remaining % 5 == 0) {
                server.sendParticles(ParticleTypes.REVERSE_PORTAL, user.getX(), user.getY(1.0), user.getZ(), 8, 0.4, 0.6, 0.4, 0.05);
            }
        }

        @Override
        public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity user) {
            if (user instanceof ServerPlayer player && level.dimension().equals(THE_SIFT)) {
                TeleportTransition home = player.findRespawnPositionAndUseSpawnBlock(false, TeleportTransition.DO_NOTHING);
                level.playSound(null, player.blockPosition(), SoundEvents.CHORUS_FRUIT_TELEPORT, SoundSource.PLAYERS, 1.0f, 0.8f);
                player.teleport(home);
                home.newLevel().playSound(null, player.blockPosition(), SoundEvents.CHORUS_FRUIT_TELEPORT, SoundSource.PLAYERS, 1.0f, 1.0f);
                stack.consume(1, player);
                player.getCooldowns().addCooldown(stack, 100);
            }
            return stack;
        }

        @Override
        public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> out, TooltipFlag flag) {
            out.accept(Component.translatable("tooltip.pysift.homeward_stone").withStyle(ChatFormatting.GRAY));
        }
    }

    static void load() {
        // 第一次進入隙浮：送一本指南書
        ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((player, origin, destination) -> {
            if (destination.dimension().equals(THE_SIFT) && !player.getAttachedOrElse(RECEIVED_GUIDE, false)) {
                player.setAttached(RECEIVED_GUIDE, true);
                player.getInventory().placeItemBackInInventory(guideBook(), net.minecraft.util.Prediction.SERVER_ONLY);
                player.sendSystemMessage(Component.translatable("message.pysift.guide.received").withStyle(ChatFormatting.LIGHT_PURPLE));
            }
        });
    }
}
