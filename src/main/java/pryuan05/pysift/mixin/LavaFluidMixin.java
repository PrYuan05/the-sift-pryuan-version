package pryuan05.pysift.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.LavaFluid;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pryuan05.pysift.fluid.SpiritInteractions;

/** 岩漿往下流進靈液：變成虛空石（原版把靈液當水，會變石頭）。 */
@Mixin(LavaFluid.class)
public abstract class LavaFluidMixin {
    @Inject(method = "spreadTo", at = @At("HEAD"), cancellable = true)
    private void pysift$intoSpirit(LevelAccessor level, BlockPos pos, BlockState state, Direction direction, FluidState fluidState,
                                   CallbackInfo ci) {
        if (direction == Direction.DOWN && SpiritInteractions.lavaFlowsDownIntoSpirit(level, pos)) {
            ci.cancel();
        }
    }
}
