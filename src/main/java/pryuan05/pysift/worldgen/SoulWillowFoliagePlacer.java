package pryuan05.pysift.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.util.valueproviders.IntProviders;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.levelgen.feature.TreeFeature;
import net.minecraft.world.level.levelgen.feature.foliageplacers.FoliagePlacer;
import net.minecraft.world.level.levelgen.feature.foliageplacers.FoliagePlacerType;
import pryuan05.pysift.PySift;

/**
 * 靈魂柳的雲朵狀樹冠：每個 FoliageAttachment（枝幹末端）長出一團主葉團，外加 clump_count - 1 團附屬葉團。
 * 整棵樹的樹冠就是所有枝端葉團的疊加，形成寬扁、頂面凹凸的穹頂。
 * <ul>
 *   <li>radius：附屬葉團中心離枝端的最大水平距離（JSON 的 radius，FoliagePlacer 共用參數）。</li>
 *   <li>offset：主葉團中心相對枝端的高度（JSON 的 offset）。附屬葉團再上下錯落 ±clump_y_spread 格。</li>
 *   <li>clump_count：每個枝端的葉團數；clump_radius：每團的水平半徑（3–6）。</li>
 *   <li>flatness：葉團高度 / 寬度（預設 0.7）；clump_y_spread：附屬葉團上下錯落的格數（預設 3）。</li>
 * </ul>
 * 葉團是上半橢球（高約為寬的 0.6 倍）、底部壓平成一層；最外圈有機率多垂一格，像邊緣微微往下捲。
 * 內部隨機留少量空隙，從下方可以看到枝幹。離枝端木節超過 6 格的位置不放葉子（否則會凋零），所以附屬葉團離太遠時只長一部分。葉子的種類（青綠／淡藍／發光）由 foliage_provider 的 weighted 決定。
 */
