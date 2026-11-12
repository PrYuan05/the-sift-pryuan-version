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
 * 靈液引擎：一格燃料，燒著的時候以 強度 15 的靈魂訊號運轉、提供 {@link #CAPACITY_PER_RPM} × RPM 的靈壓，
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
    /** 靈液泵經由靈液管送進來的靈液（mB）；燃料格空著時，每 1000 mB 燒一桶的時間。 */
    private int liquid;
    public static final int LIQUID_CAPACITY = 4000;
    private int burnMax;
    private int overload;
    /** 貼著原版紅石訊號：引擎關閉（總開關），燃料也暫停燃燒。 */
    private boolean halted;
    private final ContainerData data = new ContainerData() {
        @Override
        public int get(int i) {
            return switch (i) {
                case 0 -> burn;
                case 1 -> burnMax;
                case 2 -> network.speed();
                case 3 -> network.capacity();
                case 4 -> network.stress();
                case 5 -> network.overloaded() ? 1 : 0;
                default -> liquid;
            };
        }

        @Override
        public void set(int i, int value) {
        }

        @Override
        public int getCount() {
            return 7;
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
        boolean was = engine.sourceSpeed() != 0;
        engine.halted = SoulSignal.externalRedstone(level, pos) > 0;
        if (engine.burn > 0 && !engine.halted) {
            engine.burn--;
        }
        if (engine.burn == 0 && !engine.halted) {
            ItemStack stack = engine.fuel.getItem(0);
            int time = burnTime(stack);
            if (time <= 0 && engine.liquid >= 1000) {   // piped spirit liquid
                engine.liquid -= 1000;
                engine.burn = engine.burnMax = burnTime(new ItemStack(ModFluids.SPIRIT_LIQUID_BUCKET));
            } else if (time > 0) {
                engine.burn = engine.burnMax = time;
                engine.fuel.setItem(0, stack.is(ModFluids.SPIRIT_LIQUID_BUCKET) ? new ItemStack(Items.BUCKET) : stack.copyWithCount(stack.getCount() - 1));
            }
        }
        long now = level.getGameTime();
        // 每一次活塞行程（32 RPM ≈ 每 38 tick 轉一圈）噗一聲
        if (engine.speed != 0 && (now + pos.hashCode()) % Math.max(8, Math.round(1200f / Math.abs(engine.speed) / 1.0f)) == 0) {
            level.playSound(null, pos, pryuan05.pysift.sound.ModSounds.SPIRIT_ENGINE_CHUG, net.minecraft.sounds.SoundSource.BLOCKS,
                    0.55f, 0.9f + level.getRandom().nextFloat() * 0.15f);
        }
        boolean on = engine.sourceSpeed() != 0;
        if (on != was) {
            SoulSignal.update((ServerLevel) level, pos);
        } else if (now % SoulSignal.INTERVAL == 0 && engine.network.time() != now) {
            SoulSignal.poll((ServerLevel) level, pos);
        }
        if (on != was) {
            engine.setChanged();
        }
    }

    /** 靈液泵送來 amount mB：裝得下就收下。 */
    public boolean acceptLiquid(int amount) {
        if (liquid + amount > LIQUID_CAPACITY) {
            return false;
        }
        liquid += amount;
        setChanged();
        return true;
    }

    public int liquid() {
        return liquid;
    }

    public boolean isBurning() {
        return burn > 0;
    }

    /** 過載持續了多久（不過載就歸零）。 */
    public int countOverload(boolean overloaded, int ticks) {
        overload = overloaded ? overload + ticks : 0;
        return overload;
    }

    @Override
    public float sourceSpeed() {
        return isBurning() && !halted ? SoulSignal.SPEED : 0;
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
        output.putInt("Liquid", liquid);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        fuel.setItem(0, input.read("Fuel", ItemStack.CODEC).orElse(ItemStack.EMPTY));
        burn = input.getIntOr("Burn", 0);
        burnMax = input.getIntOr("BurnMax", 0);
        liquid = input.getIntOr("Liquid", 0);
    }
}
