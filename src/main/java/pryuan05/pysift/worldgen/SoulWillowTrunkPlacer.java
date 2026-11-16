package pryuan05.pysift.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.util.valueproviders.IntProviders;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.feature.TreeFeature;
import net.minecraft.world.level.levelgen.feature.foliageplacers.FoliagePlacer.FoliageAttachment;
import net.minecraft.world.level.levelgen.feature.trunkplacers.TrunkPlacer;
import net.minecraft.world.level.levelgen.feature.trunkplacers.TrunkPlacerType;
import pryuan05.pysift.PySift;

import java.util.ArrayList;
import java.util.List;
import java.util.function.BiConsumer;

/**
 * 靈魂柳的巨大樹幹：
 * <ul>
 *   <li>trunk_width（2–3）粗的樹幹，往上時中心緩慢漂移，看起來扭曲上升。</li>
 *   <li>約一半高度處分岔出 branch_count（4–6）條粗枝向外斜伸 branch_length 格；
 *       每條枝末端再分出 twig_count 條短枝，每條短枝末端是一個 FoliageAttachment（樹冠葉團長在這裡）。</li>
 *   <li>樹幹頂端也有一個 FoliageAttachment，填滿穹頂中央。</li>
 *   <li>基部 root_count（4–8）條板根沿地面向外延伸 root_length（3–6）格，遇到下坡就貼著地面往下；靠近樹幹的前半段高兩格。</li>
 * </ul>
 * 葉子離原木超過 6 格會凋零，所以樹冠的寬度主要來自枝條長度；每個枝端另有一個十字形木節（KNOT_RADIUS），
 * SoulWillowFoliagePlacer 只在木節 6 格內放葉子。
 */
