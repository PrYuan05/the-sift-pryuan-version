package pryuan05.pysift.mixin;

import com.llamalad7.mixinextras.injector.ModifyReturnValue;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.material.FluidState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import pryuan05.pysift.fluid.ModFluids;
import pryuan05.pysift.fluid.SpiritLogging;

/**
 * 含靈液的狀態：
 * <ul>
 *   <li>getFluidState 回傳靈液源頭（每個狀態建立時算好一個布林，getFluidState 只多讀一個欄位）。</li>
 *   <li>updateShape：像含水方塊排程水的 tick 一樣排程靈液 tick（鄰居改變時才會往外流）；
 *       方塊自己的 updateShape 若用預設狀態重建（會掉屬性），把 spiritlogged 補回去。</li>
 * </ul>
 */
@Mixin(BlockBehaviour.BlockStateBase.class)
public abstract class BlockStateBaseMixin {
    @Unique private boolean pysift$spirit;

    @Inject(method = "<init>", at = @At("TAIL"))
    private void pysift$cacheSpirit(CallbackInfo ci) {
        this.pysift$spirit = SpiritLogging.isSpiritlogged((BlockState) (Object) this);
    }

    @ModifyReturnValue(method = "getFluidState", at = @At("RETURN"))
    private FluidState pysift$spiritFluid(FluidState original) {
        return this.pysift$spirit ? SpiritLogging.source() : original;
    }

    @Inject(method = "updateShape", at = @At("HEAD"))
    private void pysift$tickSpirit(LevelReader level, ScheduledTickAccess ticks, BlockPos pos, Direction direction,
                                   BlockPos neighborPos, BlockState neighborState, RandomSource random, CallbackInfoReturnable<BlockState> cir) {
        if (this.pysift$spirit) {
            ticks.scheduleTick(pos, ModFluids.SPIRIT_LIQUID, ModFluids.SPIRIT_LIQUID.getTickDelay(level));
        }
    }

    @ModifyReturnValue(method = "updateShape", at = @At("RETURN"))
    private BlockState pysift$keepSpirit(BlockState result) {
        if (this.pysift$spirit && result != (Object) this && SpiritLogging.supports(result) && !result.getValue(SpiritLogging.SPIRITLOGGED)
                && !(result.hasProperty(BlockStateProperties.WATERLOGGED) && result.getValue(BlockStateProperties.WATERLOGGED))) {
            return result.setValue(SpiritLogging.SPIRITLOGGED, true);
        }
        return result;
    }
}
