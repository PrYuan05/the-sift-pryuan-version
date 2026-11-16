package pryuan05.pysift.mixin;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.decoration.Cushion;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.level.block.ColorCollection;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.SiftCushion;

/**
 * 篩靈色坐墊：原版用 DyeColor 挑東西的地方改成坐墊自己的顏色。原版坐墊不受影響。
 * 掉落物、中鍵選取挑的是物品（坐墊物品）；破壞粒子挑的是羊毛「方塊」（Blocks.WOOL），所以要給同色的篩靈羊毛方塊。
 */
@Mixin(Cushion.class)
public abstract class CushionMixin {
    @Redirect(method = {"getCushionItemStackWithData", "getPickResult"},
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/block/ColorCollection;pick(Lnet/minecraft/world/item/DyeColor;)Ljava/lang/Object;"))
    private Object pysift$siftItem(ColorCollection<?> items, DyeColor color) {
        return (Object) this instanceof SiftCushion sift ? sift.item() : items.pick(color);
    }

    @Redirect(method = "showBreakingParticles",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/block/ColorCollection;pick(Lnet/minecraft/world/item/DyeColor;)Ljava/lang/Object;"))
    private Object pysift$siftWool(ColorCollection<?> wool, DyeColor color) {
        return (Object) this instanceof SiftCushion sift
                ? BuiltInRegistries.BLOCK.getValue(PySift.id(sift.getSiftColor().id + "_wool"))
                : wool.pick(color);
    }
}
