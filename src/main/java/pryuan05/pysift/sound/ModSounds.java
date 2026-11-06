package pryuan05.pysift.sound;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.sounds.SoundEvent;
import pryuan05.pysift.PySift;

import java.util.List;

public class ModSounds {
    public static final SoundEvent BLUB_IDLE = register("entity.blub.idle");
    public static final SoundEvent BLUB_CARAPACE_IDLE = register("entity.blub.carapace_idle");
    public static final SoundEvent BLUB_MEADOWS_IDLE = register("entity.blub.meadows_idle");
    public static final SoundEvent BLUB_RAVINES_IDLE = register("entity.blub.ravines_idle");
    public static final SoundEvent BLUB_FUNGAL_IDLE = register("entity.blub.fungal_idle");
    public static final SoundEvent BLUB_JUMP = register("entity.blub.jump");
    public static final SoundEvent BLUB_LAND = register("entity.blub.land");
    public static final SoundEvent BLUB_STEP = register("entity.blub.step");
    // 跟原版狗一樣的一組字幕：受傷、死亡、低吼（有目標時）、嗚咽（受傷的寵物）、趴下；沿用布魯布的音檔，只改音高
    public static final SoundEvent BLUB_HURT = register("entity.blub.hurt");
    public static final SoundEvent BLUB_DEATH = register("entity.blub.death");
    public static final SoundEvent BLUB_GROWL = register("entity.blub.growl");
    public static final SoundEvent BLUB_WHINE = register("entity.blub.whine");
    public static final SoundEvent BLUB_SIT = register("entity.blub.sit");
    // 歌者與哀悼者：程式合成的人聲（tools/audio/build_sounds.py）。VOICE 是一個 F#4 的唱音，用音符盒的音高倍率播放
    public static final SoundEvent SINGER_AMBIENT = register("entity.singer.ambient");
    public static final SoundEvent SINGER_HURT = register("entity.singer.hurt");
    public static final SoundEvent SINGER_DEATH = register("entity.singer.death");
    public static final SoundEvent SINGER_VOICE = register("entity.singer.voice");
    // 歌者對世界與玩家的每個互動各有一段人聲
    public static final SoundEvent SINGER_GREET = register("entity.singer.greet");      // 從地底爬出
    public static final SoundEvent SINGER_BECKON = register("entity.singer.beckon");    // 儀式：招手等迴音碎片
    public static final SoundEvent SINGER_CALL = register("entity.singer.call");        // 回應山羊角
    public static final SoundEvent SINGER_SWEEP = register("entity.singer.sweep");      // 儀式：以歌聲清掃
    public static final SoundEvent SINGER_SUMMON = register("entity.singer.summon");    // 儀式：召喚迴音傀儡
    public static final SoundEvent SINGER_GASP = register("entity.singer.gasp");        // 儀式走調
    public static final SoundEvent SINGER_CHEER = register("entity.singer.cheer");      // 開門慶祝
    public static final SoundEvent SINGER_GIGGLE = register("entity.singer.giggle");    // 抱小傀儡玩
    public static final SoundEvent SINGER_THANKS = register("entity.singer.thanks");    // 收到靈魂晶塊
    public static final SoundEvent SINGER_UNEASE = register("entity.singer.unease");    // 看見監守者
    public static final SoundEvent SINGER_STARVE = register("entity.singer.starve");    // 快要屍化
    public static final SoundEvent SINGER_HOLLOW = register("entity.singer.hollow");    // 屍化成哀悼者
    public static final SoundEvent SINGER_REBORN = register("entity.singer.reborn");    // 哀悼者被治好、變回歌者
    public static final SoundEvent MOURNER_AMBIENT = register("entity.mourner.ambient");
    public static final SoundEvent MOURNER_HURT = register("entity.mourner.hurt");
    public static final SoundEvent MOURNER_DEATH = register("entity.mourner.death");
    public static final SoundEvent MOURNER_VOICE = register("entity.mourner.voice");
    public static final SoundEvent MOURNER_WAIL = register("entity.mourner.wail");      // 看到玩家、開始哭著唱
    public static final SoundEvent MOURNER_SOOTHE = register("entity.mourner.soothe");  // 泡靈液／聽香爐被安慰
    public static final SoundEvent MOURNER_HUSH = register("entity.mourner.hush");      // 被哀悼號角安撫

    /**
     * The Sift 各生態域的背景音樂與環境音（music.the_sift.&lt;生態域&gt;、ambient.the_sift.&lt;生態域&gt;.loop／mood／additions），
     * 由生態域 JSON 的 audio attributes 引用；sounds.json 目前指向原版音樂與環境音（tools/worldgen/build_sift_audio.py）。
     */
    public static final List<String> SIFT_BIOMES = List.of("willow_grove", "crimson_strata_canyon", "violet_slate_abyss", "amber_dunes", "red_zone_caves", "lullaby_hills",
            "soul_caldera");

    static {
        for (String biome : SIFT_BIOMES) {
            register("music.the_sift." + biome);
            for (String part : List.of("loop", "mood", "additions")) {
                register("ambient.the_sift." + biome + "." + part);
            }
        }
    }

    private static SoundEvent register(String id) {
        return Registry.register(BuiltInRegistries.SOUND_EVENT, PySift.id(id), SoundEvent.createVariableRangeEvent(PySift.id(id)));
    }

    public static void register() {
        PySift.LOGGER.info("Registering sounds for {}", PySift.MOD_ID);
    }
}
