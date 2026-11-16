package pryuan05.pysift.client.mixin;

import net.minecraft.client.Minecraft;
import net.minecraft.sounds.Music;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import pryuan05.pysift.client.BossMusic;

/** Boss 附近時，背景音樂換成 Boss 戰音樂（比照原版終界龍戰的做法）。 */
@Mixin(Minecraft.class)
public class MinecraftMusicMixin {
    @Inject(method = "getSituationalMusic", at = @At("HEAD"), cancellable = true)
    private void pysift$bossMusic(CallbackInfoReturnable<Music> cir) {
        Music boss = BossMusic.pick((Minecraft) (Object) this);
        if (boss != null) {
            cir.setReturnValue(boss);
        }
    }
}
