package pryuan05.pysift.entity;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.BarrelBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.block.ModBlocks;
import pryuan05.pysift.entity.mob.EchoGolemEntity;
import pryuan05.pysift.entity.mob.SiftWardenEntity;
import pryuan05.pysift.entity.mob.SingerEntity;
import pryuan05.pysift.progression.ModProgression;

import java.util.Map;
import java.util.UUID;
import java.util.WeakHashMap;

/**
 * 回音窟的守衛（§4.7「回音窟」）：結構裡帶實體標籤 {@value #TAG} 的隙浮守衛。平常和其他隙浮守衛一樣不理玩家；
 * 玩家在附近攻擊歌者、迴音傀儡或守衛，打開箱子，或打破回音晶簇、靈魂晶塊、紫龍晶簇、音符盒時，守衛被這陌生的聲響驚醒，
 * 對那位玩家生氣 {@link #ROUSE_TICKS} tick。附近有歌者活著時（歌聲）平靜得快一倍。被驚醒時不收迴音碎片；
 * 收服（餵迴音碎片）之後就不再是守衛。驚醒狀態只放在記憶體裡，重新載入就回到平靜。
 */
public final class DenGuard {
    public static final String TAG = "pysift_den_guard";
    static final int ROUSE_TICKS = 600;
    static final double HURT_RANGE = 32.0, CHEST_RANGE = 12.0, BREAK_RANGE = 16.0, SONG_RANGE = 16.0, CHASE_RANGE = 48.0;
    private static final Map<SiftWardenEntity, Rouse> ROUSED = new WeakHashMap<>();

    private static final class Rouse {
        UUID player;
        int ticks;
    }

    private DenGuard() {
    }

    public static boolean isGuard(SiftWardenEntity warden) {
        return warden.entityTags().contains(TAG);
    }

    /** WardenMixin：被驚醒的守衛可以對這位玩家生氣、鎖定他。 */
    public static boolean isRousedAgainst(SiftWardenEntity warden, Entity entity) {
        Rouse r = ROUSED.get(warden);
        return r != null && r.ticks > 0 && entity.getUUID().equals(r.player);
    }

    public static boolean isRoused(SiftWardenEntity warden) {
        Rouse r = ROUSED.get(warden);
        return r != null && r.ticks > 0;
    }

    /** 聽見歌聲（回音窟的合唱、哀悼號角）：被驚醒的守衛立刻平靜，但仍然是守衛。 */
    public static void calm(SiftWardenEntity warden) {
        Rouse r = ROUSED.remove(warden);
        if (r != null && warden.level() instanceof ServerLevel level) {
            Player p = level.getPlayerByUUID(r.player);
            if (p != null) {
                warden.clearAnger(p);
            }
            warden.playSound(SoundEvents.WARDEN_LISTENING, 1.5f, 1.25f);
            level.sendParticles(ParticleTypes.NOTE, warden.getX(), warden.getY() + 3.0, warden.getZ(), 3, 0.4, 0.2, 0.4, 1.0);
        }
    }

    /** 收服之後：不再是守衛，也不再生氣。 */
    public static void release(SiftWardenEntity warden) {
        warden.removeTag(TAG);
        Rouse r = ROUSED.remove(warden);
        if (r != null && warden.level() instanceof ServerLevel level) {
            Player p = level.getPlayerByUUID(r.player);
            if (p != null) {
                warden.clearAnger(p);
            }
        }
    }

    /** 驚醒 range 格內的守衛，讓他們對 player 生氣。 */
    public static void rouseNear(ServerLevel level, Vec3 at, Player player, double range) {
        if (player.isCreative() || player.isSpectator()) {
            return;
        }
        boolean woke = false;
        for (SiftWardenEntity w : level.getEntitiesOfClass(SiftWardenEntity.class, new AABB(at, at).inflate(range),
                w -> w.isAlive() && isGuard(w))) {
            Rouse r = ROUSED.computeIfAbsent(w, k -> new Rouse());
            if (r.ticks <= 0 || !player.getUUID().equals(r.player)) {
                woke = true;
                w.playSound(SoundEvents.WARDEN_ROAR, 3.0f, 1.2f);
            }
            r.player = player.getUUID();
            r.ticks = ROUSE_TICKS;
            w.increaseAngerAt(player, 150, false);
        }
        if (woke) {
            player.sendOverlayMessage(Component.translatable("message.pysift.den_guard.roused").withStyle(ChatFormatting.DARK_AQUA));
        }
    }

    /** SiftWardenEntity.tick：維持憤怒、隨時間（歌聲）平靜下來。 */
    public static void tick(SiftWardenEntity warden, ServerLevel level) {
        Rouse r = ROUSED.get(warden);
        if (r == null || r.ticks <= 0) {
            return;
        }
        boolean singing = warden.tickCount % 20 == 0
                && !level.getEntitiesOfClass(SingerEntity.class, warden.getBoundingBox().inflate(SONG_RANGE), SingerEntity::isAlive).isEmpty();
        r.ticks -= singing ? 21 : 1;   // 每 20 tick 檢查一次歌聲：有歌聲時這 20 tick 扣 40
        Player p = level.getPlayerByUUID(r.player);
        boolean gone = p == null || !p.isAlive() || p.level() != level || warden.distanceTo(p) > CHASE_RANGE;
        if (r.ticks <= 0 || gone) {
            r.ticks = 0;
            ROUSED.remove(warden);
            if (p != null) {
                warden.clearAnger(p);
            }
            warden.playSound(SoundEvents.WARDEN_LISTENING, 1.5f, 1.25f);
            level.sendParticles(ParticleTypes.NOTE, warden.getX(), warden.getY() + 3.0, warden.getZ(), 3, 0.4, 0.2, 0.4, 1.0);
            return;
        }
        if (warden.tickCount % 20 == 0) {
            warden.increaseAngerAt(p, 100, false);
        }
    }

    public static void register() {
        ServerLivingEntityEvents.AFTER_DAMAGE.register((victim, source, base, taken, blocked) -> {
            if (source.getEntity() instanceof Player player && victim.level() instanceof ServerLevel level
                    && (victim instanceof SingerEntity || victim instanceof EchoGolemEntity
                    || victim instanceof SiftWardenEntity w && isGuard(w))) {
                rouseNear(level, victim.position(), player, HURT_RANGE);
            }
        });
        UseBlockCallback.EVENT.register((player, level, hand, hit) -> {
            if (level instanceof ServerLevel server && !player.isShiftKeyDown()) {
                Block block = level.getBlockState(hit.getBlockPos()).getBlock();
                if (block instanceof ChestBlock || block instanceof BarrelBlock) {
                    rouseNear(server, Vec3.atCenterOf(hit.getBlockPos()), player, CHEST_RANGE);
                }
            }
            return InteractionResult.PASS;
        });
        PlayerBlockBreakEvents.AFTER.register((level, player, pos, state, blockEntity) -> {
            Block b = state.getBlock();
            if (level instanceof ServerLevel server && (b == ModBlocks.ECHO_CRADLE || b == Blocks.NOTE_BLOCK
                    || b == ModProgression.CHAROITE_CLUSTER || isSoulCrystal(b))) {
                rouseNear(server, Vec3.atCenterOf(pos), player, BREAK_RANGE);
            }
        });
    }

    private static boolean isSoulCrystal(Block b) {
        return net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(b).getPath().equals("soul_crystal_block");
    }
}
