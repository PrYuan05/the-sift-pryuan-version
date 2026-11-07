package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Containers;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.MenuProvider;
import pryuan05.pysift.fluid.ModFluids;
import pryuan05.pysift.progression.ModProgression;

/**
 * 靈液引擎：一格燃料，燒著的時候以 {@link SoulNetwork#SPEED} RPM 轉動、提供 {@link #CAPACITY_PER_RPM} × RPM 的靈壓，
 * 並定期重算網路。
 */
public class SpiritEngineBlockEntity extends KineticBlockEntity implements MenuProvider, SoulKinetic.Source {
    public static final float CAPACITY_PER_RPM = 8f;   // 32 RPM → 256 SP
    private final SimpleContainer fuel = new SimpleContainer(1) {
        @Override
        public void setChanged() {
            super.setChanged();
            SpiritEngineBlockEntity.this.setChanged();
        }

        @Override
        public boolean canPlaceItem(int slot, ItemStack stack) {
            return burnTime(stack) > 0;
        }
    };
    private int burn;
    private int burnMax;
    private int overload;
    private final ContainerData data = new ContainerData() {
        @Override
        public int get(int i) {
            return switch (i) {
                case 0 -> burn;
                case 1 -> burnMax;
                case 2 -> network.speed();
                case 3 -> network.capacity();
                case 4 -> network.stress();
                default -> network.overloaded() ? 1 : 0;
            };
        }

        @Override
        public void set(int i, int value) {
        }

        @Override
        public int getCount() {
            return 6;
        }
    };

    public SpiritEngineBlockEntity(BlockPos pos, BlockState state) {
        super(SoulPower.SPIRIT_ENGINE_ENTITY, pos, state);
    }

    /** 燃料能燒多少 tick（0 = 不是燃料）。 */
    public static int burnTime(ItemStack stack) {
        if (stack.is(ModFluids.SPIRIT_LIQUID_BUCKET)) {
            return 3200;
        }
        if (stack.is(ModProgression.SOUL_ESSENCE)) {
            return 800;
        }
        if (stack.is(Items.SOUL_SAND) || stack.is(Items.SOUL_SOIL)) {
            return 200;
        }
        return 0;
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, SpiritEngineBlockEntity engine) {
        boolean was = engine.isBurning();
        if (engine.burn > 0) {
            engine.burn--;
        }
        if (engine.burn == 0) {
            ItemStack stack = engine.fuel.getItem(0);
            int time = burnTime(stack);
            if (time > 0) {
                engine.burn = engine.burnMax = time;
                engine.fuel.setItem(0, stack.is(ModFluids.SPIRIT_LIQUID_BUCKET) ? new ItemStack(Items.BUCKET) : stack.copyWithCount(stack.getCount() - 1));
            }
        }
        long now = level.getGameTime();
        if (engine.isBurning() != was || (now % SoulNetwork.INTERVAL == 0 && engine.network.time() != now)) {
            SoulNetwork.update((ServerLevel) level, pos);
        }
        if (engine.isBurning() != was) {
            engine.setChanged();
        }
    }

    public boolean isBurning() {
        return burn > 0;
    }

    /** 過載持續了多久（不過載就歸零）。 */
    int countOverload(boolean overloaded, int ticks) {
        overload = overloaded ? overload + ticks : 0;
        return overload;
    }

    @Override
    public float sourceSpeed() {
        return isBurning() ? SoulNetwork.SPEED : 0;
    }

    @Override
    public float capacityPerRpm() {
        return CAPACITY_PER_RPM;
    }

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.pysift.spirit_engine");
    }

    @Override
    public AbstractContainerMenu createMenu(int id, Inventory inventory, Player player) {
        return new SpiritEngineMenu(id, inventory, fuel, data);
    }

    @Override
    public void preRemoveSideEffects(BlockPos pos, BlockState state) {
        if (level != null) {
            Containers.dropContents(level, pos, fuel);
        }
        super.preRemoveSideEffects(pos, state);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        if (!fuel.getItem(0).isEmpty()) {
            output.store("Fuel", ItemStack.CODEC, fuel.getItem(0));
        }
        output.putInt("Burn", burn);
        output.putInt("BurnMax", burnMax);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        fuel.setItem(0, input.read("Fuel", ItemStack.CODEC).orElse(ItemStack.EMPTY));
        burn = input.getIntOr("Burn", 0);
        burnMax = input.getIntOr("BurnMax", 0);
    }
}
