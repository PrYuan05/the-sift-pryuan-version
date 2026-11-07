package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * 靈魂手搖曲柄（Create 的 hand crank）：裝在傳動軸或機器的一面（背面接上），按住右鍵就以 32 RPM 轉動，
 * 但只提供 32 SP——夠一台研磨機慢慢磨，或在還沒有靈液時救急。搖久了會餓。
 */
public class SoulHandCrankBlock extends SoulMachineBlock {

    public SoulHandCrankBlock(Properties properties) {
        super(true, properties);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(FACING, context.getClickedFace());
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
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level instanceof ServerLevel server && level.getBlockEntity(pos) instanceof Entity crank) {
            boolean was = crank.cranking > 0;
            crank.cranking = 10;   // holding right-click repeats every few ticks
            player.causeFoodExhaustion(0.02f);
            if (!was) {
                SoulNetwork.update(server, pos);
            }
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new Entity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide() ? null : createTickerHelper(type, SoulPower.SOUL_HAND_CRANK_ENTITY, Entity::serverTick);
    }

    /** 曲柄：還會轉幾 tick（每次右鍵補滿）。 */
    public static class Entity extends KineticBlockEntity implements SoulKinetic.Source {
        int cranking;

        public Entity(BlockPos pos, BlockState state) {
            super(SoulPower.SOUL_HAND_CRANK_ENTITY, pos, state);
        }

        static void serverTick(Level level, BlockPos pos, BlockState state, Entity crank) {
            if (crank.cranking > 0) {
                crank.cranking--;
                if (crank.cranking == 0 || level.getGameTime() % SoulNetwork.INTERVAL == 0) {
                    SoulNetwork.update((ServerLevel) level, pos);
                }
            }
        }

        @Override
        public float sourceSpeed() {
            return cranking > 0 ? SoulNetwork.SPEED : 0;
        }

        @Override
        public float capacityPerRpm() {
            return 1f;
        }
    }
}
