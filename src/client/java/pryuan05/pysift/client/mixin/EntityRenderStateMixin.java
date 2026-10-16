package pryuan05.pysift.client.mixin;

import net.minecraft.client.renderer.entity.state.EntityRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import pryuan05.pysift.client.SoulFireRenderState;

/** 給每個實體的 render state 多一個「燒的是靈魂火」旗標。 */
@Mixin(EntityRenderState.class)
public abstract class EntityRenderStateMixin implements SoulFireRenderState {
    @Unique
    private boolean pysift$soulFire;

    @Override
    public boolean pysift$soulFire() {
        return this.pysift$soulFire;
    }

    @Override
    public void pysift$setSoulFire(boolean soulFire) {
        this.pysift$soulFire = soulFire;
    }
}
