package pryuan05.pysift.entity;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.animatable.instance.AnimatableInstanceCache;
import com.geckolib.animatable.manager.AnimatableManager;
import com.geckolib.animation.AnimationController;
import com.geckolib.animation.RawAnimation;
import com.geckolib.util.GeckoLibUtil;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.level.Level;

public abstract class PysiftGeoEntity extends PathfinderMob implements GeoEntity {
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    protected PysiftGeoEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
    }

    public String getEntityIdName() {
        Identifier id = BuiltInRegistries.ENTITY_TYPE.getKey(this.getType());
        return id != null ? id.getPath() : "mob";
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>("movement", 5, state -> {
            String mobId = getEntityIdName();
            if (state.isMoving()) {
                return state.setAndContinue(RawAnimation.begin().thenLoop("animation." + mobId + ".walk"));
            } else {
                return state.setAndContinue(RawAnimation.begin().thenLoop("animation." + mobId + ".idle"));
            }
        }));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
