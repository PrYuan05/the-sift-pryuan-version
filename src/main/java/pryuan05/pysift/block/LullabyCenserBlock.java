package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.LanternBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import pryuan05.pysift.entity.mob.MournerEntity;
import pryuan05.pysift.entity.mob.SingerEntity;
import pryuan05.pysift.entity.mob.SingerSongs;

/**
 * 搖籃曲香爐（MODDING_ROADMAP §4.7 第二部）：主世界照顧歌者的據點。外型是一盞燈籠，裡面燒著靈液，輕輕哼著搖籃曲。
 * <ul>
 *   <li>SHELTER 格內的歌者不會屍化（{@link SingerEntity#shelter}）。</li>
 *   <li>SOOTHE 格內的哀悼者慢慢被治癒，約 60 秒變回歌者（{@link MournerEntity#warmBy}），不必泡進靈液。</li>
 * </ul>
 * 用排程刻（每 PERIOD tick）運作，不需要方塊實體；資源由 tools/progression/build_story.py 產生。
 */
public class LullabyCenserBlock extends LanternBlock {
    public static final int PERIOD = 40, SHELTER = 16, SOOTHE = 8;

    public LullabyCenserBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
        super.onPlace(state, level, pos, oldState, movedByPiston);
        if (!oldState.is(this)) {
            level.scheduleTick(pos, this, PERIOD);
        }
    }

    @Override
    protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        level.scheduleTick(pos, this, PERIOD);
        long now = level.getGameTime();
        for (SingerEntity s : level.getEntitiesOfClass(SingerEntity.class, new AABB(pos).inflate(SHELTER))) {
            s.shelter(now + PERIOD * 2L);
        }
        for (MournerEntity m : level.getEntitiesOfClass(MournerEntity.class, new AABB(pos).inflate(SOOTHE))) {
            m.warmBy(level, PERIOD);
        }
        // 哼一個搖籃曲的音（依時間輪流，一段一段地唱下去）
        SingerSongs.Song song = SingerSongs.LULLABY;
        int i = (int) ((now / PERIOD) % song.length());
        int note = song.notes()[i] >= 0 ? song.notes()[i] : song.notes()[0];
        float pitch = (float) Math.pow(2.0, (note - 12) / 12.0);
        level.playSound(null, pos, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.BLOCKS, 0.35f, pitch);
        level.sendParticles(ParticleTypes.NOTE, pos.getX() + 0.5, pos.getY() + 0.9, pos.getZ() + 0.5, 0, note / 24.0, 0, 0, 1.0);
        level.sendParticles(ParticleTypes.SCULK_SOUL, pos.getX() + 0.5, pos.getY() + 0.7, pos.getZ() + 0.5, 1, 0.1, 0.1, 0.1, 0.01);
    }
}
