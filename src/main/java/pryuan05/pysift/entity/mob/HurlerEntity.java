package pryuan05.pysift.entity.mob;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.RangedAttackGoal;
import net.minecraft.world.entity.monster.RangedAttackMob;
import net.minecraft.world.entity.projectile.throwableitemprojectile.Snowball;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftMonsterEntity;

public class HurlerEntity extends PysiftMonsterEntity implements RangedAttackMob {
    public HurlerEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    @Override
    protected void registerGoals() {
        super.registerGoals();
        this.goalSelector.addGoal(1, new RangedAttackGoal(this, 1.1, 40, 20.0f));
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 26.0)
                .add(Attributes.MOVEMENT_SPEED, 0.22);
    }

    @Override
    public void performRangedAttack(LivingEntity target, float distanceFactor) {
        Vec3 vec3 = target.getDeltaMovement();
        double d = target.getX() + vec3.x - this.getX();
        double e = target.getEyeY() - 1.1 - this.getY();
        double f = target.getZ() + vec3.z - this.getZ();
        Snowball rock = new Snowball(this.level(), this, new ItemStack(Items.SNOWBALL));
        rock.shoot(d, e, f, 1.4f, 8.0f);
        this.level().addFreshEntity(rock);
    }
}
