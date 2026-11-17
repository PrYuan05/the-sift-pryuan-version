package pryuan05.pysift.mixin;

import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import pryuan05.pysift.effect.ModEffects;
import pryuan05.pysift.progression.SoulWard;

/**
 * 靈魂護佑附魔（頭盔或胸甲）：靈魂剝奪加不上去。靈魂剝奪有好幾個來源直接 addEffect（靈液、衝鋒技能、武器、
 * 過載的靈魂線路），都會先問 canBeAffected，所以在這裡一次擋掉。
 */
@Mixin(LivingEntity.class)
public class SoulWardEffectMixin {
    @Inject(method = "canBeAffected", at = @At("HEAD"), cancellable = true)
    private void pysift$soulWard(MobEffectInstance effect, CallbackInfoReturnable<Boolean> cir) {
        LivingEntity self = (LivingEntity) (Object) this;
        if (effect.is(ModEffects.SOUL_DEPRIVATION) && !self.level().isClientSide() && SoulWard.isWarded(self)) {
            cir.setReturnValue(false);
        }
    }
}
