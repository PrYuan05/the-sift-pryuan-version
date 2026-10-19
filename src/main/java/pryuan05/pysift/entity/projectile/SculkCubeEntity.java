package pryuan05.pysift.entity.projectile;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.animatable.instance.AnimatableInstanceCache;
import com.geckolib.animatable.manager.AnimatableManager;
import com.geckolib.animation.AnimationController;
import com.geckolib.animation.RawAnimation;
import com.geckolib.util.GeckoLibUtil;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
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
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.ModEntities;

/**
 * 幽匿方塊（Sculk Monstrosity 的「幽匿方塊彈幕」）：從 Boss 身邊彈出後落地，沿地面朝最近的玩家滾動，
 * 撞到人造成 {@link #DAMAGE} 點傷害並擊退後碎裂；撞牆、或滾了 6 秒還沒撞到人也會碎裂。
 * 外觀為 GeckoLib 模型 sculk_cube（tools/entity/build_sift_creatures.py）：彈出時微微脈動（idle），落地後翻滾前進、前方的石牙開闔（roll）。
 */
public class SculkCubeEntity extends ThrowableItemProjectile implements GeoEntity {
    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("animation.sculk_cube.idle");
    private static final RawAnimation ROLL = RawAnimation.begin().thenLoop("animation.sculk_cube.roll");
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private static final float DAMAGE = 7.0f;
    private static final double ROLL_SPEED = 0.32;
    private static final int LIFETIME = 120;

    public SculkCubeEntity(EntityType<? extends SculkCubeEntity> type, Level level) {
        super(type, level);
    }

    public SculkCubeEntity(Level level, LivingEntity owner) {
        super(ModEntities.SCULK_CUBE, owner, level, new ItemStack(Items.SCULK));
    }

    @Override
    protected Item getDefaultItem() {
        return Items.SCULK;
    }

    @Override
    public void tick() {
        super.tick();
        if (!(this.level() instanceof ServerLevel level) || this.isRemoved()) {
            return;
        }
        if (this.tickCount > LIFETIME) {
            shatter(level);
            return;
        }
        if (this.onGround() || this.tickCount > 12) {
            // 落地後沿地面滾向最近的玩家
            Player target = level.getNearestPlayer(this, 32);
            if (target != null && !target.isSpectator()) {
                Vec3 dir = target.position().subtract(this.position()).multiply(1, 0, 1);
                if (dir.lengthSqr() > 1.0E-4) {
                    dir = dir.normalize();
                    Vec3 v = this.getDeltaMovement();
                    this.setDeltaMovement(dir.x * ROLL_SPEED, v.y, dir.z * ROLL_SPEED);
                }
            }
            if (this.tickCount % 4 == 0) {
                level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, this.getX(), this.getY() + 0.1, this.getZ(), 2, 0.2, 0.05, 0.2, 0.01);
            }
        }
    }

    @Override
    protected void onHitBlock(BlockHitResult hit) {
        if (hit.getDirection() == Direction.UP) {
            // 落在地面上：停在地表，繼續滾
            Vec3 v = this.getDeltaMovement();
            this.setDeltaMovement(v.x, 0.0, v.z);
            this.setPos(this.getX(), hit.getLocation().y + 0.01, this.getZ());
            this.setOnGround(true);
            return;
        }
        if (this.level() instanceof ServerLevel level) {
            shatter(level);
        }
    }

    @Override
    protected void onHitEntity(EntityHitResult hit) {
        Entity e = hit.getEntity();
        if (!(this.level() instanceof ServerLevel level) || e instanceof Enemy || e == this.getOwner()) {
            return;
        }
        if (e instanceof LivingEntity living && living.hurtServer(level, this.damageSources().thrown(this, this.getOwner()), DAMAGE)) {
            Vec3 push = this.getDeltaMovement().multiply(1, 0, 1).normalize();
            living.setDeltaMovement(living.getDeltaMovement().add(push.x * 0.6, 0.3, push.z * 0.6));
            living.needsSync = true;
        }
        shatter(level);
    }

    private void shatter(ServerLevel level) {
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.SCULK.defaultBlockState()),
                this.getX(), this.getY() + 0.3, this.getZ(), 24, 0.3, 0.3, 0.3, 0.1);
        level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 0.3, this.getZ(), 3, 0.2, 0.2, 0.2, 0.02);
        this.playSound(SoundEvents.SCULK_BLOCK_BREAK, 1.0f, 0.8f);
        this.discard();
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        // 和伺服器端一樣：彈出約 12 tick 後（或落地後）開始滾
        controllers.add(new AnimationController<>("roll", 4,
                state -> state.setAndContinue(this.onGround() || this.tickCount > 12 ? ROLL : IDLE)));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
