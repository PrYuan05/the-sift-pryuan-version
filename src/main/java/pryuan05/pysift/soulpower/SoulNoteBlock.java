package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
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
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.redstone.Orientation;
import net.minecraft.world.phys.BlockHitResult;
import pryuan05.pysift.block.RitualDiscs;
import pryuan05.pysift.sound.ModSounds;

/**
 * 靈魂音符盒：八音儀式的八個音（NOTE 1～8，音高和共鳴唱片盒一樣，{@link RitualDiscs}）。右鍵換音。
 * 收到訊號的那一刻響一聲：旁邊的導線帶著靈魂訊號時，是歌者的歌聲；只有原版紅石訊號時，只剩一聲悶響（沒有靈魂的音）。
 * 用導線、靈魂中繼器和原版中繼器的延遲，就能排出開門的那首歌 1 3 7 6 5 2 4 8。
 */
public class SoulNoteBlock extends Block {
    public static final IntegerProperty NOTE = IntegerProperty.create("note", 1, 8);
    public static final BooleanProperty POWERED = BlockStateProperties.POWERED;

    public SoulNoteBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(NOTE, 1).setValue(POWERED, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(NOTE, POWERED);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level instanceof ServerLevel server) {
            BlockState next = state.setValue(NOTE, state.getValue(NOTE) % 8 + 1);
            level.setBlock(pos, next, Block.UPDATE_ALL);
            play(server, pos, next, true);
            player.sendOverlayMessage(Component.translatable("message.pysift.soul_note_block.note", next.getValue(NOTE)));
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block block, Orientation orientation, boolean movedByPiston) {
        if (!(level instanceof ServerLevel server)) {
            return;
        }
        boolean powered = level.hasNeighborSignal(pos);
        if (powered != state.getValue(POWERED)) {
            level.setBlock(pos, state.setValue(POWERED, powered), Block.UPDATE_ALL);
            if (powered) {
                play(server, pos, state, soulNear(level, pos));
            }
        }
    }

    /** 旁邊有帶著靈魂訊號的導線嗎？ */
    private static boolean soulNear(Level level, BlockPos pos) {
        for (Direction d : Direction.values()) {
            if (SoulConduitBlock.soul(level, pos.relative(d))) {
                return true;
            }
        }
        return false;
    }

    private static void play(ServerLevel level, BlockPos pos, BlockState state, boolean soul) {
        int semitone = RitualDiscs.DISCS.get(state.getValue(NOTE) - 1).semitone();
        float pitch = (float) Math.pow(2.0, (semitone - 6) / 12.0);     // 和共鳴唱片盒、歌者的八音同一組音高
        if (soul) {
            level.playSound(null, pos, ModSounds.SINGER_VOICE, SoundSource.RECORDS, 1.0f, pitch);
            level.playSound(null, pos, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.RECORDS, 0.4f, pitch);
            level.sendParticles(ParticleTypes.NOTE, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 1, 0, 0, 0, state.getValue(NOTE) / 8.0);
        } else {
            level.playSound(null, pos, SoundEvents.NOTE_BLOCK_BASEDRUM.value(), SoundSource.RECORDS, 0.6f, pitch * 0.7f);
            level.sendParticles(ParticleTypes.SMOKE, pos.getX() + 0.5, pos.getY() + 1.1, pos.getZ() + 0.5, 2, 0.1, 0.05, 0.1, 0.0);
        }
    }
}
