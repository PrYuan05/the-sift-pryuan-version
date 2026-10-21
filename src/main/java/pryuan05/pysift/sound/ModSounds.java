package pryuan05.pysift.sound;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.sounds.SoundEvent;
import pryuan05.pysift.PySift;

public class ModSounds {
    public static final SoundEvent BLUB_IDLE = register("entity.blub.idle");
    public static final SoundEvent BLUB_CARAPACE_IDLE = register("entity.blub.carapace_idle");
    public static final SoundEvent BLUB_MEADOWS_IDLE = register("entity.blub.meadows_idle");
    public static final SoundEvent BLUB_RAVINES_IDLE = register("entity.blub.ravines_idle");
    public static final SoundEvent BLUB_FUNGAL_IDLE = register("entity.blub.fungal_idle");
    public static final SoundEvent BLUB_JUMP = register("entity.blub.jump");
    public static final SoundEvent BLUB_LAND = register("entity.blub.land");
    public static final SoundEvent BLUB_STEP = register("entity.blub.step");

    private static SoundEvent register(String id) {
        return Registry.register(BuiltInRegistries.SOUND_EVENT, PySift.id(id), SoundEvent.createVariableRangeEvent(PySift.id(id)));
    }

    public static void register() {
        PySift.LOGGER.info("Registering sounds for {}", PySift.MOD_ID);
    }
}
