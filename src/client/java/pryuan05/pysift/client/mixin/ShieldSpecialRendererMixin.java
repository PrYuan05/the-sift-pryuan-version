package pryuan05.pysift.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.special.ShieldSpecialRenderer;
import net.minecraft.core.component.DataComponentMap;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pryuan05.pysift.block.SiftColors;
import pryuan05.pysift.client.SiftBannerTint;

/** 盾牌上的篩靈色旗幟：有 pysift:base_color 時，底層用那個顏色畫（手持、格擋、物品欄都走這裡）。 */
@Mixin(ShieldSpecialRenderer.class)
public abstract class ShieldSpecialRendererMixin {
    @Inject(method = "submit(Lnet/minecraft/core/component/DataComponentMap;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;IIZI)V",
            at = @At("HEAD"))
    private void pysift$begin(DataComponentMap components, PoseStack pose, SubmitNodeCollector collector, int light, int overlay,
                              boolean foil, int outline, CallbackInfo ci) {
        SiftColors.SiftColor color = components == null ? null : components.get(SiftColors.BASE_COLOR);
        SiftBannerTint.begin(color == null ? -1 : color.rgb);
    }

    @Inject(method = "submit(Lnet/minecraft/core/component/DataComponentMap;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;IIZI)V",
            at = @At("RETURN"))
    private void pysift$end(DataComponentMap components, PoseStack pose, SubmitNodeCollector collector, int light, int overlay,
                            boolean foil, int outline, CallbackInfo ci) {
        SiftBannerTint.end();
    }
}
