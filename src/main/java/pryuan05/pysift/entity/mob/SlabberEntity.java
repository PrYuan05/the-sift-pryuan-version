package pryuan05.pysift.entity.mob;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.animatable.instance.AnimatableInstanceCache;
import com.geckolib.animatable.manager.AnimatableManager;
import com.geckolib.animation.AnimationController;
import com.geckolib.animation.RawAnimation;
import com.geckolib.animation.object.PlayState;
import com.geckolib.util.GeckoLibUtil;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.BushBlock;
import net.minecraft.world.level.block.FlowerBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowParentGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import pryuan05.pysift.block.SoulCrystal;
import pryuan05.pysift.entity.ModEntities;

/**
 * 泥板獸（篩靈界的「牛」，友善）。背上是一片可以種花的土。
 * <ul>
 *   <li>種花：手持任一種花（#minecraft:flowers）右鍵光禿的背，把那朵花種上去；背上看得到那種花的模型。</li>
 *   <li>生長：每約 2 分鐘長一階（共 3 階，背上的花從 1 朵長到 5 朵）；骨粉可以直接長一階。</li>
 *   <li>採集：用剪刀剪下，長滿時得到 2~4 朵同種花（未長滿只拿回 1 朵），背上恢復光禿。</li>
 *   <li>和牛一樣用食物繁殖、會被食物引誘，但食物是靈魂晶塊；不能用桶擠奶。</li>
 * </ul>
 * 背上花朵的顯示在客戶端 SlabberRenderer（依同步的花與生長階段，畫在模型的 flower_1~5 骨骼上）。
 */
public class SlabberEntity extends Animal implements GeoEntity {
    private static final EntityDataAccessor<ItemStack> DATA_FLOWER = SynchedEntityData.defineId(SlabberEntity.class, EntityDataSerializers.ITEM_STACK);
    private static final EntityDataAccessor<Integer> DATA_GROWTH = SynchedEntityData.defineId(SlabberEntity.class, EntityDataSerializers.INT);
    /** 原版 #minecraft:flowers（含 The Sift 的花，見 build_vegetation.py 的 item/small_flowers）。 */
    private static final TagKey<Item> FLOWERS = TagKey.create(Registries.ITEM, Identifier.withDefaultNamespace("flowers"));
    public static final int MAX_GROWTH = 3;
    private static final int GROW_TICKS = 2400;

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private int growTimer;

