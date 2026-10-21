package pryuan05.pysift.entity.mob;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.animatable.instance.AnimatableInstanceCache;
import com.geckolib.animatable.manager.AnimatableManager;
import com.geckolib.animation.AnimationController;
import com.geckolib.animation.RawAnimation;
import com.geckolib.animation.object.PlayState;
import com.geckolib.util.GeckoLibUtil;
import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.RandomSource;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowOwnerGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.SitWhenOrderedToGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtTargetGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;
import pryuan05.pysift.PySift;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.sound.ModSounds;

import java.util.Comparator;
import java.util.EnumSet;
import java.util.List;
import java.util.function.Supplier;

/**
 * 布魯布（官方吉祥物，可馴服）。
 * 擁有 5 種變體（Minecraft Dungeons II）：
 * <ul>
 *   <li>Soul engorged（充盈靈魂／默認）- 生成於靈魂沙／楊柳林</li>
 *   <li>Carapace（甲殼）- 生成於琥珀沙丘</li>
 *   <li>Meadows（草甸）- 生成於楊柳林／草甸</li>
 *   <li>Ravines（峽谷）- 生成於赤紅岩峽谷</li>
 *   <li>Fungal（真菌）- 生成於幽影菌洞穴／深板岩層</li>
 * </ul>
 * 特色：
 * <ul>
 *   <li>喜歡靈魂沙／靈魂土：手持會被引誘；未馴服時餵食有 1/3 機率馴服，也用來繁殖與回血。</li>
 *   <li>馴服後會跟隨主人；主人空手（或拿非食物）右鍵切換坐下。</li>
 *   <li>血量低於 50% 時，"mood" 控制器循環播放委屈動畫（sad）。</li>
 *   <li>馴服後會幫忙打架（像狼：攻擊主人打的、或打主人的目標；不打苦力怕、主人的其他寵物與其他布魯布）。</li>
 *   <li>馴服後會撿東西：8 格內的掉落物叼起一整疊，送回主人的背包（主人自己丟出的東西不撿）。死掉時叼著的東西會掉出來。</li>
 * </ul>
 */
public class BlubEntity extends TamableAnimal implements GeoEntity {
    public enum Variant implements StringRepresentable {
        SOUL_ENGORGED(0, "soul_engorged", "entity.pysift.blub.variant.soul_engorged", () -> ModSounds.BLUB_IDLE),
        CARAPACE(1, "carapace", "entity.pysift.blub.variant.carapace", () -> ModSounds.BLUB_CARAPACE_IDLE),
        MEADOWS(2, "meadows", "entity.pysift.blub.variant.meadows", () -> ModSounds.BLUB_MEADOWS_IDLE),
        RAVINES(3, "ravines", "entity.pysift.blub.variant.ravines", () -> ModSounds.BLUB_RAVINES_IDLE),
        FUNGAL(4, "fungal", "entity.pysift.blub.variant.fungal", () -> ModSounds.BLUB_FUNGAL_IDLE);

        public static final Codec<Variant> CODEC = StringRepresentable.fromEnum(Variant::values);
        private static final Variant[] BY_ID = values();

        private final int id;
        private final String name;
        private final String translationKey;
        private final Supplier<SoundEvent> ambientSound;

        Variant(int id, String name, String translationKey, Supplier<SoundEvent> ambientSound) {
            this.id = id;
            this.name = name;
            this.translationKey = translationKey;
            this.ambientSound = ambientSound;
        }

        public int getId() {
            return this.id;
        }

        @Override
        public String getSerializedName() {
            return this.name;
        }

        public String getTranslationKey() {
            return this.translationKey;
        }

        public SoundEvent getAmbientSound() {
            return this.ambientSound.get();
        }

        public static Variant byId(int id) {
            if (id < 0 || id >= BY_ID.length) {
                return SOUL_ENGORGED;
            }
            return BY_ID[id];
        }

        public static Variant byName(String name) {
            for (Variant v : BY_ID) {
                if (v.name.equalsIgnoreCase(name)) {
                    return v;
                }
            }
            return SOUL_ENGORGED;
        }
    }

