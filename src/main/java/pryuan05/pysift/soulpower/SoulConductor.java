package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;

import java.util.List;

/**
 * 靈魂迴路（{@link SoulCircuit}）的一個方塊：靈魂導線、引擎、機器、無線轉送器。
 * 相鄰兩個方塊在相接的那一面都 {@link #conducts}，靈魂訊號就會通過。
 */
public interface SoulConductor {
    /** 這一面接得上相鄰的靈魂元件嗎？ */
    default boolean conducts(BlockState state, Direction side) {
        return true;
    }

    /**
     * 無線轉送器的方塊實體（振波、光束、靈脈）：訊號從發送端跳到接收端，每跳一次多扣一些強度。
     * 花費以「半格強度」計：2 = 少 1 級。
     */
    interface Relay {
        /** 目前連得上的另一端（發送端回傳接收端，接收端回傳發送端）。 */
        List<BlockPos> findLinks(ServerLevel level);

        /** 這一端送得出訊號嗎？訊號只從送得出的一端跳到收得到的一端（靈脈節點兩者皆是）。 */
        boolean sends();

        boolean receives();

        int hopCost();
    }
}
