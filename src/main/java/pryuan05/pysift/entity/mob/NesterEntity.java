package pryuan05.pysift.entity.mob;

import java.util.List;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.entity.PysiftMonsterEntity;

/**
 * 母巢怪（重裝母體，體型放大 1.67 倍，本體約 1.8 格高）。
 * <ul>
 *   <li>戰鬥中每 8 秒召喚 2 隻 Seedling 或 Sprout（隨機，動畫 summon），召喚出的幼體直接鎖定母體的目標。</li>
 *   <li>死亡時發出音爆：16 格內的幼體獲得迅捷 II 與力量 I 30 秒（狂暴），並鎖定殺死母體的生物。</li>
 * </ul>
 */
public class NesterEntity extends PysiftMonsterEntity {
    private static final int SUMMON_INTERVAL = 160;
    /** 體型倍率（原版 SCALE 屬性）：本體（不含觸角）約 1.8 格高。 */
    private static final double SCALE = 1.67;
    private int summonTimer = SUMMON_INTERVAL;

    public NesterEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 60.0)
                .add(Attributes.MOVEMENT_SPEED, 0.18)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.8)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.SCALE, SCALE)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("summon", "attack");
    }

    @Override
    protected String meleeAnimation() {
        return "attack";
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        LivingEntity target = this.getTarget();
        if (target == null || !target.isAlive()) {
            summonTimer = Math.max(summonTimer, 40);
            return;
        }
        if (--summonTimer > 0) {
            return;
        }
        summonTimer = SUMMON_INTERVAL;
        this.triggerAnim("skill", "summon");
        this.playSound(SoundEvents.EVOKER_PREPARE_SUMMON, 1.2f, 0.8f);
        for (int i = 0; i < 2; i++) {
            EntityType<? extends PysiftSwarmEntity> type = this.random.nextBoolean() ? ModEntities.SEEDLING : ModEntities.SPROUT;
            PysiftSwarmEntity minion = type.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (minion == null) {
                continue;
            }
            double a = this.random.nextDouble() * Math.PI * 2;
            minion.snapTo(this.getX() + Math.cos(a) * 1.2, this.getY(), this.getZ() + Math.sin(a) * 1.2, this.getYRot(), 0.0f);
            level.addFreshEntity(minion);
            minion.setTarget(target);
            level.sendParticles(ParticleTypes.POOF, minion.getX(), minion.getY() + 0.3, minion.getZ(), 6, 0.2, 0.2, 0.2, 0.02);
        }
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (!(this.level() instanceof ServerLevel level)) {
            return;
        }
        level.sendParticles(ParticleTypes.SONIC_BOOM, this.getX(), this.getY() + 0.8, this.getZ(), 1, 0, 0, 0, 0);
        this.playSound(SoundEvents.WARDEN_SONIC_BOOM, 1.5f, 1.4f);
        LivingEntity killer = source.getEntity() instanceof LivingEntity l ? l : null;
        for (PysiftSwarmEntity kin : level.getEntitiesOfClass(PysiftSwarmEntity.class, this.getBoundingBox().inflate(16.0))) {
            kin.addEffect(new MobEffectInstance(MobEffects.SPEED, 600, 1), this);
            kin.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 600, 0), this);
            if (killer != null) {
                kin.setTarget(killer);
            }
        }
    }
}
