package pryuan05.pysift.soulpower.kinetic;

import pryuan05.pysift.soulpower.*;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 靈魂齒輪／大靈魂齒輪（Create 的齒輪）：中心是一段傳動軸（兩端同軸相接），外圈的齒和同平面的齒輪咬合：
 * 相鄰的小齒輪方向相反；大齒輪和斜角的小齒輪咬合，小齒輪轉兩倍快（{@link SoulNetwork}）。
 */
public class SoulCogBlock extends SoulShaftBlock {
    private final boolean large;

    public SoulCogBlock(boolean large, Properties properties) {
        super(properties);
        this.large = large;
    }

    public boolean isLarge() {
        return large;
    }

    @Override
    public Cog cog(BlockState state) {
        return large ? Cog.LARGE : Cog.SMALL;
    }

}
