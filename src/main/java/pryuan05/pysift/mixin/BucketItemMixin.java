package pryuan05.pysift.mixin;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.BucketItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.BucketPickup;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.phys.BlockHitResult;
import org.jspecify.annotations.Nullable;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import pryuan05.pysift.fluid.ModFluids;
import pryuan05.pysift.fluid.SpiritLogging;

/**
 * 含靈液的桶子操作（玩家與發射器都走這裡）：
 * <ul>
 *   <li>靈液桶倒向可含水、目前沒含水也沒含靈液的方塊 → 變成含靈液，不會把方塊打掉。</li>
 *   <li>靈液桶倒向已含水／已含靈液的方塊、水桶倒向已含靈液的方塊 → 像倒進已滿的方塊一樣，改倒在點擊面的前一格。</li>
 *   <li>空桶舀含靈液的方塊 → 拿到靈液桶，方塊留下、只是不再含靈液。</li>
 * </ul>
 */
@Mixin(BucketItem.class)
public abstract class BucketItemMixin {
    @Shadow @Final protected Fluid content;

    @Shadow public abstract boolean emptyContents(@Nullable LivingEntity user, Level level, BlockPos pos, @Nullable BlockHitResult hitResult);

    @Shadow protected abstract void playEmptySound(@Nullable LivingEntity user, LevelAccessor level, BlockPos pos);

    @Inject(method = "emptyContents", at = @At("HEAD"), cancellable = true)
    private void pysift$spiritlog(@Nullable LivingEntity user, Level level, BlockPos pos, @Nullable BlockHitResult hitResult,
                                  CallbackInfoReturnable<Boolean> cir) {
        BlockState state = level.getBlockState(pos);
        if (!SpiritLogging.supports(state)) {
            return;
        }
        boolean spirit = ModFluids.SPIRIT_LIQUID.isSame(this.content);
        if (spirit && SpiritLogging.canTake(state)) {
            SpiritLogging.fill(level, pos, state);
            this.playEmptySound(user, level, pos);
            cir.setReturnValue(true);
        } else if (spirit || SpiritLogging.isSpiritlogged(state)) {
            // the block is already full (or holds the other liquid): pour in front of the clicked face instead
            cir.setReturnValue(hitResult != null
                    && this.emptyContents(user, level, hitResult.getBlockPos().relative(hitResult.getDirection()), null));
        }
    }

    /**
     * use() 先決定要倒在哪一格：原版只有水桶會倒進被點的那格（LiquidBlockContainer），其他液體一律倒在點擊面的前一格。
     * 靈液桶點到可以含靈液的方塊時，改成倒進那一格本身。
     */
    @WrapOperation(method = "use", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/world/item/BucketItem;emptyContents(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/phys/BlockHitResult;)Z"))
    private boolean pysift$pourIntoClicked(BucketItem bucket, @Nullable LivingEntity user, Level level, BlockPos pos,
                                           @Nullable BlockHitResult hitResult, Operation<Boolean> original) {
        if (hitResult != null && ModFluids.SPIRIT_LIQUID.isSame(this.content)
                && SpiritLogging.canTake(level.getBlockState(hitResult.getBlockPos()))) {
            pos = hitResult.getBlockPos();
        }
        return original.call(bucket, user, level, pos, hitResult);
    }

    @WrapOperation(method = "use", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/world/level/block/BucketPickup;pickupBlock(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/level/LevelAccessor;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;)Lnet/minecraft/world/item/ItemStack;"))
    private ItemStack pysift$pickupSpirit(BucketPickup pickup, LivingEntity user, LevelAccessor level, BlockPos pos, BlockState state,
                                         Operation<ItemStack> original) {
        if (SpiritLogging.isSpiritlogged(state)) {
            level.setBlock(pos, state.setValue(SpiritLogging.SPIRITLOGGED, false), 3);
            return new ItemStack(ModFluids.SPIRIT_LIQUID_BUCKET);
        }
        return original.call(pickup, user, level, pos, state);
    }
}
