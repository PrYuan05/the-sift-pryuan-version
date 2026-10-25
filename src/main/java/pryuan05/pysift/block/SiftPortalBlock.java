package pryuan05.pysift.block;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.InsideBlockEffectApplier;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.Portal;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.portal.TeleportTransition;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import pryuan05.pysift.block.entity.SiftPortalBlockEntity;

/**
 * 篩靈界傳送門（pysift:sift_portal）：完整方塊選取邊框（Shapes.block()）、無碰撞、不可破壞、最高亮度，軸向沿 X 或 Z。
 * <ul>
 *   <li>外觀由 SiftPortalBlockEntityRenderer 繪製（亮白珠光大畫布流光、內側破曉金白光帶、向外溢出的聖光束），
 *       方塊模型本身不渲染（RenderShape.INVISIBLE），物品圖示與手持模型為 3D 完整方塊。</li>
 *   <li>玩家站在門裡 2 秒後傳送（期間用戶端播放 SiftPortalTransition 過場動畫），其他實體立即傳送；原版 Portal 機制處理冷卻與跨維度：主世界 ⇄ pysift:the_sift。</li>
 *   <li>進入 The Sift（或目標維度無現有傳送門）時，在安全地表旁生成裂隙型傳送門（中央 5×3 主要進入區域 + 邊緣擴散光塊），
 *       且絕不覆蓋實心地形方塊；而在遠古城市（ancient_city）強化深板岩巨口中開門時，可取代幽匿脈絡（sculk_vein）與地毯方塊使門面完整。</li>
 * </ul>
 * 也提供儀式用的工具：{@link #fillFrame} 以 BFS 填滿強化深板岩框架內部，{@link #buildRiftPortal} 生成裂隙型傳送門。
 */
public class SiftPortalBlock extends Block implements EntityBlock, Portal {
    public static final EnumProperty<Direction.Axis> AXIS = BlockStateProperties.HORIZONTAL_AXIS;
    public static final ResourceKey<Level> SIFT_DIM = ResourceKey.create(Registries.DIMENSION, Identifier.fromNamespaceAndPath("pysift", "the_sift"));
    private static final int MAX_FILL = 180;
    /** 玩家要在門裡站多久才傳送（tick）；用戶端的過場動畫 SiftPortalTransition 用同一個長度。 */
    public static final int PLAYER_TRANSITION_TICKS = 40;
    /** 裂隙型傳送門的邊緣擴散座標（相對於底邊中央 u=0, v=0）：左右中翼與四角外擴。 */
    private static final int[][] RIFT_EDGE_OFFSETS = {
            {-3, 1}, {3, 1},
            {-3, 3}, {3, 3}
    };

    public SiftPortalBlock(Properties properties) {
        super(properties);
        this.registerDefaultState(this.stateDefinition.any().setValue(AXIS, Direction.Axis.X));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(AXIS);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        Direction.Axis facing = context.getHorizontalDirection().getAxis();
        return this.defaultBlockState().setValue(AXIS, facing == Direction.Axis.Z ? Direction.Axis.X : Direction.Axis.Z);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return Shapes.block();
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.INVISIBLE;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new SiftPortalBlockEntity(pos, state);
    }

