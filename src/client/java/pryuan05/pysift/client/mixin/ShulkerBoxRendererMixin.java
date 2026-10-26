package pryuan05.pysift.client.mixin;

import net.minecraft.client.renderer.Sheets;
import net.minecraft.client.renderer.blockentity.ShulkerBoxRenderer;
import net.minecraft.client.renderer.blockentity.state.ShulkerBoxRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.resources.model.sprite.SpriteId;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.level.block.entity.ShulkerBoxBlockEntity;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import pryuan05.pysift.block.SiftColors;
import pryuan05.pysift.client.SiftShulkerSprites;

/** 篩靈界顏色的界伏殼貼圖（見 {@link SiftShulkerSprites}）。 */
@Mixin(ShulkerBoxRenderer.class)
public abstract class ShulkerBoxRendererMixin {
    @Inject(method = "extractRenderState(Lnet/minecraft/world/level/block/entity/ShulkerBoxBlockEntity;Lnet/minecraft/client/renderer/blockentity/state/ShulkerBoxRenderState;FLnet/minecraft/world/phys/Vec3;Lnet/minecraft/client/renderer/feature/ModelFeatureRenderer$CrumblingOverlay;)V",
            at = @At("TAIL"))
    private void pysift$siftSprite(ShulkerBoxBlockEntity box, ShulkerBoxRenderState state, float partialTick, Vec3 camera,
                                   ModelFeatureRenderer.CrumblingOverlay crumbling, CallbackInfo ci) {
        SiftColors.SiftColor color = SiftColors.SHULKER_COLORS.get(box.getBlockState().getBlock());
        ((SiftShulkerSprites.State) state).pysift$setSiftSprite(color == null ? null : SiftShulkerSprites.sprite(color));
    }

    @WrapOperation(method = "submit(Lnet/minecraft/client/renderer/blockentity/state/ShulkerBoxRenderState;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;Lnet/minecraft/client/renderer/state/level/CameraRenderState;)V",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/client/renderer/Sheets;getShulkerBoxSprite(Lnet/minecraft/world/item/DyeColor;)Lnet/minecraft/client/resources/model/sprite/SpriteId;"))
    private SpriteId pysift$sprite(DyeColor color, Operation<SpriteId> original, ShulkerBoxRenderState state) {
        SpriteId sift = ((SiftShulkerSprites.State) state).pysift$siftSprite();
        return sift != null ? sift : original.call(color);
    }
}
