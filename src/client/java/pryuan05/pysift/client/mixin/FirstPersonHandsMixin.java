package pryuan05.pysift.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.FirstPersonHandsAndItemsRenderer;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.state.level.FirstPersonHandsAndItemsRenderState;
import net.minecraft.client.renderer.state.level.PlayerRenderState;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pryuan05.pysift.client.WeaponPoses;

/**
 * 第一人稱：Boss 武器使用中的自訂姿勢（{@link WeaponPoses}）。submitArmWithItem 開頭記下這隻手拿的物品，
 * 原版把物品移到手上（applyItemArmTransform）之後再疊上姿勢。
 */
@Mixin(FirstPersonHandsAndItemsRenderer.class)
public class FirstPersonHandsMixin {
    @Unique
    private ItemStack pysift$current = ItemStack.EMPTY;

    @Inject(method = "submitArmWithItem", at = @At("HEAD"))
    private void pysift$remember(PlayerRenderState player, FirstPersonHandsAndItemsRenderState state, float a, float b,
                                 InteractionHand hand, float c, ItemStack stack, float d, PoseStack pose,
                                 SubmitNodeCollector collector, int light, CallbackInfo ci) {
        pysift$current = stack;
    }

    @Inject(method = "submitArmWithItem", at = @At("RETURN"))
    private void pysift$forget(PlayerRenderState player, FirstPersonHandsAndItemsRenderState state, float a, float b,
                               InteractionHand hand, float c, ItemStack stack, float d, PoseStack pose,
                               SubmitNodeCollector collector, int light, CallbackInfo ci) {
        pysift$current = ItemStack.EMPTY;
    }

    /** 左鍵揮擊：法杖橫掃、重錘左右交替斜劈，取代原版的揮擊。 */
    @Inject(method = "applyItemArmAttackTransform", at = @At("HEAD"), cancellable = true)
    private void pysift$weaponSwing(PoseStack pose, HumanoidArm arm, float swing, CallbackInfo ci) {
        if (WeaponPoses.firstPersonSwing(pose, arm, pysift$current, swing)) {
            ci.cancel();
        }
    }

    @Inject(method = "applyItemArmTransform", at = @At("TAIL"))
    private void pysift$weaponPose(PoseStack pose, HumanoidArm arm, float equip, CallbackInfo ci) {
        WeaponPoses.firstPerson(pose, arm, pysift$current);
    }
}
