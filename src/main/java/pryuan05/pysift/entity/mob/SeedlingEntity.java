package pryuan05.pysift.entity.mob;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.PysiftMonsterEntity;

/** Seedling：蟲群幼體，行為見 {@link PysiftSwarmEntity}；也會由 Nester 召喚。 */
public class SeedlingEntity extends PysiftSwarmEntity {
    public SeedlingEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftSwarmEntity.createSwarmAttributes();
    }
}
