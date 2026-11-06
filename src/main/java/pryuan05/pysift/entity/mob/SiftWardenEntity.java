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
 *   <li>餵它迴音碎片：開始跟著你走；再餵一次就留在原地等。餵幽匿方塊回血。</li>
 *   <li>聆聽者：跟隨時 16 格內的敵對怪物每 3 秒發光（牠用聽的，隔牆也找得到）。</li>
 *   <li>守護：只對敵對怪物生氣（WardenMixin），主人被怪物打、或主人打怪物時直接加滿憤怒（{@link #registerGuarding}）。
 *       近戰攻擊力 15（原版 30）、音爆傷害減半（SoulDeprivationDamageMixin）。</li>
 *   <li>親族：24 格內的野生監守者保持平靜。</li>
 *   <li>治癒腐爛：腳下 2 格內的藍幽匿慢慢變回赤紅幽匿（{@link pryuan05.pysift.block.RotSpread#healOne}）。</li>
 *   <li>來源：監守者泡在靈液裡或待在隙浮夠久（{@link pryuan05.pysift.entity.WardenCure}）。</li>
 * </ul>
 * 貼圖：tools/models/build_sift_warden.py；用戶端 SiftWardenRenderer。
 */
public class SiftWardenEntity extends Warden {
    private static final double FOLLOW_FAR = 6.0;
    private UUID owner;
    private boolean following;

    public SiftWardenEntity(EntityType<? extends Monster> type, Level level) {
        super(type, level);
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

    /** 主人被敵對怪物打到、或主人打到敵對怪物：附近 32 格內屬於他的隙浮守衛馬上對那隻怪物生氣。 */
    public static void registerGuarding() {
        net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.AFTER_DAMAGE.register((victim, source, base, taken, blocked) -> {
            net.minecraft.world.entity.Entity attacker = source.getEntity();
            Player owner = null;
            net.minecraft.world.entity.Entity foe = null;
            if (victim instanceof Player p && attacker instanceof net.minecraft.world.entity.monster.Enemy) {
                owner = p;
                foe = attacker;
            } else if (attacker instanceof Player p && victim instanceof net.minecraft.world.entity.monster.Enemy) {
                owner = p;
                foe = victim;
            }
            if (owner == null || foe instanceof Warden || !(owner.level() instanceof ServerLevel level)) {
                return;
            }
            UUID id = owner.getUUID();
            for (SiftWardenEntity w : level.getEntitiesOfClass(SiftWardenEntity.class, owner.getBoundingBox().inflate(32.0),
                    w -> id.equals(w.owner))) {
                w.increaseAngerAt(foe, 120, false);
            }
        });
    }

    @Override
    public void tick() {
        super.tick();
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
        if (following && owner != null && this.tickCount % 10 == 0) {
            Player p = level.getPlayerByUUID(owner);
            if (p != null && p.level() == level && !p.isSpectator() && this.distanceTo(p) > FOLLOW_FAR) {
                this.getBrain().setMemory(MemoryModuleType.WALK_TARGET, new WalkTarget(p, 1.0f, 3));
            }
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
        if (!stack.is(Items.ECHO_SHARD)) {
            return super.mobInteract(player, hand);
        }
        if (this.level() instanceof ServerLevel level) {
            stack.consume(1, player);
            if (following && player.getUUID().equals(owner)) {
                following = false;
                this.getBrain().eraseMemory(MemoryModuleType.WALK_TARGET);
                player.sendOverlayMessage(Component.translatable("message.pysift.sift_warden.stay").withStyle(ChatFormatting.LIGHT_PURPLE));
            } else {
                owner = player.getUUID();
                following = true;
                player.sendOverlayMessage(Component.translatable("message.pysift.sift_warden.follow").withStyle(ChatFormatting.LIGHT_PURPLE));
            }
            this.playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 1.5f, 0.6f);
            level.sendParticles(ParticleTypes.HEART, this.getX(), this.getY() + this.getBbHeight() + 0.3, this.getZ(), 3, 0.5, 0.2, 0.5, 0);
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
