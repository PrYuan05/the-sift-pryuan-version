package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Containers;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import pryuan05.pysift.progression.ModProgression;

import java.util.Optional;

/**
 * 靈魂研磨機：0 材料、1 結果、2 靈魂精華。轉速 {@link SoulNetwork#SPEED} RPM 時一次研磨 {@link #WORK} tick，
 * 轉速越快越快（進度每 tick 加 |RPM| / SPEED），但負載也跟著轉速變大。網路太久沒更新（拆了引擎、振波斷線）就自己重算。
 * 磨的時候噴出材料的碎屑；材料格同步給用戶端，渲染器把它畫在石磨上（client/soulpower/SoulPowerRenderer）。
 */
public class SoulGrinderBlockEntity extends KineticBlockEntity implements MenuProvider {
    public static final int WORK = 100;
    public static final float ESSENCE_CHANCE = 0.1f;
    private final SimpleContainer items = new SimpleContainer(3) {
        @Override
        public void setChanged() {
            super.setChanged();
            SoulGrinderBlockEntity.this.sync();   // 用戶端要知道石磨上正在磨什麼
        }

        @Override
        public boolean canPlaceItem(int slot, ItemStack stack) {
            return slot == 0;
        }
    };
    private float progress;
    private final ContainerData data = new ContainerData() {
        @Override
        public int get(int i) {
            return switch (i) {
                case 0 -> Math.round(progress);
                case 1 -> Math.round(Math.abs(speed));
                case 2 -> network.capacity();
                case 3 -> network.stress();
                default -> network.overloaded() ? 1 : 0;
            };
        }

        @Override
        public void set(int i, int value) {
        }

        @Override
        public int getCount() {
            return 5;
        }
    };

    public SoulGrinderBlockEntity(BlockPos pos, BlockState state) {
        super(SoulPower.SOUL_GRINDER_ENTITY, pos, state);
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, SoulGrinderBlockEntity grinder) {
        ServerLevel server = (ServerLevel) level;
        long now = level.getGameTime();
        if (now - grinder.network.time() > SoulNetwork.INTERVAL * 3L && now % SoulNetwork.INTERVAL == 0) {
            grinder.network = SoulNetwork.Result.IDLE;
            SoulNetwork.update(server, pos);
        }
        ItemStack input = grinder.items.getItem(0);
        if (grinder.speed == 0 || input.isEmpty()) {
            grinder.progress = 0;
            return;
        }
        SingleRecipeInput recipeInput = new SingleRecipeInput(input);
        Optional<RecipeHolder<SoulGrindingRecipe>> recipe = server.getServer().getRecipeManager()
                .getRecipeFor(SoulPower.SOUL_GRINDING, recipeInput, level);
        if (recipe.isEmpty()) {
            grinder.progress = 0;
            return;
        }
        ItemStack result = recipe.get().value().assemble(recipeInput);
        if (!grinder.fits(1, result)) {
            return;
        }
        grinder.progress += Math.abs(grinder.speed) / SoulNetwork.SPEED;
        if (now % 4 == 0) {   // 碎屑
            server.sendParticles(new net.minecraft.core.particles.ItemParticleOption(net.minecraft.core.particles.ParticleTypes.ITEM,
                            net.minecraft.world.item.ItemStackTemplate.fromNonEmptyStack(input)),
                    pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, 3, 0.25, 0.05, 0.25, 0.05);
        }
        if (grinder.progress < WORK) {
            return;
        }
        grinder.progress = 0;
        input.shrink(1);
        grinder.add(1, result);
        ItemStack essence = new ItemStack(ModProgression.SOUL_ESSENCE);
        if (level.getRandom().nextFloat() < ESSENCE_CHANCE && grinder.fits(2, essence)) {
            grinder.add(2, essence);
        }
        grinder.setChanged();
    }

    private boolean fits(int slot, ItemStack stack) {
        ItemStack cur = items.getItem(slot);
        return cur.isEmpty() || ItemStack.isSameItemSameComponents(cur, stack) && cur.getCount() + stack.getCount() <= cur.getMaxStackSize();
    }

    private void add(int slot, ItemStack stack) {
        ItemStack cur = items.getItem(slot);
        if (cur.isEmpty()) {
            items.setItem(slot, stack.copy());
        } else {
            cur.grow(stack.getCount());
            items.setChanged();
        }
    }

    /** 正在磨的材料（用戶端畫在石磨上）。 */
    public ItemStack input() {
        return items.getItem(0);
    }

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.pysift.soul_grinder");
    }

    @Override
    public AbstractContainerMenu createMenu(int id, Inventory inventory, Player player) {
        return new SoulGrinderMenu(id, inventory, items, data);
    }

    @Override
    public void preRemoveSideEffects(BlockPos pos, BlockState state) {
        if (level != null) {
            Containers.dropContents(level, pos, items);
        }
        super.preRemoveSideEffects(pos, state);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        for (int i = 0; i < items.getContainerSize(); i++) {
            if (!items.getItem(i).isEmpty()) {
                output.store("Slot" + i, ItemStack.CODEC, items.getItem(i));
            }
        }
        output.putFloat("Progress", progress);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        for (int i = 0; i < items.getContainerSize(); i++) {
            items.setItem(i, input.read("Slot" + i, ItemStack.CODEC).orElse(ItemStack.EMPTY));
        }
        progress = input.getFloatOr("Progress", 0f);
    }
}
