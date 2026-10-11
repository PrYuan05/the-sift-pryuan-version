package pryuan05.pysift.entity.mob;

import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.*;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import pryuan05.pysift.entity.PysiftGeoEntity;

import java.util.UUID;

public class BlubEntity extends PysiftGeoEntity {
    private UUID ownerUUID;
    private boolean orderedToSit;

    public BlubEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 6.0f));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PathfinderMob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.22);
    }

    public boolean isTame() {
        return this.ownerUUID != null;
    }

    public boolean isOwnedBy(Player player) {
        return this.ownerUUID != null && this.ownerUUID.equals(player.getUUID());
    }

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack itemStack = player.getItemInHand(hand);
        if (!this.isTame()) {
            if (itemStack.is(Blocks.SOUL_SAND.asItem()) || itemStack.is(Blocks.SOUL_SOIL.asItem())) {
                if (!player.getAbilities().instabuild) {
                    itemStack.shrink(1);
                }
                if (!this.level().isClientSide()) {
                    if (this.random.nextInt(3) == 0) {
                        this.ownerUUID = player.getUUID();
                        this.level().broadcastEntityEvent(this, (byte) 7);
                    } else {
                        this.level().broadcastEntityEvent(this, (byte) 6);
                    }
                }
                return InteractionResult.SUCCESS;
            }
        } else if (this.isOwnedBy(player)) {
            if (!this.level().isClientSide()) {
                this.orderedToSit = !this.orderedToSit;
            }
            return InteractionResult.SUCCESS;
        }
        return super.mobInteract(player, hand);
    }
}
