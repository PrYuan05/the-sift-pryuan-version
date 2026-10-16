package pryuan05.pysift.client.mixin;

import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pryuan05.pysift.client.SoulFireRenderState;
import pryuan05.pysift.effect.SoulBurn;

/**
 * 靈魂火灼燒中的實體（同步的 SoulBurn.FIRE 附件）：強制顯示身上的火焰，並標記為靈魂火。
 * 實體真的沒有著火，所以不會受到一般火焰傷害，水也澆不熄。
 */
@Mixin(EntityRenderer.class)
public abstract class EntityRendererMixin {
    @Inject(method = "extractRenderState", at = @At("TAIL"))
    private void pysift$soulFire(Entity entity, EntityRenderState state, float partialTick, CallbackInfo ci) {
        boolean soul = entity.getAttachedOrElse(SoulBurn.FIRE, false) && !entity.isSpectator();
        ((SoulFireRenderState) state).pysift$setSoulFire(soul);
        if (soul) {
            state.displayFireAnimation = true;
        }
    }
}
