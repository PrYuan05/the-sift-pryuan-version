package pryuan05.pysift.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;
import pryuan05.pysift.PySift;
import pryuan05.pysift.entity.BossMechanics;

import java.util.Optional;

/**
 * Boss 競技場：圓形平整的場地，中央一圈加高一格的祭壇，外緣一圈矮牆，牆上每隔一段距離立一根石柱；
 * 可選擇在牆外圍一圈液體護城河（例如調和者的靈液湖）。生成時在祭壇上放一隻 Boss（不會消失，並以場地中心為家，
 * 見 {@link BossMechanics#setArena}）。
 * <ul>
 *   <li>場地往下填實到實心地面（最多 MAX_FOOTING 格），往上清空 CLEAR_HEIGHT 格，所以會切平地形與台地。</li>
 *   <li>radius ≤ 17、moat_width ≤ 4：最遠寫到中心外 22 格，placed feature 必須把原點放在區塊中心（offset 8）。</li>
 * </ul>
 */
public record BossArenaFeature(EntityType<?> boss, int radius, Holder<BlockStateProvider> floor, Holder<BlockStateProvider> wall,
                               Holder<BlockStateProvider> pillar, int pillarHeight, int pillarCount,
                               Optional<Holder<BlockStateProvider>> moat, int moatWidth) implements Feature {
    private static final int MAX_FOOTING = 10;
    private static final int CLEAR_HEIGHT = 16;
    private static final int DAIS_RADIUS = 3;

    public static final MapCodec<BossArenaFeature> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            BuiltInRegistries.ENTITY_TYPE.byNameCodec().fieldOf("boss").forGetter(BossArenaFeature::boss),
            Codec.intRange(6, 17).fieldOf("radius").forGetter(BossArenaFeature::radius),
            BlockStateProvider.CODEC.fieldOf("floor").forGetter(BossArenaFeature::floor),
            BlockStateProvider.CODEC.fieldOf("wall").forGetter(BossArenaFeature::wall),
            BlockStateProvider.CODEC.fieldOf("pillar").forGetter(BossArenaFeature::pillar),
            Codec.intRange(2, 12).optionalFieldOf("pillar_height", 6).forGetter(BossArenaFeature::pillarHeight),
            Codec.intRange(0, 16).optionalFieldOf("pillar_count", 8).forGetter(BossArenaFeature::pillarCount),
            BlockStateProvider.CODEC.optionalFieldOf("moat").forGetter(BossArenaFeature::moat),
            Codec.intRange(0, 4).optionalFieldOf("moat_width", 0).forGetter(BossArenaFeature::moatWidth)
    ).apply(instance, BossArenaFeature::new));

    public static final MapCodec<BossArenaFeature> TYPE = Registry.register(
            BuiltInRegistries.FEATURE_TYPE, PySift.id("boss_arena"), CODEC);

    @Override
    public MapCodec<BossArenaFeature> codec() {
        return CODEC;
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        BlockPos center = origin.below();          // 場地地面那一層
        int outer = radius + 1 + (moat.isPresent() ? moatWidth : 0);
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int dx = -outer; dx <= outer; dx++) {
            for (int dz = -outer; dz <= outer; dz++) {
                double d = Math.sqrt(dx * dx + dz * dz);
                if (d > outer + 0.5) {
                    continue;
                }
                int x = center.getX() + dx, z = center.getZ() + dz;
                if (d <= radius + 1.5) {                                   // 場地與矮牆：往上清空、往下填實
                    for (int y = 1; y <= CLEAR_HEIGHT; y++) {
                        setBlock(level, pos.set(x, center.getY() + y, z), Blocks.AIR.defaultBlockState());
                    }
                    fillDown(level, random, pos.set(x, center.getY() - 1, z));
                    setBlock(level, pos.set(x, center.getY(), z), floor.value().getState(level, random, pos));
                    if (d <= DAIS_RADIUS + 0.5) {                          // 中央祭壇
                        setBlock(level, pos.set(x, center.getY() + 1, z), floor.value().getState(level, random, pos));
                    }
                    if (d > radius + 0.5) {                                 // 外緣矮牆（一格高，東南西北留入口）
                        boolean gate = Math.abs(dx) <= 1 || Math.abs(dz) <= 1;
                        if (!gate) {
                            setBlock(level, pos.set(x, center.getY() + 1, z), wall.value().getState(level, random, pos));
                        }
                    }
                } else if (moat.isPresent()) {                              // 護城河：挖兩格深填液體
                    for (int y = 1; y <= CLEAR_HEIGHT; y++) {
                        setBlock(level, pos.set(x, center.getY() + y, z), Blocks.AIR.defaultBlockState());
                    }
                    BlockState liquid = moat.get().value().getState(level, random, pos.set(x, center.getY(), z));
                    setBlock(level, pos, liquid);
                    setBlock(level, pos.set(x, center.getY() - 1, z), liquid);
                    fillDown(level, random, pos.set(x, center.getY() - 2, z));
                }
            }
        }
        for (int i = 0; i < pillarCount; i++) {                             // 石柱（避開四個入口）
            float angle = Mth.TWO_PI * (i + 0.5f) / pillarCount;
            int x = center.getX() + Math.round(Mth.cos(angle) * (radius + 1));
            int z = center.getZ() + Math.round(Mth.sin(angle) * (radius + 1));
            int height = pillarHeight - random.nextInt(3);                  // 有幾根斷掉，像廢墟
            for (int y = 1; y <= height; y++) {
                setBlock(level, pos.set(x, center.getY() + y, z), pillar.value().getState(level, random, pos));
            }
        }
        if (boss.create(level.getLevel(), EntitySpawnReason.CHUNK_GENERATION) instanceof Mob mob) {
            mob.snapTo(center.getX() + 0.5, center.getY() + 2, center.getZ() + 0.5);
            mob.setYRot(random.nextFloat() * 360);
            BossMechanics.setArena(mob, center.above());
            mob.finalizeSpawn(level, level.getCurrentDifficultyAt(center), EntitySpawnReason.CHUNK_GENERATION, null);
            level.addFreshEntityWithPassengers(mob);
        }
        return true;
    }

    /** 往下填實到實心地面為止。 */
    private void fillDown(WorldGenLevel level, RandomSource random, BlockPos.MutableBlockPos pos) {
        for (int i = 0; i < MAX_FOOTING; i++) {
            BlockState current = level.getBlockState(pos);
            if (current.isSolidRender() && level.getFluidState(pos).isEmpty()) {
                return;
            }
            setBlock(level, pos, floor.value().getState(level, random, pos));
            pos.move(0, -1, 0);
        }
    }

    /** 觸發類別載入以完成註冊。 */
    public static void register() {
        PySift.LOGGER.info("Registered feature type {}", BuiltInRegistries.FEATURE_TYPE.getKey(TYPE));
    }
}
