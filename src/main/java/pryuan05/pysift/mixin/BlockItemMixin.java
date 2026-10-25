package pryuan05.pysift.mixin;

import com.llamalad7.mixinextras.injector.ModifyReturnValue;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.material.FluidState;
import org.jspecify.annotations.Nullable;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import pryuan05.pysift.fluid.ModFluids;
import pryuan05.pysift.fluid.SpiritLogging;

/** 含靈液：在靈液源頭裡放可含水的方塊（台階、樓梯、柵欄…）時，方塊直接含靈液，就像在水裡放會含水一樣。 */
@Mixin(BlockItem.class)
public abstract class BlockItemMixin {
    @ModifyReturnValue(method = "getPlacementState", at = @At("RETURN"))
    private @Nullable BlockState pysift$placeInSpirit(@Nullable BlockState state, BlockPlaceContext context) {
        if (state == null || !SpiritLogging.supports(state)
                || (state.hasProperty(BlockStateProperties.WATERLOGGED) && state.getValue(BlockStateProperties.WATERLOGGED))) {
            return state;
        }
        FluidState fluid = context.getLevel().getFluidState(context.getClickedPos());
        return fluid.isSource() && ModFluids.SPIRIT_LIQUID.isSame(fluid.getType())
                ? state.setValue(SpiritLogging.SPIRITLOGGED, true) : state;
    }
}
