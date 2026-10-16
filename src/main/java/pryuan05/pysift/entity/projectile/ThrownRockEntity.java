package pryuan05.pysift.entity.projectile;

import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
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
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.ModEntities;

/**
 * Hurler 投出的碎石。落地或命中時在半徑 {@link #RADIUS} 內造成鈍擊傷害並往外擊退（不傷害敵對生物）。外觀為鵝卵石物品。
 */
public class ThrownRockEntity extends ThrowableItemProjectile {
    private static final double RADIUS = 2.0;
    private float damage = 6.0f;

    public ThrownRockEntity(EntityType<? extends ThrownRockEntity> entityType, Level level) {
        super(entityType, level);
    }

    public ThrownRockEntity(Level level, LivingEntity owner, float damage) {
        super(ModEntities.THROWN_ROCK, owner, level, new ItemStack(Items.COBBLESTONE));
        this.damage = damage;
    }

    @Override
    protected Item getDefaultItem() {
        return Items.COBBLESTONE;
    }

    @Override
    protected void onHit(HitResult result) {
        super.onHit(result);
        if (!(this.level() instanceof ServerLevel level)) {
            return;
        }
        Vec3 c = this.position();
        Entity owner = this.getOwner();
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(RADIUS),
                e -> e != owner && e.isAlive() && !(e instanceof Enemy) && e.distanceToSqr(c) <= RADIUS * RADIUS * 1.5)) {
            if (e.hurtServer(level, this.damageSources().thrown(this, owner), damage)) {
                Vec3 away = e.position().subtract(c).multiply(1, 0, 1);
                Vec3 dir = away.lengthSqr() < 1.0E-4 ? Vec3.ZERO : away.normalize();
                e.setDeltaMovement(e.getDeltaMovement().add(dir.x * 0.8, 0.35, dir.z * 0.8));
                e.needsSync = true;
            }
        }
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.COBBLESTONE.defaultBlockState()),
                c.x, c.y + 0.2, c.z, 30, 0.6, 0.3, 0.6, 0.2);
        this.playSound(SoundEvents.STONE_BREAK, 1.5f, 0.7f);
        this.discard();
    }
}
