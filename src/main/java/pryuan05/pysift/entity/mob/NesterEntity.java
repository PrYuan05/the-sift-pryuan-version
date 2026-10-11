package pryuan05.pysift.entity.mob;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.entity.PysiftMonsterEntity;

public class NesterEntity extends PysiftMonsterEntity {
    private int spawnCooldown = 160;

    public NesterEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 35.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2)
                .add(Attributes.ARMOR, 2.0);
    }

    @Override
    public void tick() {
        super.tick();
        if (!this.level().isClientSide() && this.getTarget() != null) {
            spawnCooldown--;
            if (spawnCooldown <= 0) {
                spawnCooldown = 200;
                SeedlingEntity minion = ModEntities.SEEDLING.create(this.level(), EntitySpawnReason.MOB_SUMMONED);
                if (minion != null) {
                    minion.snapTo(this.getX(), this.getY(), this.getZ(), this.getYRot(), 0.0f);
                    minion.setTarget(this.getTarget());
                    this.level().addFreshEntity(minion);
                }
            }
        }
    }
}
