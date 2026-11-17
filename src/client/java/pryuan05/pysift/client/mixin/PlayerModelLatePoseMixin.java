package pryuan05.pysift.client.mixin;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pryuan05.pysift.client.EntityIdRenderState;
import pryuan05.pysift.client.WeaponPoses;
import pryuan05.pysift.client.compat.AnimCompat;

/**
 * 第三人稱玩家：其他動畫模組（例如 Punchy! Moves）在 PlayerModel.setupAnim 結尾再改一次姿勢，
 * 會把 HumanoidModelMixin 套上的武器姿勢蓋掉。這裡用很高的 mixin 優先度，在它們之後把姿勢套回去。
 * 只在 {@link AnimCompat#latePose()} 時生效（沒有那些模組時仍由 HumanoidModelMixin 處理）。
 */
@Mixin(value = PlayerModel.class, priority = 5000)
public class PlayerModelLatePoseMixin {
    @Inject(method = "setupAnim(Lnet/minecraft/client/renderer/entity/state/AvatarRenderState;)V", at = @At("TAIL"), require = 0)
    private void pysift$latePose(AvatarRenderState state, CallbackInfo ci) {
        if (AnimCompat.latePose()) {
            WeaponPoses.thirdPerson((HumanoidModel<?>) (Object) this, state, ((EntityIdRenderState) state).pysift$entityId());
        }
    }
}
