package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;

/** 靈魂動力網路的一個方塊：哪幾面接得上傳動，以及網路算完後要怎麼更新自己。 */
public interface SoulKinetic {
    /** 運轉中（轉速 > 0）：模型換成會動的貼圖。 */
    BooleanProperty POWERED = BlockStateProperties.POWERED;

    /** 這一面接得上相鄰的靈魂動力方塊嗎？ */
    boolean connects(BlockState state, Direction side);

    /** 網路算完的結果（只在伺服器端）。 */
    default void onNetwork(ServerLevel level, BlockPos pos, BlockState state, SoulNetwork.Result result) {
        boolean powered = result.speed() > 0;
        if (state.getValue(POWERED) != powered) {
            level.setBlock(pos, state.setValue(POWERED, powered), 2);
        }
        if (level.getBlockEntity(pos) instanceof Member member) {
            member.setNetwork(result);
        }
    }

    /** 有方塊實體的成員：記住網路狀態（GUI、機器運作用）。 */
    interface Member {
        void setNetwork(SoulNetwork.Result result);
    }
}
