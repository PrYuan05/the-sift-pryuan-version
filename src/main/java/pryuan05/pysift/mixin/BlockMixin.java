package pryuan05.pysift.mixin;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;
import pryuan05.pysift.fluid.SpiritLogging;

/**
 * 含靈液：預設狀態一律 spiritlogged=false。各方塊通常用 stateDefinition.any() 再設自己的屬性，
 * 而 any() 取的是每個屬性的第一個值（布林是 true），不改的話所有可含水方塊預設都會含靈液。
 */
@Mixin(Block.class)
public abstract class BlockMixin {
    @ModifyVariable(method = "registerDefaultState", at = @At("HEAD"), argsOnly = true)
    private BlockState pysift$notSpiritlogged(BlockState state) {
        return SpiritLogging.supports(state) ? state.setValue(SpiritLogging.SPIRITLOGGED, false) : state;
    }
}
