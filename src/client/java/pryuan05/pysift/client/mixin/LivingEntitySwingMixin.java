package pryuan05.pysift.client.mixin;

import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.component.SwingAnimation;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import pryuan05.pysift.client.WeaponPoses;

/** 客戶端：記下每個實體揮了幾次（重錘的左錘、右錘輪流交替，WeaponPoses）。 */
@Mixin(LivingEntity.class)
public class LivingEntitySwingMixin {
    @Inject(method = "swing(Lnet/minecraft/world/InteractionHand;Lnet/minecraft/world/item/component/SwingAnimation;Z)Z", at = @At("RETURN"))
    private void pysift$countSwing(InteractionHand hand, SwingAnimation animation, boolean force, CallbackInfoReturnable<Boolean> cir) {
        LivingEntity self = (LivingEntity) (Object) this;
        if (cir.getReturnValue() && self.level().isClientSide()) {
            WeaponPoses.onSwing(self.getId());
        }
    }
}
