package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.BlockHitResult;

/**
 * 靈魂濾波器：串在導線上，只讓一種訊號通過。SOUL = true：只過靈魂訊號（擋掉原版紅石訊號）；
 * false：只過原版訊號（擋掉靈魂訊號，後面的機器不會動）。右鍵切換。六面都能接。
 */
public class SoulFilterBlock extends SoulPartBlock {
    public static final BooleanProperty SOUL = BooleanProperty.create("soul");

    public SoulFilterBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(SOUL, true));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(SOUL);
    }

    @Override
    public boolean passes(BlockState state, boolean soul) {
        return state.getValue(SOUL) == soul;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level instanceof ServerLevel server) {
            boolean soul = !state.getValue(SOUL);
            level.setBlock(pos, state.setValue(SOUL, soul), Block.UPDATE_ALL);
            level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 0.8f, soul ? 1.4f : 0.7f);
            player.sendOverlayMessage(Component.translatable(soul ? "message.pysift.soul_filter.soul" : "message.pysift.soul_filter.plain"));
            SoulSignal.update(server, pos);
        }
        return InteractionResult.SUCCESS;
    }
}
