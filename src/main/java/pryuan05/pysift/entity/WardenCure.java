package pryuan05.pysift.entity;

import java.util.Map;
import java.util.WeakHashMap;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.ConversionParams;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.warden.Warden;
import pryuan05.pysift.block.SiftPortalBlock;
import pryuan05.pysift.entity.mob.SiftWardenEntity;
import pryuan05.pysift.fluid.SpiritInteractions;
import pryuan05.pysift.progression.StoryTriggers;

/**
 * 治癒監守者（MODDING_ROADMAP §4.7 第六幕）：監守者泡在靈液裡（每秒 +SOAK）或待在隙浮（每秒 +SIFT），累積到 CURE 就長回皮毛，
 * 變成 {@link SiftWardenEntity}。離開這些地方會慢慢退回去。進度只記在記憶體裡（重開伺服器從頭算）。
 * 泡靈液 15 秒，或在隙浮待 30 秒。
 */
public final class WardenCure {
    private static final int SOAK = 20, SIFT = 10, CURE = 300;
    private static final Map<Warden, Integer> PROGRESS = new WeakHashMap<>();

    private WardenCure() {
    }

    public static void register() {
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            if (server.getTickCount() % 20 == 0) {
                for (ServerLevel level : server.getAllLevels()) {
                    tick(level);
                }
            }
        });
    }

    private static void tick(ServerLevel level) {
        boolean inSift = level.dimension() == SiftPortalBlock.SIFT_DIM;
        for (Warden w : level.getEntities(net.minecraft.world.entity.EntityTypes.WARDEN, w -> w.isAlive() && !(w instanceof SiftWardenEntity))) {
            boolean soaking = SpiritInteractions.isSpirit(level.getFluidState(w.blockPosition()))
                    || SpiritInteractions.isSpirit(level.getFluidState(w.blockPosition().above()));
            int gain = (soaking ? SOAK : 0) + (inSift ? SIFT : 0);
            int p = Math.max(0, PROGRESS.getOrDefault(w, 0) + (gain > 0 ? gain : -10));
            PROGRESS.put(w, p);
            if (gain > 0) {   // 皮毛在長：發光、鐘聲越來越高
                level.sendParticles(ParticleTypes.GLOW, w.getX(), w.getY() + 1.6, w.getZ(), 4 + p / 30, 0.7, 0.9, 0.7, 0.02);
                level.playSound(null, w.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.NEUTRAL, 1.2f, 0.5f + p / (float) CURE);
                WardenSoothing.soothe(level, w, 60);   // 治癒中的監守者很安靜
            }
            if (p >= CURE) {
                PROGRESS.remove(w);
                SiftWardenEntity cured = w.convertTo(ModEntities.SIFT_WARDEN, ConversionParams.single(w, false, false),
                        s -> {
                            s.setPersistenceRequired();
                            s.addTag(pryuan05.pysift.fluid.SpiritFluid.REBORN);
                        });
                if (cured != null) {
                    level.sendParticles(ParticleTypes.SCULK_SOUL, cured.getX(), cured.getY() + 1.5, cured.getZ(), 50, 0.8, 1.2, 0.8, 0.04);
                    level.sendParticles(ParticleTypes.NOTE, cured.getX(), cured.getY() + 3.2, cured.getZ(), 10, 1.0, 0.3, 1.0, 1.0);
                    level.playSound(null, cured.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.NEUTRAL, 2.5f, 0.8f);
                    StoryTriggers.wardenCured(level, cured.position());
                }
            }
        }
    }

    public static int progress(Warden w) {
        return PROGRESS.getOrDefault(w, 0);
    }
}
