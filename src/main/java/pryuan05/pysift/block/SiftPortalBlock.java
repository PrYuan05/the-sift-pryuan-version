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
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.portal.TeleportTransition;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import pryuan05.pysift.block.entity.SiftPortalBlockEntity;

/**
 * 篩靈界傳送門（pysift:sift_portal）：無碰撞、不可破壞、最高亮度，軸向沿 X 或 Z。
 * <ul>
 *   <li>外觀由 SiftPortalBlockEntityRenderer 繪製（跨方塊大畫布珠光流光、內側破曉光帶、向外溢出的聖光束），
 *       方塊模型本身不渲染（RenderShape.INVISIBLE），只提供破壞粒子與物品圖示。</li>
 *   <li>玩家站在門裡 2 秒後傳送（期間用戶端播放 SiftPortalTransition 過場動畫），其他實體立即傳送；原版 Portal 機制處理冷卻與跨維度：主世界 ⇄ pysift:the_sift。落點取目標維度同 (X, Z) 的地表；
 *       沒有安全地面時在 Y = 80 鋪 5×5 dark_slate 平台。落點 16 格內沒有傳送門時，在平台旁自動蓋一座返回門。</li>
 * </ul>
 * 也提供儀式用的工具：{@link #fillFrame} 以 BFS 填滿強化深板岩框架內部，{@link #buildFrame} 蓋一座小框架。
 */
public class SiftPortalBlock extends Block implements EntityBlock, Portal {
    public static final EnumProperty<Direction.Axis> AXIS = BlockStateProperties.HORIZONTAL_AXIS;
    public static final ResourceKey<Level> SIFT_DIM = ResourceKey.create(Registries.DIMENSION, Identifier.fromNamespaceAndPath("pysift", "the_sift"));
    private static final VoxelShape X_SHAPE = Block.box(0, 0, 6, 16, 16, 10);
    private static final VoxelShape Z_SHAPE = Block.box(6, 0, 0, 10, 16, 16);
    private static final int MAX_FILL = 180;
    /** 玩家要在門裡站多久才傳送（tick）；用戶端的過場動畫 SiftPortalTransition 用同一個長度。 */
    public static final int PLAYER_TRANSITION_TICKS = 40;

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
        // 面向北／南時門板沿 X 軸展開
        return this.defaultBlockState().setValue(AXIS, facing == Direction.Axis.Z ? Direction.Axis.X : Direction.Axis.Z);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return state.getValue(AXIS) == Direction.Axis.Z ? Z_SHAPE : X_SHAPE;
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
        BlockPos landing = findLanding(target, pos.getX(), pos.getZ());
        ensureReturnPortal(target, landing);
        Vec3 at = Vec3.atBottomCenterOf(landing);
        return new TeleportTransition(target, at, Vec3.ZERO, entity.getYRot(), entity.getXRot(), TeleportTransition.PLAY_PORTAL_SOUND);
    }

    /** 目標維度 (x, z) 的安全落點（腳下）；沒有固體地面（虛空、液體、超出高度）時在 Y = 80 鋪 5×5 dark_slate 平台。 */
    private static BlockPos findLanding(ServerLevel level, int x, int z) {
        level.getChunk(x >> 4, z >> 4);
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
        BlockPos feet = new BlockPos(x, y, z);
        BlockState ground = level.getBlockState(feet.below());
        boolean safe = y > level.getMinY() + 1 && y < level.getMaxY() - 3 && ground.isSolid() && level.getFluidState(feet.below()).isEmpty()
                && level.getBlockState(feet).isAir() && level.getBlockState(feet.above()).isAir();
        if (safe) {
            return feet;
        }
        BlockPos platform = new BlockPos(x, 80, z);
        BlockState slate = ModBlocks.BY_NAME.getOrDefault("dark_slate", Blocks.DEEPSLATE).defaultBlockState();
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                level.setBlockAndUpdate(platform.offset(dx, -1, dz), slate);
                for (int dy = 0; dy < 3; dy++) {
                    level.setBlockAndUpdate(platform.offset(dx, dy, dz), Blocks.AIR.defaultBlockState());
                }
            }
        }
        return platform;
    }

    /** 落點 16 格內沒有傳送門時，在落點東側 3 格蓋一座外框 3×4 的返回門（強化深板岩外框，內部 1×2 傳送門）。 */
    private static void ensureReturnPortal(ServerLevel level, BlockPos landing) {
        Block portal = ModBlocks.SIFT_PORTAL;
        for (BlockPos p : BlockPos.betweenClosed(landing.offset(-16, -8, -16), landing.offset(16, 8, 16))) {
            if (level.getBlockState(p).is(portal)) {
                return;
            }
        }
        BlockPos base = landing.offset(3, -1, -1);   // 外框左下角，與平台同一層
        buildFrame(level, base, Direction.Axis.Z, 3, 4);
    }

    // ------------------------------------------------------------------ frame helpers (also used by the Singer ritual)
    /**
     * 蓋一座外框 outerW × outerH 的強化深板岩框架（base 為外框左下角，沿 axis 展開），內部填滿對應軸向的傳送門，
     * 並清空框架前後一格的空間。
     */
    public static void buildFrame(ServerLevel level, BlockPos base, Direction.Axis axis, int outerW, int outerH) {
        Direction along = axis == Direction.Axis.X ? Direction.EAST : Direction.SOUTH;
        Direction across = axis == Direction.Axis.X ? Direction.SOUTH : Direction.EAST;
        BlockState frame = Blocks.REINFORCED_DEEPSLATE.defaultBlockState();
        BlockState portal = ModBlocks.SIFT_PORTAL.defaultBlockState().setValue(AXIS, axis);
        for (int w = 0; w < outerW; w++) {
            for (int h = 0; h < outerH; h++) {
                BlockPos p = base.relative(along, w).above(h);
                boolean edge = w == 0 || h == 0 || w == outerW - 1 || h == outerH - 1;
                if (!edge) {
                    level.setBlockAndUpdate(p.relative(across), Blocks.AIR.defaultBlockState());
                    level.setBlockAndUpdate(p.relative(across.getOpposite()), Blocks.AIR.defaultBlockState());
                }
                level.setBlock(p, edge ? frame : portal, Block.UPDATE_CLIENTS);
            }
        }
    }

    /**
     * 在 centre 周圍 radius 格內找強化深板岩框架，沿框架所在的垂直平面（X-Y 或 Z-Y）從內側空氣做 BFS，
     * 以強化深板岩（或其他非空氣方塊）為邊界；區域封閉且不超過 180 格時整片換成傳送門。
     * 回傳填入的方塊（找不到封閉框架時為空清單）。
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
                    if (!level.getBlockState(start).isAir() || !tried.add(start)) {
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

    /** 平面 BFS：只走空氣，碰到其他方塊即為邊界；必須至少有一面碰到強化深板岩，超過上限視為不封閉（回傳 null）。 */
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
                if (s.isAir()) {
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
