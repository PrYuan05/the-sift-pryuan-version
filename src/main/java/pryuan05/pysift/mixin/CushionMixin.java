package pryuan05.pysift.mixin;

import net.minecraft.world.entity.decoration.Cushion;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.level.block.ColorCollection;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import pryuan05.pysift.block.SiftCushion;

/** 篩靈色坐墊：原版用 DyeColor 挑物品（掉落物、中鍵選取、破壞粒子）的地方改成坐墊自己的物品。原版坐墊不受影響。 */
@Mixin(Cushion.class)
public abstract class CushionMixin {
    @Redirect(method = {"showBreakingParticles", "getCushionItemStackWithData", "getPickResult"},
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/block/ColorCollection;pick(Lnet/minecraft/world/item/DyeColor;)Ljava/lang/Object;"))
    private Object pysift$siftItem(ColorCollection<?> items, DyeColor color) {
        return (Object) this instanceof SiftCushion sift ? sift.item() : items.pick(color);
    }
}
