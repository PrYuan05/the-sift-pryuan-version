package pryuan05.pysift.client.mixin;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pryuan05.pysift.client.WeaponPoses;

/** 第三人稱：Boss 武器使用中的自訂手臂姿勢（{@link WeaponPoses}），在原版姿勢算完後覆蓋。 */
@Mixin(HumanoidModel.class)
public class HumanoidModelMixin {
    @Inject(method = "setupAnim(Lnet/minecraft/client/renderer/entity/state/HumanoidRenderState;)V", at = @At("TAIL"))
    private void pysift$weaponPose(HumanoidRenderState state, CallbackInfo ci) {
        WeaponPoses.thirdPerson((HumanoidModel<?>) (Object) this, state, ((pryuan05.pysift.client.EntityIdRenderState) state).pysift$entityId());
    }
}
