package pryuan05.pysift.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.Model;
import net.minecraft.client.renderer.OrderedSubmitNodeCollector;
import net.minecraft.client.renderer.Sheets;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BannerRenderer;
import net.minecraft.client.renderer.blockentity.state.BannerRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.resources.model.sprite.SpriteGetter;
import net.minecraft.client.resources.model.sprite.SpriteId;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.level.block.entity.BannerBlockEntity;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pryuan05.pysift.block.SiftColors;
import pryuan05.pysift.client.SiftBannerTint;

/** 篩靈界顏色旗幟的底色（見 {@link SiftBannerTint}）。 */
@Mixin(BannerRenderer.class)
public abstract class BannerRendererMixin {
    @Inject(method = "extractRenderState(Lnet/minecraft/world/level/block/entity/BannerBlockEntity;Lnet/minecraft/client/renderer/blockentity/state/BannerRenderState;FLnet/minecraft/world/phys/Vec3;Lnet/minecraft/client/renderer/feature/ModelFeatureRenderer$CrumblingOverlay;)V",
            at = @At("TAIL"))
    private void pysift$siftTint(BannerBlockEntity banner, BannerRenderState state, float partialTick, Vec3 camera,
                                 ModelFeatureRenderer.CrumblingOverlay crumbling, CallbackInfo ci) {
        SiftColors.SiftColor color = SiftColors.BANNER_COLORS.get(banner.getBlockState().getBlock());
        ((SiftBannerTint.State) state).pysift$setSiftTint(color == null ? -1 : color.rgb);
    }

    @Inject(method = "submit(Lnet/minecraft/client/renderer/blockentity/state/BannerRenderState;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;Lnet/minecraft/client/renderer/state/level/CameraRenderState;)V",
            at = @At("HEAD"))
    private void pysift$begin(BannerRenderState state, PoseStack pose, SubmitNodeCollector collector, CameraRenderState camera, CallbackInfo ci) {
        SiftBannerTint.begin(((SiftBannerTint.State) state).pysift$siftTint());
    }

    @Inject(method = "submit(Lnet/minecraft/client/renderer/blockentity/state/BannerRenderState;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;Lnet/minecraft/client/renderer/state/level/CameraRenderState;)V",
            at = @At("RETURN"))
    private void pysift$end(BannerRenderState state, PoseStack pose, SubmitNodeCollector collector, CameraRenderState camera, CallbackInfo ci) {
        SiftBannerTint.end();
    }

    @Inject(method = "submitPatternLayer", at = @At("HEAD"))
    private static void pysift$layer(SpriteGetter sprites, PoseStack pose, OrderedSubmitNodeCollector collector, int light, int overlay,
                                     Model<?> model, Object modelState, SpriteId sprite, DyeColor color, CallbackInfo ci) {
        SiftBannerTint.layer(sprite == Sheets.BANNER_PATTERN_BASE || sprite == Sheets.SHIELD_PATTERN_BASE);
    }

    @Redirect(method = "submitPatternLayer", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/item/DyeColor;getTextureDiffuseColor()I"))
    private static int pysift$baseColor(DyeColor color) {
        return SiftBannerTint.baseColor(color);
    }
}
