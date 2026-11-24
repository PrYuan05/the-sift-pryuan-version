package pryuan05.pysift.entity.mob;

import java.util.EnumSet;
import java.util.List;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.Identifier;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Shearable;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;
import pryuan05.pysift.entity.PysiftAnimalEntity;

/**
 * 親暱獸（溫馴，被動）。
 * <ul>
 *   <li>會主動走向 10 格內的玩家蹭臉（動畫 nuzzle），給予 10 秒發光與生命恢復 I；冷卻 60 秒。</li>
 *   <li>被攻擊時尖叫，並以 1.5 倍速度逃離攻擊者 10 秒。</li>
 *   <li>像原版的羊（使用者）：剪刀剪毛掉 1～3 個羊毛（沒染色是紅色羊毛，染過是那個顏色），剪過的毛 2～4 分鐘長回來；
 *       染料右鍵把毛染色。發射器也能剪（{@link Shearable}）。毛色、剪毛狀態同步給用戶端，渲染器換貼圖與染色。</li>
 * </ul>
 */
public class NuzzleEntity extends PysiftAnimalEntity implements Shearable {
    /** 毛：低 5 位元＝染色（0 是天生的紅色，n 是 DyeColor n-1），0x20＝剪過。 */
    private static final EntityDataAccessor<Byte> DATA_FUR = SynchedEntityData.defineId(NuzzleEntity.class, EntityDataSerializers.BYTE);
    private static final int SHEARED = 0x20;
    private int nuzzleCooldown = 100;
    private int furRegrow;

    public NuzzleEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftAnimalEntity.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.30);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new AvoidEntityGoal<>(this, LivingEntity.class, 12.0f, 1.5, 1.5, this::isRecentAttacker));
        this.goalSelector.addGoal(3, new NuzzlePlayerGoal());
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 6.0f));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
    }

    private boolean isRecentAttacker(LivingEntity e) {
        return e == this.getLastHurtByMob() && this.tickCount - this.getLastHurtByMobTimestamp() < 200;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_FUR, (byte) 0);
    }

    public boolean isSheared() {
        return (entityData.get(DATA_FUR) & SHEARED) != 0;
    }

    public void setSheared(boolean sheared) {
        int fur = entityData.get(DATA_FUR);
        entityData.set(DATA_FUR, (byte) (sheared ? fur | SHEARED : fur & ~SHEARED));
    }

    /** 染過的毛色；沒染過是 null（天生的顏色）。 */
    public @Nullable DyeColor getFurColor() {
        int c = entityData.get(DATA_FUR) & 0x1F;
        return c == 0 ? null : DyeColor.byId(c - 1);
    }

    public void setFurColor(@Nullable DyeColor color) {
        int fur = entityData.get(DATA_FUR) & SHEARED;
        entityData.set(DATA_FUR, (byte) (fur | (color == null ? 0 : color.getId() + 1)));
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (stack.is(Items.SHEARS)) {
            if (level() instanceof ServerLevel level && readyForShearing()) {
                shear(level, SoundSource.PLAYERS, stack);
                gameEvent(GameEvent.SHEAR, player);
                stack.hurtAndBreak(1, player, hand.asEquipmentSlot());
                return InteractionResult.SUCCESS_SERVER;
            }
            return InteractionResult.CONSUME;
        }
        DyeColor dye = stack.get(DataComponents.DYE);
        if (dye != null && !isSheared() && dye != getFurColor()) {
            if (!level().isClientSide()) {
                setFurColor(dye);
                level().playSound(null, this, SoundEvents.DYE_USE, SoundSource.PLAYERS, 1.0f, 1.0f);
                stack.consume(1, player);
            }
            return InteractionResult.SUCCESS;
        }
        return super.mobInteract(player, hand);
    }

    @Override
    public void shear(ServerLevel level, SoundSource source, ItemStack tool) {
        level.playSound(null, this, SoundEvents.SHEEP_SHEAR, source, 1.0f, 1.0f);
        setSheared(true);
        furRegrow = 2400 + random.nextInt(2400);
        DyeColor color = getFurColor();
        Item wool = BuiltInRegistries.ITEM.getValue(Identifier.withDefaultNamespace((color == null ? "red" : color.getName()) + "_wool"));
        int count = 1 + random.nextInt(3);
        for (int i = 0; i < count; i++) {
            ItemEntity drop = spawnAtLocation(level, new ItemStack(wool), 1.0f);
            if (drop != null) {
                drop.setDeltaMovement(drop.getDeltaMovement().add((random.nextFloat() - random.nextFloat()) * 0.1f,
                        random.nextFloat() * 0.05f, (random.nextFloat() - random.nextFloat()) * 0.1f));
            }
        }
    }

    @Override
    public boolean readyForShearing() {
        return isAlive() && !isSheared() && !isBaby();
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putByte("Fur", entityData.get(DATA_FUR));
        output.putInt("FurRegrow", furRegrow);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        entityData.set(DATA_FUR, input.getByteOr("Fur", (byte) 0));
        furRegrow = input.getIntOr("FurRegrow", 0);
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("nuzzle");
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        return super.hurtServer(level, source, amount);   // 尖叫由 getHurtSound 播放
    }

    @Override
    protected net.minecraft.sounds.SoundEvent getAmbientSound() {
        return pryuan05.pysift.sound.ModSounds.NUZZLE_AMBIENT;
    }

    @Override
    protected net.minecraft.sounds.SoundEvent getHurtSound(DamageSource source) {
        return pryuan05.pysift.sound.ModSounds.NUZZLE_HURT;
    }

    @Override
    protected net.minecraft.sounds.SoundEvent getDeathSound() {
        return pryuan05.pysift.sound.ModSounds.NUZZLE_DEATH;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (nuzzleCooldown > 0) {
            nuzzleCooldown--;
        }
        if (isSheared() && --furRegrow <= 0) {                  // 毛長回來
            setSheared(false);
        }
    }

    /** 走向最近的玩家，貼近後蹭一下。 */
    private class NuzzlePlayerGoal extends Goal {
        private Player player;

        NuzzlePlayerGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (nuzzleCooldown > 0 || tickCount - getLastHurtByMobTimestamp() < 200) {
                return false;
            }
            player = level().getNearestPlayer(NuzzleEntity.this, 10.0);
            return player != null && !player.isSpectator();
        }

        @Override
        public boolean canContinueToUse() {
            return player != null && player.isAlive() && nuzzleCooldown <= 0 && distanceToSqr(player) < 14 * 14;
        }

        @Override
        public void tick() {
            getLookControl().setLookAt(player, 30.0f, 30.0f);
            if (distanceToSqr(player) > 2.25) {
                if (tickCount % 10 == 0) {
                    getNavigation().moveTo(player, 1.0);
                }
                return;
            }
            getNavigation().stop();
            nuzzleCooldown = 1200;
            triggerAnim("skill", "nuzzle");
            playSound(pryuan05.pysift.sound.ModSounds.NUZZLE_NUZZLE, 1.0f, 1.0f);
            player.addEffect(new MobEffectInstance(MobEffects.GLOWING, 200, 0), NuzzleEntity.this);
            player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 200, 0), NuzzleEntity.this);
            if (level() instanceof ServerLevel level) {
                level.sendParticles(ParticleTypes.HEART, getX(), getY() + getBbHeight(), getZ(), 5, 0.4, 0.3, 0.4, 0.0);
            }
        }

        @Override
        public void stop() {
            player = null;
        }
    }
}
