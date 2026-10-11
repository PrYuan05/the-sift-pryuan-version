package pryuan05.pysift.client;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.model.DefaultedEntityGeoModel;
import com.geckolib.renderer.base.GeoRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Entity;
import pryuan05.pysift.PySift;

public class PysiftUniversalGeoModel<T extends Entity & GeoEntity> extends DefaultedEntityGeoModel<T> {
    private final String entityId;

    public PysiftUniversalGeoModel(String entityId) {
        super(PySift.id(entityId));
        this.entityId = entityId;
    }

    @Override
    public Identifier getModelResource(GeoRenderState renderState) {
        return PySift.id("geo/" + this.entityId + ".geo.json");
    }

    @Override
    public Identifier getTextureResource(GeoRenderState renderState) {
        return PySift.id("textures/entity/" + this.entityId + ".png");
    }

    @Override
    public Identifier getAnimationResource(T animatable) {
        return PySift.id("animations/" + this.entityId + ".animation.json");
    }
}
