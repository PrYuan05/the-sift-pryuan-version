package pryuan05.pysift.soulpower;

import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** 靈魂研磨機的介面：材料、結果、靈魂精華三格；資料 0 進度、1 轉速、2 容量、3 需求、4 是否過載。 */
public class SoulGrinderMenu extends AbstractContainerMenu {
    private final Container items;
    private final ContainerData data;

    public SoulGrinderMenu(int id, Inventory inventory) {
        this(id, inventory, new SimpleContainer(3), new SimpleContainerData(5));
    }

    public SoulGrinderMenu(int id, Inventory inventory, Container items, ContainerData data) {
        super(SoulPower.SOUL_GRINDER_MENU, id);
        this.items = items;
        this.data = data;
        addSlot(new Slot(items, 0, 56, 35));
        addSlot(new OutputSlot(items, 1, 116, 35));
        addSlot(new OutputSlot(items, 2, 116, 60));
        addStandardInventorySlots(inventory, 8, 84);
        addDataSlots(data);
    }

    public float progress() {
        return (float) data.get(0) / SoulGrinderBlockEntity.WORK;
    }

    public int speed() {
        return data.get(1);
    }

    public int capacity() {
        return data.get(2);
    }

    public int stress() {
        return data.get(3);
    }

    public boolean overloaded() {
        return data.get(4) != 0;
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        return SoulMenus.quickMove(this, slots, index, 3);
    }

    @Override
    public boolean stillValid(Player player) {
        return items.stillValid(player);
    }

    boolean move(ItemStack stack, int from, int to, boolean reverse) {
        // into the machine: only the input slot
        return moveItemStackTo(stack, from, from == 0 && !reverse ? 1 : to, reverse);
    }

    private static final class OutputSlot extends Slot {
        OutputSlot(Container container, int slot, int x, int y) {
            super(container, slot, x, y);
        }

        @Override
        public boolean mayPlace(ItemStack stack) {
            return false;
        }
    }
}
