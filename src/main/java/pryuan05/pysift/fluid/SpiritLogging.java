package pryuan05.pysift.fluid;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.material.FluidState;

/**
 * 「含靈液」（spiritlogged）：和原版的含水一樣，但裡面是靈液。
 * <ul>
 *   <li>所有有 {@code waterlogged} 屬性的方塊（原版、本模組、其他模組）在建立狀態表時自動多一個 {@link #SPIRITLOGGED}
 *       屬性（StateDefinitionBuilderMixin），預設 false（BlockMixin）。</li>
 *   <li>{@code spiritlogged=true} 的狀態，流體是靈液源頭（BlockStateBaseMixin.getFluidState），所以渲染、流動、
 *       實體浸泡效果、方塊被破壞後留下靈液，都和含水的水一樣自動成立。</li>
 *   <li>靈液桶倒進可含水的方塊、空桶舀起、在靈液裡放置方塊：BucketItemMixin、BlockItemMixin。</li>
 *   <li>同一格不會同時含水又含靈液：已含靈液的方塊倒水會失敗（像倒進已經含水的方塊），反之亦然。</li>
 * </ul>
 * 這個類別在原版方塊註冊（Bootstrap）時就會被載入，所以這裡不能在靜態初始化時碰 ModFluids。
 */
public final class SpiritLogging {
    public static final BooleanProperty SPIRITLOGGED = BooleanProperty.create("spiritlogged");

    private SpiritLogging() {
    }

    /** 這個狀態能不能含靈液（有 waterlogged 屬性的方塊才有 spiritlogged）。 */
    public static boolean supports(BlockState state) {
        return state.hasProperty(SPIRITLOGGED);
    }

    public static boolean isSpiritlogged(BlockState state) {
        return state.hasProperty(SPIRITLOGGED) && state.getValue(SPIRITLOGGED);
    }

    /** 可以倒入靈液：支援、而且目前既沒含水也沒含靈液。 */
    public static boolean canTake(BlockState state) {
        return supports(state) && !state.getValue(SPIRITLOGGED)
                && !(state.hasProperty(BlockStateProperties.WATERLOGGED) && state.getValue(BlockStateProperties.WATERLOGGED));
    }

    public static FluidState source() {
        return ModFluids.SPIRIT_LIQUID.getSource(false);
    }

    /** 倒入靈液：設成 spiritlogged 並排程流體 tick，讓它往外流。 */
    public static boolean fill(LevelAccessor level, BlockPos pos, BlockState state) {
        if (!canTake(state)) {
            return false;
        }
        if (!level.isClientSide()) {
            level.setBlock(pos, state.setValue(SPIRITLOGGED, true), 3);
            level.scheduleTick(pos, ModFluids.SPIRIT_LIQUID, ModFluids.SPIRIT_LIQUID.getTickDelay(level));
        }
        return true;
    }
}
