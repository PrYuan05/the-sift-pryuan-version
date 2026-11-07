package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * 紫龍晶光束發射器／接收器：背面接傳動。發射器運轉時從正面射出紫龍晶光束（{@link CharoiteBeam}），
 * 打中接收器的正面就無線連通（容量只打 {@link SoulNetwork#BEAM_EFFICIENCY} 折，比振波損耗少，但要瞄準）。
 * 光束會灼傷穿過它的生物。
 */
public class CharoiteBeamBlock extends SoulMachineBlock {
    public final boolean emitter;
    private final VoxelShape[] shapes = new VoxelShape[6];

    public CharoiteBeamBlock(boolean emitter, Properties properties) {
        super(true, properties);
        this.emitter = emitter;
        for (Direction d : Direction.values()) {
            shapes[d.ordinal()] = switch (d) {   // the base is on the back
                case UP -> Block.box(1, 0, 1, 15, 12, 15);
                case DOWN -> Block.box(1, 4, 1, 15, 16, 15);
                case NORTH -> Block.box(1, 1, 4, 15, 15, 16);
                case SOUTH -> Block.box(1, 1, 0, 15, 15, 12);
                case WEST -> Block.box(4, 1, 1, 16, 15, 15);
                case EAST -> Block.box(0, 1, 1, 12, 15, 15);
            };
        }
    }

    @Override
    public boolean connects(BlockState state, Direction side) {
        return side == state.getValue(FACING).getOpposite();
    }

    @Override
    public Direction.Axis axis(BlockState state) {
        return state.getValue(FACING).getAxis();
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shapes[state.getValue(FACING).ordinal()];
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new CharoiteBeamBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide() ? null : createTickerHelper(type, SoulPower.CHAROITE_BEAM_ENTITY, CharoiteBeamBlockEntity::serverTick);
    }
}
