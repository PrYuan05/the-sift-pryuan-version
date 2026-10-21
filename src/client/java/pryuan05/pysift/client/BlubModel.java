package pryuan05.pysift.client;

import com.geckolib.model.DefaultedEntityGeoModel;
import com.geckolib.renderer.base.GeoRenderState;
import net.minecraft.resources.Identifier;
import pryuan05.pysift.PySift;
import pryuan05.pysift.entity.mob.BlubEntity;

public class BlubModel extends DefaultedEntityGeoModel<BlubEntity> {
    private static final Identifier MODEL_SOUL_ENGORGED = PySift.id("entity/blub");
    private static final Identifier MODEL_CARAPACE = PySift.id("entity/blub_carapace");
    private static final Identifier MODEL_MEADOWS = PySift.id("entity/blub_meadows");
    private static final Identifier MODEL_RAVINES = PySift.id("entity/blub_ravines");
    private static final Identifier MODEL_FUNGAL = PySift.id("entity/blub_fungal");

    private static final Identifier TEX_SOUL_ENGORGED = PySift.id("textures/entity/blub.png");
    private static final Identifier TEX_CARAPACE = PySift.id("textures/entity/blub_carapace.png");
    private static final Identifier TEX_MEADOWS = PySift.id("textures/entity/blub_meadows.png");
    private static final Identifier TEX_RAVINES = PySift.id("textures/entity/blub_ravines.png");
    private static final Identifier TEX_FUNGAL = PySift.id("textures/entity/blub_fungal.png");

    private static final Identifier ANIM_SOUL_ENGORGED = PySift.id("entity/blub");
    private static final Identifier ANIM_CARAPACE = PySift.id("entity/blub_carapace");
    private static final Identifier ANIM_MEADOWS = PySift.id("entity/blub_meadows");
    private static final Identifier ANIM_RAVINES = PySift.id("entity/blub_ravines");
    private static final Identifier ANIM_FUNGAL = PySift.id("entity/blub_fungal");

    public BlubModel() {
        super(PySift.id("blub"));
    }

    @Override
    public Identifier getModelResource(GeoRenderState renderState) {
        BlubEntity.Variant variant = renderState.getOrDefaultGeckolibData(BlubRenderer.VARIANT, BlubEntity.Variant.SOUL_ENGORGED);
        return switch (variant) {
            case CARAPACE -> MODEL_CARAPACE;
            case MEADOWS -> MODEL_MEADOWS;
            case RAVINES -> MODEL_RAVINES;
            case FUNGAL -> MODEL_FUNGAL;
            case SOUL_ENGORGED -> MODEL_SOUL_ENGORGED;
        };
    }

    @Override
    public Identifier getTextureResource(GeoRenderState renderState) {
        BlubEntity.Variant variant = renderState.getOrDefaultGeckolibData(BlubRenderer.VARIANT, BlubEntity.Variant.SOUL_ENGORGED);
        return switch (variant) {
            case CARAPACE -> TEX_CARAPACE;
            case MEADOWS -> TEX_MEADOWS;
            case RAVINES -> TEX_RAVINES;
            case FUNGAL -> TEX_FUNGAL;
            case SOUL_ENGORGED -> TEX_SOUL_ENGORGED;
        };
    }

    @Override
    public Identifier getAnimationResource(BlubEntity animatable) {
        if (animatable == null) {
            return ANIM_SOUL_ENGORGED;
        }
        return switch (animatable.getVariant()) {
            case CARAPACE -> ANIM_CARAPACE;
            case MEADOWS -> ANIM_MEADOWS;
            case RAVINES -> ANIM_RAVINES;
            case FUNGAL -> ANIM_FUNGAL;
            case SOUL_ENGORGED -> ANIM_SOUL_ENGORGED;
        };
    }

    @Override
    public Identifier[] getAnimationResourceFallbacks(BlubEntity animatable) {
        return new Identifier[]{ ANIM_SOUL_ENGORGED };
    }
}
