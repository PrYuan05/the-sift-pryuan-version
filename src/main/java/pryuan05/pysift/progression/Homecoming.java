package pryuan05.pysift.progression;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.block.RotSpread;
import pryuan05.pysift.block.SiftPortalBlock;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.entity.mob.SiftWardenEntity;
import pryuan05.pysift.entity.mob.SingerEntity;
import pryuan05.pysift.entity.mob.SingerSongs;

/**
 * 終章「回家」（MODDING_ROADMAP §4.7）。條件：
 * <ol>
 *   <li>腐爛已止息（擊敗幽匿巨怪，{@link RotSpread.State#stilled}）；</li>
 *   <li>玩家站在遠古城市的強化深板岩門框附近（FRAME 格內至少 FRAME_BLOCKS 塊強化深板岩）；</li>
 *   <li>KIN 格內有一隻歌者和一隻隙浮守衛。</li>
 * </ol>
 * 這時吹響哀悼號角，歌者會正著唱一次八音（{@link SingerSongs#OPENING}），門框亮起；唱完後歌者鑽回地底、守衛挖地離開，
 * 門框 HEAL 格內的藍幽匿在 3 秒內全部變回赤紅幽匿，頒發最終成就 story/homecoming。
 * 之後玩家下一次進入隙浮時，送回去的守衛會帶著一隻歌者出現在附近（重逢，{@link #reunite}）。
 */
public final class Homecoming {
    private static final int FRAME = 16, FRAME_BLOCKS = 10, HEAL = 24, HEAL_TICKS = 60;
    private static final double KIN = 24.0;

    private Homecoming() {
    }

    public static void load() {
        ServerTickEvents.END_SERVER_TICK.register(server -> tickHealing());
        ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((player, origin, destination) -> {
            if (destination.dimension() == SiftPortalBlock.SIFT_DIM) {
                reunite(destination, player);
            }
        });
    }

    /** 條件齊全就開始終章並回傳 true；否則回傳 false（號角照常安撫）。站在門框旁但條件不齊時，提示少了什麼。 */
    public static boolean tryBegin(ServerLevel level, ServerPlayer player) {
        BlockPos frame = frameCentre(level, player.blockPosition());
        if (frame == null) {
            return false;
        }
        SingerEntity singer = nearest(level, SingerEntity.class, player, s -> !s.isRitual() && !s.isLeaving() && !s.isEmerging());
        SiftWardenEntity warden = nearest(level, SiftWardenEntity.class, player, w -> !w.isGoingHome());
        String missing = !RotSpread.State.get(level.getServer()).stilled() ? "rot"
                : singer == null ? "singer" : warden == null ? "warden" : null;
        if (missing != null) {
            player.sendSystemMessage(Component.translatable("message.pysift.homecoming.missing_" + missing).withStyle(ChatFormatting.GRAY));
            return false;
        }
        Vec3 c = Vec3.atCenterOf(frame);
        singer.getNavigation().stop();
        singer.getLookControl().setLookAt(c.x, c.y, c.z);
        singer.triggerAnim("skill", "sing");
        warden.getNavigation().moveTo(c.x, frame.getY(), c.z, 0.8);
        player.sendSystemMessage(Component.translatable("message.pysift.homecoming.begin").withStyle(ChatFormatting.LIGHT_PURPLE));
        level.playSound(null, frame, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 2.5f, 0.8f);
        StoryItems.play(level, singer, SingerSongs.OPENING, 8, i -> {
            level.sendParticles(ParticleTypes.END_ROD, c.x, c.y, c.z, 12 + i * 4, 1.5, 1.5, 1.5, 0.03);
            level.sendParticles(ParticleTypes.SCULK_SOUL, c.x, c.y, c.z, 6, 2.0, 1.5, 2.0, 0.02);
        }, () -> finish(level, frame, singer, warden));
        return true;
    }

    private static void finish(ServerLevel level, BlockPos frame, SingerEntity singer, SiftWardenEntity warden) {
        Vec3 c = Vec3.atCenterOf(frame);
        level.playSound(null, frame, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 3.0f, 1.0f);
        level.playSound(null, frame, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.BLOCKS, 1.0f, 1.8f);
        level.sendParticles(ParticleTypes.SCULK_SOUL, c.x, c.y, c.z, 120, 4.0, 2.0, 4.0, 0.05);
        if (singer.isAlive()) {
            singer.startLeaving();
        }
        if (warden.isAlive()) {
            warden.goHome();
        }
        // 門框打開，之後一直開著：玩家可以跟著牠們回隙浮（框架不封閉時，在門框中央開一道裂隙門）
        if (!SiftPortalBlock.hasPortalNear(level, frame)) {
            SiftPortalBlock.Frame door = SiftPortalBlock.findFrame(level, frame, 14, Blocks.REINFORCED_DEEPSLATE);
            if (door != null) {
                SiftPortalBlock.fillFrame(level, door);
            } else {
                SiftPortalBlock.buildRiftPortal(level, groundUnder(level, frame),
                        warden.getDirection().getAxis() == net.minecraft.core.Direction.Axis.X
                                ? net.minecraft.core.Direction.Axis.Z : net.minecraft.core.Direction.Axis.X);
            }
        }
        RotSpread.State state = RotSpread.State.get(level.getServer());
        state.setHomeward(state.homeward() + 1);
        // 門框附近的藍幽匿在 3 秒內全部變回紅色
        List<BlockPos> blue = new ArrayList<>();
        for (BlockPos p : BlockPos.betweenClosed(frame.offset(-HEAL, -12, -HEAL), frame.offset(HEAL, 12, HEAL))) {
            if (level.getBlockState(p).is(Blocks.SCULK) || level.getBlockState(p).is(Blocks.SCULK_VEIN)) {
                blue.add(p.immutable());
            }
        }
        blue.sort(Comparator.comparingDouble(p -> p.distSqr(frame)));   // 從門框往外擴散
        HEALING.add(new Healing(level, blue));
        for (ServerPlayer p : level.getEntitiesOfClass(ServerPlayer.class, new AABB(frame).inflate(48))) {
            p.sendSystemMessage(Component.translatable("message.pysift.homecoming.done").withStyle(ChatFormatting.LIGHT_PURPLE));
            StoryTriggers.award(p, "homecoming");
        }
    }

