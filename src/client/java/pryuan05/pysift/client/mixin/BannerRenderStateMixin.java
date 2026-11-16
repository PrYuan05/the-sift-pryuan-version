package pryuan05.pysift.client.mixin;

import net.minecraft.client.renderer.blockentity.state.BannerRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import pryuan05.pysift.client.SiftBannerTint;

/** 旗幟的 render state 多記一個篩靈界底色（-1 = 原版旗幟）。 */
@Mixin(BannerRenderState.class)
public abstract class BannerRenderStateMixin implements SiftBannerTint.State {
    @Unique
    private int pysift$siftTint = -1;

    @Override
    public int pysift$siftTint() {
        return this.pysift$siftTint;
    }

    @Override
    public void pysift$setSiftTint(int rgb) {
        this.pysift$siftTint = rgb;
    }
}
