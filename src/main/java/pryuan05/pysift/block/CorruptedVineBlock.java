package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

import java.util.EnumMap;
import java.util.Map;

/**
 * 腐化藤蔓（Corrupted Vine）：
 * <ul>
 *   <li>像原版發光地衣／幽匿脈絡一樣，六個方向（{@code up, down, north, east, south, west}）皆可貼附在實心方塊表面上（例如 {@code dark_slate_pillar}）。</li>
 *   <li>具有 {@code corruption = 0..3} 四個腐化蔓延階段：在已貼附的藤蔓方塊上再次手持 {@code corrupted_vine} 右鍵，
 *       若點擊的面尚未貼附，則優先在該面新增藤蔓；若該面已經有藤蔓，則將整格的 {@code corruption} 從 {@code 0 -> 1 -> 2 -> 3} 升級（最多 4 層）。</li>
 *   <li>支撐方塊被破壞時，對應方向的藤蔓面會自動脫落；當六個面全部脫落時，方塊破壞並掉落對應階段數量的物品。</li>
 * </ul>
 */
public class CorruptedVineBlock extends Block {
    public static final IntegerProperty CORRUPTION = IntegerProperty.create("corruption", 0, 3);
    public static final BooleanProperty UP = BooleanProperty.create("up");
    public static final BooleanProperty DOWN = BooleanProperty.create("down");
    public static final BooleanProperty NORTH = BooleanProperty.create("north");
    public static final BooleanProperty EAST = BooleanProperty.create("east");
    public static final BooleanProperty SOUTH = BooleanProperty.create("south");
    public static final BooleanProperty WEST = BooleanProperty.create("west");

    /** 貼附在哪個方向的鄰格表面上（例如 NORTH 代表貼在北側 pos.north() 方塊的南面上）。 */
    public static final Map<Direction, BooleanProperty> FACES = Map.of(
            Direction.UP, UP,
            Direction.DOWN, DOWN,
            Direction.NORTH, NORTH,
            Direction.EAST, EAST,
            Direction.SOUTH, SOUTH,
            Direction.WEST, WEST
    );

    private static final Map<Direction, VoxelShape> FACE_SHAPES = new EnumMap<>(Map.of(
            Direction.UP, Block.box(0.0, 15.0, 0.0, 16.0, 16.0, 16.0),
            Direction.DOWN, Block.box(0.0, 0.0, 0.0, 16.0, 1.0, 16.0),
            Direction.NORTH, Block.box(0.0, 0.0, 0.0, 16.0, 16.0, 1.0),
            Direction.SOUTH, Block.box(0.0, 0.0, 15.0, 16.0, 16.0, 16.0),
            Direction.WEST, Block.box(0.0, 0.0, 0.0, 1.0, 16.0, 16.0),
            Direction.EAST, Block.box(15.0, 0.0, 0.0, 16.0, 16.0, 16.0)
    ));

    public CorruptedVineBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any()
                .setValue(CORRUPTION, 0)
                .setValue(UP, false)
                .setValue(DOWN, false)
                .setValue(NORTH, true)
                .setValue(EAST, false)
                .setValue(SOUTH, false)
                .setValue(WEST, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(CORRUPTION, UP, DOWN, NORTH, EAST, SOUTH, WEST);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        VoxelShape shape = Shapes.empty();
        for (Map.Entry<Direction, BooleanProperty> e : FACES.entrySet()) {
            if (state.getValue(e.getValue())) {
                shape = Shapes.or(shape, FACE_SHAPES.get(e.getKey()));
            }
        }
        return shape.isEmpty() ? Shapes.block() : shape;
    }

    @Override
    protected boolean propagatesSkylightDown(BlockState state) {
        return true;
    }

    public static boolean canAttachTo(BlockGetter level, BlockPos pos, Direction attachDir) {
        BlockPos supportPos = pos.relative(attachDir);
        return level.getBlockState(supportPos).isFaceSturdy(level, supportPos, attachDir.getOpposite());
    }

