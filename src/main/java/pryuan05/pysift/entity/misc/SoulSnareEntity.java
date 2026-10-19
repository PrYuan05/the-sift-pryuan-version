package pryuan05.pysift.entity.misc;

import java.util.UUID;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import pryuan05.pysift.effect.ModEffects;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.fluid.SpiritInteractions;

/**
 * 靈魂陷阱（Trapper 埋在地上）：沒有模型，只偶爾冒出一點淡淡的靈魂微光，細心才看得到。
 * 非敵對生物踩到時合上：{@link #DAMAGE} 點傷害並定身 {@link #ROOT_TICKS} tick（{@link ModEffects#ENSNARED}），然後消失。
 * 放置 {@link #LIFETIME} tick 後自己消散；不存檔。
 */
public class SoulSnareEntity extends Entity {
    private static final int LIFETIME = 600;
    private static final int ROOT_TICKS = 50;
    private static final float DAMAGE = 3.0f;
    private UUID ownerId;

    public SoulSnareEntity(EntityType<? extends SoulSnareEntity> type, Level level) {
        super(type, level);
    }

    public static SoulSnareEntity place(ServerLevel level, LivingEntity owner, double x, double y, double z) {
        SoulSnareEntity snare = new SoulSnareEntity(ModEntities.SOUL_SNARE, level);
        snare.ownerId = owner.getUUID();
        snare.setPos(x, y, z);
        level.addFreshEntity(snare);
        level.sendParticles(ParticleTypes.SOUL, x, y + 0.1, z, 6, 0.3, 0.05, 0.3, 0.01);
        snare.playSound(SoundEvents.SOUL_SAND_PLACE, 0.8f, 0.7f);
        return snare;
    }

    @Override
    public void tick() {
        super.tick();
        if (!(this.level() instanceof ServerLevel level)) {
            return;
        }
        if (this.tickCount > LIFETIME) {
            level.sendParticles(ParticleTypes.SOUL, this.getX(), this.getY() + 0.1, this.getZ(), 4, 0.2, 0.05, 0.2, 0.01);
            this.discard();
            return;
        }
        if (this.tickCount % 20 == 0 && this.random.nextInt(2) == 0) {   // 偶爾一點微光
            level.sendParticles(ParticleTypes.SOUL, this.getX() + (this.random.nextDouble() - 0.5) * 0.6, this.getY() + 0.05,
                    this.getZ() + (this.random.nextDouble() - 0.5) * 0.6, 1, 0, 0, 0, 0.005);
        }
        if (this.tickCount < 10) {   // 剛放下時不會立刻觸發
            return;
        }
        for (LivingEntity victim : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(0.15),
                e -> e.isAlive() && !(e instanceof Enemy) && !(e instanceof Player p && (p.isSpectator() || p.isCreative())))) {
            spring(level, victim);
            return;
        }
    }

    private void spring(ServerLevel level, LivingEntity victim) {
        Entity owner = ownerId != null ? level.getEntity(ownerId) : null;
        DamageSource source = owner instanceof LivingEntity living ? this.damageSources().mobAttack(living) : this.damageSources().magic();
        victim.hurtServer(level, source, DAMAGE);
        victim.addEffect(new MobEffectInstance(ModEffects.ENSNARED, ROOT_TICKS, 0), owner);
        victim.setDeltaMovement(0, Math.min(0, victim.getDeltaMovement().y), 0);
        victim.needsSync = true;
        this.playSound(SoundEvents.EVOKER_FANGS_ATTACK, 1.0f, 1.3f);
        level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 0.3, this.getZ(), 6, 0.3, 0.2, 0.3, 0.02);
        SpiritInteractions.releaseSouls(level, this.blockPosition(), 3);
        this.discard();
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        return false;
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
    }
}
