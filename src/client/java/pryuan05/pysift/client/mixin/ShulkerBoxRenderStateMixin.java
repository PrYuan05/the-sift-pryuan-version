package pryuan05.pysift.client.mixin;

import net.minecraft.client.renderer.blockentity.state.ShulkerBoxRenderState;
import net.minecraft.client.resources.model.sprite.SpriteId;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import pryuan05.pysift.client.SiftShulkerSprites;

/** 界伏殼的 render state 多記一個篩靈界顏色的貼圖（null = 原版界伏殼）。 */
@Mixin(ShulkerBoxRenderState.class)
public abstract class ShulkerBoxRenderStateMixin implements SiftShulkerSprites.State {
    @Unique
    private SpriteId pysift$siftSprite;

    @Override
    public SpriteId pysift$siftSprite() {
        return this.pysift$siftSprite;
    }

    @Override
    public void pysift$setSiftSprite(SpriteId sprite) {
        this.pysift$siftSprite = sprite;
    }
}
