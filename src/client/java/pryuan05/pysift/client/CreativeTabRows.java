package pryuan05.pysift.client;

import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.function.Function;

/**
 * 創造模式分頁排版：同一列鍵（rowKey）的物品排在一起，並補空格到下一列開頭，讓每一組從新的一列開始。
 * 一般方塊的列鍵是它自己的 Item（所有 block_state 變體同一列）；建材組整組共用一個列鍵。
 * 空格是 ItemStack.EMPTY，在創造模式畫面中就是點了沒反應的空格子。
 */
public final class CreativeTabRows {
    public static final int COLUMNS = 9;

    private CreativeTabRows() {
    }

    public static List<ItemStack> padByItem(List<ItemStack> items) {
        return padBy(items, ItemStack::getItem);
    }

    public static List<ItemStack> padBy(List<ItemStack> items, Function<ItemStack, Object> rowKey) {
        List<ItemStack> out = new ArrayList<>(items.size() + COLUMNS * 8);
        for (int i = 0; i < items.size(); i++) {
            ItemStack stack = items.get(i);
            out.add(stack);
            boolean lastOfGroup = i + 1 == items.size() || !Objects.equals(rowKey.apply(items.get(i + 1)), rowKey.apply(stack));
            if (lastOfGroup && i + 1 < items.size()) {
                while (out.size() % COLUMNS != 0) {
                    out.add(ItemStack.EMPTY);
                }
            }
        }
        return out;
    }
}
