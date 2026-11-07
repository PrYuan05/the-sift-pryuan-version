package pryuan05.pysift.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.redstone.Orientation;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pryuan05.pysift.block.AutoConnect;

/**
 * Automatic neighbour detection for pysift walls, fences, panes, stairs and spirit pipes ({@link AutoConnect}),
 * hooked on the state-level methods so it runs however the block was placed and whatever the block class overrides.
 */
@Mixin(BlockBehaviour.BlockStateBase.class)
public abstract class AutoConnectMixin {
    @Inject(method = "onPlace", at = @At("TAIL"))
    private void pysift$autoConnectPlaced(Level level, BlockPos pos, BlockState oldState, boolean movedByPiston, CallbackInfo ci) {
        BlockState self = (BlockState) (Object) this;
        if (!level.isClientSide() && !oldState.is(self.getBlock()) && AutoConnect.isConnecting(self.getBlock())) {
            AutoConnect.placed(level, pos);
        }
    }

    @Inject(method = "handleNeighborChanged", at = @At("TAIL"))
    private void pysift$autoConnectChanged(Level level, BlockPos pos, Block neighbor, Orientation orientation, boolean movedByPiston,
                                           CallbackInfo ci) {
        BlockState self = (BlockState) (Object) this;
        if (!level.isClientSide() && AutoConnect.isConnecting(self.getBlock())) {
            AutoConnect.changed(level, pos);
        }
    }
}
