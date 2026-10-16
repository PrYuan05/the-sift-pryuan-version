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
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.util.valueproviders.IntProviders;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;
import pryuan05.pysift.PySift;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * 層狀圓台（平頂台地）：一層層 2 格高的大圓餅疊成，邊緣逐層內縮成台階，頂面寬而平好走
 * （參考影片《I Recreated The Sift in Minecraft 26.3》與使用者給的台地參考圖）。
 * <ul>
 *   <li>主體 tiers 層：每層半徑不變或內縮 1–2 格（只往內收、不外擴，所以沒有懸空的部分）；最少保留底半徑的 60%。</li>
 *   <li>頂部 cap_steps 層：每層半徑減 1–2，形成邊緣的台階，中間仍是大片平頂。</li>
 *   <li>每層露出的頂面（上一層沒蓋住的部分）用 top；每 band_every 層夾一條 band；其餘用 body。</li>
 *   <li>body 是由上到下的漸層（例如 abyssal_strata depth 0→1→2→void_stone），交界處抖動混合。</li>
 *   <li>底部往下填實到實心地面（最多 MAX_FOOTING 格），坡地與懸崖邊也不會懸空。</li>
 * </ul>
 * 半徑上限 18 再加邊緣雜訊，最遠寫到原點外 23 格（MAX_REACH 截斷）：placed feature 必須把原點放在區塊中心
 * （不用 in_square，改用 random_offset xz_spread=8），才不會超出 feature 可寫入的 3×3 區塊範圍。
 * JSON 範例見 tools/worldgen/build_the_sift.py 的 SPIRES。
 */
