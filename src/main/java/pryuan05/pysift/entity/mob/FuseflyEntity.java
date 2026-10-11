package pryuan05.pysift.entity.mob;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.PysiftMonsterEntity;

public class FuseflyEntity extends PysiftMonsterEntity {
    private int fuseTimer = 30;
    private boolean ignited = false;

    public FuseflyEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.35);
    }

    @Override
    public void tick() {
        super.tick();
        LivingEntity target = this.getTarget();
        if (target != null && this.distanceToSqr(target) < 9.0) {
            ignited = true;
        }
        if (ignited) {
            fuseTimer--;
            if (fuseTimer <= 0 && !this.level().isClientSide()) {
                this.level().explode(this, this.getX(), this.getY(), this.getZ(), 2.0f, Level.ExplosionInteraction.MOB);
                this.discard();
            }
        }
    }
}
