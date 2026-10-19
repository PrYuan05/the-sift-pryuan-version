package pryuan05.pysift.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FlowingFluid;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import pryuan05.pysift.fluid.SpiritInteractions;

/** 靈液與岩漿、水相遇的結果（見 SpiritInteractions）；原版會把靈液當成水，變出黑曜石／鵝卵石。 */
@Mixin(LiquidBlock.class)
public abstract class LiquidBlockMixin {
    @Shadow
    @Final
    protected FlowingFluid fluid;

    @Inject(method = "shouldSpreadLiquid", at = @At("HEAD"), cancellable = true)
    private void pysift$spiritInteractions(Level level, BlockPos pos, BlockState state, CallbackInfoReturnable<Boolean> cir) {
        if (this.fluid.is(FluidTags.LAVA)) {
            if (SpiritInteractions.solidifyLava(level, pos, LiquidBlock.POSSIBLE_FLOW_DIRECTIONS)) {
                cir.setReturnValue(false);
            }
        } else if (SpiritInteractions.isSpirit(level.getFluidState(pos))) {
            if (SpiritInteractions.crystallizeSpirit(level, pos)) {
                cir.setReturnValue(false);
            }
        }
    }
}
