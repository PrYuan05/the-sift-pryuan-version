package pryuan05.pysift.mixin;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.entity.SculkShriekerBlockEntity;
import net.minecraft.world.phys.AABB;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pryuan05.pysift.entity.mob.SingerEntity;

/**
 * 八音儀式進行中（附近 48 格有儀式歌者）時，幽匿尖嘯體不會尖叫，也就不會累積警告、召喚伏守者。
 * 包括一開始吹山羊角的那一下（尖嘯體反應比歌者爬出來慢）；歌者開門後離開，尖嘯體恢復正常。
 */
@Mixin(SculkShriekerBlockEntity.class)
public abstract class RitualQuietShriekerMixin {
    @Inject(method = "tryShriek", at = @At("HEAD"), cancellable = true)
    private void pysift$quietDuringRitual(ServerLevel level, ServerPlayer player, CallbackInfo ci) {
        SculkShriekerBlockEntity self = (SculkShriekerBlockEntity) (Object) this;
        if (!level.getEntitiesOfClass(SingerEntity.class, new AABB(self.getBlockPos()).inflate(48), SingerEntity::isRitual).isEmpty()) {
            ci.cancel();
        }
    }
}
