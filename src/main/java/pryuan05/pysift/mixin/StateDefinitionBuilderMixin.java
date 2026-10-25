package pryuan05.pysift.mixin;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.Property;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import pryuan05.pysift.fluid.SpiritLogging;

import java.util.Map;

/** 含靈液：方塊的狀態表建立前，凡是有 waterlogged 屬性的方塊都多加 spiritlogged（見 {@link SpiritLogging}）。 */
@Mixin(StateDefinition.Builder.class)
public abstract class StateDefinitionBuilderMixin<O, S> {
    @Shadow @Final private O owner;
    @Shadow @Final private Map<String, Property<?>> properties;

    @Inject(method = "create", at = @At("HEAD"))
    private void pysift$addSpiritlogged(CallbackInfoReturnable<StateDefinition<O, ?>> cir) {
        if (this.owner instanceof Block
                && this.properties.get(BlockStateProperties.WATERLOGGED.getName()) == BlockStateProperties.WATERLOGGED
                && !this.properties.containsKey(SpiritLogging.SPIRITLOGGED.getName())) {
            this.properties.put(SpiritLogging.SPIRITLOGGED.getName(), SpiritLogging.SPIRITLOGGED);
        }
    }
}
