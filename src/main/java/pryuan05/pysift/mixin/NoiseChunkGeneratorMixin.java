package pryuan05.pysift.mixin;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Aquifer;
import net.minecraft.world.level.levelgen.NoiseBasedChunkGenerator;
import net.minecraft.world.level.levelgen.NoiseGeneratorSettings;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import pryuan05.pysift.PySift;

/**
 * 隙浮的地底沒有岩漿：原版把 y -54 以下的全域流體寫死成岩漿（{@code createFluidPicker}），
 * 這裡在預設流體是靈液的維度（the_sift）把它換成靈液，最深的洞穴底部因此是靈液湖而不是岩漿海。
 * 其他維度完全不受影響。
 */
@Mixin(NoiseBasedChunkGenerator.class)
public abstract class NoiseChunkGeneratorMixin {
    @Inject(method = "createFluidPicker", at = @At("RETURN"), cancellable = true)
    private static void pysift$spiritInsteadOfLava(NoiseGeneratorSettings settings, CallbackInfoReturnable<Aquifer.FluidPicker> cir) {
        BlockState spirit = settings.defaultFluid();
        if (!BuiltInRegistries.BLOCK.getKey(spirit.getBlock()).equals(PySift.id("spirit_liquid"))) {
            return;
        }
        Aquifer.FluidPicker original = cir.getReturnValue();
        cir.setReturnValue((x, y, z) -> {
            Aquifer.FluidStatus status = original.computeFluid(x, y, z);
            return status.fluidType().is(Blocks.LAVA) ? new Aquifer.FluidStatus(status.fluidLevel(), spirit) : status;
        });
    }
}
