package pryuan05.pysift.sound;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.sounds.SoundEvent;
import pryuan05.pysift.PySift;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

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
    // 用免費素材（sound_sources/）加工的生物音效，見 tools/audio/build_sounds.py 與 assets/pysift/sounds/CREDITS.md
    public static final SoundEvent NUZZLE_AMBIENT = register("entity.nuzzle.ambient");
    public static final SoundEvent NUZZLE_NUZZLE = register("entity.nuzzle.nuzzle");
    public static final SoundEvent NUZZLE_HURT = register("entity.nuzzle.hurt");
    public static final SoundEvent NUZZLE_DEATH = register("entity.nuzzle.death");
    public static final SoundEvent SLABBER_AMBIENT = register("entity.slabber.ambient");
    public static final SoundEvent SLABBER_HURT = register("entity.slabber.hurt");
    public static final SoundEvent SLABBER_DEATH = register("entity.slabber.death");
    public static final SoundEvent SLABBER_EAT = register("entity.slabber.eat");
    public static final SoundEvent ECHO_GOLEM_AMBIENT = register("entity.echo_golem.ambient");
    public static final SoundEvent ECHO_GOLEM_STEP = register("entity.echo_golem.step");
    public static final SoundEvent ECHO_GOLEM_HURT = register("entity.echo_golem.hurt");
    public static final SoundEvent ECHO_GOLEM_DEATH = register("entity.echo_golem.death");
    public static final SoundEvent ECHO_GOLEM_WORK = register("entity.echo_golem.work");   // 挖地、放下唱片盒
    public static final SoundEvent ECHO_GOLEM_GIFT = register("entity.echo_golem.gift");   // 送東西、立約、長回晶塊
    // 完全合成的生物音效
    public static final SoundEvent TUNER_AMBIENT = register("entity.tuner.ambient");
    public static final SoundEvent TUNER_AURA = register("entity.tuner.aura");
    public static final SoundEvent TUNER_HURT = register("entity.tuner.hurt");
    public static final SoundEvent TUNER_DEATH = register("entity.tuner.death");
    public static final SoundEvent FUSEFLY_AMBIENT = register("entity.fusefly.ambient");
    public static final SoundEvent FUSEFLY_HURT = register("entity.fusefly.hurt");
    public static final SoundEvent FUSEFLY_DEATH = register("entity.fusefly.death");
    public static final SoundEvent FUSEFLY_FUSE = register("entity.fusefly.fuse");
    public static final SoundEvent HARMONIZER_AMBIENT = register("entity.harmonizer.ambient");
    public static final SoundEvent HARMONIZER_HURT = register("entity.harmonizer.hurt");
    public static final SoundEvent HARMONIZER_DEATH = register("entity.harmonizer.death");
    public static final SoundEvent HARMONIZER_ROAR = register("entity.harmonizer.roar");
    public static final SoundEvent HARMONIZER_CONE = register("entity.harmonizer.cone");
    public static final SoundEvent HARMONIZER_RESONANCE = register("entity.harmonizer.resonance");
    public static final SoundEvent HARMONIZER_VORTEX = register("entity.harmonizer.vortex");
    public static final SoundEvent HARMONIZER_SLAM = register("entity.harmonizer.slam");
    public static final SoundEvent HARMONIZER_GRAB = register("entity.harmonizer.grab");

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

    /**
     * 用 Pixabay 素材加工的生物聲音（tools/audio/creatures.py）：不逐一寫常數，啟動時從 sounds.json 找出
     * entity.&lt;生物&gt;.&lt;種類&gt; 全部註冊。種類 = ambient／hurt／death，或技能動畫的名稱（動畫開始時自動播放，
     * 見 PysiftGeoEntity），或程式另外呼叫的動作（PysiftGeoEntity.voice）。
     */
    public static final Set<String> VOICED_MOBS = Set.of("pollinator", "roamroot", "bloombud", "sentinel", "stalker", "hunter",
            "trapper", "dartback", "prickle", "nester", "seedling", "sprout", "scavenger", "hurler", "wobble", "lootkin", "monarch",
            "sculk_monstrosity");
    private static final Map<String, SoundEvent> VOICES = new HashMap<>();
    // Boss 戰音樂（tools/audio/music.py；client/BossMusic 在 Boss 附近播放）
    public static final SoundEvent MUSIC_BOSS_HARMONIZER = register("music.boss.harmonizer");
    public static final SoundEvent MUSIC_BOSS_MONARCH = register("music.boss.monarch");
    public static final SoundEvent MUSIC_BOSS_SCULK_MONSTROSITY = register("music.boss.sculk_monstrosity");

    static {
        try (InputStream in = ModSounds.class.getResourceAsStream("/assets/pysift/sounds.json")) {
            com.google.gson.JsonObject json = com.google.gson.JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            for (String id : json.keySet()) {
                String[] parts = id.split("\\.");
                if (parts.length == 3 && parts[0].equals("entity") && VOICED_MOBS.contains(parts[1])) {
                    VOICES.put(parts[1] + "." + parts[2], register(id));
                }
            }
        } catch (Exception e) {
            throw new IllegalStateException("cannot read pysift sounds.json", e);
        }
    }

    /** 生物 mob 的 kind 聲音；沒有就回傳 null。 */
    public static SoundEvent voice(String mob, String kind) {
        return VOICES.get(mob + "." + kind);
    }

    /** 已註冊的生物聲音數（啟動檢查用）。 */
    public static int voiceCount() {
        return VOICES.size();
    }

    private static SoundEvent register(String id) {
        return Registry.register(BuiltInRegistries.SOUND_EVENT, PySift.id(id), SoundEvent.createVariableRangeEvent(PySift.id(id)));
    }

    public static void register() {
        PySift.LOGGER.info("Registering sounds for {} ({} creature voices)", PySift.MOD_ID, VOICES.size());
    }
}
