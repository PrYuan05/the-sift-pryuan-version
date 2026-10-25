package pryuan05.pysift.progression;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;

import java.util.function.Consumer;

/** 一般物品，說明欄顯示用法提示（例如召喚印記要在哪裡用、隙浮信標寶石怎麼鑲嵌）。 */
public class HintItem extends Item {
    private final String[] hintKeys;

    public HintItem(Properties properties, String... hintKeys) {
        super(properties);
        this.hintKeys = hintKeys;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> out, TooltipFlag flag) {
        for (String key : hintKeys) {
            out.accept(Component.translatable(key).withStyle(ChatFormatting.GRAY));
        }
    }
}
