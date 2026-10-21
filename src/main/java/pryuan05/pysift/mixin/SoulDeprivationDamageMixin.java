package pryuan05.pysift.mixin;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;
import pryuan05.pysift.progression.BossWeapons;

/** 怪物版靈魂剝奪：被剝奪的非玩家生物受到的傷害 +30%（玩家的靈魂剝奪規則見 SoulBurn）。 */
@Mixin(LivingEntity.class)
public abstract class SoulDeprivationDamageMixin {
    @ModifyVariable(method = "hurtServer", at = @At("HEAD"), argsOnly = true)
    private float pysift$soulDeprivedTakesMore(float amount, ServerLevel level, DamageSource source) {
        return BossWeapons.deprivedFoe((LivingEntity) (Object) this) ? amount * 1.3f : amount;
    }
}
