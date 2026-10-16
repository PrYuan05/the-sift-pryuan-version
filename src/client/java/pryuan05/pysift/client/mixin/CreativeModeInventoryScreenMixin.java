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
import pryuan05.pysift.block.ModBlocks;
import pryuan05.pysift.item.ModItems;

import java.util.List;

/**
 * 「Sift 方塊」分頁：每個方塊（含 block_state 變體）從新的一列開始。
 * 在分頁內容填入 menu.items 之後補上空格，再重新捲動一次讓格子更新。
 */
@Mixin(CreativeModeInventoryScreen.class)
public abstract class CreativeModeInventoryScreenMixin {
    @Shadow
    private static CreativeModeTab selectedTab;

    @Shadow
    private float scrollOffs;

    @Inject(method = {"selectTab", "refreshCurrentTabContents"}, at = @At("TAIL"))
    private void pysift$oneBlockPerRow(CallbackInfo ci) {
        if (selectedTab != ModItems.BLOCKS_TAB && selectedTab != ModItems.UNUSED_BLOCKS_TAB) {
            return;
        }
        CreativeModeInventoryScreen.ItemPickerMenu menu = ((CreativeModeInventoryScreen) (Object) this).getMenu();
        List<ItemStack> padded = CreativeTabRows.padBy(List.copyOf(menu.items), ModBlocks::rowKey);
        menu.items.clear();
        menu.items.addAll(padded);
        menu.scrollTo(this.scrollOffs);
    }
}
