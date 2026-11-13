package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;

/** 靈液引擎：燒靈液（或靈魂精華、靈魂沙／土）產生轉動動力，除了正面（GUI 那一面）以外都能接傳動。 */
public class SpiritEngineBlock extends SoulMachineBlock {
    public SpiritEngineBlock(Properties properties) {
        super(false, properties);
    }

    @Override
    public boolean connects(BlockState state, Direction side) {
        return side != state.getValue(FACING);
    }

    /** 飛輪的軸：引擎正面的右手邊（飛輪裝在側面，可以直接接傳動軸）。 */
    @Override
    public Direction.Axis axis(BlockState state) {
        return state.getValue(FACING).getClockWise().getAxis();
    }

    /** 運轉時燃燒口冒出藍綠色的靈魂火，煙囪冒煙。 */
    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (!state.getValue(POWERED)) {
            return;
        }
        Direction f = state.getValue(FACING);
        double x = pos.getX() + 0.5 + f.getStepX() * 0.52, z = pos.getZ() + 0.5 + f.getStepZ() * 0.52;
        double side = (random.nextDouble() - 0.5) * 0.4;
        x += f.getStepZ() * side;
        z += f.getStepX() * side;
        if (random.nextInt(6) == 0) {   // 使用者（v2.1.0）：靈魂粒子太多，原本 1/3
            level.addParticle(ParticleTypes.SOUL_FIRE_FLAME, x, pos.getY() + 0.35, z, 0, 0.01, 0);
        }
        // 煙囪在正面看過去的左後方（模型 tools/progression/build_soul_power.py 的 chimney）
        Direction left = f.getCounterClockWise();
        level.addParticle(ParticleTypes.SMOKE, pos.getX() + 0.5 + left.getStepX() * 0.22 - f.getStepX() * 0.22,
                pos.getY() + 1.05, pos.getZ() + 0.5 + left.getStepZ() * 0.22 - f.getStepZ() * 0.22, 0, 0.04, 0);
        if (random.nextInt(40) == 0) {
            level.playLocalSound(pos, SoundEvents.FURNACE_FIRE_CRACKLE, SoundSource.BLOCKS, 0.6f, 0.8f, false);
        }
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new SpiritEngineBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide() ? null : createTickerHelper(type, SoulPower.SPIRIT_ENGINE_ENTITY, SpiritEngineBlockEntity::serverTick);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide()) {
            player.openMenu(state.getMenuProvider(level, pos));
        }
        return InteractionResult.SUCCESS;
    }
}