    public static boolean hasAnyFace(BlockState state) {
        for (BooleanProperty prop : FACES.values()) {
            if (state.getValue(prop)) {
                return true;
            }
        }
        return false;
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        boolean any = false;
        for (Map.Entry<Direction, BooleanProperty> e : FACES.entrySet()) {
            if (state.getValue(e.getValue()) && canAttachTo(level, pos, e.getKey())) {
                any = true;
            }
        }
        return any;
    }

    /**
     * 手持 corrupted_vine 對著已存在的 corrupted_vine 右鍵時：
     * 若還可以升級（corruption < 3）或還可以貼上新的支撐面，則允許替換並升級。
     */
    @Override
    protected boolean canBeReplaced(BlockState state, BlockPlaceContext context) {
        if (!context.getItemInHand().is(this.asItem())) {
            return false;
        }
        if (state.getValue(CORRUPTION) < 3) {
            return true;
        }
        for (Direction dir : context.getNearestLookingDirections()) {
            BooleanProperty prop = FACES.get(dir);
            if (!state.getValue(prop) && canAttachTo(context.getLevel(), context.getClickedPos(), dir)) {
                return true;
            }
        }
        return false;
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        LevelReader level = context.getLevel();
        BlockPos pos = context.getClickedPos();
        BlockState existing = level.getBlockState(pos);
        boolean isExisting = existing.is(this);

        if (isExisting) {
            // 1) 若玩家點擊的對向面（或視線方向）有新的實心面尚未貼附，可同時貼上該面；
            // 2) 若點擊的面已經貼附（或無法新增面），則將 corruption + 1（最高到 3）。
            Direction clickedAttach = context.getClickedFace().getOpposite();
            BooleanProperty clickedProp = FACES.get(clickedAttach);
            if (!existing.getValue(clickedProp) && canAttachTo(level, pos, clickedAttach)) {
                return existing.setValue(clickedProp, true);
            }
            if (existing.getValue(CORRUPTION) < 3) {
                return existing.setValue(CORRUPTION, existing.getValue(CORRUPTION) + 1);
            }
            for (Direction dir : context.getNearestLookingDirections()) {
                BooleanProperty prop = FACES.get(dir);
                if (!existing.getValue(prop) && canAttachTo(level, pos, dir)) {
                    return existing.setValue(prop, true);
                }
            }
            return null;
        }

        // 全新放置：所有面預設為 false，只打開貼著點擊面的那一側（或第一個可貼附的方向）
        BlockState blank = defaultBlockState().setValue(NORTH, false);
        Direction primary = context.getClickedFace().getOpposite();
        if (canAttachTo(level, pos, primary)) {
            return blank.setValue(FACES.get(primary), true);
        }
        for (Direction dir : context.getNearestLookingDirections()) {
            if (canAttachTo(level, pos, dir)) {
                return blank.setValue(FACES.get(dir), true);
            }
        }
        return null;
    }

    @Override
    protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos,
                                     Direction direction, BlockPos neighborPos, BlockState neighborState, RandomSource random) {
        BooleanProperty prop = FACES.get(direction);
        if (state.getValue(prop) && !canAttachTo(level, pos, direction)) {
            BlockState updated = state.setValue(prop, false);
            if (!hasAnyFace(updated)) {
                ticks.scheduleTick(pos, this, 1);
                return Blocks.AIR.defaultBlockState();
            }
            return updated;
        }
        return state;
    }

    @Override
    protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (!canSurvive(state, level, pos)) {
            level.destroyBlock(pos, true);
        }
    }

    @Override
    protected BlockState rotate(BlockState state, Rotation rotation) {
        BlockState out = state;
        for (Direction dir : Direction.Plane.HORIZONTAL) {
            out = out.setValue(FACES.get(rotation.rotate(dir)), state.getValue(FACES.get(dir)));
        }
        return out;
    }

    @Override
    protected BlockState mirror(BlockState state, Mirror mirror) {
        return this.rotate(state, mirror.getRotation(Direction.NORTH));
    }
}
