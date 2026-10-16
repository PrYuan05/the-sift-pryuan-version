package pryuan05.pysift.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;
import pryuan05.pysift.PySift;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * 記錄世界中所有已生成的 Boss 競技場位置，以便透過指令跨區塊（即使區塊已卸載）快速定位。
 */
public class BossArenaSavedData extends SavedData {

    public record ArenaRecord(String arenaType, String bossKey, BlockPos pos) {
        public static final Codec<ArenaRecord> CODEC = RecordCodecBuilder.create(instance -> instance.group(
                Codec.STRING.fieldOf("arena_type").forGetter(ArenaRecord::arenaType),
                Codec.STRING.fieldOf("boss_key").forGetter(ArenaRecord::bossKey),
                BlockPos.CODEC.fieldOf("pos").forGetter(ArenaRecord::pos)
        ).apply(instance, ArenaRecord::new));
    }

    private final List<ArenaRecord> arenas = new ArrayList<>();

    public static final Codec<BossArenaSavedData> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            ArenaRecord.CODEC.listOf().fieldOf("arenas").forGetter(d -> d.arenas)
    ).apply(instance, list -> {
        BossArenaSavedData data = new BossArenaSavedData();
        data.arenas.addAll(list);
        return data;
    }));

    public static final SavedDataType<BossArenaSavedData> TYPE = new SavedDataType<>(
            PySift.id("boss_arenas"),
            BossArenaSavedData::new,
            CODEC,
            DataFixTypes.LEVEL
    );

    public static BossArenaSavedData get(ServerLevel level) {
        return level.getDataStorage().computeIfAbsent(TYPE);
    }

    public static void record(ServerLevel level, String arenaType, String bossKey, BlockPos pos) {
        BossArenaSavedData data = get(level);
        // 避免同位置重複記錄
        for (ArenaRecord r : data.arenas) {
            if (r.pos().distSqr(pos) < 16 * 16) {
                return;
            }
        }
        data.arenas.add(new ArenaRecord(arenaType, bossKey, pos.immutable()));
        data.setDirty();
        PySift.LOGGER.info("Recorded boss arena {} ({}) at {}", arenaType, bossKey, pos);
    }

    public Optional<ArenaRecord> findNearest(String bossIdOrKey, BlockPos origin) {
        ArenaRecord nearest = null;
        double minDistance = Double.MAX_VALUE;
        for (ArenaRecord arena : arenas) {
            if (arena.arenaType().equalsIgnoreCase(bossIdOrKey) || arena.bossKey().contains(bossIdOrKey.toLowerCase())) {
                double dist = arena.pos().distSqr(origin);
                if (dist < minDistance) {
                    minDistance = dist;
                    nearest = arena;
                }
            }
        }
        return Optional.ofNullable(nearest);
    }

    public List<ArenaRecord> getArenas() {
        return arenas;
    }
}
