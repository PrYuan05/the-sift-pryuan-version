package pryuan05.pysift.client;

import com.geckolib.constant.dataticket.DataTicket;
import com.geckolib.renderer.base.GeoRenderState;
import com.geckolib.renderer.base.RenderPassInfo;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import org.jspecify.annotations.Nullable;
import pryuan05.pysift.entity.mob.BlubEntity;

public class BlubRenderer extends PysiftUniversalGeoRenderer<BlubEntity> {
    public static final DataTicket<BlubEntity.Variant> VARIANT = DataTicket.create("pysift_blub_variant", BlubEntity.Variant.class);

    public BlubRenderer(EntityRendererProvider.Context context) {
        super(context, new BlubModel());
        // 只有草甸變體（blub_meadows）頭頂有青藍提燈，其他 4 種 Blub 不啟用發光層
        withRenderLayer(new VanillaGlowLayer<>(this) {
            @Override
            protected @Nullable RenderType getRenderType(EntityRenderState renderState) {
                BlubEntity.Variant v = ((GeoRenderState) renderState).getOrDefaultGeckolibData(VARIANT, BlubEntity.Variant.SOUL_ENGORGED);
                return v == BlubEntity.Variant.MEADOWS ? super.getRenderType(renderState) : null;
            }
        });
    }

    @Override
    public void addRenderData(BlubEntity animatable, Void relatedObject, EntityRenderState renderState, float partialTick) {
        super.addRenderData(animatable, relatedObject, renderState, partialTick);
        ((GeoRenderState) renderState).addGeckolibData(VARIANT, animatable.getVariant());
    }

    @Override
    public void scaleModelForRender(RenderPassInfo<EntityRenderState> renderPass, float widthScale, float heightScale) {
        float age = renderPass.renderState() instanceof LivingEntityRenderState living && living.isBaby ? 0.6f : 1.0f;
        super.scaleModelForRender(renderPass, widthScale * age, heightScale * age);
    }
}
