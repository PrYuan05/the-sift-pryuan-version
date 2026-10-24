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

    /**
     * The Sift 各生態域的背景音樂與環境音（music.the_sift.&lt;生態域&gt;、ambient.the_sift.&lt;生態域&gt;.loop／mood／additions），
     * 由生態域 JSON 的 audio attributes 引用；sounds.json 目前指向原版音樂與環境音（tools/worldgen/build_sift_audio.py）。
     */
    public static final List<String> SIFT_BIOMES = List.of("willow_grove", "crimson_strata_canyon", "violet_slate_abyss", "amber_dunes", "red_zone_caves");

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
