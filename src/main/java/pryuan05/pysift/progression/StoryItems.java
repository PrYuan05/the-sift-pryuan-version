package pryuan05.pysift.progression;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import java.util.function.IntConsumer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.ConversionParams;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.warden.Warden;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.Level;
import pryuan05.pysift.block.RitualDiscs;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.entity.WardenSoothing;
import pryuan05.pysift.entity.mob.MournerEntity;
import pryuan05.pysift.entity.mob.SiftWardenEntity;
import pryuan05.pysift.entity.mob.SingerEntity;
import pryuan05.pysift.entity.mob.SingerSongs;
import pryuan05.pysift.fluid.SpiritInteractions;

/**
 * 故事物品的功能（MODDING_ROADMAP §4.7 第二部）：
 * <ul>
 *   <li>哀悼號角：玩家版的倒唱八音，24 格內的監守者平靜 30 秒、哀悼者停止哭泣；在強化深板岩門框前、條件齊全時改成終章（{@link Homecoming}）。</li>
 *   <li>八音陶片（{@link OctaveSherdItem}）：右鍵由左到右奏出八個唱片盒的音，動作列逐一顯示每一盒要的唱片。</li>
 *   <li>隙浮之心：幽匿巨怪之心丟進靈液 3 秒後淨化而成；右鍵監守者立刻變成隙浮守衛，右鍵哀悼者立刻變回歌者。</li>
 * </ul>
 * 資源（配方、貼圖、語系）由 tools/progression/build_story.py 產生。
 */
public final class StoryItems {
    public static final int HORN_COOLDOWN = 1200, SOOTHE_TICKS = 600;
    public static final double HORN_RANGE = 24.0;

    public static final Item MOURNING_HORN = ModProgression.registerItem("mourning_horn", MourningHornItem::new,
            new Item.Properties().durability(32).rarity(Rarity.RARE));
    public static final Item SIFT_HEART = ModProgression.registerItem("sift_heart", SiftHeartItem::new,
            new Item.Properties().stacksTo(16).rarity(Rarity.EPIC));

    public static final Item RIFT_SEAL = ModProgression.registerItem("rift_seal", RiftSealItem::new,
            new Item.Properties().stacksTo(16).rarity(Rarity.RARE));

    public static final net.minecraft.world.level.block.Block LULLABY_CENSER = ModProgression.registerBlock("lullaby_censer",
            pryuan05.pysift.block.LullabyCenserBlock::new, net.minecraft.world.level.block.Blocks.SOUL_LANTERN);

    private StoryItems() {
    }

