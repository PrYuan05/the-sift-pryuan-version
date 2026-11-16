package pryuan05.pysift.entity.mob;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import pryuan05.pysift.entity.PysiftMonsterEntity;
import pryuan05.pysift.entity.ai.SkillGoal;
import pryuan05.pysift.entity.projectile.ThrownRockEntity;

/**
 * 投擲巨獸（重型投手）。目標在 3~20 格且有視線時，從地面挖起碎石投向目標（動畫 throw，冷卻 4 秒）；
 * 碎石落點半徑 2 格 6 點鈍擊傷害並擊退。貼身時改用一般近戰。
 */
public class HurlerEntity extends PysiftMonsterEntity {
    public HurlerEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 35.0)
                .add(Attributes.MOVEMENT_SPEED, 0.20)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.4);
    }

    @Override
    protected void registerGoals() {
        super.registerGoals();
        this.goalSelector.addGoal(1, new SkillGoal(this, "throw", 14, 24, 80, 3.0, 20.0, true, this::throwRock));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("throw", "attack");
    }

    @Override
    protected String meleeAnimation() {
        return "attack";
    }

    private void throwRock(ServerLevel level, LivingEntity target) {
        if (target == null || !target.isAlive()) {
            return;
        }
        BlockState ground = level.getBlockState(BlockPos.containing(this.getX(), this.getY() - 0.5, this.getZ()));
        if (!ground.isAir()) {
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), this.getX(), this.getY() + 0.1, this.getZ(),
                    20, 0.5, 0.1, 0.5, 0.15);
        }
        ThrownRockEntity rock = new ThrownRockEntity(level, this, 6.0f);
        rock.setPos(this.getX(), this.getY() + this.getBbHeight() + 0.3, this.getZ());
        double dx = target.getX() - rock.getX();
        double dz = target.getZ() - rock.getZ();
        double dy = target.getY(0.3) - rock.getY() + Math.sqrt(dx * dx + dz * dz) * 0.2;
        rock.shoot(dx, dy, dz, 1.2f, 4.0f);
        level.addFreshEntity(rock);
        this.playSound(SoundEvents.SNOWBALL_THROW, 1.5f, 0.5f);
    }
}
