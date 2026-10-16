package pryuan05.pysift.entity.projectile;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.entity.projectile.arrow.Arrow;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.ModEntities;

/**
 * 尖刺飛鏢（Dartback 背刺、Prickle 的尖刺環）。外觀沿用原版箭矢渲染器，不能撿起。
 */
public class DartEntity extends Arrow {
    public DartEntity(EntityType<? extends Arrow> entityType, Level level) {
        super(entityType, level);
        this.pickup = AbstractArrow.Pickup.DISALLOWED;
    }

    /** 從 shooter 身上 (x, y, z) 發射的飛鏢，傷害為 damage（原版箭的基礎傷害是 2，實際傷害會乘上速度）。 */
    public static DartEntity create(Level level, LivingEntity shooter, double x, double y, double z, double damage) {
        DartEntity dart = new DartEntity(ModEntities.DART, level);
        dart.setOwner(shooter);
        dart.setPos(x, y, z);
        dart.setBaseDamage(damage);
        return dart;
    }
}
