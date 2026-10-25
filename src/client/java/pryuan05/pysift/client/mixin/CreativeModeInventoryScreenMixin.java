package pryuan05.pysift.client.mixin;

import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pryuan05.pysift.client.CreativeTabRows;
import pryuan05.pysift.item.CreativeLayout;
import pryuan05.pysift.item.ModItems;

import java.util.List;

/**
 * pysift 的三個分頁：依類別排序（生態域用到的排前面），每個類別從新的一列開始、大族獨佔整列、小族接在一起
 * （CreativeLayout + CreativeTabRows.layout）。在分頁內容填入 menu.items 之後重排，再重新捲動一次讓格子更新。
 */
@Mixin(CreativeModeInventoryScreen.class)
public abstract class CreativeModeInventoryScreenMixin {
    @Shadow
    private static CreativeModeTab selectedTab;

    @Shadow
    private float scrollOffs;

    @Inject(method = {"selectTab", "refreshCurrentTabContents"}, at = @At("TAIL"))
    private void pysift$arrangeRows(CallbackInfo ci) {
        if (selectedTab != ModItems.BLOCKS_TAB && selectedTab != ModItems.UNUSED_BLOCKS_TAB && selectedTab != ModItems.ITEMS_TAB) {
            return;
        }
        CreativeModeInventoryScreen.ItemPickerMenu menu = ((CreativeModeInventoryScreen) (Object) this).getMenu();
        List<ItemStack> padded = CreativeTabRows.layout(CreativeLayout.arrange(List.copyOf(menu.items)),
                CreativeLayout::section, CreativeLayout::group);
        menu.items.clear();
        menu.items.addAll(padded);
        menu.scrollTo(this.scrollOffs);
    }
}
