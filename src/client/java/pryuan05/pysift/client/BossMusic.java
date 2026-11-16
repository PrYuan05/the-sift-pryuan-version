package pryuan05.pysift.client;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.sounds.Music;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.entity.LivingEntity;
import pryuan05.pysift.entity.mob.HarmonizerEntity;
import pryuan05.pysift.entity.mob.MonarchEntity;
import pryuan05.pysift.entity.mob.SculkMonstrosityEntity;
import pryuan05.pysift.sound.ModSounds;

import java.util.Comparator;

/**
 * Boss 戰音樂（tools/audio/music.py 合成）：玩家 48 格內有活著的調和者、君王（不含鏡像）或幽匿巨怪時，
 * 背景音樂換成那隻 Boss 的曲子（MinecraftMusicMixin）；Boss 不見了就立刻停掉。
 */
public final class BossMusic {
    private static final double RANGE = 48.0;
    private static Music playing;

    private BossMusic() {
    }

    private static Music music(SoundEvent event) {
        return new Music(BuiltInRegistries.SOUND_EVENT.wrapAsHolder(event), 0, 0, true);
    }

    private static final Music HARMONIZER = music(ModSounds.MUSIC_BOSS_HARMONIZER);
    private static final Music MONARCH = music(ModSounds.MUSIC_BOSS_MONARCH);
    private static final Music SCULK_MONSTROSITY = music(ModSounds.MUSIC_BOSS_SCULK_MONSTROSITY);

    /** 附近 Boss 的音樂；沒有 Boss 回傳 null。 */
    public static Music pick(Minecraft mc) {
        if (mc.player == null || mc.level == null) {
            return null;
        }
        LivingEntity boss = mc.level.getEntitiesOfClass(LivingEntity.class, mc.player.getBoundingBox().inflate(RANGE), BossMusic::isBoss)
                .stream().min(Comparator.comparingDouble(e -> e.distanceToSqr(mc.player))).orElse(null);
        if (boss instanceof HarmonizerEntity) {
            return HARMONIZER;
        }
        if (boss instanceof MonarchEntity) {
            return MONARCH;
        }
        if (boss instanceof SculkMonstrosityEntity) {
            return SCULK_MONSTROSITY;
        }
        return null;
    }

    private static boolean isBoss(LivingEntity e) {
        if (!e.isAlive()) {
            return false;
        }
        if (e instanceof MonarchEntity m) {
            return !m.isEcho();
        }
        return e instanceof HarmonizerEntity || e instanceof SculkMonstrosityEntity;
    }

    public static void register() {
        ClientTickEvents.END_CLIENT_TICK.register(mc -> {
            Music now = pick(mc);
            if (playing != null && now != playing) {
                mc.getMusicManager().stopPlaying(playing);   // Boss 死了或離開：Boss 曲立刻停，換回生態域音樂
            }
            playing = now;
        });
    }
}
