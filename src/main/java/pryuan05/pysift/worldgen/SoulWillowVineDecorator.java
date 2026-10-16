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
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.feature.TreeFeature;
import net.minecraft.world.level.levelgen.feature.treedecorators.TreeDecorator;
import net.minecraft.world.level.levelgen.feature.treedecorators.TreeDecoratorType;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.SoulWillowVineBlock;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * 靈魂柳的邊緣垂藤：只從「下方是空氣、且位於葉團外緣（水平四鄰至少一格不是這棵樹的葉子）」的葉子底下垂下。
 * <ul>
 *   <li>vine_chance：每片外緣葉子長出垂藤的機率（0.4–0.6）。</li>
 *   <li>長度隨離樹中心的水平距離遞增：最內側 vine_min_length ～ vine_min_length+3，
 *       最外圈 vine_max_length/2 ～ vine_max_length，中間線性內插，末端長度隨機。</li>
 *   <li>往下遇到非空氣（含水面、地面）就停止。</li>
 *   <li>glow_chance：整串改用發光版的機率。</li>
 *   <li>顏色漸層：上 45% shade=0（青綠）、到 85% shade=1（淡藍）、其餘 shade=2（白／淡紫）。</li>
 *   <li>面（像原版藤蔓貼在叢林木上）：只有背向樹幹的面才有藤，朝樹幹那一側永遠沒有。
 *       最正對外側的面一定有；另一個也偏向外側的面以 side_chance 隨機長出（讓斜角處不會太單薄）。
 *       整串每一段都用同樣的面，從上到下連成一條。</li>
 *   <li>full_chance：整串四面都有藤的機率（讓垂簾更茂密，從裡面看也有藤）。</li>
 *   <li>tip：最後一段一定是 tip；下半段（strand 的後 60%）每段另有 tip_chance 機率用 tip 貼圖。</li>
 * </ul>
 */
