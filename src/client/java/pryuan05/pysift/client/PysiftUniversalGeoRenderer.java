package pryuan05.pysift.client;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.constant.dataticket.DataTicket;
import com.geckolib.model.GeoModel;
import com.geckolib.renderer.GeoEntityRenderer;
import com.geckolib.renderer.base.GeoRenderState;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import pryuan05.pysift.entity.PysiftGeoEntity;

public class PysiftUniversalGeoRenderer<T extends Entity & GeoEntity> extends GeoEntityRenderer<T, EntityRenderState> {
    /** 這隻生物有比原版長的死亡動畫（{@link PysiftGeoEntity#deathDuration()} &gt; 20）。 */
    private static final DataTicket<Boolean> LONG_DEATH = DataTicket.create("pysift_long_death", Boolean.class);

    public PysiftUniversalGeoRenderer(EntityRendererProvider.Context context, String entityId) {
        super(context, new PysiftUniversalGeoModel<>(entityId));
    }

    public PysiftUniversalGeoRenderer(EntityRendererProvider.Context context, GeoModel<T> model) {
        super(context, model);
    }

    private static boolean longDeath(Entity entity) {
        return entity instanceof PysiftGeoEntity mob && mob.deathDuration() > 20;
    }

    @Override
    public void addRenderData(T animatable, Void relatedObject, EntityRenderState renderState, float partialTick) {
        super.addRenderData(animatable, relatedObject, renderState, partialTick);
        ((GeoRenderState) renderState).addGeckolibData(LONG_DEATH, longDeath(animatable));
    }

    /** 有自己完整死亡動畫的生物不套用原版的倒地翻轉（否則動畫會被整個轉 90 度）。 */
    @Override
    protected float getDeathMaxRotation(GeoRenderState renderState) {
        return renderState.getOrDefaultGeckolibData(LONG_DEATH, false) ? 0.0f : super.getDeathMaxRotation(renderState);
    }

    /** 同上：死亡演出期間不整段染成受傷紅色，只在真的受到攻擊時閃紅。 */
    @Override
    public int getPackedOverlay(T animatable, Void relatedObject, float u, float partialTick) {
        if (longDeath(animatable) && animatable instanceof LivingEntity living && living.deathTime > 0) {
            return OverlayTexture.pack(OverlayTexture.u(u), OverlayTexture.v(false));
        }
        return super.getPackedOverlay(animatable, relatedObject, u, partialTick);
    }
}