    // ------------------------------------------------------------------ ambience
    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        // 效能：越靠近門，每 tick 被抽到的門方塊越多，所以每次最多一顆，而且 END_ROD 活很久（會越積越多），只佔一小部分
        boolean x = state.getValue(AXIS) == Direction.Axis.X;
        if (random.nextBoolean()) {
            double px = pos.getX() + (x ? random.nextDouble() : 0.5 + (random.nextDouble() - 0.5) * 0.6);
            double py = pos.getY() + random.nextDouble();
            double pz = pos.getZ() + (x ? 0.5 + (random.nextDouble() - 0.5) * 0.6 : random.nextDouble());
            level.addParticle(random.nextInt(6) == 0 ? ParticleTypes.END_ROD : ParticleTypes.PORTAL,
                    px, py, pz, (random.nextDouble() - 0.5) * 0.04, 0.02, (random.nextDouble() - 0.5) * 0.04);
        }
        // 夜晚：光點從門面往前後兩側飄出去
        float night = SiftDayPhase.night(level);
        if (night > 0.2f && random.nextFloat() < night * 0.25f) {
            double out = (random.nextBoolean() ? 1 : -1) * (0.04 + random.nextDouble() * 0.05);
            double px = pos.getX() + (x ? random.nextDouble() : 0.5);
            double pz = pos.getZ() + (x ? 0.5 : random.nextDouble());
            level.addParticle(random.nextInt(5) == 0 ? ParticleTypes.END_ROD : ParticleTypes.GLOW, px, pos.getY() + random.nextDouble(), pz,
                    x ? 0 : out, 0.01, x ? out : 0);
        }
        if (random.nextInt(480) == 0) {   // 大門有上百格，聲音太密會把音效通道塞滿
            level.playLocalSound(pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, SoundEvents.AMETHYST_BLOCK_CHIME,
                    SoundSource.BLOCKS, 0.6f, 0.6f + random.nextFloat() * 0.6f, false);
        }
    }

    // ------------------------------------------------------------------ teleport (vanilla Portal handles cooldown)
    @Override
    protected void entityInside(BlockState state, Level level, BlockPos pos, Entity entity, InsideBlockEffectApplier effects, boolean intersects) {
        if (!level.isClientSide() && entity.canUsePortal(false)) {
            entity.setAsInsidePortal(this, pos);
        }
    }

    /** 玩家 2 秒（播放過場動畫），其他實體幾乎立即傳送。 */
    @Override
    public int getPortalTransitionTime(ServerLevel level, Entity entity) {
        return entity instanceof Player ? PLAYER_TRANSITION_TICKS : 1;
    }

    @Override
    public Portal.Transition getLocalTransition() {
        return Portal.Transition.NONE;
    }

    @Override
    public TeleportTransition getPortalDestination(ServerLevel level, Entity entity, BlockPos pos) {
        ResourceKey<Level> targetKey = level.dimension() == SIFT_DIM ? Level.OVERWORLD : SIFT_DIM;
        ServerLevel target = level.getServer().getLevel(targetKey);
        if (target == null) {
            return null;
        }
        BlockPos landing = prepareLanding(target, pos.getX(), pos.getZ());
        Vec3 at = Vec3.atBottomCenterOf(landing);
        return new TeleportTransition(target, at, Vec3.ZERO, entity.getYRot(), entity.getXRot(), TeleportTransition.PLAY_PORTAL_SOUND);
    }

    /**
     * 目標維度 (x, z) 附近的落點：附近已經有門就站到門前；沒有就先找地面、蓋一座回程門，
     * 再重新找一次門前的空地（落點是蓋門之前選的，門框、緩坡或地基可能剛好蓋在上面，玩家會卡在方塊裡）。
     */
    public static BlockPos prepareLanding(ServerLevel target, int x, int z) {
        BlockPos existing = findExistingPortalLanding(target, x, z);
        if (existing != null) {
            return existing;
        }
        BlockPos landing = findLanding(target, x, z);
        ensureReturnPortal(target, landing);
        BlockPos afterBuild = findExistingPortalLanding(target, landing.getX(), landing.getZ());
        if (afterBuild != null && isSafeStandSpot(target, afterBuild)) {
            return afterBuild;
        }
        return isSafeStandSpot(target, landing) ? landing : nearestSafeSpot(target, landing, landing);
    }

    /** 落點可以站：腳下實心、腳和頭的位置都沒有碰撞箱。 */
    public static boolean isSafeLanding(ServerLevel level, BlockPos feet) {
        return isSafeStandSpot(level, feet);
    }

    /**
     * 傳送門允許取代的方塊：空氣、遠古城市巨口內的幽匿脈絡（sculk_vein）與地毯、以及無液體的可被取代薄層植物／火焰，
     * 絕不取代任何實心地形方塊。
     */
    public static boolean canPortalReplace(BlockState state) {
        if (state.isAir()) {
            return true;
        }
        if (!state.getFluidState().isEmpty()) {
            return false;
        }
        return state.is(Blocks.SCULK_VEIN)
                || state.is(BlockTags.WOOL_CARPETS)
                || state.is(Blocks.MOSS_CARPET)
                || state.is(Blocks.PALE_MOSS_CARPET)
                || state.is(BlockTags.REPLACEABLE_BY_TREES)
                || state.is(BlockTags.FLOWERS)
                || state.canBeReplaced();
    }

    /** 判斷位置是否可供玩家站立（無碰撞箱、無液體、非傳送門本體）。 */
    private static boolean canStandIn(ServerLevel level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        return !state.is(ModBlocks.SIFT_PORTAL)
                && state.getFluidState().isEmpty()
                && state.getCollisionShape(level, pos).isEmpty();
    }

    private static boolean isSafeStandSpot(ServerLevel level, BlockPos feet) {
        int y = feet.getY();
        if (y <= level.getMinY() + 1 || y >= level.getMaxY() - 3) {
            return false;
        }
        BlockPos below = feet.below();
        BlockState ground = level.getBlockState(below);
        return ground.isSolid()
                && !ground.is(ModBlocks.SIFT_PORTAL)
                && level.getFluidState(below).isEmpty()
                && canStandIn(level, feet)
                && canStandIn(level, feet.above());
    }

    /**
     * 若目標維度 (x, z) 水平 24 格內已有傳送門（例如主世界地底的遠古城市巨口或 The Sift 已生成的裂隙門），
     * 直接找該傳送門外圍的安全站立點，避免重複生門或覆蓋地形。
     */
    private static BlockPos findExistingPortalLanding(ServerLevel level, int x, int z) {
        int cx = x >> 4, cz = z >> 4;
        BlockPos nearestPortal = null;
        double bestDist = Double.MAX_VALUE;
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                LevelChunk chunk = level.getChunk(cx + dx, cz + dz);
                for (BlockEntity be : chunk.getBlockEntities().values()) {
                    if (!(be instanceof SiftPortalBlockEntity)) {
                        continue;
                    }
                    BlockPos p = be.getBlockPos();
                    if (!level.getBlockState(p).is(ModBlocks.SIFT_PORTAL)) {
                        continue;
                    }
                    double d2 = (p.getX() - x) * (double) (p.getX() - x) + (p.getZ() - z) * (double) (p.getZ() - z);
                    if (d2 <= 24 * 24 && (nearestPortal == null || p.getY() < nearestPortal.getY() || (p.getY() == nearestPortal.getY() && d2 < bestDist))) {
                        nearestPortal = p;
                        bestDist = d2;
                    }
                }
            }
        }
        if (nearestPortal == null) {
            return null;
        }
        BlockState portalState = level.getBlockState(nearestPortal);
        Direction.Axis axis = portalState.hasProperty(AXIS) ? portalState.getValue(AXIS) : Direction.Axis.X;
        Direction across = axis == Direction.Axis.X ? Direction.SOUTH : Direction.EAST;
        Direction along = axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
        for (int dist = 2; dist <= 8; dist++) {
            for (Direction side : new Direction[]{across, across.getOpposite()}) {
                for (int u : new int[]{0, 1, -1, 2, -2}) {
                    for (int dy = 2; dy >= -6; dy--) {   // 緩坡往外一路往下，所以往下多找幾格
                        BlockPos candidate = nearestPortal.relative(side, dist).relative(along, u).above(dy);
                        if (isSafeStandSpot(level, candidate)) {
                            return candidate;
                        }
                    }
                }
            }
        }
        return nearestSafeSpot(level, nearestPortal.relative(across, 2), nearestPortal.relative(across, 2));
    }

    /**
     * centre 附近（水平 8 格、上下 6 格內）最近的安全站立點；都沒有就在 fallback 挖出兩格高的空間（不動傳送門與基岩），
     * 保證玩家不會卡在方塊裡。
     */
    private static BlockPos nearestSafeSpot(ServerLevel level, BlockPos centre, BlockPos fallback) {
        BlockPos best = null;
        double bestDist = Double.MAX_VALUE;
        for (BlockPos p : BlockPos.betweenClosed(centre.offset(-8, -6, -8), centre.offset(8, 6, 8))) {
            double d = p.distSqr(centre);
            if (d < bestDist && isSafeStandSpot(level, p)) {
                best = p.immutable();
                bestDist = d;
            }
        }
        if (best != null) {
            return best;
        }
        for (BlockPos p : new BlockPos[]{fallback, fallback.above()}) {
            BlockState state = level.getBlockState(p);
            if (!state.isAir() && !state.is(ModBlocks.SIFT_PORTAL) && state.getDestroySpeed(level, p) >= 0) {
                level.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
            }
        }
        return fallback;
    }

    /** 目標維度 (x, z) 的安全落點（腳下）；優先在周圍 16 格內尋找乾燥實心地表，絕不覆蓋地形方塊。 */
    private static BlockPos findLanding(ServerLevel level, int x, int z) {
        for (int r = 0; r <= 16; r++) {
            for (int dx = -r; dx <= r; dx++) {
                for (int dz = -r; dz <= r; dz++) {
                    if (r > 0 && Math.abs(dx) != r && Math.abs(dz) != r) {
                        continue;
                    }
                    int tx = x + dx, tz = z + dz;
                    level.getChunk(tx >> 4, tz >> 4);
                    int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, tx, tz);
                    BlockPos feet = new BlockPos(tx, y, tz);
                    if (isSafeStandSpot(level, feet)) {
                        return feet;
                    }
                }
            }
        }
        // 僅在完全沒有固體地面（如虛空或整片深海）時，於不破壞地形的前提下鋪設平台
        int y = Math.max(80, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z) + 1);
        BlockPos platform = new BlockPos(x, y, z);
        BlockState slate = ModBlocks.BY_NAME.getOrDefault("dark_slate", Blocks.DEEPSLATE).defaultBlockState();
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                BlockPos floorPos = platform.offset(dx, -1, dz);
                BlockState cur = level.getBlockState(floorPos);
                if (canPortalReplace(cur) || !cur.getFluidState().isEmpty()) {
                    level.setBlockAndUpdate(floorPos, slate);
                }
            }
        }
        return platform;
    }

    /**
     * 落點 16 格內沒有傳送門時，在落點旁挑選最開闊的方向生成裂隙型傳送門（中央 5×3 主要進入區域 + 邊緣擴散效果），
     * 只取代空氣與薄層植被，不取代任何實心地形方塊。
     */
    private static void ensureReturnPortal(ServerLevel level, BlockPos landing) {
        Block portal = ModBlocks.SIFT_PORTAL;
        for (BlockPos p : BlockPos.betweenClosed(landing.offset(-16, -12, -16), landing.offset(16, 12, 16))) {
            if (level.getBlockState(p).is(portal)) {
                return;
            }
        }
        Direction[] dirs = {Direction.EAST, Direction.WEST, Direction.SOUTH, Direction.NORTH};
        BlockPos bestCentre = landing.east(4);
        Direction.Axis bestAxis = Direction.Axis.Z;
        int bestScore = Integer.MIN_VALUE;
        for (Direction dir : dirs) {
            Direction.Axis axis = dir.getAxis() == Direction.Axis.X ? Direction.Axis.Z : Direction.Axis.X;
            BlockPos horiz = landing.relative(dir, 4);
            int groundY = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, horiz.getX(), horiz.getZ());
            int baseY = Math.max(landing.getY(), groundY);
            for (int lift = 0; lift <= 2; lift++) {
                BlockPos candidate = new BlockPos(horiz.getX(), baseY + lift, horiz.getZ());
                int score = scoreRiftPlacement(level, candidate, axis) - lift;
                if (score > bestScore) {
                    bestScore = score;
                    bestCentre = candidate;
                    bestAxis = axis;
                }
            }
        }
        if (level.dimension() == SIFT_DIM) {
            // 篩靈界這一端：使用者設計的到達門（依生態域色系三選一）；結構檔不在時退回程式畫的縮小版巨口
            if (!buildArrivalPortal(level, bestCentre, bestAxis)) {
                buildMouthFrame(level, bestCentre, bestAxis);
            }
        } else {
            buildRiftPortal(level, bestCentre, bestAxis);
        }
    }

    /**
     * 縮小版的伏守者巨口（13 寬 × 9 高，由下往上；中央 9×5 是傳送門）：
     * <pre>
     *   SS.........SS   靈魂晶塊的「角」
     *   CC#########CC
     *   .#PPPPPPPPP#.
     *   .#PPPPPPPPP#.
     *   .CPPPPPPPPPC.
     *   .#PPPPPPPPP#.
     *   .#PPPPPPPPP#.
     *   CC#########CC
     *   #############   地基（取代地面）
     * </pre>
     * # 深色板岩磚、C 浮雕深色板岩磚、S 靈魂晶塊。baseCentre 是地面高度（站立高度）的中央；門前後一格會清空方便走進去，
     * 地基下方懸空時往下補到實心為止。
     */
    private static final String[] MOUTH = {
            "#############",
            "CC#########CC",
            ".#PPPPPPPPP#.",
            ".#PPPPPPPPP#.",
            ".CPPPPPPPPPC.",
            ".#PPPPPPPPP#.",
            ".#PPPPPPPPP#.",
            "CC#########CC",
            "SS.........SS"};

    public static void buildMouthFrame(ServerLevel level, BlockPos baseCentre, Direction.Axis axis) {
        Direction along = axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
        Direction normal = axis == Direction.Axis.X ? Direction.SOUTH : Direction.EAST;
        BlockState brick = block("dark_slate_bricks", Blocks.DEEPSLATE_BRICKS);
        BlockState chiseled = block("chiseled_dark_slate_bricks", Blocks.CHISELED_DEEPSLATE);
        BlockState crystal = pryuan05.pysift.block.SoulCrystal.SOUL_CRYSTAL_BLOCK.defaultBlockState();
        BlockState portal = ModBlocks.SIFT_PORTAL.defaultBlockState().setValue(AXIS, axis);
        int half = MOUTH[0].length() / 2;
        for (int row = 0; row < MOUTH.length; row++) {
            int y = row - 1;   // 第 0 列是地基，在地面下一格
            for (int i = 0; i < MOUTH[row].length(); i++) {
                BlockPos p = baseCentre.relative(along, i - half).above(y);
                char c = MOUTH[row].charAt(i);
                BlockState state = switch (c) {
                    case '#' -> brick;
                    case 'C' -> chiseled;
                    case 'S' -> crystal;
                    case 'P' -> portal;
                    default -> null;
                };
                if (state == null) {
                    if (row > 0 && !level.getBlockState(p).isAir() && level.getBlockState(p).getDestroySpeed(level, p) >= 0) {
                        level.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);   // 輪廓外清乾淨
                    }
                    continue;
                }
                level.setBlock(p, state, Block.UPDATE_ALL);
                if (row == 0) {   // 地基下方懸空：往下補實
                    for (int d = 1; d <= 8 && level.getBlockState(p.below(d)).canBeReplaced(); d++) {
                        level.setBlock(p.below(d), brick, Block.UPDATE_ALL);
                    }
                }
                if (c == 'P') {   // 門前後各清一格，方便走進去
                    for (Direction side : new Direction[]{normal, normal.getOpposite()}) {
                        BlockPos q = p.relative(side);
                        if (!level.getBlockState(q).isAir() && level.getBlockState(q).getDestroySpeed(level, q) >= 0) {
                            level.setBlock(q, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
                        }
                    }
                }
            }
        }
    }

    /**
     * 到達門的三種設計（data/pysift/structure/portal/*.nbt，由 tools/worldgen/build_portal_designs.py 從使用者在遊戲裡
     * 蓋的門產生），依生態域的色系挑選；沒列出的生態域用 silted。
     */
    public static final java.util.Map<String, String> PORTAL_DESIGNS = java.util.Map.of(
            "crimson_strata_canyon", "ember", "amber_dunes", "dune", "lullaby_hills", "ember",
            "violet_slate_abyss", "slate",
            "willow_grove", "silted");
    /** 每種設計的階梯石材：{整塊, 半磚}。 */
    private static final java.util.Map<String, String[]> RAMP_BLOCKS = java.util.Map.of(
            "ember", new String[]{"ember_stone", "ember_stone_slab"},
            "slate", new String[]{"dark_slate", "dark_slate_slab"},
            "silted", new String[]{"silted_strata", "silted_strata_slab"},
            "dune", new String[]{"bleached_sandstone_bricks", "bleached_sandstone_brick_slab"});
    /** 結構檔裡傳送門底邊中央的位置（門面沿 Z 軸）。 */
    private static final BlockPos DESIGN_ANCHOR = new BlockPos(2, 2, 8);

    /** 在 base（站立高度）蓋到達門，門底在 base 上方 2 格。成功回傳 true。 */
    public static boolean buildArrivalPortal(ServerLevel level, BlockPos base, Direction.Axis axis) {
        String biome = level.getBiome(base).unwrapKey().map(k -> k.identifier().getPath()).orElse("");
        String design = PORTAL_DESIGNS.getOrDefault(biome, "silted");
        java.util.Optional<net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate> template =
                level.getStructureTemplateManager().get(pryuan05.pysift.PySift.id("portal/" + design));
        if (template.isEmpty()) {
            return false;
        }
        // 每座門的朝向（轉 180°）和左右鏡像都隨機，同一種設計看起來也不會每次一模一樣
        RandomSource random = level.getRandom();
        net.minecraft.world.level.block.Rotation rotation = axis == Direction.Axis.Z
                ? (random.nextBoolean() ? net.minecraft.world.level.block.Rotation.NONE : net.minecraft.world.level.block.Rotation.CLOCKWISE_180)
                : (random.nextBoolean() ? net.minecraft.world.level.block.Rotation.CLOCKWISE_90 : net.minecraft.world.level.block.Rotation.COUNTERCLOCKWISE_90);
        var settings = new net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings()
                .setRotation(rotation)
                .setMirror(random.nextBoolean() ? net.minecraft.world.level.block.Mirror.NONE : net.minecraft.world.level.block.Mirror.LEFT_RIGHT);
        BlockPos anchor = net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate
                .calculateRelativePosition(settings, DESIGN_ANCHOR);
        BlockPos origin = base.above(2).subtract(anchor);
        var box = template.get().getBoundingBox(settings, origin);
        // 先清空地面以上的範圍（門面與裝飾不會卡進地形），再放結構
        for (BlockPos p : BlockPos.betweenClosed(box.minX(), origin.getY(), box.minZ(), box.maxX(), box.maxY(), box.maxZ())) {
            BlockState state = level.getBlockState(p);
            if (!state.isAir() && state.getDestroySpeed(level, p) >= 0) {
                level.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
            }
        }
        template.get().placeInWorld(level, origin, origin, settings, level.getRandom(), Block.UPDATE_CLIENTS);
        // 底下懸空：每一直排找結構最底下的實心方塊（只看底下兩層，拱頂的突出不算），往下補地基到實心地面為止
        BlockState footing = block(RAMP_BLOCKS.getOrDefault(design, RAMP_BLOCKS.get("silted"))[0], Blocks.STONE_BRICKS);
        for (int x = box.minX(); x <= box.maxX(); x++) {
            for (int z = box.minZ(); z <= box.maxZ(); z++) {
                for (int y = origin.getY(); y <= origin.getY() + 1; y++) {
                    BlockPos p = new BlockPos(x, y, z);
                    BlockState bottom = level.getBlockState(p);
                    if (bottom.canBeReplaced() || bottom.getCollisionShape(level, p).isEmpty()) {
                        continue;
                    }
                    BlockState fill = bottom.isCollisionShapeFullBlock(level, p) ? bottom : footing;
                    for (int d = 1; d <= 24 && loose(level, p.below(d)); d++) {
                        level.setBlock(p.below(d), fill, Block.UPDATE_CLIENTS);
                    }
                    break;
                }
            }
        }
        buildRamps(level, base.above(2), axis, design);
        return true;
    }

    /**
     * 門前後各一道 7 格寬的緩坡，讓玩家不用跳就能走進門：先量出門前地板（設計本身的地台，或門底）最外緣的高度，
     * 再往外每格降半格（整塊、半磚交替），直到接上地面（最多 10 格）。只填空的位置（不會破壞門本身的設計），
     * 坡上清出 3 格高的走道，坡下懸空就補實（最多 24 格）。portalBottom：傳送門最底下那一格。
     * 坡面用當地的地表方塊和同色系的半磚（看起來像地面延伸上去），坡下填地表底下那層。
     * 每座門都不一樣：坡寬 5～9 格、兩側邊緣參差（隨機提早結束），坡腳再散落幾塊設計石材的碎石。
     */
    private static void buildRamps(ServerLevel level, BlockPos portalBottom, Direction.Axis axis, String design) {
        String[] names = RAMP_BLOCKS.getOrDefault(design, RAMP_BLOCKS.get("silted"));
        BlockState full = block(names[0], Blocks.STONE_BRICKS);
        BlockState slab = block(names[1], Blocks.STONE_BRICK_SLAB);
        Direction along = axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
        Direction normal = axis == Direction.Axis.X ? Direction.SOUTH : Direction.EAST;
        RandomSource random = level.getRandom();
        for (Direction side : new Direction[]{normal, normal.getOpposite()}) {
            int half = 2 + random.nextInt(3);   // 坡寬 5～9
            int[] length = new int[half * 2 + 1];   // 每一直條最多鋪幾格；最外側兩條隨機短一點
            for (int u = -half; u <= half; u++) {
                length[u + half] = Math.abs(u) >= half - 1 ? 2 + random.nextInt(9) : 99;
            }
            int lastD = 0;
            // 坡面用當地的地表方塊（整塊）和同色系的半磚，坡下的填充用地表底下那層；量不到地表就用設計的石材
            BlockState[] local = sampleGround(level, portalBottom, side, along);
            BlockState surface = local != null ? local[0] : full;
            BlockState under = local != null ? local[1] : full;
            BlockState surfaceHalf = local != null ? surfaceSlab(local[0], slab) : slab;
            // 門前地板的最外緣：離門 1~3 格內、高度在門底 ±2 的實心地板，取最外面那一格（以半格為單位）
            int startD = 0, startTop = portalBottom.getY() * 2;
            for (int d = 1; d <= 3; d++) {
                Integer top = surfaceTop2(level, portalBottom.relative(side, d), portalBottom.getY() + 2, portalBottom.getY() - 2);
                if (top == null || top < portalBottom.getY() * 2) {
                    break;
                }
                startD = d;
                startTop = top;
            }
            for (int d = startD + 1, target = startTop - 1; d <= startD + 10; d++, target--) {   // target：這一格坡面的高度（半格）
                BlockPos centre = portalBottom.relative(side, d);
                Integer ground = surfaceTop2(level, centre, portalBottom.getY() + 2, portalBottom.getY() - 14);
                if (ground != null && ground >= target) {
                    break;   // 接上地面了
                }
                lastD = d;
                int blockY = Math.floorDiv(target - 1, 2);
                boolean isSlab = target % 2 != 0;   // 半格高 -> 下半磚
                for (int u = -half; u <= half; u++) {
                    if (d - startD > length[u + half]) {
                        continue;
                    }
                    BlockPos stepPos = new BlockPos(centre.getX(), blockY, centre.getZ()).relative(along, u);
                    if (loose(level, stepPos)) {
                        level.setBlock(stepPos, isSlab ? surfaceHalf : surface, Block.UPDATE_CLIENTS);
                    }
                    for (int dy = 1; dy <= 3; dy++) {   // 坡上的走道
                        BlockPos air = stepPos.above(dy);
                        BlockState in = level.getBlockState(air);
                        if (!in.isAir() && !in.is(ModBlocks.SIFT_PORTAL) && in.getDestroySpeed(level, air) >= 0) {
                            level.setBlock(air, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
                        }
                    }
                    for (int down = 1; down <= 24 && loose(level, stepPos.below(down)); down++) {
                        level.setBlock(stepPos.below(down), under, Block.UPDATE_CLIENTS);
                    }
                }
            }
            // 坡腳附近散落幾塊碎石（半磚或整塊），只放在實心地面上
            for (int i = 2 + random.nextInt(5); i > 0; i--) {
                int d = Math.max(startD, lastD) + 1 + random.nextInt(3);
                int u = random.nextInt(half * 2 + 5) - half - 2;
                BlockPos column = portalBottom.relative(side, d).relative(along, u);
                Integer top = surfaceTop2(level, column, portalBottom.getY() + 2, portalBottom.getY() - 14);
                if (top == null || top % 2 != 0) {
                    continue;
                }
                BlockPos rubble = new BlockPos(column.getX(), top / 2, column.getZ());
                if (loose(level, rubble) && level.getBlockState(rubble.below()).isFaceSturdy(level, rubble.below(), Direction.UP)) {
                    level.setBlock(rubble, random.nextInt(3) == 0 ? full : slab, Block.UPDATE_CLIENTS);
                }
            }
        }
    }

    /** 可以直接蓋過去的位置：空氣、液體、花草這類沒有碰撞箱的方塊（原版的花不算 canBeReplaced，會讓地基停在花上面而懸空）；傳送門本身除外。 */
    private static boolean loose(ServerLevel level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        return !state.is(ModBlocks.SIFT_PORTAL) && (state.canBeReplaced() || state.getCollisionShape(level, pos).isEmpty());
    }

    /**
     * 門外 5～12 格、坡會鋪到的那一帶最常見的地表方塊（實心整塊）和它底下那一層：{地表, 底下}。量不到回傳 null。
     */
    private static BlockState[] sampleGround(ServerLevel level, BlockPos portalBottom, Direction side, Direction along) {
        java.util.Map<BlockState, Integer> tops = new java.util.HashMap<>();
        java.util.Map<BlockState, BlockState> unders = new java.util.HashMap<>();
        for (int d = 5; d <= 12; d++) {
            for (int u = -3; u <= 3; u++) {
                BlockPos column = portalBottom.relative(side, d).relative(along, u);
                for (int y = portalBottom.getY() + 4; y >= portalBottom.getY() - 16; y--) {
                    BlockPos p = new BlockPos(column.getX(), y, column.getZ());
                    if (loose(level, p)) {
                        continue;
                    }
                    BlockState state = level.getBlockState(p);
                    if (state.isCollisionShapeFullBlock(level, p) && !state.hasBlockEntity() && level.getFluidState(p).isEmpty()) {
                        tops.merge(state, 1, Integer::sum);
                        BlockState below = level.getBlockState(p.below());
                        unders.putIfAbsent(state, below.isCollisionShapeFullBlock(level, p.below()) && !below.hasBlockEntity() ? below : state);
                    }
                    break;
                }
            }
        }
        return tops.entrySet().stream().max(java.util.Map.Entry.comparingByValue())
                .map(e -> new BlockState[]{e.getKey(), unders.get(e.getKey())}).orElse(null);
    }

    /**
     * 跟地表同色系的半磚：「X_capped_Y」（頂面是 X 色）找 X_strata_slab、X_stone_slab、X_marble_slab、X_slab，
     * 沙子用漂白砂岩半磚，其他找「名稱_slab」；都沒有就用 fallback。
     */
    private static BlockState surfaceSlab(BlockState surface, BlockState fallback) {
        String name = net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(surface.getBlock()).getPath();
        List<String> candidates = new ArrayList<>();
        int capped = name.indexOf("_capped_");
        if (capped > 0) {
            String cap = name.substring(0, capped);
            candidates.addAll(List.of(cap + "_strata_slab", cap + "_stone_slab", cap + "_marble_slab", cap + "_slab"));
        }
        if (name.endsWith("sand")) {
            candidates.add("bleached_sandstone_slab");
        }
        candidates.add(name.replaceAll("_\\d+$", "") + "_slab");
        for (String c : candidates) {
            Block b = net.minecraft.core.registries.BuiltInRegistries.BLOCK.getOptional(pryuan05.pysift.PySift.id(c)).orElse(null);
            if (b instanceof net.minecraft.world.level.block.SlabBlock) {
                return b.defaultBlockState();
            }
        }
        return fallback;
    }

    /** column 從 top 往下到 bottom，第一個能站的表面高度（半格為單位；植物這類可取代的方塊不算）；找不到回傳 null。 */
    private static Integer surfaceTop2(ServerLevel level, BlockPos column, int top, int bottom) {
        for (int y = top; y >= bottom; y--) {
            BlockPos p = new BlockPos(column.getX(), y, column.getZ());
            BlockState state = level.getBlockState(p);
            if (state.canBeReplaced() || state.getCollisionShape(level, p).isEmpty() || state.is(ModBlocks.SIFT_PORTAL)) {
                continue;
            }
            double h = state.getCollisionShape(level, p).max(Direction.Axis.Y);
            return y * 2 + (int) Math.round(h * 2);
        }
        return null;
    }

    /** 結構轉 90° 時，傳送門的軸向跟著換。 */
    @Override
    protected BlockState rotate(BlockState state, net.minecraft.world.level.block.Rotation rotation) {
        return switch (rotation) {
            case CLOCKWISE_90, COUNTERCLOCKWISE_90 -> state.setValue(AXIS, state.getValue(AXIS) == Direction.Axis.X ? Direction.Axis.Z : Direction.Axis.X);
            default -> state;
        };
    }

    private static BlockState block(String name, Block fallback) {
        return net.minecraft.core.registries.BuiltInRegistries.BLOCK.getOptional(pryuan05.pysift.PySift.id(name))
                .orElse(fallback).defaultBlockState();
    }

    private static int scoreRiftPlacement(ServerLevel level, BlockPos baseCentre, Direction.Axis axis) {
        Direction along = axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
        int score = 0;
        for (int u = -2; u <= 2; u++) {
            for (int v = 0; v <= 2; v++) {
                if (canPortalReplace(level.getBlockState(baseCentre.relative(along, u).above(v)))) {
                    score += 2;
                }
            }
        }
        for (int[] off : RIFT_EDGE_OFFSETS) {
            if (canPortalReplace(level.getBlockState(baseCentre.relative(along, off[0]).above(off[1])))) {
                score += 1;
            }
        }
        return score;
    }

    /**
     * 生成無邊框裂隙型傳送門（進入 The Sift 後的傳送門形式）：
     * <ul>
     *   <li>主要進入區域：中央 5 寬 × 3 高（u = -2..2, v = 0..2）。</li>
     *   <li>邊緣擴散效果：左右中翼（u = ±3, v = 1）、頂部兩角外擴（u = ±3, v = 3）與底部外側擴散塊（u = -4, v = 0；若受地形阻擋則改放 u = 4, v = 0）。</li>
     *   <li>嚴格檢查 {@link #canPortalReplace}，絕不覆蓋實心地形方塊。</li>
     * </ul>
     */
    public static void buildRiftPortal(net.minecraft.world.level.LevelAccessor level, BlockPos baseCentre, Direction.Axis axis) {
        Direction along = axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
        BlockState portal = ModBlocks.SIFT_PORTAL.defaultBlockState().setValue(AXIS, axis);
        // 1. 中央 5×3 主要進入區域（保底確保中間 1×2 可通行，但仍只替換非實心地形）
        for (int u = -2; u <= 2; u++) {
            for (int v = 0; v <= 2; v++) {
                BlockPos p = baseCentre.relative(along, u).above(v);
                if (canPortalReplace(level.getBlockState(p))) {
                    level.setBlock(p, portal, Block.UPDATE_CLIENTS);
                }
            }
        }
        // 2. 邊緣擴散光塊
        for (int[] off : RIFT_EDGE_OFFSETS) {
            BlockPos p = baseCentre.relative(along, off[0]).above(off[1]);
            if (canPortalReplace(level.getBlockState(p))) {
                level.setBlock(p, portal, Block.UPDATE_CLIENTS);
            }
        }
        BlockPos outerLeft = baseCentre.relative(along, -4);
        BlockPos outerRight = baseCentre.relative(along, 4);
        if (canPortalReplace(level.getBlockState(outerLeft))) {
            level.setBlock(outerLeft, portal, Block.UPDATE_CLIENTS);
        } else if (canPortalReplace(level.getBlockState(outerRight))) {
            level.setBlock(outerRight, portal, Block.UPDATE_CLIENTS);
        }
    }

    // ------------------------------------------------------------------ frame helpers (also used by the Singer ritual)
    /**
     * 蓋一座外框 outerW × outerH 的強化深板岩框架（base 為外框左下角，沿 axis 展開），內部填滿對應軸向的傳送門；
     * 只在可替換位置放置，不覆蓋實心地形方塊。
     */
    public static void buildFrame(ServerLevel level, BlockPos base, Direction.Axis axis, int outerW, int outerH) {
        Direction along = axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
        BlockState frame = Blocks.REINFORCED_DEEPSLATE.defaultBlockState();
        BlockState portal = ModBlocks.SIFT_PORTAL.defaultBlockState().setValue(AXIS, axis);
        for (int w = 0; w < outerW; w++) {
            for (int h = 0; h < outerH; h++) {
                BlockPos p = base.relative(along, w).above(h);
                if (!canPortalReplace(level.getBlockState(p))) {
                    continue;
                }
                boolean edge = w == 0 || h == 0 || w == outerW - 1 || h == outerH - 1;
                level.setBlock(p, edge ? frame : portal, Block.UPDATE_CLIENTS);
            }
        }
    }

    /** 一個封閉框架的內部（尚未填門）：內部方塊與框架所在平面的軸向。 */
    public record Frame(List<BlockPos> interior, Direction.Axis axis) {
        public Vec3 centre() {
            double x = 0, y = 0, z = 0;
            for (BlockPos p : interior) {
                x += p.getX() + 0.5;
                y += p.getY() + 0.5;
                z += p.getZ() + 0.5;
            }
            return new Vec3(x / interior.size(), y / interior.size(), z / interior.size());
        }

        /** 框架寬度方向的正中點（世界座標，可能是半格）。用內部的最左與最右算，不受不規則形狀影響。 */
        public double alongMiddle() {
            boolean x = axis == Direction.Axis.X;
            int min = interior.stream().mapToInt(p -> x ? p.getX() : p.getZ()).min().orElse(0);
            int max = interior.stream().mapToInt(p -> x ? p.getX() : p.getZ()).max().orElse(0);
            return (min + max + 1) / 2.0;
        }

        public int bottomY() {
            return interior.stream().mapToInt(BlockPos::getY).min().orElse(0);
        }

        public int topY() {
            return interior.stream().mapToInt(BlockPos::getY).max().orElse(0);
        }
    }

    /**
     * 在 centre 周圍 radius 格內找以 frameBlock 圍成的框架，沿框架所在的垂直平面（X-Y 或 Z-Y）從內側做 BFS，
     * 可穿越空氣、遠古城市巨口內的幽匿脈絡（sculk_vein）與地毯方塊，以 frameBlock（或其他實心方塊）為邊界；
     * 區域封閉且不超過 180 格時回傳該內部（不放方塊）。找不到時回傳 null。
     */
    public static Frame findFrame(ServerLevel level, BlockPos centre, int radius, Block frameBlock) {
        Set<BlockPos> triedX = new HashSet<>();
        Set<BlockPos> triedZ = new HashSet<>();
        for (BlockPos frame : BlockPos.betweenClosed(centre.offset(-radius, -radius, -radius), centre.offset(radius, radius, radius))) {
            if (!level.getBlockState(frame).is(frameBlock)) {
                continue;
            }
            for (Direction.Axis axis : new Direction.Axis[]{Direction.Axis.X, Direction.Axis.Z}) {
                Direction along = axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
                for (Direction d : new Direction[]{Direction.UP, Direction.DOWN, along, along.getOpposite()}) {
                    BlockPos start = frame.relative(d).immutable();
                    Set<BlockPos> tried = axis == Direction.Axis.X ? triedX : triedZ;
                    if (!canPortalReplace(level.getBlockState(start)) || !tried.add(start)) {
                        continue;
                    }
                    List<BlockPos> region = flood(level, start, axis, frameBlock);
                    if (region != null) {
                        return new Frame(region, axis);
                    }
                }
            }
        }
        return null;
    }

    /** 把框架內部整片換成傳送門。 */
    public static void fillFrame(ServerLevel level, Frame frame) {
        BlockState portal = ModBlocks.SIFT_PORTAL.defaultBlockState().setValue(AXIS, frame.axis());
        for (BlockPos p : frame.interior()) {
            level.setBlock(p, portal, Block.UPDATE_CLIENTS);
        }
    }

    /** 找強化深板岩框架並填門（舊介面）。回傳填入的方塊（找不到封閉框架時為空清單）。 */
    public static List<BlockPos> fillFrame(ServerLevel level, BlockPos centre, int radius) {
        Frame frame = findFrame(level, centre, radius, Blocks.REINFORCED_DEEPSLATE);
        if (frame == null) {
            return List.of();
        }
        fillFrame(level, frame);
        return frame.interior();
    }

    /** near 附近（3 格內）有沒有傳送門方塊。 */
    public static boolean hasPortalNear(ServerLevel level, BlockPos near) {
        for (BlockPos p : BlockPos.betweenClosed(near.offset(-3, -3, -3), near.offset(3, 3, 3))) {
            if (level.getBlockState(p).is(ModBlocks.SIFT_PORTAL)) {
                return true;
            }
        }
        return false;
    }

    /** 清掉 near 附近（3 格內）那一片相連的傳送門方塊（關門）。回傳清掉幾格。 */
    public static int clearPortal(ServerLevel level, BlockPos near) {
        BlockPos seed = null;
        for (BlockPos p : BlockPos.betweenClosed(near.offset(-3, -3, -3), near.offset(3, 3, 3))) {
            if (level.getBlockState(p).is(ModBlocks.SIFT_PORTAL)) {
                seed = p.immutable();
                break;
            }
        }
        if (seed == null) {
            return 0;
        }
        Set<BlockPos> seen = new HashSet<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        queue.add(seed);
        seen.add(seed);
        while (!queue.isEmpty() && seen.size() < 600) {
            BlockPos p = queue.poll();
            for (Direction d : Direction.values()) {
                BlockPos n = p.relative(d);
                if (level.getBlockState(n).is(ModBlocks.SIFT_PORTAL) && seen.add(n)) {
                    queue.add(n);
                }
            }
        }
        for (BlockPos p : seen) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
        }
        return seen.size();
    }

    /** 平面 BFS：可走空氣、幽匿脈絡（sculk_vein）與地毯等可替換方塊，碰到實心方塊即為邊界；必須至少有一面碰到框架方塊，超過上限視為不封閉（回傳 null）。 */
    private static List<BlockPos> flood(ServerLevel level, BlockPos start, Direction.Axis axis, Block frameBlock) {
        Direction along = axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
        Direction[] dirs = {Direction.UP, Direction.DOWN, along, along.getOpposite()};
        List<BlockPos> out = new ArrayList<>();
        Set<BlockPos> seen = new HashSet<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        queue.add(start);
        seen.add(start);
        boolean touchesFrame = false;
        while (!queue.isEmpty()) {
            BlockPos p = queue.poll();
            out.add(p);
            if (out.size() > MAX_FILL) {
                return null;
            }
            for (Direction d : dirs) {
                BlockPos n = p.relative(d);
                BlockState s = level.getBlockState(n);
                if (canPortalReplace(s)) {
                    if (seen.add(n)) {
                        queue.add(n);
                    }
                } else if (s.is(frameBlock)) {
                    touchesFrame = true;
                }
            }
        }
        return touchesFrame ? out : null;
    }
}
