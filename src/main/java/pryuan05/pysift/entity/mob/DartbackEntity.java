package pryuan05.pysift.entity.mob;

import java.util.List;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.PysiftMonsterEntity;
import pryuan05.pysift.entity.ai.ChargeGoal;
import pryuan05.pysift.entity.ai.KeepRangeGoal;
import pryuan05.pysift.entity.ai.SkillGoal;
import pryuan05.pysift.entity.projectile.DartEntity;

/**
 * 飛鏢背甲獸（遠程射手）。體型放大 3.15 倍（約 2 格高）。
 * <ul>
 *   <li>和目標保持 6~12 格（風箏），每 2 秒從背甲上射出一根尖刺飛鏢（動畫 shoot，3 點基礎傷害）。</li>
 *   <li>衝撞：目標在 4~10 格時刨地 0.75 秒（動畫 charge），沿直線衝刺最多 1 秒，撞到的生物受 7 點傷害並被撞飛；
 *       撞牆會停下。方向在衝刺開始時鎖定，可以側閃。冷卻 7 秒。</li>
 *   <li>甲殼：來自背後的傷害減半。</li>
 * </ul>
 */
public class DartbackEntity extends PysiftMonsterEntity {
    /** 體型倍率（原版 SCALE 屬性），模型與碰撞箱一起放大。 */
    private static final double SCALE = 3.15;

    public DartbackEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 24.0)
                .add(Attributes.MOVEMENT_SPEED, 0.23)
                .add(Attributes.SCALE, SCALE)          // 模型本身約 0.64 格高，放大後約 2 格高
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        // 衝撞：目標在 4~10 格時刨地 0.75 秒後直線衝刺（最多 1 秒），撞到 7 點傷害並撞飛，冷卻 7 秒
        this.goalSelector.addGoal(1, new ChargeGoal(this, "charge", 15, 20, 15, 140, 4.0, 10.0, 0.75, 7.0f, 1.4));
        this.goalSelector.addGoal(1, new SkillGoal(this, "shoot", 8, 16, 40, 3.0, 16.0, true, this::shootDart));
        this.goalSelector.addGoal(3, new KeepRangeGoal(this, 6.0, 12.0, 1.0));
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8.0f));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));

        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("shoot", "charge");
    }

    private void shootDart(ServerLevel level, LivingEntity target) {
        if (target == null || !target.isAlive()) {
            return;
        }
        DartEntity dart = DartEntity.create(level, this, this.getX(), this.getY() + this.getBbHeight() + 0.2, this.getZ(), 3.0);
        double dx = target.getX() - dart.getX();
        double dz = target.getZ() - dart.getZ();
        double dy = target.getY(0.5) - dart.getY() + Math.sqrt(dx * dx + dz * dz) * 0.15;
        dart.shoot(dx, dy, dz, 1.6f, 6.0f);
        level.addFreshEntity(dart);
        this.playSound(SoundEvents.ARROW_SHOOT, 1.0f, 1.3f);
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        Vec3 from = source.getSourcePosition();
        if (from != null) {
            Vec3 forward = Vec3.directionFromRotation(0.0f, this.yBodyRot);
            Vec3 toSource = from.subtract(this.position()).multiply(1, 0, 1);
            if (toSource.lengthSqr() > 1.0E-4 && forward.dot(toSource.normalize()) < -0.3) {
                amount *= 0.5f;   // 背甲擋下一半
                this.playSound(SoundEvents.SHIELD_BLOCK.value(), 0.8f, 1.2f);
            }
        }
        return super.hurtServer(level, source, amount);
    }
}