    private static final EntityDataAccessor<Integer> DATA_VARIANT = SynchedEntityData.defineId(BlubEntity.class, EntityDataSerializers.INT);

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    /** 正叼著、要送回給主人的東西（不放在手上，免得武器加到攻擊力或被當成裝備掉落）。 */
    private ItemStack carried = ItemStack.EMPTY;

    public BlubEntity(EntityType<? extends TamableAnimal> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.28)
                .add(Attributes.ATTACK_DAMAGE, 4.0);
    }

    private static boolean isSoulBlock(ItemStack stack) {
        return stack.is(Blocks.SOUL_SAND.asItem()) || stack.is(Blocks.SOUL_SOIL.asItem());
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_VARIANT, Variant.SOUL_ENGORGED.getId());
    }

    public Variant getVariant() {
        return Variant.byId(this.entityData.get(DATA_VARIANT));
    }

    public void setVariant(Variant variant) {
        this.entityData.set(DATA_VARIANT, variant.getId());
    }

    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason, @Nullable SpawnGroupData spawnData) {
        SpawnGroupData data = super.finalizeSpawn(level, difficulty, reason, spawnData);
        Variant variant = determineVariant(level, this.blockPosition(), this.random);
        this.setVariant(variant);
        return data;
    }

    private static Variant determineVariant(ServerLevelAccessor level, BlockPos pos, RandomSource random) {
        Holder<Biome> biomeHolder = level.getBiome(pos);
        Identifier biomeKey = biomeHolder.unwrapKey().map(net.minecraft.resources.ResourceKey::identifier).orElse(null);
        if (biomeKey != null) {
            String path = biomeKey.getPath();
            if (path.contains("amber_dunes")) return Variant.CARAPACE;
            if (path.contains("crimson_strata_canyon")) return Variant.RAVINES;
            if (path.contains("willow_grove")) return random.nextBoolean() ? Variant.MEADOWS : Variant.SOUL_ENGORGED;
            if (path.contains("violet_slate_abyss")) return Variant.FUNGAL;
            // 原版維度生成的適配
            if (path.contains("soul_sand")) return Variant.SOUL_ENGORGED;
            if (path.contains("desert") || path.contains("badlands") || path.contains("savanna")) return Variant.CARAPACE;
            if (path.contains("meadow") || path.contains("plains") || path.contains("forest")) return Variant.MEADOWS;
            if (path.contains("canyon") || path.contains("dripstone") || path.contains("ravine")) return Variant.RAVINES;
            if (path.contains("mushroom") || path.contains("deep_dark") || path.contains("lush_caves") || path.contains("swamp")) return Variant.FUNGAL;
        }
        if (pos.getY() < 40) {
            return Variant.FUNGAL;
        }
        return Variant.byId(random.nextInt(Variant.values().length));
    }

    @Override
    public void setCustomName(@Nullable Component name) {
        super.setCustomName(name);
        if (name != null) {
            String str = name.getString().trim().toLowerCase();
            if (str.contains("carapace")) {
                this.setVariant(Variant.CARAPACE);
            } else if (str.contains("meadow")) {
                this.setVariant(Variant.MEADOWS);
            } else if (str.contains("ravine")) {
                this.setVariant(Variant.RAVINES);
            } else if (str.contains("fungal") || str.contains("fungus")) {
                this.setVariant(Variant.FUNGAL);
            } else if (str.contains("soul")) {
                this.setVariant(Variant.SOUL_ENGORGED);
            }
        }
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new PanicGoal(this, 1.25));
        this.goalSelector.addGoal(2, new SitWhenOrderedToGoal(this));
        this.goalSelector.addGoal(3, new MeleeAttackGoal(this, 1.25, true));
        this.goalSelector.addGoal(4, new FetchItemGoal(this));
        this.goalSelector.addGoal(5, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(6, new TemptGoal(this, 1.1, BlubEntity::isSoulBlock, false));
        this.goalSelector.addGoal(7, new FollowOwnerGoal(this, 1.0, 6.0f, 2.0f));
        this.goalSelector.addGoal(8, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(9, new LookAtPlayerGoal(this, Player.class, 6.0f));
        this.goalSelector.addGoal(10, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new OwnerHurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new OwnerHurtTargetGoal(this));
        this.targetSelector.addGoal(3, new HurtByTargetGoal(this).setAlertOthers());
    }

    // ---------------------------------------------------------------- fighting
    @Override
    public boolean wantsToAttack(LivingEntity target, LivingEntity owner) {
        if (target instanceof Creeper || target instanceof BlubEntity) {
            return false;
        }
        if (target instanceof TamableAnimal pet && pet.isTame() && pet.getOwner() == owner) {
            return false;
        }
        return !(target instanceof Player victim && owner instanceof Player master && !master.canHarmPlayer(victim));
    }

    // ---------------------------------------------------------------- fetching
    /** 叼著東西回到主人身邊：放進主人背包（滿了就丟在主人腳邊）。 */
    private void deliver(Player owner) {
        if (!owner.getInventory().add(carried)) {
            this.spawnAtLocation((ServerLevel) this.level(), carried);
        }
        carried = ItemStack.EMPTY;
        this.playSound(SoundEvents.ITEM_PICKUP, 0.6f, 1.4f);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level() instanceof ServerLevel && !carried.isEmpty() && this.getOwner() instanceof Player owner
                && this.distanceToSqr(owner) < 6.25) {
            deliver(owner);
        }
    }

    @Override
    protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean killedByPlayer) {
        super.dropCustomDeathLoot(level, source, killedByPlayer);
        if (!carried.isEmpty()) {
            this.spawnAtLocation(level, carried);
            carried = ItemStack.EMPTY;
        }
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (!carried.isEmpty()) {
            output.store("Carried", ItemStack.CODEC, carried);
        }
        output.putInt("Variant", this.getVariant().getId());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        carried = input.read("Carried", ItemStack.CODEC).orElse(ItemStack.EMPTY);
        setVariant(Variant.byId(input.getIntOr("Variant", 0)));
    }

    // ---------------------------------------------------------------- sounds
    @Override
    protected SoundEvent getAmbientSound() {
        return this.getVariant().getAmbientSound();
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return ModSounds.BLUB_LAND;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return ModSounds.BLUB_LAND;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        this.playSound(ModSounds.BLUB_STEP, 0.4f, 1.0f);
    }

    @Override
    public void jumpFromGround() {
        super.jumpFromGround();
        this.playSound(ModSounds.BLUB_JUMP, 0.45f, 1.0f);
    }

    @Override
    protected void checkFallDamage(double y, boolean onGround, BlockState state, BlockPos pos) {
        super.checkFallDamage(y, onGround, state, pos);
        if (onGround && this.fallDistance > 0.5f) {
            this.playSound(ModSounds.BLUB_LAND, 0.4f, 1.0f);
        }
    }

    /** 走到附近的掉落物把它叼起來；叼到之後由 FollowOwnerGoal 跟回主人，在 aiStep 交貨。 */
    static class FetchItemGoal extends Goal {
        private static final double RANGE = 8.0;
        private final BlubEntity blub;
        private ItemEntity target;
        private int timeout;

        FetchItemGoal(BlubEntity blub) {
            this.blub = blub;
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (!blub.isTame() || blub.isOrderedToSit() || !blub.carried.isEmpty() || blub.getTarget() != null
                    || !(blub.getOwner() instanceof Player owner) || blub.distanceToSqr(owner) > 24 * 24
                    || blub.getRandom().nextInt(5) != 0) {
                return false;
            }
            List<ItemEntity> items = blub.level().getEntitiesOfClass(ItemEntity.class, blub.getBoundingBox().inflate(RANGE, 3.0, RANGE),
                    item -> item.isAlive() && !item.hasPickUpDelay() && item.getOwner() != owner && !item.getItem().isEmpty());
            target = items.stream().min(Comparator.comparingDouble(item -> item.distanceToSqr(blub))).orElse(null);
            return target != null;
        }

        @Override
        public boolean canContinueToUse() {
            return target != null && target.isAlive() && blub.carried.isEmpty() && timeout > 0 && !blub.isOrderedToSit()
                    && blub.getTarget() == null;
        }

        @Override
        public void start() {
            timeout = 200;
            blub.getNavigation().moveTo(target, 1.2);
        }

        @Override
        public void stop() {
            target = null;
            blub.getNavigation().stop();
        }

        @Override
        public void tick() {
            timeout--;
            blub.getLookControl().setLookAt(target, 30.0f, 30.0f);
            if (blub.distanceToSqr(target) < 2.25) {
                blub.carried = target.getItem().copy();
                blub.take(target, blub.carried.getCount());
                target.discard();
                blub.playSound(SoundEvents.ITEM_PICKUP, 0.6f, 1.0f);
                target = null;
            } else if (blub.getNavigation().isDone()) {
                blub.getNavigation().moveTo(target, 1.2);
            }
        }
    }

    @Override
    public boolean isFood(ItemStack stack) {
        return isSoulBlock(stack);
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        if (player.getAbilities().instabuild && player.isShiftKeyDown()) {
            if (!this.level().isClientSide()) {
                Variant next = Variant.byId((this.getVariant().getId() + 1) % Variant.values().length);
                this.setVariant(next);
                player.sendSystemMessage(Component.literal("Blub Variant: " + next.getSerializedName()));
            }
            return InteractionResult.SUCCESS;
        }
        ItemStack stack = player.getItemInHand(hand);
        if (!this.isTame() && isSoulBlock(stack)) {
            stack.consume(1, player);
            if (this.level() instanceof ServerLevel) {
                if (this.random.nextInt(3) == 0) {
                    this.tame(player);
                    this.navigation.stop();
                    this.setOrderedToSit(true);
                    this.level().broadcastEntityEvent(this, (byte) 7);   // 愛心粒子
                } else {
                    this.level().broadcastEntityEvent(this, (byte) 6);   // 煙霧粒子
                }
            }
            return InteractionResult.SUCCESS;
        }
        if (this.isTame() && isSoulBlock(stack) && this.getHealth() < this.getMaxHealth()) {
            stack.consume(1, player);
            this.heal(4.0f);
            return InteractionResult.SUCCESS;
        }
        InteractionResult result = super.mobInteract(player, hand);   // 繁殖
        if (!result.consumesAction() && this.isTame() && this.isOwnedBy(player)) {
            this.setOrderedToSit(!this.isOrderedToSit());
            this.jumping = false;
            this.navigation.stop();
            this.setTarget(null);
            return InteractionResult.SUCCESS;
        }
        return result;
    }

    @Override
    public AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        BlubEntity baby = ModEntities.BLUB.create(level, EntitySpawnReason.BREEDING);
        if (baby != null) {
            if (this.isTame()) {
                baby.setOwnerReference(this.getOwnerReference());
                baby.setTame(true, true);
            }
            if (partner instanceof BlubEntity otherBlub) {
                baby.setVariant(this.random.nextBoolean() ? this.getVariant() : otherBlub.getVariant());
            } else {
                baby.setVariant(this.getVariant());
            }
        }
        return baby;
    }

    // ---------------------------------------------------------------- GeckoLib
    private boolean isSad() {
        return this.getHealth() < this.getMaxHealth() * 0.5f;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>("movement", 4, state -> {
            if (state.isMoving()) {
                if (this.isSprinting() || this.isPanicking() || this.getTarget() != null) {
                    return state.setAndContinue(RawAnimation.begin().thenLoop("animation.blub.run"));
                }
                return state.setAndContinue(RawAnimation.begin().thenLoop("animation.blub.walk"));
            }
            return state.setAndContinue(RawAnimation.begin().thenLoop("animation.blub.idle"));
        }));
        // 耳朵／心情：血量低於一半時循環 sad（客戶端依同步的血量判斷）
        controllers.add(new AnimationController<>("mood", 8, state -> this.isSad()
                ? state.setAndContinue(RawAnimation.begin().thenLoop("animation.blub.sad"))
                : PlayState.STOP));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
