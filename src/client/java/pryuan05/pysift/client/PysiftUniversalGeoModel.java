package pryuan05.pysift.client;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.model.DefaultedEntityGeoModel;
import net.minecraft.world.entity.Entity;
import pryuan05.pysift.PySift;

public class PysiftUniversalGeoModel<T extends Entity & GeoEntity> extends DefaultedEntityGeoModel<T> {
    public PysiftUniversalGeoModel(String entityId) {
        super(PySift.id(entityId));
    }
}
