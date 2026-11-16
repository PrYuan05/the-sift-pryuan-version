package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.ItemTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.phys.BlockHitResult;
import pryuan05.pysift.fluid.ModFluids;

/**
 * 鏽黑石（rusted_dark_cobble，v2.1.0）：靈魂火山錐上的富鐵火山渣。火山噴的是靈魂不是岩漿，火山口的靈液湖冒出帶著靈魂的
 * 水氣，濕氣讓石頭裡的鐵慢慢生鏽，所以越靠近火山口越鏽（世界生成：y 90-104 是 rust 0／1，y 104-120 是 rust 2／3）。
 * <ul>
 *   <li>像原版的銅一樣會變化：附近（{@link #SPIRIT_RANGE} 格內）有靈液時，隨機刻有 1 / {@link #RUST_CHANCE} 的機率再鏽一階，
 *       最多到 3。離開靈液就停在原地。</li>
 *   <li>斧頭右鍵刮掉一階鏽（像刮銅）；蜂巢右鍵封住（sealed=true，像上蠟），封住的不會再鏽，斧頭會先把封蠟刮掉。</li>
 *   <li>最鏽的 rust 3 放進靈魂研磨機會磨出鐵粒（data/pysift/recipe/soul_grinding/rust_blackstone.json）。</li>
 * </ul>
 * 挖下來會保留鏽蝕程度與封蠟（掉落表 copy_state）。
 */
public class RustBlackstone extends Block {
    public static final IntegerProperty RUST = IntegerProperty.create("rust", 0, 3);
    public static final BooleanProperty SEALED = BooleanProperty.create("sealed");
    /** 靈液要在這個距離（格）內才會生鏽。 */
    public static final int SPIRIT_RANGE = 3;
    /** 每次隨機刻再鏽一階的機率是 1 / RUST_CHANCE（原版銅約 1/18，這裡快一點，因為只有靈液旁才會鏽）。 */
    public static final int RUST_CHANCE = 6;

    public RustBlackstone(BlockBehaviour.Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(RUST, 0).setValue(SEALED, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(RUST, SEALED);
    }

    @Override
    protected boolean isRandomlyTicking(BlockState state) {
        return !state.getValue(SEALED) && state.getValue(RUST) < 3;
    }

    @Override
    protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (random.nextInt(RUST_CHANCE) == 0 && nearSpiritLiquid(level, pos)) {
            level.setBlock(pos, state.setValue(RUST, state.getValue(RUST) + 1), Block.UPDATE_ALL);
        }
    }

    /** 附近有沒有靈液（水源或流動的都算：濕氣就是從那裡來的）。 */
    private static boolean nearSpiritLiquid(Level level, BlockPos pos) {
        for (BlockPos p : BlockPos.betweenClosed(pos.offset(-SPIRIT_RANGE, -SPIRIT_RANGE, -SPIRIT_RANGE),
                pos.offset(SPIRIT_RANGE, SPIRIT_RANGE, SPIRIT_RANGE))) {
            var fluid = level.getFluidState(p).getType();
            if (fluid == ModFluids.SPIRIT_LIQUID || fluid == ModFluids.FLOWING_SPIRIT_LIQUID) {
                return true;
            }
        }
        return false;
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          InteractionHand hand, BlockHitResult hit) {
        if (stack.is(ItemTags.AXES)) {
            BlockState changed;
            if (state.getValue(SEALED)) {                               // the wax comes off first, like waxed copper
                changed = state.setValue(SEALED, false);
                level.playSound(player, pos, SoundEvents.AXE_WAX_OFF.value(), SoundSource.BLOCKS, 1.0f, 1.0f);
                level.levelEvent(player, 3004, pos, 0);
            } else if (state.getValue(RUST) > 0) {                      // scrape one stage of rust off
                changed = state.setValue(RUST, state.getValue(RUST) - 1);
                level.playSound(player, pos, SoundEvents.AXE_SCRAPE.value(), SoundSource.BLOCKS, 1.0f, 1.0f);
                level.levelEvent(player, 3005, pos, 0);
            } else {
                return InteractionResult.TRY_WITH_EMPTY_HAND;
            }
            apply(level, pos, player, changed);
            stack.hurtAndBreak(1, player, hand.asEquipmentSlot());
            return InteractionResult.SUCCESS;
        }
        if (stack.is(Items.HONEYCOMB) && !state.getValue(SEALED)) {     // seal it: no more rust
            apply(level, pos, player, state.setValue(SEALED, true));
            level.playSound(player, pos, SoundEvents.HONEYCOMB_WAX_ON, SoundSource.BLOCKS, 1.0f, 1.0f);
            level.levelEvent(player, 3003, pos, 0);
            stack.consume(1, player);
            return InteractionResult.SUCCESS;
        }
        return super.useItemOn(stack, state, level, pos, player, hand, hit);
    }

    private static void apply(Level level, BlockPos pos, Player player, BlockState changed) {
        level.setBlock(pos, changed, Block.UPDATE_ALL_IMMEDIATE);
        level.gameEvent(GameEvent.BLOCK_CHANGE, pos, GameEvent.Context.of(player, changed));
    }
}
