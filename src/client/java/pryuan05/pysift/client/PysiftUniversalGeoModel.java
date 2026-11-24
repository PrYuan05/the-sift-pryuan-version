package pryuan05.pysift.client;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.model.DefaultedEntityGeoModel;
import com.geckolib.renderer.base.GeoRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Entity;
import pryuan05.pysift.PySift;
import pryuan05.pysift.entity.ClimateVariant;

public class PysiftUniversalGeoModel<T extends Entity & GeoEntity> extends DefaultedEntityGeoModel<T> {
    /** 氣候變體的貼圖：[0] 原樣、[1] 熱帶、[2] 寒帶（textures/entity/<id>_tropical.png、_cold.png）。 */
    private final Identifier[] climateTextures;
    /** 有變體模型時：[1] 熱帶、[2] 寒帶的模型；沒有則為 null。 */
    private final Identifier[] climateModels;

    public PysiftUniversalGeoModel(String entityId) {
        super(PySift.id(entityId));
        climateModels = ClimateVariant.VARIANT_MODELS.contains(entityId) ? new Identifier[]{null,
                PySift.id("entity/" + entityId + "_tropical"), PySift.id("entity/" + entityId + "_cold")} : null;
        climateTextures = new Identifier[]{null,
                PySift.id("textures/entity/" + entityId + ClimateVariant.suffix(ClimateVariant.TROPICAL) + ".png"),
                PySift.id("textures/entity/" + entityId + ClimateVariant.suffix(ClimateVariant.COLD) + ".png")};
    }

    @Override
    public Identifier getModelResource(GeoRenderState renderState) {
        int climate = renderState.getOrDefaultGeckolibData(PysiftUniversalGeoRenderer.CLIMATE, ClimateVariant.NORMAL);
        if (climateModels != null && (climate == ClimateVariant.TROPICAL || climate == ClimateVariant.COLD)) {
            return climateModels[climate];
        }
        return super.getModelResource(renderState);
    }

    @Override
    public Identifier getTextureResource(GeoRenderState renderState) {
        int climate = renderState.getOrDefaultGeckolibData(PysiftUniversalGeoRenderer.CLIMATE, ClimateVariant.NORMAL);
        if (climate == ClimateVariant.TROPICAL || climate == ClimateVariant.COLD) {
            return climateTextures[climate];
        }
        return super.getTextureResource(renderState);
    }
}
