package pryuan05.pysift.entity.mob;

import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.PysiftMonsterEntity;

import java.util.List;

public class TunerEntity extends PysiftMonsterEntity {
    private int buffCooldown = 40;

    public TunerEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 24.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24);
    }

    @Override
    public void tick() {
        super.tick();
        if (!this.level().isClientSide()) {
            buffCooldown--;
            if (buffCooldown <= 0) {
                buffCooldown = 60;
                List<Monster> allies = this.level().getEntitiesOfClass(
                        Monster.class,
                        this.getBoundingBox().inflate(10.0),
                        m -> m != this
                );
                for (Monster ally : allies) {
                    ally.addEffect(new MobEffectInstance(MobEffects.SPEED, 100, 1));
                    ally.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 100, 0));
                }
            }
        }
    }
}
