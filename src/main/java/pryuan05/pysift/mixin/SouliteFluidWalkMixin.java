package pryuan05.pysift.mixin;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import pryuan05.pysift.progression.SouliteGear;

/** 靈髓靴子：穿著時可以站在靈液上（和熾足獸站在岩漿上同一個機制；用戶端與伺服器都會跑，所以移動不會被拉回）。掉進靈液後照常游泳、跳躍。 */
@Mixin(LivingEntity.class)
public abstract class SouliteFluidWalkMixin {
    /** 26.3：站在液體上還需要生物提供「踩在液體上的碰撞形狀」（熾足獸也有），玩家預設是空的。哪種液體能踩由 canStandOnFluid 決定。 */
    @Inject(method = "getLiquidCollisionShape", at = @At("HEAD"), cancellable = true)
    private void pysift$liquidFloor(CallbackInfoReturnable<VoxelShape> cir) {
        if (SouliteGear.standsOnLiquid((LivingEntity) (Object) this)) {
            cir.setReturnValue(SouliteGear.LIQUID_FLOOR);
        }
    }

    @Inject(method = "canStandOnFluid", at = @At("HEAD"), cancellable = true)
    private void pysift$walkOnSpiritLiquid(FluidState fluid, CallbackInfoReturnable<Boolean> cir) {
        if (SouliteGear.walksOnSpirit((LivingEntity) (Object) this, fluid)) {
            cir.setReturnValue(true);
        }
    }
}
