package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;

/**
 * 靈魂動力網路的一個方塊（Create 式的轉動動力）：
 * <ul>
 *   <li>{@link #connects}：哪幾面像傳動軸一樣同軸相接（轉速相同）；</li>
 *   <li>{@link #cog}：齒輪的大小（相鄰齒輪互相帶動、方向相反；大小齒輪斜向咬合時轉速 ×2／÷2，見 {@link SoulNetwork}）；</li>
 *   <li>{@link #impact}：每 1 RPM 吃掉多少靈壓（負載 = impact × |RPM|，轉越快越吃力）；</li>
 *   <li>{@link #axis}：會轉的部件繞哪個軸轉（渲染與齒輪用）。</li>
 * </ul>
 */
public interface SoulKinetic {
    /** 運轉中（轉速 ≠ 0）。 */
    BooleanProperty POWERED = BlockStateProperties.POWERED;

    enum Cog { NONE, SMALL, LARGE }

    /** 這一面接得上相鄰的靈魂動力方塊嗎（同軸、轉速相同）？ */
    boolean connects(BlockState state, Direction side);

    /** 轉動的軸；null = 沒有固定的軸（例如引擎、研磨機本體）。 */
    default Direction.Axis axis(BlockState state) {
        return null;
    }

    default Cog cog(BlockState state) {
        return Cog.NONE;
    }

    /** 每 1 RPM 的負載（SP）。 */
    default float impact(BlockState state) {
        return 0;
    }

    /** 網路算完的結果（只在伺服器端）：speed 是這個方塊自己的轉速（有正負號，正 = 沿軸的正方向看逆時針）。 */
    default void onNetwork(ServerLevel level, BlockPos pos, BlockState state, SoulNetwork.Result result, float speed) {
        boolean powered = speed != 0;
        if (state.hasProperty(POWERED) && state.getValue(POWERED) != powered) {
            level.setBlock(pos, state.setValue(POWERED, powered), 2);
        }
        if (level.getBlockEntity(pos) instanceof Member member) {
            member.setNetwork(result, speed);
        }
    }

    /** 有方塊實體的成員：記住網路狀態（GUI、機器運作、用戶端動畫用）。 */
    interface Member {
        void setNetwork(SoulNetwork.Result result, float speed);
    }

    /** 動力源（引擎）：自己的轉速（0 = 沒在運轉）與每 1 RPM 提供的靈壓。 */
    interface Source {
        float sourceSpeed();

        float capacityPerRpm();
    }
}
