package pryuan05.pysift.entity.mob;

import java.util.List;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import pryuan05.pysift.entity.PysiftGeoEntity;
import pryuan05.pysift.entity.ai.GroundSlamGoal;

/**
 * 漫遊樹精（植物巨像，被動）。平常緩慢漫遊、不主動攻擊；被攻擊後反擊：
 * 一般近戰（動畫 attack），目標 3 格內時重踏（動畫 stomp）——半徑 3.5 格 7 點傷害並往上擊飛，地面冒出地刺粒子，冷卻 4 秒。
 */
public class RoamrootEntity extends PysiftGeoEntity {
    public RoamrootEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PathfinderMob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 70.0)
                .add(Attributes.MOVEMENT_SPEED, 0.16)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.9)
                .add(Attributes.ATTACK_DAMAGE, 8.0)
                .add(Attributes.FOLLOW_RANGE, 20.0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new GroundSlamGoal(this, "stomp", 12, 22, 80, 3.0, 3.5, 7.0f, 0.5, e -> false) {
            @Override
            protected void perform(ServerLevel level, LivingEntity target) {
                super.perform(level, target);
                // 地刺：一圈往上噴的根系／尖石碎屑
                for (int i = 0; i < 16; i++) {
                    double a = i * Math.PI * 2 / 16;
                    double r = 1.5 + level.getRandom().nextDouble() * 2.0;
                    level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.POINTED_DRIPSTONE.defaultBlockState()),
                            getX() + Math.cos(a) * r, getY() + 0.2, getZ() + Math.sin(a) * r, 6, 0.1, 0.6, 0.1, 0.3);
                }
            }
        });
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.0, true));
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.6));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0f));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));

        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("stomp", "attack");
    }

    @Override
    protected String meleeAnimation() {
        return "attack";
    }
}