public record StrataSpireFeature(IntProvider tiers, IntProvider radius, IntProvider capSteps, int bandEvery,
                                 Holder<BlockStateProvider> top, List<Holder<BlockStateProvider>> body,
                                 Optional<Holder<BlockStateProvider>> band) implements Feature {
    private static final int MAX_RADIUS = 18;
    /** 原點在區塊中心時，feature 可寫入範圍到原點的最近距離。 */
    private static final float MAX_REACH = 23.0F;
    private static final int TIER_HEIGHT = 2;
    private static final int MAX_FOOTING = 64;

    public static final MapCodec<StrataSpireFeature> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            IntProviders.codec(1, 32).fieldOf("tiers").forGetter(StrataSpireFeature::tiers),
            IntProviders.codec(2, MAX_RADIUS).fieldOf("radius").forGetter(StrataSpireFeature::radius),
            IntProviders.codec(0, 8).fieldOf("cap_steps").forGetter(StrataSpireFeature::capSteps),
            Codec.intRange(0, 32).optionalFieldOf("band_every", 0).forGetter(StrataSpireFeature::bandEvery),
            BlockStateProvider.CODEC.fieldOf("top").forGetter(StrataSpireFeature::top),
            BlockStateProvider.CODEC.listOf(1, 8).fieldOf("body").forGetter(StrataSpireFeature::body),
            BlockStateProvider.CODEC.optionalFieldOf("band").forGetter(StrataSpireFeature::band)
    ).apply(instance, StrataSpireFeature::new));

    public static final MapCodec<StrataSpireFeature> TYPE = Registry.register(
            BuiltInRegistries.FEATURE_TYPE, PySift.id("strata_spire"), CODEC);

    @Override
    public MapCodec<StrataSpireFeature> codec() {
        return CODEC;
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        if (!level.getFluidState(origin.below()).isEmpty() || level.getBlockState(origin.below()).isAir()) {
            return false;
        }
        List<Tier> tiers = shape(random);
        int height = tiers.size() * TIER_HEIGHT;
        int reach = Math.min(tiers.stream().mapToInt(t -> t.radius).max().orElse(0) + 4, (int) MAX_REACH);   // 半徑 + 邊緣雜訊
        // 頂面與色帶每層只抽一次：weighted 的 top（例如 teal / rose 兩種覆蓋石）會變成一層一層交替的色環
        BlockState[] tierTop = new BlockState[tiers.size()];
        BlockState[] tierBand = new BlockState[tiers.size()];
        for (int i = 0; i < tiers.size(); i++) {
            BlockPos at = origin.above(i * TIER_HEIGHT);
            tierTop[i] = top.value().getState(level, random, at);
            boolean banded = band.isPresent() && bandEvery > 0 && (i + 1) % bandEvery == 0;
            tierBand[i] = banded ? band.get().value().getState(level, random, at) : null;
        }
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int dx = -reach; dx <= reach; dx++) {
            for (int dz = -reach; dz <= reach; dz++) {
                for (int i = 0; i < tiers.size(); i++) {
                    if (!tiers.get(i).contains(dx, dz)) {
                        break;      // 下層沒蓋到的地方上層也不放：塔身只會往上收，不會有懸空的突出
                    }
                    boolean exposed = i + 1 == tiers.size() || !tiers.get(i + 1).contains(dx, dz);
                    for (int dy = 0; dy < TIER_HEIGHT; dy++) {
                        int h = i * TIER_HEIGHT + dy;
                        pos.set(origin.getX() + dx, origin.getY() + h, origin.getZ() + dz);
                        BlockState state;
                        if (exposed && dy == TIER_HEIGHT - 1) {
                            state = tierTop[i];
                        } else if (tierBand[i] != null) {
                            state = tierBand[i];
                        } else {
                            state = bodyAt(level, random, pos, h, height);
                        }
                        setBlock(level, pos, state);
                    }
                }
                if (tiers.get(0).contains(dx, dz)) {
                    footing(level, random, pos.set(origin.getX() + dx, origin.getY() - 1, origin.getZ() + dz), height);
                }
            }
        }
        return true;
    }

    /** 由下而上的每層半徑：主體不變或內縮，塔頂逐階內縮。 */
    private List<Tier> shape(RandomSource random) {
        int bodyTiers = tiers.sample(random);
        int base = Math.min(radius.sample(random), MAX_RADIUS);
        List<Tier> out = new ArrayList<>();
        int r = base;
        for (int i = 0; i < bodyTiers; i++) {
            if (i > 0) {
                float progress = (float) i / bodyTiers;
                float roll = random.nextFloat();
                // 台地：多數層不變或往內收一點，讓側面是一圈圈台階，頂面仍保持寬大
                float shrink = 0.30F + 0.15F * progress;       // 越往上越容易內縮
                if (roll < shrink) {
                    r -= 1;
                } else if (roll < shrink + 0.10F) {
                    r -= 2;
                }
                r = Math.max(r, Math.max(2, base * 3 / 5));
            }
            out.add(new Tier(r, random));
        }
        int steps = capSteps.sample(random);
        for (int i = 0; i < steps && r > 2; i++) {
            r = Math.max(2, r - 1 - random.nextInt(2));
            out.add(new Tier(r, random));
        }
        return out;
    }

    /** body 由上到下漸層；交界處以 ±半格的抖動混合。 */
    private BlockState bodyAt(WorldGenLevel level, RandomSource random, BlockPos pos, int h, int height) {
        float depth = 1.0F - (h + 0.5F) / height;                      // 0 = 塔頂，1 = 塔底
        float jitter = (random.nextFloat() - 0.5F) / body.size();
        int index = Mth.clamp((int) ((depth + jitter) * body.size()), 0, body.size() - 1);
        return body.get(index).value().getState(level, random, pos);
    }

    /** 往下填到實心地面為止（穿過空氣、液體與植物），用 body 最底層的材質。 */
    private void footing(WorldGenLevel level, RandomSource random, BlockPos.MutableBlockPos pos, int height) {
        for (int i = 0; i < MAX_FOOTING; i++) {
            BlockState current = level.getBlockState(pos);
            if (current.isSolidRender() && level.getFluidState(pos).isEmpty()) {
                return;
            }
            if (current.is(Blocks.BEDROCK)) {
                return;
            }
            setBlock(level, pos, body.getLast().value().getState(level, random, pos));
            pos.move(0, -1, 0);
        }
    }

    /** 一層圓餅：半徑加上隨角度起伏的邊緣雜訊（三個諧波），讓圓邊不要太規整。 */
    private static final class Tier {
        final int radius;
        private final float a1, a2, a3, p1, p2, p3;

        Tier(int radius, RandomSource random) {
            this.radius = radius;
            float scale = 1.0F + radius / 10.0F;           // 大圓的邊緣起伏稍大，避免像圓規畫的
            this.a1 = (0.25F + random.nextFloat() * 0.25F) * scale;
            this.a2 = random.nextFloat() * 0.25F * scale;
            this.a3 = random.nextFloat() * 0.2F * scale;
            this.p1 = random.nextFloat() * Mth.TWO_PI;
            this.p2 = random.nextFloat() * Mth.TWO_PI;
            this.p3 = random.nextFloat() * Mth.TWO_PI;
        }

        boolean contains(int dx, int dz) {
            float angle = (float) Mth.atan2(dz, dx);
            float edge = radius + 0.45F + a1 * Mth.sin(2 * angle + p1) + a2 * Mth.sin(3 * angle + p2) + a3 * Mth.sin(5 * angle + p3);
            edge = Math.min(edge, MAX_REACH);
            return dx * dx + dz * dz <= edge * edge;
        }
    }

    /** 觸發類別載入以完成註冊。 */
    public static void register() {
        PySift.LOGGER.info("Registered feature type {}", BuiltInRegistries.FEATURE_TYPE.getKey(TYPE));
    }
}
