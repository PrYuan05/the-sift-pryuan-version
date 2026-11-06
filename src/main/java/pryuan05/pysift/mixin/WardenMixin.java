package pryuan05.pysift.mixin;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.monster.warden.Warden;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import pryuan05.pysift.entity.WardenSoothing;

/** 被歌者安撫的監守者不會生氣、不會鎖定目標（{@link WardenSoothing}）。 */
@Mixin(Warden.class)
public abstract class WardenMixin {
    @Inject(method = "increaseAngerAt(Lnet/minecraft/world/entity/Entity;IZ)V", at = @At("HEAD"), cancellable = true)
    private void pysift$soothedNoAnger(Entity entity, int amount, boolean playSound, CallbackInfo ci) {
        if (WardenSoothing.isSoothed((Warden) (Object) this)) {
            ci.cancel();
        }
    }

    /** 隙浮守衛不會讓周圍陷入黑暗。 */
    @Inject(method = "applyDarknessAround", at = @At("HEAD"), cancellable = true)
    private static void pysift$noDarknessFromSiftWarden(net.minecraft.server.level.ServerLevel level, net.minecraft.world.phys.Vec3 pos,
                                                         Entity source, int radius, CallbackInfo ci) {
        if (source instanceof pryuan05.pysift.entity.mob.SiftWardenEntity) {
            ci.cancel();
        }
    }

    @Inject(method = "canTargetEntity", at = @At("HEAD"), cancellable = true)
    private void pysift$soothedNoTarget(Entity entity, CallbackInfoReturnable<Boolean> cir) {
        if (WardenSoothing.isSoothed((Warden) (Object) this)) {
            cir.setReturnValue(false);
        }
    }
}
