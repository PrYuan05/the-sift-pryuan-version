package pryuan05.pysift.client.mixin;

import com.llamalad7.mixinextras.injector.ModifyExpressionValue;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import net.minecraft.client.renderer.ScreenEffectRenderer;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.resources.model.sprite.SpriteGetter;
import net.minecraft.client.resources.model.sprite.SpriteId;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import pryuan05.pysift.client.SoulFireRenderState;

/** 第一人稱：自己燒著靈魂火時，螢幕下方也顯示火焰，並改用原版 soul_fire_1。 */
@Mixin(ScreenEffectRenderer.class)
public abstract class ScreenEffectRendererMixin {
    @ModifyExpressionValue(method = "submit", at = @At(value = "FIELD",
            target = "Lnet/minecraft/client/renderer/state/level/PlayerRenderState;isOnFire:Z"))
    private boolean pysift$showSoulFire(boolean onFire) {
        return onFire || SoulFireRenderState.localPlayerOnSoulFire();
    }

    @WrapOperation(method = "submit", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/resources/model/sprite/SpriteGetter;get(Lnet/minecraft/client/resources/model/sprite/SpriteId;)Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;"))
    private TextureAtlasSprite pysift$soulFireSprite(SpriteGetter sprites, SpriteId id, Operation<TextureAtlasSprite> original) {
        return original.call(sprites, SoulFireRenderState.localPlayerOnSoulFire() ? SoulFireRenderState.SOUL_FIRE_1 : id);
    }
}
