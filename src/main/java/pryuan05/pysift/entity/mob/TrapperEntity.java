package pryuan05.pysift.entity.mob;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
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
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftMonsterEntity;
import pryuan05.pysift.entity.ai.KeepDistanceGoal;
import pryuan05.pysift.entity.ai.SkillGoal;
import pryuan05.pysift.entity.misc.SoulSnareEntity;
import pryuan05.pysift.entity.projectile.TrapperNetEntity;

/**
 * 陷阱師（Monarch 麾下，不喜歡正面打）。
 * <ul>
 *   <li>走位：和目標保持 5~10 格；被貼到 2.5 格內才用長爪近戰（動畫 attack）。</li>
 *   <li>佈陷阱：在目標前進的路線上（自己與目標之間、偏目標那側）埋一個靈魂陷阱，踩到 3 點傷害並定身 2.5 秒；
 *       同時最多 3 個，冷卻 8 秒（動畫 set_trap）。</li>
 *   <li>丟網：4~12 格丟出網子，命中緩速 III 4 秒並定身 1 秒，冷卻 6 秒（動畫 throw_net）。</li>
 * </ul>
 */
public class TrapperEntity extends PysiftMonsterEntity {
    private static final int MAX_SNARES = 3;
    private final List<UUID> snares = new ArrayList<>();

    public TrapperEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 24.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.FOLLOW_RANGE, 28.0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new SkillGoal(this, "set_trap", 12, 24, 160, 3.0, 16.0, false, this::setTrap) {
            @Override
            public boolean canUse() {
                return liveSnares() < MAX_SNARES && super.canUse();
            }
        });
        this.goalSelector.addGoal(2, new SkillGoal(this, "throw_net", 10, 18, 120, 4.0, 12.0, true, this::throwNet));
        this.goalSelector.addGoal(3, new KeepDistanceGoal(this, 5.0, 10.0, 2.5, 1.0));
        this.goalSelector.addGoal(4, new MeleeAttackGoal(this, 1.1, false));
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8.0f));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));

        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("attack", "set_trap", "throw_net");
    }

    @Override
    protected String meleeAnimation() {
        return "attack";
    }

    private int liveSnares() {
        if (!(this.level() instanceof ServerLevel level)) {
            return 0;
        }
        snares.removeIf(id -> !(level.getEntity(id) instanceof SoulSnareEntity s) || !s.isAlive());
        return snares.size();
    }

    /** 埋在目標前進路線上：目標往自己這邊走時剛好踩到。 */
    private void setTrap(ServerLevel level, LivingEntity target) {
        if (target == null || !target.isAlive()) {
            return;
        }
        Vec3 spot = this.position().lerp(target.position(), 0.65)
                .add(target.getDeltaMovement().multiply(10, 0, 10))
                .add((this.random.nextDouble() - 0.5) * 1.5, 0, (this.random.nextDouble() - 0.5) * 1.5);
        BlockPos ground = BlockPos.containing(spot.x, target.getY() + 1, spot.z);
        for (int i = 0; i < 4 && level.getBlockState(ground.below()).isAir(); i++) {
            ground = ground.below();
        }
        if (!level.getBlockState(ground.below()).isSolid()) {
            return;
        }
        snares.add(SoulSnareEntity.place(level, this, spot.x, ground.getY(), spot.z).getUUID());
    }

    private void throwNet(ServerLevel level, LivingEntity target) {
        if (target == null || !target.isAlive()) {
            return;
        }
        TrapperNetEntity net = new TrapperNetEntity(level, this);
        double dx = target.getX() - this.getX();
        double dz = target.getZ() - this.getZ();
        double dy = target.getY(0.5) - net.getY() + Math.sqrt(dx * dx + dz * dz) * 0.15;
        net.shoot(dx, dy, dz, 1.1f, 3.0f);
        level.addFreshEntity(net);
        this.playSound(SoundEvents.WITCH_THROW, 1.0f, 0.7f);
    }
}
