package pryuan05.pysift.client;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.model.GeoModel;
import com.geckolib.renderer.GeoEntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.world.entity.Entity;

public class PysiftUniversalGeoRenderer<T extends Entity & GeoEntity> extends GeoEntityRenderer<T, EntityRenderState> {
    public PysiftUniversalGeoRenderer(EntityRendererProvider.Context context, String entityId) {
        super(context, new PysiftUniversalGeoModel<>(entityId));
    }

    public PysiftUniversalGeoRenderer(EntityRendererProvider.Context context, GeoModel<T> model) {
        super(context, model);
    }
}
