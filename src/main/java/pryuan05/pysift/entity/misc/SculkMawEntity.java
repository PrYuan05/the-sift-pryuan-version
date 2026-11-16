package pryuan05.pysift.entity.misc;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.animatable.instance.AnimatableInstanceCache;
import com.geckolib.animatable.manager.AnimatableManager;
import com.geckolib.animation.AnimationController;
import com.geckolib.animation.RawAnimation;
import com.geckolib.util.GeckoLibUtil;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.progression.BossWeapons;

import java.util.UUID;

/**
 * 幽匿咬刺（重錘砸地、靈髓斧留下的「幽匿藤蔓」）：一圈六根幽匿尖牙從地面竄出（emerge），張著口微微抽動（idle），
 * 時間到時先再張大、接著猛然咬合，中間的靈魂核心炸開（bite）：半徑 {@link #RADIUS} 內的敵人受到 {@link #DAMAGE} 點傷害
 * 並被靈魂剝奪，然後尖牙縮回地底。外觀是 GeckoLib 模型 sculk_maw（tools/entity/build_sculk_maw.py）。不存檔。
 */
public class SculkMawEntity extends Entity implements GeoEntity {
    private static final RawAnimation EMERGE = RawAnimation.begin().thenPlay("animation.sculk_maw.emerge")
            .thenLoop("animation.sculk_maw.idle");
    private static final RawAnimation BITE = RawAnimation.begin().thenPlay("animation.sculk_maw.bite");
    private static final EntityDataAccessor<Boolean> BITING = SynchedEntityData.defineId(SculkMawEntity.class, EntityDataSerializers.BOOLEAN);
    /** 咬合動畫裡尖牙合上的那一刻（tick）、整段長度。 */
    private static final int SNAP_TICK = 5, BITE_TICKS = 12;
    private static final double RADIUS = 2.5;
    private static final float DAMAGE = 6.0f;

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private UUID ownerId;
    private int fuse = 40;
    private int biteAge = -1;

    public SculkMawEntity(EntityType<? extends SculkMawEntity> type, Level level) {
        super(type, level);
    }

    /** 在 (x, y, z) 長出一個咬刺，fuse tick 後咬合。 */
    public static SculkMawEntity plant(ServerLevel level, LivingEntity owner, double x, double y, double z, int fuse) {
        SculkMawEntity maw = new SculkMawEntity(ModEntities.SCULK_MAW, level);
        maw.ownerId = owner.getUUID();
        maw.fuse = fuse;
        maw.setPos(x, y, z);
        maw.setYRot(level.getRandom().nextFloat() * 360.0f);
        level.addFreshEntity(maw);
        level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, x, y + 0.1, z, 6, 0.3, 0.05, 0.3, 0.02);
        maw.playSound(SoundEvents.SCULK_BLOCK_SPREAD, 1.0f, 1.2f);
        return maw;
    }

    @Override
    public void tick() {
        super.tick();
        if (!(this.level() instanceof ServerLevel level)) {
            return;
        }
        if (biteAge < 0) {
            if (this.tickCount % 4 == 0) {
                level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, this.getX(), this.getY() + 0.4, this.getZ(), 1, 0.2, 0.1, 0.2, 0.01);
            }
            if (this.tickCount >= fuse) {
                biteAge = 0;
                this.entityData.set(BITING, true);
                this.playSound(SoundEvents.SCULK_SHRIEKER_SHRIEK, 0.5f, 1.8f);
            }
            return;
        }
        biteAge++;
        if (biteAge == SNAP_TICK) {
            snap(level);
        }
        if (biteAge >= BITE_TICKS) {
            this.discard();
        }
    }

    /** 尖牙合上、核心炸開。 */
    private void snap(ServerLevel level) {
        Entity owner = ownerId != null ? level.getEntity(ownerId) : null;
        if (owner instanceof LivingEntity living) {
            DamageSource source = level.damageSources().indirectMagic(this, living);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(this.blockPosition()).inflate(RADIUS),
                    e -> BossWeapons.isFoe(living, e))) {
                if (e.hurtServer(level, source, DAMAGE)) {
                    BossWeapons.soulDeprive(e, living);
                }
            }
        }
        double y = this.getY() + 0.5;
        level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), y, this.getZ(), 14, 0.5, 0.4, 0.5, 0.06);
        level.sendParticles(ParticleTypes.SONIC_BOOM, this.getX(), y, this.getZ(), 1, 0, 0, 0, 0);
        level.sendParticles(new net.minecraft.core.particles.SculkChargeParticleOptions(0.0f), this.getX(), this.getY() + 0.1, this.getZ(),
                10, 0.6, 0.05, 0.6, 0.0);
        this.playSound(SoundEvents.EVOKER_FANGS_ATTACK, 1.0f, 0.8f);
        this.playSound(SoundEvents.WARDEN_ATTACK_IMPACT, 0.8f, 1.4f);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>("maw", 0,
                state -> state.setAndContinue(this.entityData.get(BITING) ? BITE : EMERGE)));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        builder.define(BITING, false);
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
