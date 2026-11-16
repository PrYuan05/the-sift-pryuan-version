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

/** 靈液引擎的介面：一格燃料，資料 0 燃燒剩餘、1 燃燒總長、2 轉速、3 容量、4 需求、5 是否過載。 */
public class SpiritEngineMenu extends AbstractContainerMenu {
    private final Container fuel;
    private final ContainerData data;

    public SpiritEngineMenu(int id, Inventory inventory) {
        this(id, inventory, new SimpleContainer(1), new SimpleContainerData(7));
    }

    public SpiritEngineMenu(int id, Inventory inventory, Container fuel, ContainerData data) {
        super(SoulPower.SPIRIT_ENGINE_MENU, id);
        this.fuel = fuel;
        this.data = data;
        addSlot(new Slot(fuel, 0, 56, 53) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return SpiritEngineBlockEntity.burnTime(stack) > 0;
            }
        });
        addStandardInventorySlots(inventory, 8, 84);
        addDataSlots(data);
    }

    public float burnProgress() {
        int max = data.get(1);
        return max <= 0 ? 0 : (float) data.get(0) / max;
    }

    public int speed() {
        return data.get(2);
    }

    public int capacity() {
        return data.get(3);
    }

    public int stress() {
        return data.get(4);
    }

    public boolean overloaded() {
        return data.get(5) != 0;
    }

    /** 靈液泵送進來、還沒燒的靈液（mB）。 */
    public int liquid() {
        return data.get(6);
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        return SoulMenus.quickMove(this, slots, index, 1);
    }

    @Override
    public boolean stillValid(Player player) {
        return fuel.stillValid(player);
    }

    boolean move(ItemStack stack, int from, int to, boolean reverse) {
        return moveItemStackTo(stack, from, to, reverse);
    }
}
