package pryuan05.pysift.mixin;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.ShieldDecorationRecipe;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import pryuan05.pysift.block.SiftColors;

/** 篩靈色旗幟套到盾牌上：結果另外記 pysift:base_color（原版的 base_color 是白色）。 */
@Mixin(ShieldDecorationRecipe.class)
public abstract class ShieldDecorationRecipeMixin {
    @Inject(method = "assemble(Lnet/minecraft/world/item/crafting/CraftingInput;)Lnet/minecraft/world/item/ItemStack;", at = @At("RETURN"))
    private void pysift$siftBase(CraftingInput input, CallbackInfoReturnable<ItemStack> cir) {
        ItemStack result = cir.getReturnValue();
        if (result.isEmpty()) {
            return;
        }
        for (int i = 0; i < input.size(); i++) {
            SiftColors.SiftColor color = SiftColors.bannerColor(input.getItem(i));
            if (color != null) {
                result.set(SiftColors.BASE_COLOR, color);
                return;
            }
        }
        result.remove(SiftColors.BASE_COLOR);   // a vanilla banner on a shield that had a Sift one before
    }
}
