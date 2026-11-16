package pryuan05.pysift.entity.mob;

import java.util.Optional;
import java.util.UUID;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.UUIDUtil;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Unit;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.warden.Warden;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * 隙浮守衛（MODDING_ROADMAP §4.7 第六幕）：治癒後的監守者，長回了赤紅的毛，不再挨餓、不再暴怒。
 * <ul>
 *   <li>沿用原版監守者的模型、動作與大腦，只是永遠不會生氣、不會鎖定目標、不會放黑暗（{@link pryuan05.pysift.entity.WardenSoothing}
 *       與 WardenMixin），也不會鑽回地底（一直刷新 DIG_COOLDOWN）。</li>
 *   <li>餵它一次迴音碎片就是你的了（收服），開始緊跟著你（超過 TELEPORT 格直接傳送到你身邊）。之後主人空手或拿別的東西右鍵：
 *       在「跟隨」與「坐下等待」之間切換（坐下動畫在用戶端 SiftWardenModel）。餵幽匿方塊回血。</li>
 *   <li>聆聽者：跟隨時 16 格內的敵對怪物每 3 秒發光（牠用聽的，隔牆也找得到）。</li>
 *   <li>不會自己找敵人、不會循著聲音或氣味去調查；只有主人被敵對怪物打到、或主人打了敵對怪物時，才對那一隻生氣（{@link #registerGuarding}、
 *       {@link #mayAttack}，WardenMixin）。
 *       近戰攻擊力 15（原版 30）、音爆傷害減半（SoulDeprivationDamageMixin）。</li>
 *   <li>親族：24 格內的野生監守者保持平靜。</li>
 *   <li>治癒腐爛：腳下 2 格內的藍幽匿慢慢變回赤紅幽匿（{@link pryuan05.pysift.block.RotSpread#healOne}）。</li>
 *   <li>來源：監守者泡在靈液裡或待在隙浮夠久（{@link pryuan05.pysift.entity.WardenCure}）。</li>
 * </ul>
 * 貼圖：tools/models/build_sift_warden.py；用戶端 SiftWardenRenderer。
 */
public class SiftWardenEntity extends Warden {
    private static final double FOLLOW_FAR = 4.0, TELEPORT = 14.0, GUARD_RANGE = 32.0;
    /** 主人被這隻怪物打了：唯一允許攻擊的對象（打死或離太遠就清掉）。 */
    private net.minecraft.world.entity.Entity guardTarget;
    private UUID owner;
    private boolean following;

    public SiftWardenEntity(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    /** 坐下等待（同步給用戶端播坐下動畫）。 */
    private static final net.minecraft.network.syncher.EntityDataAccessor<Boolean> DATA_SITTING =
            net.minecraft.network.syncher.SynchedEntityData.defineId(SiftWardenEntity.class, net.minecraft.network.syncher.EntityDataSerializers.BOOLEAN);
    /** 用戶端：坐下的進度 0（站）~ 1（坐），每 tick 往目標靠近，動畫才不會一瞬間跳過去。 */
    private float sitAmount, sitAmountO;

    @Override
    protected void defineSynchedData(net.minecraft.network.syncher.SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_SITTING, false);
    }

    public boolean isSitting() {
        return this.entityData.get(DATA_SITTING);
    }

    public float getSitAmount(float partialTick) {
        return net.minecraft.util.Mth.lerp(partialTick, sitAmountO, sitAmount);
    }

    private static final double LISTEN = 16.0, KIN = 24.0;
    /** 終章：鑽回地底、回到隙浮（{@link pryuan05.pysift.progression.Homecoming}）。 */
    private int homeTicks;

    public void goHome() {
        if (homeTicks > 0) {
            return;
        }
        homeTicks = 100;
        following = false;
        this.getBrain().eraseMemory(MemoryModuleType.WALK_TARGET);
        this.setPose(net.minecraft.world.entity.Pose.DIGGING);
        this.playSound(SoundEvents.WARDEN_DIG, 2.0f, 1.2f);
    }

    public boolean isGoingHome() {
        return homeTicks > 0;
    }

    public static net.minecraft.world.entity.ai.attributes.AttributeSupplier.Builder createSiftAttributes() {
        return Warden.createAttributes().add(net.minecraft.world.entity.ai.attributes.Attributes.ATTACK_DAMAGE, 15.0);
    }

    public UUID getOwner() {
        return owner;
    }

    /** 守衛可以攻擊 / 對牠生氣：只有主人剛和牠交手（被牠打、或打了牠）的那隻敵對怪物。 */
    public boolean mayAttack(net.minecraft.world.entity.Entity entity) {
        return entity != null && entity == guardTarget && entity.isAlive();
    }

    /** 主人被敵對怪物打到、或主人打了敵對怪物：附近 32 格內屬於他的隙浮守衛馬上對那隻怪物生氣（其他時候不會主動出手）。 */
    public static void registerGuarding() {
        net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.AFTER_DAMAGE.register((victim, source, base, taken, blocked) -> {
            net.minecraft.world.entity.Entity attacker = source.getEntity();
            Player owner;
            net.minecraft.world.entity.Entity foe;
            if (victim instanceof Player p && attacker instanceof net.minecraft.world.entity.monster.Enemy) {
                owner = p;
                foe = attacker;
            } else if (attacker instanceof Player p && victim instanceof net.minecraft.world.entity.monster.Enemy) {
                owner = p;
                foe = victim;
            } else {
                return;
            }
            if (foe instanceof Warden || !(owner.level() instanceof ServerLevel level)) {
                return;
            }
            UUID id = owner.getUUID();
            for (SiftWardenEntity w : level.getEntitiesOfClass(SiftWardenEntity.class, owner.getBoundingBox().inflate(GUARD_RANGE),
                    w -> id.equals(w.owner))) {
                w.guardTarget = foe;
                w.increaseAngerAt(foe, 120, false);
            }
        });
    }

    /** 不自己找事：清掉聲音／氣味的調查目標；沒在護主時也清掉攻擊與怒吼目標。被驚醒的回音窟守衛除外。 */
    private void suppressHunting(ServerLevel level) {
        if (pryuan05.pysift.entity.DenGuard.isRoused(this)) {
            return;
        }
        if (guardTarget != null && (!guardTarget.isAlive() || guardTarget.level() != level || this.distanceTo(guardTarget) > GUARD_RANGE)) {
            guardTarget = null;
        }
        var brain = this.getBrain();
        brain.eraseMemory(MemoryModuleType.DISTURBANCE_LOCATION);
        brain.setMemoryWithExpiry(MemoryModuleType.SNIFF_COOLDOWN, Unit.INSTANCE, 200L);
        if (guardTarget == null) {
            brain.eraseMemory(MemoryModuleType.ROAR_TARGET);
            brain.eraseMemory(MemoryModuleType.ATTACK_TARGET);
        }
    }

    /** 主人身邊 2~3 格內找一個站得下的位置，傳送過去。 */
    private boolean teleportTo(ServerLevel level, Player p) {
        for (int i = 0; i < 12; i++) {
            int dx = this.random.nextInt(7) - 3, dz = this.random.nextInt(7) - 3;
            if (Math.abs(dx) < 2 && Math.abs(dz) < 2) {
                continue;
            }
            for (int dy = 1; dy >= -2; dy--) {
                net.minecraft.core.BlockPos at = p.blockPosition().offset(dx, dy, dz);
                if (!level.getBlockState(at.below()).isFaceSturdy(level, at.below(), net.minecraft.core.Direction.UP)) {
                    continue;
                }
                var box = this.getBoundingBox().move(at.getX() + 0.5 - this.getX(), at.getY() - this.getY(), at.getZ() + 0.5 - this.getZ());
                if (level.noCollision(this, box) && !level.containsAnyLiquid(box)) {
                    this.snapTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, this.getYRot(), this.getXRot());
                    this.getNavigation().stop();
                    level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 1.0, this.getZ(), 12, 0.6, 1.0, 0.6, 0.03);
                    return true;
                }
            }
        }
        return false;
    }

    @Override
    public void tick() {
        super.tick();
        sitAmountO = sitAmount;
        sitAmount = net.minecraft.util.Mth.approach(sitAmount, isSitting() ? 1.0f : 0.0f, 0.1f);
        if (!(this.level() instanceof ServerLevel level)) {
            return;
        }
        if (homeTicks > 0) {   // 回家中：往下鑽，冒出泥土與靈魂，播完就消失
            this.getNavigation().stop();
            this.setDeltaMovement(0, this.getDeltaMovement().y, 0);
            if (homeTicks % 10 == 0) {
                level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 0.3, this.getZ(), 6, 0.7, 0.2, 0.7, 0.03);
            }
            if (--homeTicks == 0) {
                this.discard();
            }
            return;
        }
        // 不鑽回地底：監守者沒事做 1200 tick 後會挖地消失
        this.getBrain().setMemoryWithExpiry(MemoryModuleType.DIG_COOLDOWN, Unit.INSTANCE, 1200L);
        suppressHunting(level);
        boolean fighting = guardTarget != null || pryuan05.pysift.entity.DenGuard.isRoused(this);
        this.entityData.set(DATA_SITTING, !following && owner != null && !fighting);
        if (following && owner != null && !fighting && this.tickCount % 5 == 0) {
            Player p = level.getPlayerByUUID(owner);
            if (p != null && p.level() == level && !p.isSpectator()) {
                double d = this.distanceTo(p);
                if (d > TELEPORT && p.onGround()) {
                    teleportTo(level, p);
                } else if (d > FOLLOW_FAR) {
                    this.getBrain().setMemory(MemoryModuleType.WALK_TARGET, new WalkTarget(p, 1.2f, 2));
                } else {
                    this.getBrain().eraseMemory(MemoryModuleType.WALK_TARGET);
                }
            }
        } else if (!following && owner != null && !fighting) {   // 等待：站在原地不動（原版的閒晃會一直給牠新的走路目標）
            this.getBrain().eraseMemory(MemoryModuleType.WALK_TARGET);
            this.getNavigation().stop();
            this.setDeltaMovement(0, this.getDeltaMovement().y, 0);
        }
        if (following && this.tickCount % 60 == 0) {   // 聆聽者：附近的敵對怪物發光
            for (net.minecraft.world.entity.Mob m : level.getEntitiesOfClass(net.minecraft.world.entity.Mob.class,
                    this.getBoundingBox().inflate(LISTEN), m -> m instanceof net.minecraft.world.entity.monster.Enemy && !(m instanceof Warden))) {
                m.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.GLOWING, 80, 0, true, false));
            }
        }
        if (this.tickCount % 100 == 0) {   // 親族：野生監守者保持平靜
            for (Warden w : level.getEntitiesOfClass(Warden.class, this.getBoundingBox().inflate(KIN), w -> !(w instanceof SiftWardenEntity))) {
                pryuan05.pysift.entity.WardenSoothing.soothe(level, w, 120);
            }
        }
        pryuan05.pysift.entity.DenGuard.tick(this, level);   // 回音窟的守衛：被驚醒時追趕入侵者
        if (this.tickCount % 10 == 0) {   // 走過的地方，藍幽匿慢慢變回紅色
            net.minecraft.core.BlockPos p = this.blockPosition().offset(this.random.nextInt(5) - 2, -1 - this.random.nextInt(2), this.random.nextInt(5) - 2);
            pryuan05.pysift.block.RotSpread.healOne(level, p);
        }
        if (this.tickCount % 60 == 0 && this.random.nextInt(2) == 0) {
            level.sendParticles(ParticleTypes.GLOW, this.getX(), this.getY() + 2.2, this.getZ(), 2, 0.5, 0.4, 0.5, 0.01);
        }
    }

    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (stack.is(Items.SCULK) && this.getHealth() < this.getMaxHealth()) {   // 餵幽匿回血
            if (this.level() instanceof ServerLevel level) {
                stack.consume(1, player);
                this.heal(20.0f);
                this.playSound(SoundEvents.SCULK_BLOCK_CHARGE, 1.0f, 1.2f);
                level.sendParticles(ParticleTypes.HEART, this.getX(), this.getY() + this.getBbHeight() + 0.3, this.getZ(), 2, 0.4, 0.2, 0.4, 0);
            }
            return InteractionResult.SUCCESS;
        }
        boolean mine = owner != null && player.getUUID().equals(owner);
        if (owner == null) {   // 還沒有主人：餵一次迴音碎片就收服（被驚醒的回音窟守衛不收）
            if (!stack.is(Items.ECHO_SHARD) || pryuan05.pysift.entity.DenGuard.isRoused(this)) {
                return super.mobInteract(player, hand);
            }
            if (this.level() instanceof ServerLevel level) {
                stack.consume(1, player);
                pryuan05.pysift.entity.DenGuard.release(this);   // 收服之後不再是回音窟的守衛
                owner = player.getUUID();
                following = true;
                player.sendOverlayMessage(Component.translatable("message.pysift.sift_warden.tamed").withStyle(ChatFormatting.LIGHT_PURPLE));
                this.playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 1.5f, 0.6f);
                level.sendParticles(ParticleTypes.HEART, this.getX(), this.getY() + this.getBbHeight() + 0.3, this.getZ(), 6, 0.6, 0.3, 0.6, 0);
            }
            return InteractionResult.SUCCESS;
        }
        if (!mine || hand != InteractionHand.MAIN_HAND) {
            return super.mobInteract(player, hand);
        }
        if (this.level() instanceof ServerLevel level) {   // 主人右鍵：跟隨 ⇄ 坐下等待（不消耗任何東西）
            following = !following;
            guardTarget = null;
            this.getBrain().eraseMemory(MemoryModuleType.WALK_TARGET);
            this.getNavigation().stop();
            player.sendOverlayMessage(Component.translatable(following ? "message.pysift.sift_warden.follow" : "message.pysift.sift_warden.stay")
                    .withStyle(ChatFormatting.LIGHT_PURPLE));
            this.playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 1.0f, following ? 0.8f : 0.5f);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.WARDEN_LISTENING;   // 只會低聲咕嚕，不會哀嚎
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 1.25f;
    }

    @Override
    public void checkDespawn() {
        // 不會因為和平難度或距離而消失
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Following", following);
        if (owner != null) {
            output.store("Owner", UUIDUtil.CODEC, owner);
        }
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        following = input.getBooleanOr("Following", false);
        Optional<UUID> o = input.read("Owner", UUIDUtil.CODEC);
        owner = o.orElse(null);
    }
}
