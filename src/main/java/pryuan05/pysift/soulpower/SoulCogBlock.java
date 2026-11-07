package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * 靈魂齒輪／大靈魂齒輪（Create 的齒輪）：中心是一段傳動軸（兩端同軸相接），外圈的齒和同平面的齒輪咬合：
 * 相鄰的小齒輪方向相反；大齒輪和斜角的小齒輪咬合，小齒輪轉兩倍快（{@link SoulNetwork}）。
 */
public class SoulCogBlock extends SoulShaftBlock {
    private final boolean large;
    private final VoxelShape[] shapes = new VoxelShape[3];

    public SoulCogBlock(boolean large, Properties properties) {
        super(properties);
        this.large = large;
        double r = large ? 8 : 7;   // 碰撞箱：大齒輪本身比一格大，碰撞只取一格
        for (Direction.Axis axis : Direction.Axis.values()) {
            VoxelShape disc = switch (axis) {
                case X -> Block.box(6, 8 - r, 8 - r, 10, 8 + r, 8 + r);
                case Y -> Block.box(8 - r, 6, 8 - r, 8 + r, 10, 8 + r);
                case Z -> Block.box(8 - r, 8 - r, 6, 8 + r, 8 + r, 10);
            };
            VoxelShape shaft = switch (axis) {
                case X -> Block.box(0, 6, 6, 16, 10, 10);
                case Y -> Block.box(6, 0, 6, 10, 16, 10);
                case Z -> Block.box(6, 6, 0, 10, 10, 16);
            };
            shapes[axis.ordinal()] = Shapes.or(disc, shaft);
        }
    }

    public boolean isLarge() {
        return large;
    }

    @Override
    public Cog cog(BlockState state) {
        return large ? Cog.LARGE : Cog.SMALL;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shapes[state.getValue(AXIS).ordinal()];
    }
}
