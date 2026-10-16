package pryuan05.pysift.entity.mob;

import java.util.List;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AreaEffectCloud;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.PysiftMonsterEntity;

/**
 * 晃晃怪（不穩定的滑稽生物）。左右搖晃著走（walk 動畫）並近戰（動畫 attack）；
 * 死亡時像史萊姆一樣彈起（動畫 death），留下 3 秒、半徑 3 格的反胃迷霧（接觸者反胃 8 秒）。
 */
public class WobbleEntity extends PysiftMonsterEntity {
    public WobbleEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.ATTACK_DAMAGE, 3.0);
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("attack");
    }

    @Override
    protected String meleeAnimation() {
        return "attack";
    }

    @Override
    protected boolean hasDeathAnimation() {
        return true;
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (!(this.level() instanceof ServerLevel level)) {
            return;
        }
        this.setDeltaMovement(this.getDeltaMovement().x * 0.3, 0.6, this.getDeltaMovement().z * 0.3);
        this.needsSync = true;
        this.playSound(SoundEvents.SLIME_JUMP, 1.2f, 0.7f);
        AreaEffectCloud cloud = new AreaEffectCloud(level, this.getX(), this.getY(), this.getZ());
        cloud.setOwner(this);
        cloud.setRadius(3.0f);
        cloud.setDuration(60);
        cloud.setWaitTime(0);
        cloud.setRadiusPerTick(0.0f);
        cloud.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 160, 0));
        level.addFreshEntity(cloud);
    }
}