    static void load() {
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            tickSongs();
            if (server.getTickCount() % 10 == 0) {
                for (ServerLevel level : server.getAllLevels()) {
                    purifyHearts(level);
                }
            }
        });
    }

    // ---------------------------------------------------------------- songs played over time by an entity
    private static final class Playing {
        final ServerLevel level;
        final Entity source;
        final SingerSongs.Song song;
        final int step;
        final IntConsumer onNote;
        final Runnable onEnd;
        int t;

        Playing(ServerLevel level, Entity source, SingerSongs.Song song, int step, IntConsumer onNote, Runnable onEnd) {
            this.level = level;
            this.source = source;
            this.song = song;
            this.step = step;
            this.onNote = onNote;
            this.onEnd = onEnd;
        }
    }

    private static final List<Playing> PLAYING = new ArrayList<>();

    /** 讓 source 用笛聲（加一點鐘聲）唱一首曲子；每個新音呼叫 onNote(第幾格)，唱完呼叫 onEnd。 */
    public static void play(ServerLevel level, Entity source, SingerSongs.Song song, int step, IntConsumer onNote, Runnable onEnd) {
        PLAYING.add(new Playing(level, source, song, step, onNote, onEnd));
    }

    private static void tickSongs() {
        if (PLAYING.isEmpty()) {
            return;
        }
        List<Runnable> ends = new ArrayList<>();
        for (Iterator<Playing> it = PLAYING.iterator(); it.hasNext(); ) {
            Playing p = it.next();
            if (p.source.isRemoved()) {
                it.remove();
                continue;
            }
            int t = p.t++;
            int i = t / p.step;
            if (i >= p.song.length()) {
                it.remove();
                if (p.onEnd != null) {
                    ends.add(p.onEnd);
                }
                continue;
            }
            if (t % p.step == 0 && p.song.onset()[i]) {
                int note = p.song.notes()[i];
                float pitch = (float) Math.pow(2.0, (note - 12) / 12.0);
                p.level.playSound(null, p.source.getX(), p.source.getEyeY(), p.source.getZ(), SoundEvents.NOTE_BLOCK_FLUTE.value(),
                        SoundSource.PLAYERS, 1.0f, pitch);
                p.level.playSound(null, p.source.getX(), p.source.getEyeY(), p.source.getZ(), SoundEvents.NOTE_BLOCK_CHIME.value(),
                        SoundSource.PLAYERS, 0.4f, pitch);
                p.level.sendParticles(ParticleTypes.NOTE, p.source.getX(), p.source.getEyeY() + 0.6, p.source.getZ(), 0, note / 24.0, 0, 0, 1.0);
                if (p.onNote != null) {
                    p.onNote.accept(i);
                }
            }
        }
        ends.forEach(Runnable::run);
    }

    // ---------------------------------------------------------------- Mourning Horn
    public static class MourningHornItem extends Item {
        public MourningHornItem(Properties properties) {
            super(properties);
        }

        @Override
        public InteractionResult use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            if (player.getCooldowns().isOnCooldown(stack)) {
                return InteractionResult.PASS;
            }
            if (level instanceof ServerLevel server && player instanceof ServerPlayer sp) {
                player.getCooldowns().addCooldown(stack, HORN_COOLDOWN);
                stack.hurtAndBreak(1, sp, hand == InteractionHand.MAIN_HAND
                        ? net.minecraft.world.entity.EquipmentSlot.MAINHAND : net.minecraft.world.entity.EquipmentSlot.OFFHAND);
                server.playSound(null, player.blockPosition(), SoundEvents.WARDEN_LISTENING_ANGRY, SoundSource.PLAYERS, 0.8f, 1.6f);
                if (!Homecoming.tryBegin(server, sp)) {   // 終章的條件不齊：一般的安撫
                    play(server, player, SingerSongs.MOURNING, 5, null, () -> soothe(server, player));
                }
            }
            return InteractionResult.SUCCESS;
        }
    }

    /** 號角唱完：24 格內的野生監守者平靜、哀悼者停止哭泣。 */
    static void soothe(ServerLevel level, Player player) {
        int calmed = 0;
        for (Warden w : level.getEntitiesOfClass(Warden.class, player.getBoundingBox().inflate(HORN_RANGE),
                w -> !(w instanceof SiftWardenEntity))) {
            WardenSoothing.soothe(level, w, SOOTHE_TICKS);
            level.sendParticles(ParticleTypes.SCULK_SOUL, w.getX(), w.getY() + 1.5, w.getZ(), 20, 0.6, 0.8, 0.6, 0.02);
            calmed++;
        }
        for (MournerEntity m : level.getEntitiesOfClass(MournerEntity.class, player.getBoundingBox().inflate(HORN_RANGE))) {
            m.hush(SOOTHE_TICKS);
        }
        for (SiftWardenEntity g : level.getEntitiesOfClass(SiftWardenEntity.class, player.getBoundingBox().inflate(HORN_RANGE),
                pryuan05.pysift.entity.DenGuard::isRoused)) {   // 回音窟被驚醒的守衛：聽到歌聲就安靜
            pryuan05.pysift.entity.DenGuard.calm(g);
            calmed++;
        }
        if (calmed > 0 && player instanceof ServerPlayer sp) {
            StoryTriggers.wardenSoothed(sp);
            sp.sendOverlayMessage(Component.translatable("message.pysift.mourning_horn.calmed", calmed).withStyle(ChatFormatting.LIGHT_PURPLE));
        }
    }

    // ---------------------------------------------------------------- Octave sherd: the ritual hint
    public static class OctaveSherdItem extends Item {
        public OctaveSherdItem(Properties properties) {
            super(properties);
        }

        @Override
        public InteractionResult use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            if (player.getCooldowns().isOnCooldown(stack)) {
                return InteractionResult.PASS;
            }
            if (level instanceof ServerLevel server && player instanceof ServerPlayer sp) {
                player.getCooldowns().addCooldown(stack, 100);
                int[] notes = new int[RitualDiscs.DISCS.size()];
                boolean[] onset = new boolean[notes.length];
                for (int i = 0; i < notes.length; i++) {
                    notes[i] = RitualDiscs.forSeat(i).semitone() + 6;   // 唱片盒的音高（RitualDiscs.Disc.pitch）
                    onset[i] = true;
                }
                play(server, player, new SingerSongs.Song("octave", notes, onset), 12, i -> {
                    RitualDiscs.Disc disc = RitualDiscs.forSeat(i);
                    sp.sendOverlayMessage(Component.translatable("message.pysift.octave_sherd.seat", i + 1,
                            Component.translatable(RitualDiscs.songKey(disc)).withColor(disc.color() & 0xFFFFFF)));
                }, null);
            }
            return InteractionResult.SUCCESS;
        }
    }

    // ---------------------------------------------------------------- Rift Seal (act 7)
    /** 對隙浮裡的傳送門使用：門關閉，周圍的腐爛停止並慢慢變回紅色（{@link pryuan05.pysift.block.RotSpread#seal}）。 */
    public static class RiftSealItem extends Item {
        public RiftSealItem(Properties properties) {
            super(properties);
        }

        @Override
        public InteractionResult useOn(net.minecraft.world.item.context.UseOnContext ctx) {
            if (!ctx.getLevel().getBlockState(ctx.getClickedPos()).is(pryuan05.pysift.block.ModBlocks.SIFT_PORTAL)) {
                return InteractionResult.PASS;
            }
            if (!(ctx.getLevel() instanceof ServerLevel level) || !(ctx.getPlayer() instanceof ServerPlayer player)) {
                return InteractionResult.SUCCESS;
            }
            if (level.dimension() != pryuan05.pysift.block.SiftPortalBlock.SIFT_DIM) {
                player.sendOverlayMessage(Component.translatable("message.pysift.rift_seal.not_here").withStyle(ChatFormatting.GRAY));
                return InteractionResult.FAIL;
            }
            net.minecraft.core.BlockPos at = ctx.getClickedPos();
            if (pryuan05.pysift.block.RotSpread.seal(level, at)) {
                ctx.getItemInHand().consume(1, player);
                level.playSound(null, at, SoundEvents.RESPAWN_ANCHOR_DEPLETE.value(), SoundSource.BLOCKS, 1.5f, 0.8f);
                level.playSound(null, at, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 2.0f, 0.6f);
                level.sendParticles(ParticleTypes.SCULK_SOUL, at.getX() + 0.5, at.getY() + 1.0, at.getZ() + 0.5, 40, 1.2, 1.2, 1.2, 0.03);
                player.sendSystemMessage(Component.translatable("message.pysift.rift_seal.sealed").withStyle(ChatFormatting.LIGHT_PURPLE));
                StoryTriggers.award(player, "rift_sealed");
            }
            return InteractionResult.SUCCESS_SERVER;
        }
    }

    // ---------------------------------------------------------------- Sift Heart
    public static class SiftHeartItem extends Item {
        public SiftHeartItem(Properties properties) {
            super(properties);
        }

        @Override
        public InteractionResult interactLivingEntity(ItemStack stack, Player player, LivingEntity target, InteractionHand hand) {
            if (!(player.level() instanceof ServerLevel level)) {
                return target instanceof Warden || target instanceof MournerEntity ? InteractionResult.SUCCESS : InteractionResult.PASS;
            }
            if (target instanceof Warden w && !(w instanceof SiftWardenEntity)) {
                SiftWardenEntity cured = w.convertTo(ModEntities.SIFT_WARDEN, ConversionParams.single(w, false, false), s -> {
                    s.setPersistenceRequired();
                    s.addTag(pryuan05.pysift.fluid.SpiritFluid.REBORN);
                });
                if (cured != null) {
                    stack.consume(1, player);
                    burst(level, cured);
                    StoryTriggers.wardenCured(level, cured.position());
                    return InteractionResult.SUCCESS_SERVER;
                }
            } else if (target instanceof MournerEntity m) {
                SingerEntity singer = m.convertTo(ModEntities.SINGER, ConversionParams.single(m, false, false), s -> { });
                if (singer != null) {
                    stack.consume(1, player);
                    burst(level, singer);
                    StoryTriggers.mournerCured(level, singer.position());
                    return InteractionResult.SUCCESS_SERVER;
                }
            }
            return InteractionResult.PASS;
        }
    }

    private static void burst(ServerLevel level, Entity e) {
        level.sendParticles(ParticleTypes.SCULK_SOUL, e.getX(), e.getY() + e.getBbHeight() * 0.5, e.getZ(), 40, 0.6, 0.9, 0.6, 0.04);
        level.sendParticles(ParticleTypes.NOTE, e.getX(), e.getY() + e.getBbHeight() + 0.3, e.getZ(), 10, 0.8, 0.3, 0.8, 1.0);
        level.playSound(null, e.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.NEUTRAL, 2.0f, 1.0f);
    }

    /** 幽匿巨怪之心泡在靈液裡 PURIFY tick：淨化成隙浮之心（每 10 tick 檢查一次所有掉落物）。 */
    private static final int PURIFY = 60;
    private static final Map<ItemEntity, Integer> SOAKING = new WeakHashMap<>();

    private static void purifyHearts(ServerLevel level) {
        for (ItemEntity item : level.getEntities(net.minecraft.world.entity.EntityTypes.ITEM,
                i -> i.getItem().is(BossRewards.SCULK_MONSTROSITY_HEART))) {
            boolean wet = SpiritInteractions.isSpirit(level.getFluidState(item.blockPosition()));
            int t = wet ? SOAKING.getOrDefault(item, 0) + 10 : 0;
            SOAKING.put(item, t);
            if (!wet) {
                continue;
            }
            level.sendParticles(ParticleTypes.GLOW, item.getX(), item.getY() + 0.3, item.getZ(), 3, 0.2, 0.2, 0.2, 0.01);
            if (t >= PURIFY) {
                SOAKING.remove(item);
                ItemStack old = item.getItem();
                item.setItem(new ItemStack(SIFT_HEART, old.getCount()));
                level.sendParticles(ParticleTypes.SCULK_SOUL, item.getX(), item.getY() + 0.4, item.getZ(), 20, 0.3, 0.3, 0.3, 0.03);
                level.playSound(null, item.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.NEUTRAL, 1.5f, 1.4f);
            }
        }
    }
}
