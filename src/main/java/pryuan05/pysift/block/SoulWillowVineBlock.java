package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import pryuan05.pysift.PySift;

import java.util.Map;

/**
 * 靈魂柳的垂藤：一格垂藤，每個水平面（north / east / south / west）各自決定有沒有藤蔓貼圖，
 * 像原版藤蔓貼在叢林木上那樣，可以整串從樹冠邊緣垂下。
 * <ul>
 *   <li>四個面：世界生成時，朝向樹冠外側（葉子那一側沒有葉子）的面一定有；其他面隨機，
 *       而且上一段有的面下一段也一定有，所以整串由上往下只會變茂密、不會斷開（見 SoulWillowVineDecorator）。</li>
 *   <li>tip：較細碎的末端貼圖。最下面一段一定是 tip；世界生成時下半段也會隨機出現 tip。
 *       下方的垂藤被移除時自己變成 tip；下方接上垂藤時保持原樣（所以隨機的 tip 不會被洗掉）。</li>
 *   <li>shade：顏色漸層 0 = 上段（原圖）、1 = 下段淡藍、2 = 末端白／淡紫；每個 shade 各有一張貼圖，方塊本身不染色。</li>
 *   <li>存活條件：上方是 {@link #SUPPORTS} 標籤的靈魂柳葉，或另一段靈魂柳垂藤（含發光版）；
 *       上方被破壞時排程一個 tick 把自己破壞，於是整串由上往下消失。</li>
 *   <li>無碰撞、不遮擋、可被替換（properties 由 ModVegetation 從原版 vine 複製並加上 noOcclusion）。</li>
 * </ul>
 * 掉落只在剪刀／絲綢之觸時發生（loot table 由 tools/worldgen/build_vegetation.py 產生）。
 */
public class SoulWillowVineBlock extends Block {
    public static final BooleanProperty TIP = BooleanProperty.create("tip");
    public static final IntegerProperty SHADE = IntegerProperty.create("shade", 0, 2);
    public static final BooleanProperty NORTH = BooleanProperty.create("north");
    public static final BooleanProperty EAST = BooleanProperty.create("east");
    public static final BooleanProperty SOUTH = BooleanProperty.create("south");
    public static final BooleanProperty WEST = BooleanProperty.create("west");
    /** 水平方向 → 該面的屬性。 */
    public static final Map<Direction, BooleanProperty> SIDES = Map.of(
            Direction.NORTH, NORTH, Direction.EAST, EAST, Direction.SOUTH, SOUTH, Direction.WEST, WEST);
    /** 垂藤可以掛在哪些方塊下面（靈魂柳的三種樹葉）。 */
    public static final TagKey<Block> SUPPORTS = TagKey.create(Registries.BLOCK, PySift.id("soul_willow_vine_supports"));

    private static final VoxelShape SHAPE = Block.column(14.0, 0.0, 16.0);

    public SoulWillowVineBlock(Properties properties) {
        super(properties);
        // 預設四面都有：舊存檔裡沒有面屬性的垂藤載入後外觀不變
        registerDefaultState(stateDefinition.any().setValue(TIP, true).setValue(SHADE, 0)
                .setValue(NORTH, true).setValue(EAST, true).setValue(SOUTH, true).setValue(WEST, true));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(TIP, SHADE, NORTH, EAST, SOUTH, WEST);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE;
    }

    @Override
    protected boolean propagatesSkylightDown(BlockState state) {
        return true;
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        BlockState above = level.getBlockState(pos.above());
        return above.is(SUPPORTS) || above.getBlock() instanceof SoulWillowVineBlock;
    }

    /**
     * 玩家手動放置：接在上一段垂藤下面時延續它的漸層（往下越淡）和它有的面；
     * 直接掛在葉子下時，只在那片葉子朝外（旁邊不是靈魂柳葉）的面長藤，四周都是葉子時四面都長。
     */
    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        LevelReader level = context.getLevel();
        BlockPos pos = context.getClickedPos();
        BlockState above = level.getBlockState(pos.above());
        boolean tip = !(level.getBlockState(pos.below()).getBlock() instanceof SoulWillowVineBlock);
        BlockState state = defaultBlockState().setValue(TIP, tip);
        if (above.getBlock() instanceof SoulWillowVineBlock) {
            state = state.setValue(SHADE, Math.min(2, above.getValue(SHADE) + 1));
            for (BooleanProperty side : SIDES.values()) {
                state = state.setValue(side, above.getValue(side));
            }
            return state;
        }
        boolean any = false;
        for (Map.Entry<Direction, BooleanProperty> e : SIDES.entrySet()) {
            boolean outward = !level.getBlockState(pos.above().relative(e.getKey())).is(SUPPORTS);
            state = state.setValue(e.getValue(), outward);
            any |= outward;
        }
        return any ? state : withAllSides(state);
    }

    /** 四個面全部打開。 */
    public static BlockState withAllSides(BlockState state) {
        for (BooleanProperty side : SIDES.values()) {
            state = state.setValue(side, true);
        }
        return state;
    }

    @Override
    protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos,
                                     Direction direction, BlockPos neighborPos, BlockState neighborState, RandomSource random) {
        if (direction == Direction.UP && !canSurvive(state, level, pos)) {
            ticks.scheduleTick(pos, this, 1);
        }
        if (direction == Direction.DOWN && !(neighborState.getBlock() instanceof SoulWillowVineBlock)) {
            return state.setValue(TIP, true);   // 成為新的末端；下方接上垂藤時保留原本的 tip（世界生成的隨機 tip）
        }
        return state;
    }

    @Override
    protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (!canSurvive(state, level, pos)) {
            level.destroyBlock(pos, true);
        }
    }
}
