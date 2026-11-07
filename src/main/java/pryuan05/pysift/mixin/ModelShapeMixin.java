package pryuan05.pysift.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import pryuan05.pysift.block.ModelShapes;

/**
 * Blocks with their own models get the shape of that model (block/ModelShapes, from
 * tools/models/build_block_shapes.py). Collision (when the block has any), occlusion and the support shape are all
 * derived from getShape by vanilla, so they follow too.
 */
@Mixin(BlockBehaviour.BlockStateBase.class)
public abstract class ModelShapeMixin {
    @Inject(method = "getShape(Lnet/minecraft/world/level/BlockGetter;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/phys/shapes/CollisionContext;)Lnet/minecraft/world/phys/shapes/VoxelShape;",
            at = @At("HEAD"), cancellable = true)
    private void pysift$modelShape(BlockGetter level, BlockPos pos, CollisionContext context, CallbackInfoReturnable<VoxelShape> cir) {
        VoxelShape shape = ModelShapes.get((BlockState) (Object) this);
        if (shape != null) {
            cir.setReturnValue(shape);
        }
    }
}