    public SlabberEntity(EntityType<? extends Animal> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 30.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2)
                .add(Attributes.ARMOR, 4.0);
    }

    private static boolean isFoodItem(ItemStack stack) {
        return stack.is(SoulCrystal.SOUL_CRYSTAL_BLOCK_ITEM);
    }

    private static boolean isFlowerItem(ItemStack stack) {
        if (stack.is(FLOWERS)) {
            return true;
        }
        if (stack.getItem() instanceof BlockItem bi) {
            return bi.getBlock() instanceof FlowerBlock || bi.getBlock() instanceof BushBlock;
        }
        return false;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.SNIFFER_IDLE;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.SNIFFER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SNIFFER_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        this.playSound(SoundEvents.SNIFFER_STEP, 0.15f, 1.0f);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new PanicGoal(this, 1.6));
        this.goalSelector.addGoal(2, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(3, new TemptGoal(this, 1.2, SlabberEntity::isFoodItem, false));
        this.goalSelector.addGoal(4, new FollowParentGoal(this, 1.1));
        this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 6.0f));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
    }

    @Override
    public boolean isFood(ItemStack stack) {
        return isFoodItem(stack);
    }

    @Override
    public AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return ModEntities.SLABBER.create(level, EntitySpawnReason.BREEDING);
    }

    // ---------------------------------------------------------------- flowers on the back
    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_FLOWER, ItemStack.EMPTY);
        builder.define(DATA_GROWTH, 0);
    }

    /** 背上種的花（一朵）；空 = 光禿。 */
    public ItemStack getFlower() {
        return this.entityData.get(DATA_FLOWER);
    }

    /** 0 ~ MAX_GROWTH。 */
    public int getGrowth() {
        return this.entityData.get(DATA_GROWTH);
    }

    private void setFlower(ItemStack flower, int growth) {
        this.entityData.set(DATA_FLOWER, flower.copyWithCount(1));
        this.entityData.set(DATA_GROWTH, growth);
        growTimer = 0;
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (this.isBaby()) {
            if (isFoodItem(stack)) {
                this.usePlayerItem(player, hand, stack);
                this.ageUp(getSpeedUpSecondsWhenFeeding(-this.age), true);
                this.triggerAnim("skill", "eat");
                this.playSound(SoundEvents.SNIFFER_EAT, 1.0f, 1.2f);
                return InteractionResult.SUCCESS;
            }
            return super.mobInteract(player, hand);
        }
        if (stack.is(Items.BUCKET)) {
            return InteractionResult.PASS; // 泥板獸不是乳牛，不能擠奶
        }
        boolean bare = getFlower().isEmpty();
        if (bare && isFlowerItem(stack)) {                                 // 種花
            if (this.level() instanceof ServerLevel level) {
                setFlower(stack, 0);
                stack.consume(1, player);
                this.playSound(SoundEvents.CROP_PLANTED, 1.0f, 1.0f);
                level.sendParticles(ParticleTypes.HAPPY_VILLAGER, this.getX(), this.getY() + this.getBbHeight(), this.getZ(), 6, 0.4, 0.2, 0.4, 0);
            }
            return InteractionResult.SUCCESS;
        }
        if (!bare && stack.is(Items.BONE_MEAL) && getGrowth() < MAX_GROWTH) {      // 骨粉：長一階
            if (this.level() instanceof ServerLevel level) {
                stack.consume(1, player);
                setFlower(getFlower(), getGrowth() + 1);
                level.sendParticles(ParticleTypes.HAPPY_VILLAGER, this.getX(), this.getY() + this.getBbHeight(), this.getZ(), 10, 0.5, 0.3, 0.5, 0);
            }
            return InteractionResult.SUCCESS;
        }
        if (!bare && stack.is(Items.SHEARS)) {                                     // 採集
            if (this.level() instanceof ServerLevel level) {
                int count = getGrowth() >= MAX_GROWTH ? 2 + this.random.nextInt(3) : 1;
                this.spawnAtLocation(level, getFlower().copyWithCount(count), this.getBbHeight());
                setFlower(ItemStack.EMPTY, 0);
                stack.hurtAndBreak(1, player, hand);
                level.playSound(null, this, SoundEvents.SHEEP_SHEAR, SoundSource.PLAYERS, 1.0f, 1.0f);
            }
            return InteractionResult.SUCCESS;
        }
        if (isFoodItem(stack)) {
            InteractionResult res = super.mobInteract(player, hand);
            if (res.consumesAction()) {
                this.triggerAnim("skill", "eat");
                this.playSound(SoundEvents.SNIFFER_EAT, 1.0f, 1.0f);
            }
            return res;
        }
        return super.mobInteract(player, hand);   // 繁殖（靈魂晶塊）；不能擠奶
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (!getFlower().isEmpty() && getGrowth() < MAX_GROWTH && ++growTimer >= GROW_TICKS) {
            setFlower(getFlower(), getGrowth() + 1);
        }
        // 閒置時有機率低頭聞嗅地面花草或靈魂土壤
        if (this.random.nextInt(250) == 0 && this.getDeltaMovement().horizontalDistanceSqr() < 1.0e-4) {
            this.triggerAnim("skill", "sniff");
        }
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (!getFlower().isEmpty()) {
            output.store("Flower", ItemStack.CODEC, getFlower());
        }
        output.putInt("FlowerGrowth", getGrowth());
        output.putInt("FlowerTimer", growTimer);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        setFlower(input.read("Flower", ItemStack.CODEC).orElse(ItemStack.EMPTY), input.getIntOr("FlowerGrowth", 0));
        growTimer = input.getIntOr("FlowerTimer", 0);
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (source.is(DamageTypeTags.IS_PROJECTILE)) {
            this.triggerAnim("skill", "deflect");
            level.playSound(null, this, SoundEvents.SHIELD_BLOCK, SoundSource.NEUTRAL, 1.0f, 0.8f);
            level.sendParticles(ParticleTypes.CRIT, this.getX(), this.getY() + this.getBbHeight() * 0.8, this.getZ(), 8, 0.2, 0.2, 0.2, 0.1);
            return super.hurtServer(level, source, amount * 0.25f);
        }
        if (source.getEntity() != null) {
            this.triggerAnim("skill", "deflect");
        }
        return super.hurtServer(level, source, amount);
    }

    // ---------------------------------------------------------------- GeckoLib
    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>("movement", 5, state ->
                state.setAndContinue(state.isMoving()
                        ? RawAnimation.begin().thenLoop("animation.slabber.walk")
                        : RawAnimation.begin().thenLoop("animation.slabber.idle"))));

        AnimationController<SlabberEntity> skill = new AnimationController<>("skill", 2, state -> PlayState.STOP);
        skill.triggerableAnim("deflect", RawAnimation.begin().thenPlay("animation.slabber.deflect"));
        skill.triggerableAnim("sniff", RawAnimation.begin().thenPlay("animation.slabber.sniff"));
        skill.triggerableAnim("eat", RawAnimation.begin().thenPlay("animation.slabber.eat"));
        controllers.add(skill);
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
