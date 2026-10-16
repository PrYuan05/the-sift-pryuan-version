package pryuan05.pysift.mixin;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.food.FoodData;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import pryuan05.pysift.effect.SoulBurn;

/**
 * 靈魂火灼燒的血量抽離期間，擋下飽食度帶來的自然回血（FoodData.tick 裡的兩次 heal：飽和快速回血與一般回血）。
 * 藥水、金蘋果等其他治療不受影響。
 */
@Mixin(FoodData.class)
public abstract class FoodDataMixin {
    @WrapOperation(method = "tick", at = @At(value = "INVOKE", target = "Lnet/minecraft/server/level/ServerPlayer;heal(F)V"))
    private void pysift$noRegenWhileSoulDrained(ServerPlayer player, float amount, Operation<Void> original) {
        if (!SoulBurn.regenBlocked(player)) {
            original.call(player, amount);
        }
    }
}
