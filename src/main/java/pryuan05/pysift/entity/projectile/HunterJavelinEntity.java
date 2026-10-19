package pryuan05.pysift.entity.projectile;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.entity.projectile.arrow.Arrow;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.ModEntities;

/**
 * 獵人的靈魂標槍：外觀是使用者畫的標槍（HunterJavelinRenderer，箭矢模型放大 2 倍），不能撿起，飛行時拖著靈魂火。
 * 傷害 = 基礎傷害 × 速度（{@link #create} 用 3.5，投擲速度 1.7 時約 6 點）。
 */
public class HunterJavelinEntity extends Arrow {
    public HunterJavelinEntity(EntityType<? extends Arrow> entityType, Level level) {
        super(entityType, level);
        this.pickup = AbstractArrow.Pickup.DISALLOWED;
    }

    public static HunterJavelinEntity create(Level level, LivingEntity thrower) {
        HunterJavelinEntity javelin = new HunterJavelinEntity(ModEntities.HUNTER_JAVELIN, level);
        javelin.setOwner(thrower);
        javelin.setPos(thrower.getX(), thrower.getEyeY() - 0.2, thrower.getZ());
        javelin.setBaseDamage(3.5);
        return javelin;
    }

    @Override
    public void tick() {
        super.tick();
        if (this.level() instanceof ServerLevel level && !this.isInGround() && this.tickCount % 2 == 0) {
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, this.getX(), this.getY(), this.getZ(), 1, 0.02, 0.02, 0.02, 0.0);
        }
    }
}
