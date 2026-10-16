package pryuan05.pysift.entity.mob;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.animatable.instance.AnimatableInstanceCache;
import com.geckolib.animatable.manager.AnimatableManager;
import com.geckolib.animation.AnimationController;
import com.geckolib.animation.RawAnimation;
import com.geckolib.animation.object.PlayState;
import com.geckolib.util.GeckoLibUtil;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.BreedGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowOwnerGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.SitWhenOrderedToGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import pryuan05.pysift.entity.ModEntities;

/**
 * 布魯布（官方吉祥物，可馴服）。
 * <ul>
 *   <li>喜歡靈魂沙／靈魂土：手持會被引誘；未馴服時餵食有 1/3 機率馴服，也用來繁殖與回血。</li>
 *   <li>馴服後會跟隨主人；主人空手（或拿非食物）右鍵切換坐下。</li>
 *   <li>血量低於 50% 時，"mood" 控制器循環播放委屈動畫（sad）。</li>
 * </ul>
 */
public class BlubEntity extends TamableAnimal implements GeoEntity {
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    public BlubEntity(EntityType<? extends TamableAnimal> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.28);
    }

    private static boolean isSoulBlock(ItemStack stack) {
        return stack.is(Blocks.SOUL_SAND.asItem()) || stack.is(Blocks.SOUL_SOIL.asItem());
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new PanicGoal(this, 1.25));
        this.goalSelector.addGoal(2, new SitWhenOrderedToGoal(this));
        this.goalSelector.addGoal(3, new BreedGoal(this, 1.0));
        this.goalSelector.addGoal(4, new TemptGoal(this, 1.1, BlubEntity::isSoulBlock, false));
        this.goalSelector.addGoal(5, new FollowOwnerGoal(this, 1.0, 6.0f, 2.0f));
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 6.0f));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
    }

    @Override
    public boolean isFood(ItemStack stack) {
        return isSoulBlock(stack);
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
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
        if (baby != null && this.isTame()) {
            baby.setOwnerReference(this.getOwnerReference());
            baby.setTame(true, true);
        }
        return baby;
    }

    // ---------------------------------------------------------------- GeckoLib
    private boolean isSad() {
        return this.getHealth() < this.getMaxHealth() * 0.5f;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>("movement", 5, state ->
                state.setAndContinue(state.isMoving()
                        ? RawAnimation.begin().thenLoop("animation.blub.walk")
                        : RawAnimation.begin().thenLoop("animation.blub.idle"))));
        // 耳朵／心情：血量低於一半時循環 sad（客戶端依同步的血量判斷）
        controllers.add(new AnimationController<>("mood", 8, state -> isSad()
                ? state.setAndContinue(RawAnimation.begin().thenLoop("animation.blub.sad"))
                : PlayState.STOP));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