    // ---------------------------------------------------------------- healing the city, a few blocks per tick
    private record Healing(ServerLevel level, List<BlockPos> blocks) {
    }

    private static final List<Healing> HEALING = new ArrayList<>();

    private static void tickHealing() {
        for (var it = HEALING.iterator(); it.hasNext(); ) {
            Healing h = it.next();
            int n = Math.max(1, (int) Math.ceil(h.blocks.size() / (double) HEAL_TICKS));
            for (int i = 0; i < n && !h.blocks.isEmpty(); i++) {
                RotSpread.healOne(h.level, h.blocks.remove(0));
            }
            if (h.blocks.isEmpty()) {
                it.remove();
            }
        }
    }

    // ---------------------------------------------------------------- reunion in The Sift
    /** 送回去的守衛還沒重逢：在玩家附近 12~16 格的地面上，生成一隻隙浮守衛和一隻歌者。 */
    public static void reunite(ServerLevel sift, ServerPlayer player) {
        RotSpread.State state = RotSpread.State.get(sift.getServer());
        if (state.homeward() <= 0) {
            return;
        }
        double a = sift.getRandom().nextDouble() * Math.PI * 2;
        int x = player.getBlockX() + (int) (Math.cos(a) * 14), z = player.getBlockZ() + (int) (Math.sin(a) * 14);
        int y = sift.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
        BlockPos at = new BlockPos(x, y, z);
        SiftWardenEntity warden = ModEntities.SIFT_WARDEN.create(sift, EntitySpawnReason.EVENT);
        SingerEntity singer = ModEntities.SINGER.create(sift, EntitySpawnReason.EVENT);
        if (warden == null || singer == null) {
            return;
        }
        warden.snapTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, (float) Math.toDegrees(a) + 90, 0);
        warden.setPersistenceRequired();
        singer.snapTo(at.getX() + 2.5, at.getY(), at.getZ() + 0.5, (float) Math.toDegrees(a) + 90, 0);
        singer.setPersistenceRequired();
        sift.addFreshEntity(warden);
        sift.addFreshEntity(singer);
        singer.startEmerging();
        sift.sendParticles(ParticleTypes.NOTE, at.getX() + 1.5, at.getY() + 3.5, at.getZ() + 0.5, 10, 1.0, 0.4, 1.0, 1.0);
        state.setHomeward(state.homeward() - 1);
        player.sendSystemMessage(Component.translatable("message.pysift.homecoming.reunion").withStyle(ChatFormatting.LIGHT_PURPLE));
    }

    // ---------------------------------------------------------------- helpers
    /** 門框中心往下找到第一個實心地面，回傳它上面那一格（裂隙門的底邊）。 */
    private static BlockPos groundUnder(ServerLevel level, BlockPos from) {
        BlockPos p = from;
        for (int i = 0; i < 16 && level.getBlockState(p.below()).getCollisionShape(level, p.below()).isEmpty(); i++) {
            p = p.below();
        }
        return p;
    }

    /** FRAME 格內的強化深板岩夠多（遠古城市的門框）：回傳它們的中心，否則 null。 */
    private static BlockPos frameCentre(ServerLevel level, BlockPos near) {
        long sx = 0, sy = 0, sz = 0;
        int n = 0;
        for (BlockPos p : BlockPos.betweenClosed(near.offset(-FRAME, -8, -FRAME), near.offset(FRAME, 12, FRAME))) {
            if (level.getBlockState(p).is(Blocks.REINFORCED_DEEPSLATE)) {
                sx += p.getX();
                sy += p.getY();
                sz += p.getZ();
                n++;
            }
        }
        return n < FRAME_BLOCKS ? null : new BlockPos((int) (sx / n), (int) (sy / n), (int) (sz / n));
    }

    private static <T extends net.minecraft.world.entity.LivingEntity> T nearest(ServerLevel level, Class<T> type, ServerPlayer player,
                                                                                  java.util.function.Predicate<T> ok) {
        return level.getEntitiesOfClass(type, player.getBoundingBox().inflate(KIN), e -> e.isAlive() && ok.test(e)).stream()
                .min(Comparator.comparingDouble(player::distanceToSqr)).orElse(null);
    }
}
