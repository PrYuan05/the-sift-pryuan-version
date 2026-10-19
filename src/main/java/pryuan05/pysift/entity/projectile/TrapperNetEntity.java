package pryuan05.pysift.entity.projectile;

import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import pryuan05.pysift.effect.ModEffects;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.item.ModItems;

/**
 * Trapper 丟出的網（外觀是使用者畫的粉紫靈魂網，物品 trapper_net）：命中非敵對生物時 2 點傷害、緩速 III 4 秒、定身 1 秒；撞到方塊就散開。
 */
public class TrapperNetEntity extends ThrowableItemProjectile {
    private static final float DAMAGE = 2.0f;

    public TrapperNetEntity(EntityType<? extends TrapperNetEntity> type, Level level) {
        super(type, level);
    }

    public TrapperNetEntity(Level level, LivingEntity owner) {
        super(ModEntities.TRAPPER_NET, owner, level, new ItemStack(ModItems.TRAPPER_NET));
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.TRAPPER_NET;
    }

    @Override
    protected void onHitEntity(EntityHitResult hit) {
        Entity e = hit.getEntity();
        if (!(this.level() instanceof ServerLevel level) || e instanceof Enemy || e == this.getOwner()) {
            return;
        }
        if (e instanceof LivingEntity living) {
            living.hurtServer(level, this.damageSources().thrown(this, this.getOwner()), DAMAGE);
            living.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 2), this.getOwner());
            living.addEffect(new MobEffectInstance(ModEffects.ENSNARED, 20, 0), this.getOwner());
            this.playSound(SoundEvents.WOOL_PLACE, 1.0f, 0.6f);
        }
        burst(level);
    }

    @Override
    protected void onHitBlock(BlockHitResult hit) {
        super.onHitBlock(hit);
        if (this.level() instanceof ServerLevel level) {
            burst(level);
        }
    }

    private void burst(ServerLevel level) {
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.COBWEB.defaultBlockState()),
                this.getX(), this.getY(), this.getZ(), 16, 0.3, 0.3, 0.3, 0.05);
        this.discard();
    }
}
