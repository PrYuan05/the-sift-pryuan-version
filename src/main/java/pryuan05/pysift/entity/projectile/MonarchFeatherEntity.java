package pryuan05.pysift.entity.projectile;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.item.ModItems;

/**
 * Monarch 的羽毛彈：先在原地懸停並閃著微光（{@code armTicks}，預設 5 秒），時間到後射向最近的玩家，
 * 命中造成 {@link #DAMAGE} 點傷害；碰到方塊或飛行 4 秒後消失。外觀為使用者畫的羽刃（物品 monarch_feather），發光。
 */
public class MonarchFeatherEntity extends ThrowableItemProjectile {
    private static final EntityDataAccessor<Boolean> DATA_ARMED = SynchedEntityData.defineId(MonarchFeatherEntity.class, EntityDataSerializers.BOOLEAN);
    private static final float DAMAGE = 5.0f;
    private int armTicks = 100;
    private int flightTicks;

    public MonarchFeatherEntity(EntityType<? extends MonarchFeatherEntity> type, Level level) {
        super(type, level);
    }

    public MonarchFeatherEntity(Level level, LivingEntity owner, Vec3 at, int armTicks) {
        super(ModEntities.MONARCH_FEATHER, owner, level, new ItemStack(ModItems.MONARCH_FEATHER));
        this.setPos(at.x, at.y, at.z);
        this.setDeltaMovement(Vec3.ZERO);
        this.armTicks = armTicks;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_ARMED, false);
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.MONARCH_FEATHER;
    }

    @Override
    protected double getDefaultGravity() {
        return 0.0;
    }

    @Override
    public void tick() {
        if (!this.entityData.get(DATA_ARMED)) {
            // 懸停：不移動、不碰撞，只閃微光
            this.setDeltaMovement(Vec3.ZERO);
            if (this.level() instanceof ServerLevel level) {
                if (this.tickCount % 5 == 0) {
                    level.sendParticles(ParticleTypes.END_ROD, this.getX(), this.getY(), this.getZ(), 1, 0.05, 0.05, 0.05, 0.0);
                }
                if (this.tickCount >= armTicks) {
                    launch(level);
                }
            }
            this.baseTick();
            return;
        }
        super.tick();
        if (this.level() instanceof ServerLevel level && ++flightTicks > 80) {
            this.discard();
        }
    }

    private void launch(ServerLevel level) {
        Player target = level.getNearestPlayer(this, 40);
        if (target == null || target.isSpectator()) {
            this.discard();
            return;
        }
        Vec3 to = target.getEyePosition().subtract(this.position());
        this.shoot(to.x, to.y, to.z, 1.3f, 0.0f);
        this.entityData.set(DATA_ARMED, true);
        this.playSound(SoundEvents.PHANTOM_FLAP, 0.8f, 1.6f);
    }

    @Override
    protected void onHitEntity(EntityHitResult hit) {
        Entity e = hit.getEntity();
        if (!(this.level() instanceof ServerLevel level) || e instanceof Enemy || e == this.getOwner()) {
            return;
        }
        e.hurtServer(level, this.damageSources().thrown(this, this.getOwner()), DAMAGE);
        this.discard();
    }

    @Override
    protected void onHitBlock(BlockHitResult hit) {
        if (this.level() instanceof ServerLevel level) {
            level.sendParticles(ParticleTypes.END_ROD, this.getX(), this.getY(), this.getZ(), 4, 0.1, 0.1, 0.1, 0.02);
        }
        this.discard();
    }
}
