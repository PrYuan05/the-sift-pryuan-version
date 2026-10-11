package pryuan05.pysift.entity.mob;

import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.PysiftAnimalEntity;

import java.util.List;

public class PollinatorEntity extends PysiftAnimalEntity {
    private int sporeCooldown = 60;

    public PollinatorEntity(EntityType<? extends PysiftAnimalEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftAnimalEntity.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.28);
    }

    @Override
    public void tick() {
        super.tick();
        if (!this.level().isClientSide()) {
            sporeCooldown--;
            if (sporeCooldown <= 0) {
                sporeCooldown = 100;
                List<Player> players = this.level().getEntitiesOfClass(
                        Player.class,
                        this.getBoundingBox().inflate(6.0)
                );
                for (Player player : players) {
                    player.addEffect(new MobEffectInstance(MobEffects.LEVITATION, 40, 0));
                }
            }
        }
    }
}
