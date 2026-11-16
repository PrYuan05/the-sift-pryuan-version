package pryuan05.pysift.client;

import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.function.Function;

/**
 * 創造模式分頁排版。{@link #layout} 依類別與族排版（pysift 三個分頁用）；{@link #padBy} 則是每一組都從新的一列開始。
 * 一般方塊的列鍵是它自己的 Item（所有 block_state 變體同一列）；建材組整組共用一個列鍵。
 * 空格是 ItemStack.EMPTY，在創造模式畫面中就是點了沒反應的空格子。
 */
public final class CreativeTabRows {
    public static final int COLUMNS = 9;

    private CreativeTabRows() {
    }

    /** 族的大小達到這個數量就獨佔整列（從新的一列開始、結束後補空格）；比較小的族接在同一列。 */
    public static final int BIG_GROUP = 5;

    /**
     * 分類排版：section 改變時一定換列；大族（≥ {@value #BIG_GROUP} 個）前後換列，小族緊接著排，
     * 減少一個物品佔一整列的空格。items 必須已經依族排在一起（CreativeLayout.arrange）。
     */
    public static List<ItemStack> layout(List<ItemStack> items, Function<ItemStack, Object> section, Function<ItemStack, Object> group) {
        List<ItemStack> out = new ArrayList<>(items.size() + COLUMNS * 8);
        int i = 0;
        Object lastSection = null;
        boolean lastWasBig = false;
        while (i < items.size()) {
            Object key = group.apply(items.get(i));
            int end = i;
            while (end < items.size() && Objects.equals(group.apply(items.get(end)), key)) {
                end++;
            }
            Object sec = section.apply(items.get(i));
            boolean big = end - i >= BIG_GROUP;
            if (!out.isEmpty() && (!Objects.equals(sec, lastSection) || big || lastWasBig)) {
                padRow(out);
            }
            out.addAll(items.subList(i, end));
            lastSection = sec;
            lastWasBig = big;
            i = end;
        }
        return out;
    }

    private static void padRow(List<ItemStack> out) {
        while (out.size() % COLUMNS != 0) {
            out.add(ItemStack.EMPTY);
        }
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
