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
        boolean x = state.getValue(AXIS) == Direction.Axis.X;
        for (int i = 0; i < 2; i++) {
            double px = pos.getX() + (x ? random.nextDouble() : 0.5 + (random.nextDouble() - 0.5) * 0.6);
            double py = pos.getY() + random.nextDouble();
            double pz = pos.getZ() + (x ? 0.5 + (random.nextDouble() - 0.5) * 0.6 : random.nextDouble());
            level.addParticle(random.nextInt(3) == 0 ? ParticleTypes.END_ROD : ParticleTypes.PORTAL,
                    px, py, pz, (random.nextDouble() - 0.5) * 0.04, 0.02, (random.nextDouble() - 0.5) * 0.04);
        }
        if (random.nextInt(160) == 0) {
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
        BlockPos existingLanding = findExistingPortalLanding(target, pos.getX(), pos.getZ());
        BlockPos landing;
        if (existingLanding != null) {
            landing = existingLanding;
        } else {
            landing = findLanding(target, pos.getX(), pos.getZ());
            ensureReturnPortal(target, landing);
        }
        Vec3 at = Vec3.atBottomCenterOf(landing);
        return new TeleportTransition(target, at, Vec3.ZERO, entity.getYRot(), entity.getXRot(), TeleportTransition.PLAY_PORTAL_SOUND);
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
        for (int dist = 2; dist <= 5; dist++) {
            for (Direction side : new Direction[]{across, across.getOpposite()}) {
                for (int dy = -2; dy <= 2; dy++) {
                    BlockPos candidate = nearestPortal.relative(side, dist).above(dy);
                    if (isSafeStandSpot(level, candidate)) {
                        return candidate;
                    }
                }
            }
        }
        return nearestPortal;
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
        buildRiftPortal(level, bestCentre, bestAxis);
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
    public static void buildRiftPortal(ServerLevel level, BlockPos baseCentre, Direction.Axis axis) {
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

    /**
     * 在 centre 周圍 radius 格內找強化深板岩框架，沿框架所在的垂直平面（X-Y 或 Z-Y）從內側做 BFS，
     * 可穿越並取代空氣、遠古城市巨口內的幽匿脈絡（sculk_vein）與地毯方塊，以強化深板岩（或其他實心方塊）為邊界；
     * 區域封閉且不超過 180 格時整片換成傳送門。回傳填入的方塊（找不到封閉框架時為空清單）。
     */
    public static List<BlockPos> fillFrame(ServerLevel level, BlockPos centre, int radius) {
        Set<BlockPos> triedX = new HashSet<>();
        Set<BlockPos> triedZ = new HashSet<>();
        for (BlockPos frame : BlockPos.betweenClosed(centre.offset(-radius, -radius, -radius), centre.offset(radius, radius, radius))) {
            if (!level.getBlockState(frame).is(Blocks.REINFORCED_DEEPSLATE)) {
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
                    List<BlockPos> region = flood(level, start, axis);
                    if (region != null) {
                        BlockState portal = ModBlocks.SIFT_PORTAL.defaultBlockState().setValue(AXIS, axis);
                        for (BlockPos p : region) {
                            level.setBlock(p, portal, Block.UPDATE_CLIENTS);
                        }
                        return region;
                    }
                }
            }
        }
        return List.of();
    }

    /** 平面 BFS：可走空氣、幽匿脈絡（sculk_vein）與地毯等可替換方塊，碰到實心方塊即為邊界；必須至少有一面碰到強化深板岩，超過上限視為不封閉（回傳 null）。 */
    private static List<BlockPos> flood(ServerLevel level, BlockPos start, Direction.Axis axis) {
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
                } else if (s.is(Blocks.REINFORCED_DEEPSLATE)) {
                    touchesFrame = true;
                }
            }
        }
        return touchesFrame ? out : null;
    }
}