public class SoulWillowVineDecorator extends TreeDecorator {
    public static final MapCodec<SoulWillowVineDecorator> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            Codec.floatRange(0.0F, 1.0F).fieldOf("vine_chance").forGetter(d -> d.vineChance),
            Codec.intRange(1, 64).fieldOf("vine_min_length").forGetter(d -> d.minLength),
            Codec.intRange(1, 64).fieldOf("vine_max_length").forGetter(d -> d.maxLength),
            Codec.floatRange(0.0F, 1.0F).fieldOf("glow_chance").forGetter(d -> d.glowChance),
            BuiltInRegistries.BLOCK.byNameCodec().fieldOf("vine").forGetter(d -> d.vine),
            BuiltInRegistries.BLOCK.byNameCodec().fieldOf("glowing_vine").forGetter(d -> d.glowingVine),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("side_chance", 0.25F).forGetter(d -> d.sideChance),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("tip_chance", 0.3F).forGetter(d -> d.tipChance),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("full_chance", 0.15F).forGetter(d -> d.fullChance)
    ).apply(instance, SoulWillowVineDecorator::new));

    public static final TreeDecoratorType<SoulWillowVineDecorator> TYPE = Registry.register(
            BuiltInRegistries.TREE_DECORATOR_TYPE, PySift.id("soul_willow_vines"), new TreeDecoratorType<>(CODEC));

    private final float vineChance;
    private final int minLength;
    private final int maxLength;
    private final float glowChance;
    private final Block vine;
    private final Block glowingVine;
    private final float sideChance;
    private final float tipChance;
    private final float fullChance;

    public SoulWillowVineDecorator(float vineChance, int minLength, int maxLength, float glowChance, Block vine, Block glowingVine,
                                   float sideChance, float tipChance, float fullChance) {
        this.vineChance = vineChance;
        this.minLength = minLength;
        this.maxLength = Math.max(minLength, maxLength);
        this.glowChance = glowChance;
        this.vine = vine;
        this.glowingVine = glowingVine;
        this.sideChance = sideChance;
        this.tipChance = tipChance;
        this.fullChance = fullChance;
    }

    @Override
    protected TreeDecoratorType<?> type() {
        return TYPE;
    }

    @Override
    public void place(Context context) {
        RandomSource random = context.random();
        Set<BlockPos> leaves = new HashSet<>(context.leaves());
        List<BlockPos> base = TreeFeature.getLowestTrunkOrRootOfTree(context);
        if (base.isEmpty()) {
            base = context.logs();
        }
        double centerX = base.stream().mapToInt(BlockPos::getX).average().orElse(0);
        double centerZ = base.stream().mapToInt(BlockPos::getZ).average().orElse(0);

        List<BlockPos> rim = new ArrayList<>();
        double farthest = 1;
        for (BlockPos leaf : context.leaves()) {
            if (!context.isAir(leaf.below()) || !onOuterEdge(leaf, leaves)) {
                continue;
            }
            rim.add(leaf);
            farthest = Math.max(farthest, Math.hypot(leaf.getX() + 0.5 - centerX, leaf.getZ() + 0.5 - centerZ));
        }
        for (BlockPos leaf : rim) {
            if (random.nextFloat() >= vineChance) {
                continue;
            }
            float t = (float) (Math.hypot(leaf.getX() + 0.5 - centerX, leaf.getZ() + 0.5 - centerZ) / farthest);
            int lo = Math.round(Mth.lerp(t, minLength, maxLength / 2.0F));
            int hi = Math.max(lo, Math.round(Mth.lerp(t, minLength + 3.0F, maxLength)));
            int length = lo + random.nextInt(hi - lo + 1);
            hang(context, leaf, centerX, centerZ, length, random.nextFloat() < glowChance ? glowingVine : vine);
        }
    }

    private static boolean onOuterEdge(BlockPos leaf, Set<BlockPos> leaves) {
        for (Direction direction : Direction.Plane.HORIZONTAL) {
            if (!leaves.contains(leaf.relative(direction))) {
                return true;
            }
        }
        return false;
    }

    /**
     * 由葉子下方往下放一串垂藤，遇到非空氣提早收尾。面只開在背向樹幹的那側（見 {@link #outwardSides}），
     * 整串相同。最後一段 tip=true，下半段另有 tipChance 的隨機 tip。
     */
    private void hang(Context context, BlockPos leaf, double centerX, double centerZ, int length, Block block) {
        RandomSource random = context.random();
        BlockPos start = leaf.below();
        int placed = 0;
        while (placed < length && context.isAir(start.below(placed))) {
            placed++;
        }
        EnumMap<Direction, Boolean> sides = outwardSides(leaf.getX() + 0.5 - centerX, leaf.getZ() + 0.5 - centerZ, random);
        for (int i = 0; i < placed; i++) {
            float along = (i + 0.5F) / placed;
            int shade = along < 0.45F ? 0 : along < 0.85F ? 1 : 2;
            boolean tip = i == placed - 1 || (along > 0.4F && random.nextFloat() < tipChance);
            BlockState state = block.defaultBlockState();
            if (state.hasProperty(SoulWillowVineBlock.SHADE)) {
                state = state.setValue(SoulWillowVineBlock.SHADE, shade).setValue(SoulWillowVineBlock.TIP, tip);
                for (var e : SoulWillowVineBlock.SIDES.entrySet()) {
                    state = state.setValue(e.getValue(), sides.get(e.getKey()));
                }
            }
            context.setBlock(start.below(i), state);
        }
    }

    /**
     * 從樹中心指向這串垂藤的水平向量 (dx, dz)：最正對外側的面一定有藤，另一個也朝外（分量 > 0）的面以 sideChance 隨機有，
     * 朝樹幹的兩個面一定沒有。正好在樹幹正下方（向量為 0）時只開一個隨機面。
     */
    private EnumMap<Direction, Boolean> outwardSides(double dx, double dz, RandomSource random) {
        EnumMap<Direction, Boolean> sides = new EnumMap<>(Direction.class);
        for (Direction direction : Direction.Plane.HORIZONTAL) {
            sides.put(direction, false);
        }
        if (random.nextFloat() < fullChance) {
            sides.replaceAll((direction, on) -> true);
            return sides;
        }
        if (dx == 0 && dz == 0) {
            sides.put(Direction.Plane.HORIZONTAL.getRandomDirection(random), true);
            return sides;
        }
        Direction xSide = dx > 0 ? Direction.EAST : Direction.WEST;
        Direction zSide = dz > 0 ? Direction.SOUTH : Direction.NORTH;
        boolean xMain = Math.abs(dx) >= Math.abs(dz);
        sides.put(xMain ? xSide : zSide, true);
        double minor = xMain ? Math.abs(dz) : Math.abs(dx);
        if (minor > 0.5 && random.nextFloat() < sideChance) {
            sides.put(xMain ? zSide : xSide, true);
        }
        return sides;
    }

    /** 觸發類別載入以完成註冊。 */
    public static void register() {
        PySift.LOGGER.info("Registered tree decorator {}", BuiltInRegistries.TREE_DECORATOR_TYPE.getKey(TYPE));
    }
}
