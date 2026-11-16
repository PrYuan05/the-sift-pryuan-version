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

    /** 訊號可以從這一面進來嗎？（靈魂中繼器只收背面） */
    default boolean accepts(BlockState state, Direction side) {
        return conducts(state, side);
    }

    /** 訊號可以從這一面出去嗎？（靈魂中繼器只從正面送出） */
    default boolean emits(BlockState state, Direction side) {
        return conducts(state, side);
    }

    /** 訊號到這裡補回強度 15 嗎？（靈魂中繼器） */
    default boolean boosts(BlockState state) {
        return false;
    }

    /** 這種訊號過得去嗎？soul = 靈魂訊號，否則是原版紅石訊號。（靈魂濾波器） */
    default boolean passes(BlockState state, boolean soul) {
        return true;
    }

    /** 不是機器的元件在強度 15 時吃的靈壓（SP）。 */
    default float load(BlockState state) {
        return 0;
    }

    /**
     * 無線轉送器的方塊實體（紫龍晶光束）：訊號從發送端跳到接收端，每跳一次多扣一些強度。
     * 花費以「半格強度」計：2 = 少 1 級。
     */
    interface Relay {
        /** 目前連得上的另一端（發送端回傳接收端，接收端回傳發送端）。 */
        List<BlockPos> findLinks(ServerLevel level);

        /** 這一端送得出訊號嗎？訊號只從送得出的一端跳到收得到的一端。 */
        boolean sends();

        boolean receives();

        int hopCost();
    }
}
