package pryuan05.pysift.client.mixin;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.feature.FeatureFrameContext;
import net.minecraft.client.renderer.feature.FlameFeatureRenderer;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import pryuan05.pysift.client.SoulFireRenderState;

import java.util.List;

/**
 * 實體身上的火焰（第三人稱）：標記為靈魂火的實體改用原版 soul_fire_0 / soul_fire_1，
 * 形狀、動畫、位置都和原版著火一樣，只換貼圖。
 */
@Mixin(FlameFeatureRenderer.class)
public abstract class FlameFeatureRendererMixin {
    @WrapOperation(method = "buildGroup", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/feature/FlameFeatureRenderer;prepare(Lnet/minecraft/client/renderer/feature/FlameFeatureRenderer$Submit;Lcom/mojang/blaze3d/vertex/VertexConsumer;Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;)V"))
    private void pysift$soulFireSprites(FlameFeatureRenderer self, FlameFeatureRenderer.Submit submit, VertexConsumer consumer,
                                        TextureAtlasSprite fire0, TextureAtlasSprite fire1, Operation<Void> original,
                                        FeatureFrameContext context, List<FlameFeatureRenderer.Submit> submits) {
        if (((SoulFireRenderState) submit.entityRenderState()).pysift$soulFire()) {
            original.call(self, submit, consumer, context.atlasManager().get(SoulFireRenderState.SOUL_FIRE_0),
                    context.atlasManager().get(SoulFireRenderState.SOUL_FIRE_1));
        } else {
            original.call(self, submit, consumer, fire0, fire1);
        }
    }
}