public class SoulWillowFoliagePlacer extends FoliagePlacer {
    public static final MapCodec<SoulWillowFoliagePlacer> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            IntProviders.codec(0, 16).fieldOf("radius").forGetter(p -> p.radius),
            IntProviders.codec(0, 16).fieldOf("offset").forGetter(p -> p.offset),
            IntProviders.codec(1, 8).fieldOf("clump_count").forGetter(p -> p.clumpCount),
            IntProviders.codec(1, 8).fieldOf("clump_radius").forGetter(p -> p.clumpRadius),
            Codec.floatRange(0.2F, 1.5F).optionalFieldOf("flatness", 0.7F).forGetter(p -> p.flatness),
            Codec.intRange(0, 6).optionalFieldOf("clump_y_spread", 3).forGetter(p -> p.clumpYSpread)
    ).apply(instance, SoulWillowFoliagePlacer::new));

    public static final FoliagePlacerType<SoulWillowFoliagePlacer> TYPE = Registry.register(
            BuiltInRegistries.FOLIAGE_PLACER_TYPE, PySift.id("soul_willow_foliage_placer"), new FoliagePlacerType<>(CODEC));

    private static final float CURL_FROM = 0.75F;    // 距中心超過半徑的這個比例，就算外圈（可往下捲一格）
    private static final float CURL_CHANCE = 0.55F;
    private static final float GAP_CHANCE = 0.05F;   // 內部空隙
    private static final int MAX_LEAF_REACH = 6;     // 葉子離原木的最大距離（再遠會凋零）

    private final IntProvider clumpCount;
    private final IntProvider clumpRadius;
    /** 葉團高度 / 寬度（穹頂的扁平程度）。 */
    private final float flatness;
    /** 附屬葉團中心上下錯落的最大格數。 */
    private final int clumpYSpread;

    public SoulWillowFoliagePlacer(IntProvider radius, IntProvider offset, IntProvider clumpCount, IntProvider clumpRadius,
                                   float flatness, int clumpYSpread) {
        super(radius, offset);
        this.clumpCount = clumpCount;
        this.clumpRadius = clumpRadius;
        this.flatness = flatness;
        this.clumpYSpread = clumpYSpread;
    }

    @Override
    protected FoliagePlacerType<?> type() {
        return TYPE;
    }

    @Override
    protected void createFoliage(WorldGenLevel level, FoliageSetter setter, RandomSource random, TreeFeature config,
                                 int maxFreeTreeHeight, FoliageAttachment attachment, int foliageHeight, int foliageRadius,
                                 int offset) {
        BlockPos knot = attachment.pos().below();       // SoulWillowTrunkPlacer 在這裡放了十字形木節
        BlockPos anchor = attachment.pos().above(offset);
        int clumps = Math.max(1, clumpCount.sample(random));
        for (int i = 0; i < clumps; i++) {
            BlockPos center = anchor;
            if (i > 0 && foliageRadius > 0) {    // 附屬葉團：在枝端周圍隨機方向、高度錯落
                float angle = random.nextFloat() * Mth.TWO_PI;
                int distance = 1 + random.nextInt(foliageRadius);
                center = anchor.offset(Math.round(Mth.cos(angle) * distance), random.nextInt(2 * clumpYSpread + 1) - clumpYSpread,
                        Math.round(Mth.sin(angle) * distance));
            }
            placeClump(level, setter, random, config, center, Math.max(1, clumpRadius.sample(random)), knot);
        }
    }

    /** 一團上半橢球：dy ≥ 0 是穹頂，dy = -1 是壓平的底層，dy = -2 只在外圈隨機出現（向下捲的邊）。 */
    private void placeClump(WorldGenLevel level, FoliageSetter setter, RandomSource random, TreeFeature config,
                            BlockPos center, int radius, BlockPos knot) {
        float horizontal = radius + 0.5F;
        float vertical = radius * flatness + 0.5F;
        int top = Mth.ceil(vertical);
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int dy = -2; dy <= top; dy++) {
            for (int dx = -radius; dx <= radius; dx++) {
                for (int dz = -radius; dz <= radius; dz++) {
                    float h = Mth.sqrt(dx * dx + dz * dz) / horizontal;
                    if (h > 1.0F) {
                        continue;
                    }
                    boolean inside;
                    if (dy >= 0) {
                        float v = dy / vertical;
                        float shell = h * h + v * v;
                        // 頂面：最外一層稍微隨機缺角，形成凹凸；內部偶爾留空隙
                        inside = shell <= 1.0F && !(shell > 0.8F && random.nextFloat() < 0.2F)
                                && !(shell < 0.5F && random.nextFloat() < GAP_CHANCE);
                    } else if (dy == -1) {
                        inside = true;
                    } else {
                        inside = h > CURL_FROM && random.nextFloat() < CURL_CHANCE;
                    }
                    pos.setWithOffset(center, dx, dy, dz);
                    if (inside && distanceToKnot(pos, knot) <= MAX_LEAF_REACH) {
                        tryPlaceLeaf(level, setter, random, config, pos);
                    }
                }
            }
        }
    }

    /** 到十字形木節（中心 ± KNOT_RADIUS 的 x、z 兩條線）的曼哈頓距離。 */
    private static int distanceToKnot(BlockPos pos, BlockPos knot) {
        int dx = Math.abs(pos.getX() - knot.getX()), dy = Math.abs(pos.getY() - knot.getY()), dz = Math.abs(pos.getZ() - knot.getZ());
        int r = SoulWillowTrunkPlacer.KNOT_RADIUS;
        return dy + Math.min(Math.max(dx - r, 0) + dz, dx + Math.max(dz - r, 0));
    }

    @Override
    public int foliageHeight(RandomSource random, int treeHeight, TreeFeature config) {
        return 4;
    }

    /** 原版共用的逐列放置路徑才會用到；這裡的葉團自己判斷形狀，只保留圓形裁角。 */
    @Override
    protected boolean shouldSkipLocation(RandomSource random, int dx, int y, int dz, int range, boolean doubleTrunk) {
        return dx * dx + dz * dz > range * range;
    }

    /** 觸發類別載入以完成註冊。 */
    public static void register() {
        PySift.LOGGER.info("Registered foliage placer {}", BuiltInRegistries.FOLIAGE_PLACER_TYPE.getKey(TYPE));
    }
}