public class SoulWillowTrunkPlacer extends TrunkPlacer {
    public static final MapCodec<SoulWillowTrunkPlacer> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            Codec.intRange(0, 32).fieldOf("base_height").forGetter(p -> p.baseHeight),
            Codec.intRange(0, 24).fieldOf("height_rand_a").forGetter(p -> p.heightRandA),
            Codec.intRange(0, 24).fieldOf("height_rand_b").forGetter(p -> p.heightRandB),
            IntProviders.codec(1, 3).fieldOf("trunk_width").forGetter(p -> p.trunkWidth),
            IntProviders.codec(0, 8).fieldOf("branch_count").forGetter(p -> p.branchCount),
            IntProviders.codec(1, 12).fieldOf("branch_length").forGetter(p -> p.branchLength),
            IntProviders.codec(0, 4).fieldOf("twig_count").forGetter(p -> p.twigCount),
            IntProviders.codec(0, 12).fieldOf("root_count").forGetter(p -> p.rootCount),
            IntProviders.codec(1, 8).fieldOf("root_length").forGetter(p -> p.rootLength)
    ).apply(instance, SoulWillowTrunkPlacer::new));

    public static final TrunkPlacerType<SoulWillowTrunkPlacer> TYPE = Registry.register(
            BuiltInRegistries.TRUNK_PLACER_TYPE, PySift.id("soul_willow_trunk_placer"), new TrunkPlacerType<>(CODEC));

    /** 每個枝端（葉團中心）的十字形木節半徑：葉子要在原木 6 格內才不會凋零，木節讓大葉團也連得到原木。 */
    public static final int KNOT_RADIUS = 2;

    private final IntProvider trunkWidth;
    private final IntProvider branchCount;
    private final IntProvider branchLength;
    private final IntProvider twigCount;
    private final IntProvider rootCount;
    private final IntProvider rootLength;

    public SoulWillowTrunkPlacer(int baseHeight, int heightRandA, int heightRandB, IntProvider trunkWidth,
                                 IntProvider branchCount, IntProvider branchLength, IntProvider twigCount,
                                 IntProvider rootCount, IntProvider rootLength) {
        super(baseHeight, heightRandA, heightRandB);
        this.trunkWidth = trunkWidth;
        this.branchCount = branchCount;
        this.branchLength = branchLength;
        this.twigCount = twigCount;
        this.rootCount = rootCount;
        this.rootLength = rootLength;
    }

    @Override
    protected TrunkPlacerType<?> type() {
        return TYPE;
    }

    @Override
    public List<FoliageAttachment> placeTrunk(WorldGenLevel level, BiConsumer<BlockPos, BlockState> trunkSetter,
                                              RandomSource random, int treeHeight, BlockPos origin, TreeFeature config) {
        List<FoliageAttachment> attachments = new ArrayList<>();
        int width = trunkWidth.sample(random);
        float half = (width - 1) / 2.0F;
        for (int x = 0; x < width; x++) {
            for (int z = 0; z < width; z++) {
                placeBelowTrunkBlock(level, trunkSetter, random, origin.offset(x, -1, z), config);
            }
        }

        // ---- 扭曲上升的樹幹：中心每格隨機漂移，總偏移不超過 2 格 ----
        float driftX = 0, driftZ = 0;
        float stepX = (random.nextFloat() - 0.5F) * 0.35F, stepZ = (random.nextFloat() - 0.5F) * 0.35F;
        int forkY = Math.max(3, Math.round(treeHeight * (0.45F + random.nextFloat() * 0.15F)));
        float forkX = 0, forkZ = 0;
        for (int y = 0; y < treeHeight; y++) {
            if (y > 2) {
                stepX = Mth.clamp(stepX + (random.nextFloat() - 0.5F) * 0.2F, -0.4F, 0.4F);
                stepZ = Mth.clamp(stepZ + (random.nextFloat() - 0.5F) * 0.2F, -0.4F, 0.4F);
                driftX = Mth.clamp(driftX + stepX, -2.0F, 2.0F);
                driftZ = Mth.clamp(driftZ + stepZ, -2.0F, 2.0F);
            }
            int ox = Math.round(driftX), oz = Math.round(driftZ);
            for (int x = 0; x < width; x++) {
                for (int z = 0; z < width; z++) {
                    placeLog(level, trunkSetter, random, origin.offset(x + ox, y, z + oz), config);
                }
            }
            if (y == forkY) {
                forkX = driftX;
                forkZ = driftZ;
            }
        }
        BlockPos top = origin.offset(Math.round(half + driftX), treeHeight, Math.round(half + driftZ));
        attachments.add(new FoliageAttachment(top, 0, false));
        knot(level, trunkSetter, random, config, top.below());

        // ---- 粗枝：平均分佈的方向加上抖動，邊伸邊往上斜 ----
        int branches = branchCount.sample(random);
        float start = random.nextFloat() * Mth.TWO_PI;
        for (int b = 0; b < branches; b++) {
            float angle = start + Mth.TWO_PI * b / branches + (random.nextFloat() - 0.5F) * 0.6F;
            int startY = forkY + random.nextInt(3) - 1;
            float rise = 0.35F + random.nextFloat() * 0.35F;
            float cx = half + forkX, cz = half + forkZ;
            int length = branchLength.sample(random);
            BlockPos end = line(level, trunkSetter, random, config, origin, cx, startY, cz, angle, length, rise);
            int twigs = twigCount.sample(random);
            if (twigs == 0) {
                attachments.add(new FoliageAttachment(end.above(), 0, false));
                knot(level, trunkSetter, random, config, end);
            }
            for (int t = 0; t < twigs; t++) {     // 枝端再分出短枝，讓葉團散開
                float twigAngle = angle + (twigs == 1 ? 0 : (t / (twigs - 1.0F) - 0.5F) * 1.6F) + (random.nextFloat() - 0.5F) * 0.4F;
                BlockPos twigEnd = line(level, trunkSetter, random, config, origin,
                        end.getX() - origin.getX() + 0.5F, end.getY() - origin.getY(), end.getZ() - origin.getZ() + 0.5F,
                        twigAngle, 2 + random.nextInt(2), 0.5F);
                attachments.add(new FoliageAttachment(twigEnd.above(), 0, false));
                knot(level, trunkSetter, random, config, twigEnd);
            }
        }

        // ---- 板根：從樹幹邊緣沿地面放射狀延伸 ----
        int roots = rootCount.sample(random);
        float rootStart = random.nextFloat() * Mth.TWO_PI;
        for (int r = 0; r < roots; r++) {
            float angle = rootStart + Mth.TWO_PI * r / roots + (random.nextFloat() - 0.5F) * 0.5F;
            root(level, trunkSetter, random, config, origin, half, angle, rootLength.sample(random));
        }
        return attachments;
    }

    /** 從 (x, y, z)（相對 origin）沿水平角度 angle 放一條 length 格的枝，每格往上 rise；回傳末端位置。 */
    private BlockPos line(WorldGenLevel level, BiConsumer<BlockPos, BlockState> setter, RandomSource random,
                          TreeFeature config, BlockPos origin, float x, float y, float z, float angle, int length, float rise) {
        float dx = Mth.cos(angle), dz = Mth.sin(angle);
        Direction.Axis axis = Math.abs(dx) > Math.abs(dz) ? Direction.Axis.X : Direction.Axis.Z;
        BlockPos last = origin.offset(Mth.floor(x), Mth.floor(y), Mth.floor(z));
        for (int s = 1; s <= length; s++) {
            BlockPos pos = origin.offset(Mth.floor(x + dx * s), Mth.floor(y + rise * s), Mth.floor(z + dz * s));
            if (pos.getY() > last.getY()) {   // 往上跳一格時補一塊，讓枝條連續
                placeLog(level, setter, random, last.above(), config, s2 -> s2.trySetValue(RotatedPillarBlock.AXIS, Direction.Axis.Y));
            }
            placeLog(level, setter, random, pos, config, s2 -> s2.trySetValue(RotatedPillarBlock.AXIS, axis));
            last = pos;
        }
        return last;
    }

    /** 枝端的十字形木節（水平 ±KNOT_RADIUS），埋在葉團裡。 */
    private void knot(WorldGenLevel level, BiConsumer<BlockPos, BlockState> setter, RandomSource random,
                      TreeFeature config, BlockPos center) {
        for (int d = -KNOT_RADIUS; d <= KNOT_RADIUS; d++) {
            if (d != 0) {
                placeLog(level, setter, random, center.offset(d, 0, 0), config, st -> st.trySetValue(RotatedPillarBlock.AXIS, Direction.Axis.X));
                placeLog(level, setter, random, center.offset(0, 0, d), config, st -> st.trySetValue(RotatedPillarBlock.AXIS, Direction.Axis.Z));
            }
        }
    }

    /** 一條板根：貼著地面往外，遇到下坡往下找地面（最多 3 格）；前半段疊兩格高。 */
    private void root(WorldGenLevel level, BiConsumer<BlockPos, BlockState> setter, RandomSource random,
                      TreeFeature config, BlockPos origin, float half, float angle, int length) {
        float dx = Mth.cos(angle), dz = Mth.sin(angle);
        Direction.Axis axis = Math.abs(dx) > Math.abs(dz) ? Direction.Axis.X : Direction.Axis.Z;
        float startRadius = half + 1.0F;
        int y = 0;
        for (int s = 0; s < length; s++) {
            float distance = startRadius + s;
            int x = Mth.floor(half + 0.5F + dx * distance), z = Mth.floor(half + 0.5F + dz * distance);
            for (int drop = 0; drop < 3 && validTreePos(level, origin.offset(x, y - 1, z)); drop++) {
                y--;
            }
            BlockPos pos = origin.offset(x, y, z);
            if (!placeLog(level, setter, random, pos, config, st -> st.trySetValue(RotatedPillarBlock.AXIS, axis))) {
                return;
            }
            if (s < length / 2) {
                placeLog(level, setter, random, pos.above(), config, st -> st.trySetValue(RotatedPillarBlock.AXIS, axis));
            }
        }
    }

    /** 觸發類別載入以完成註冊。 */
    public static void register() {
        PySift.LOGGER.info("Registered trunk placer {}", BuiltInRegistries.TRUNK_PLACER_TYPE.getKey(TYPE));
    }
}
