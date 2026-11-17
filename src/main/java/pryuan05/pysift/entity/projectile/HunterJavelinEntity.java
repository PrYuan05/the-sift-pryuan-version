package pryuan05.pysift.entity.projectile;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.entity.projectile.arrow.Arrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.ModEntities;

/**
 * 獵人的靈魂標槍：外觀是使用者畫的標槍（HunterJavelinRenderer，箭矢模型放大 2 倍），不能撿起，飛行時拖著靈魂火。
 * 傷害 = 基礎傷害 × 速度（{@link #create} 用 3.5，投擲速度 1.7 時約 6 點）。
 * <p>
 * 玩家擲出的標槍（{@link #thrown}）帶著物品本身：命中時算物品上的附魔（放血、纏縛，{@link #getWeaponItem}），
 * 有歸魂附魔時照原版三叉戟的忠誠飛回主人身邊（回程速度讀附魔資料的 trident_return_acceleration，數值也照三叉戟）。
 */
public class HunterJavelinEntity extends Arrow {
    private static final double BASE_DAMAGE = 3.5;
    /** 歸魂等級；-1 = 還沒從物品讀出來（讀存檔後重新讀）。 */
    private int homecoming = -1;
    private boolean dealtDamage;
    private boolean returnSounded;

    public HunterJavelinEntity(EntityType<? extends Arrow> entityType, Level level) {
        super(entityType, level);
        this.pickup = AbstractArrow.Pickup.DISALLOWED;
    }

    public static HunterJavelinEntity create(Level level, LivingEntity thrower) {
        HunterJavelinEntity javelin = new HunterJavelinEntity(ModEntities.HUNTER_JAVELIN, level);
        javelin.setOwner(thrower);
        javelin.setPos(thrower.getX(), thrower.getEyeY() - 0.2, thrower.getZ());
        javelin.setBaseDamage(BASE_DAMAGE);
        return javelin;
    }

    /** 玩家擲出的靈魂標槍（物品 soul_javelin）：可以撿回來，創造模式不會掉。 */
    public static HunterJavelinEntity thrown(Level level, Player thrower, ItemStack stack) {
        HunterJavelinEntity javelin = new HunterJavelinEntity(ModEntities.HUNTER_JAVELIN, level);
        javelin.setOwner(thrower);
        javelin.setPos(thrower.getX(), thrower.getEyeY() - 0.1, thrower.getZ());
        javelin.setBaseDamage(BASE_DAMAGE);
        javelin.setPickupItemStack(stack.copyWithCount(1));
        javelin.pickup = thrower.hasInfiniteMaterials() ? AbstractArrow.Pickup.CREATIVE_ONLY : AbstractArrow.Pickup.ALLOWED;
        return javelin;
    }

    /** 玩家擲出的才帶著物品（獵人丟的不能撿，也沒有附魔）。 */
    private boolean isPlayerThrown() {
        return this.pickup != AbstractArrow.Pickup.DISALLOWED;
    }

    @Override
    public ItemStack getWeaponItem() {
        return isPlayerThrown() ? this.getPickupItemStackOrigin() : super.getWeaponItem();
    }

    private int homecoming() {
        if (this.homecoming < 0) {
            this.homecoming = this.level() instanceof ServerLevel server && isPlayerThrown()
                    ? Mth.clamp(EnchantmentHelper.getTridentReturnToOwnerAcceleration(server, this.getPickupItemStackOrigin(), this), 0, 127) : 0;
        }
        return this.homecoming;
    }

    @Override
    public void tick() {
        if (this.inGroundTime > 4) {
            this.dealtDamage = true;
        }
        Entity owner = this.getOwner();
        int loyalty = this.level() instanceof ServerLevel ? homecoming() : 0;
        if (loyalty > 0 && (this.dealtDamage || this.isNoPhysics()) && owner != null) {
            if (!owner.isAlive() || owner.isSpectator()) {
                if (this.level() instanceof ServerLevel server && this.pickup == AbstractArrow.Pickup.ALLOWED) {
                    this.spawnAtLocation(server, this.getPickupItem(), 0.1f);
                }
                this.discard();
                return;
            }
            // ThrownTrident.tick: fly back to the owner's eyes
            this.setNoPhysics(true);
            Vec3 to = owner.getEyePosition().subtract(this.position());
            this.setPosRaw(this.getX(), this.getY() + to.y * 0.015 * loyalty, this.getZ());
            this.setDeltaMovement(this.getDeltaMovement().scale(0.95).add(to.normalize().scale(0.05 * loyalty)));
            this.needsSync = true;
            if (!this.returnSounded) {
                this.playSound(SoundEvents.TRIDENT_RETURN, 10.0f, 1.0f);
                this.returnSounded = true;
            }
        }
        super.tick();
        if (this.level() instanceof ServerLevel level && !this.isInGround() && this.tickCount % 2 == 0) {
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, this.getX(), this.getY(), this.getZ(), 1, 0.02, 0.02, 0.02, 0.0);
        }
    }

    /** 有歸魂時像三叉戟一樣命中後彈開（之後飛回來）；沒有時和箭一樣。 */
    @Override
    protected void onHitEntity(EntityHitResult result) {
        if (homecoming() <= 0) {
            super.onHitEntity(result);
            return;
        }
        Entity target = result.getEntity();
        Entity owner = this.getOwner();
        DamageSource source = this.damageSources().arrow(this, owner == null ? this : owner);
        float damage = (float) Mth.ceil(Mth.clamp(this.getDeltaMovement().length() * BASE_DAMAGE, 0.0, Integer.MAX_VALUE));
        if (this.level() instanceof ServerLevel server) {
            damage = EnchantmentHelper.modifyDamage(server, this.getWeaponItem(), target, source, damage);
        }
        this.dealtDamage = true;
        if (target.hurtOrSimulate(source, damage) && target instanceof LivingEntity living) {
            if (this.level() instanceof ServerLevel server) {
                EnchantmentHelper.doPostAttackEffectsWithItemSourceOnBreak(server, living, source, this.getWeaponItem(), item -> this.discard());
            }
            this.doKnockback(living, source);
            this.doPostHurtEffects(living);
        }
        this.setDeltaMovement(this.getDeltaMovement().multiply(-0.02, -0.2, -0.02));
        this.playSound(SoundEvents.TRIDENT_HIT, 1.0f, 1.0f);
    }

    /** 飛回來的標槍碰到主人就回到背包（ThrownTrident.tryPickup）。 */
    @Override
    protected boolean tryPickup(Player player) {
        return super.tryPickup(player) || this.isNoPhysics() && this.ownedBy(player) && player.getInventory().add(this.getPickupItem());
    }

    /** 有歸魂的標槍不會因為插在地上太久而消失（它會飛回來）。 */
    @Override
    protected void tickDespawn() {
        if (homecoming() <= 0 || this.pickup != AbstractArrow.Pickup.ALLOWED) {
            super.tickDespawn();
        }
    }
}
