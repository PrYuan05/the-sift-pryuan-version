package pryuan05.pysift.soulpower;

import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

import java.util.List;

/** 靈魂動力機器介面的共用：shift 點擊在機器格與背包之間移動。 */
final class SoulMenus {
    private SoulMenus() {
    }

    /** 機器格是 0..machineSlots-1，後面是背包（27 + 快捷列 9）。 */
    static ItemStack quickMove(AbstractContainerMenu menu, List<Slot> slots, int index, int machineSlots) {
        Slot slot = slots.get(index);
        if (!slot.hasItem()) {
            return ItemStack.EMPTY;
        }
        ItemStack stack = slot.getItem();
        ItemStack copy = stack.copy();
        boolean moved = index < machineSlots
                ? move(menu, stack, machineSlots, machineSlots + 36, true)
                : move(menu, stack, 0, machineSlots, false);
        if (!moved) {
            return ItemStack.EMPTY;
        }
        if (stack.isEmpty()) {
            slot.setByPlayer(ItemStack.EMPTY);
        } else {
            slot.setChanged();
        }
        return copy;
    }

    private static boolean move(AbstractContainerMenu menu, ItemStack stack, int from, int to, boolean reverse) {
        if (menu instanceof SpiritEngineMenu m) {
            return m.move(stack, from, to, reverse);
        }
        return menu instanceof SoulGrinderMenu m && m.move(stack, from, to, reverse);
    }
}
