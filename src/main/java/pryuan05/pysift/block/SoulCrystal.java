package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.core.Registry;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.block.state.BlockState;
import pryuan05.pysift.fluid.SpiritInteractions;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import pryuan05.pysift.PySift;
import pryuan05.pysift.item.ModItems;

import java.util.Map;

/**
 * 靈魂晶塊：迴音傀儡頭頂慢慢凝結的晶瑩剔透的水晶（外觀同傀儡模型頭頂那顆方塊）。
 * 傀儡會把它送給歌者，玩家也能右鍵傀儡取下；泥板厚甲怪用它繁殖。資源由 tools/worldgen/build_soul_crystal.py 產生。
 * 靈液碰到水也會凝成靈魂晶塊（SpiritInteractions）。放在世界裡的晶塊挖得掉但不掉落（掉落表是空的），
 * 消失時（挖掉、炸掉、被取代）會放出一群自訂的靈魂粒子 soul_wisp。
 * 模型是「半透明外殼＋內縮 2 格的晶核」；相鄰的晶塊互相連通（六個方向的布林屬性），連通的那一側外殼的邊框不畫、
 * 晶核延伸到方塊邊緣接上隔壁的晶核，所以一整片晶塊看起來是一塊大水晶（模型由 tools/worldgen/paint_soul_crystal.py 產生）。
 */
public final class SoulCrystal {
    public static final Block SOUL_CRYSTAL_BLOCK;
    public static final Item SOUL_CRYSTAL_BLOCK_ITEM;

    static {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id("soul_crystal_block"));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id("soul_crystal_block"));
        SOUL_CRYSTAL_BLOCK = Registry.register(BuiltInRegistries.BLOCK, blockKey, new SoulCrystalBlock(
                BlockBehaviour.Properties.ofFullCopy(Blocks.GLASS).sound(SoundType.AMETHYST).strength(1.5f)
                        .lightLevel(state -> 10).setId(blockKey)));
        SOUL_CRYSTAL_BLOCK_ITEM = Registry.register(BuiltInRegistries.ITEM, itemKey,
                new BlockItem(SOUL_CRYSTAL_BLOCK, new Item.Properties().setId(itemKey)));
    }

    private SoulCrystal() {
    }

    /** 方塊消失時，晶塊裡的靈魂飄出來；和相鄰的靈魂晶塊連通。 */
    public static class SoulCrystalBlock extends TransparentBlock {
        public static final BooleanProperty UP = BooleanProperty.create("up");
        public static final BooleanProperty DOWN = BooleanProperty.create("down");
        public static final BooleanProperty NORTH = BooleanProperty.create("north");
        public static final BooleanProperty EAST = BooleanProperty.create("east");
        public static final BooleanProperty SOUTH = BooleanProperty.create("south");
        public static final BooleanProperty WEST = BooleanProperty.create("west");
        /** 某個方向的鄰格也是靈魂晶塊時為 true。 */
        public static final Map<Direction, BooleanProperty> CONNECTED = Map.of(Direction.UP, UP, Direction.DOWN, DOWN,
                Direction.NORTH, NORTH, Direction.EAST, EAST, Direction.SOUTH, SOUTH, Direction.WEST, WEST);

        public SoulCrystalBlock(BlockBehaviour.Properties properties) {
            super(properties);
            BlockState state = stateDefinition.any();
            for (BooleanProperty prop : CONNECTED.values()) {
                state = state.setValue(prop, false);
            }
            registerDefaultState(state);
        }

        @Override
        protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
            builder.add(UP, DOWN, NORTH, EAST, SOUTH, WEST);
        }

        private BlockState connect(BlockState state, BlockGetter level, BlockPos pos) {
            for (Map.Entry<Direction, BooleanProperty> e : CONNECTED.entrySet()) {
                state = state.setValue(e.getValue(), level.getBlockState(pos.relative(e.getKey())).is(this));
            }
            return state;
        }

        @Override
        public BlockState getStateForPlacement(BlockPlaceContext context) {
            return connect(defaultBlockState(), context.getLevel(), context.getClickedPos());
        }

        @Override
        protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos,
                                         Direction direction, BlockPos neighborPos, BlockState neighborState, RandomSource random) {
            return state.setValue(CONNECTED.get(direction), neighborState.is(this));
        }

        /** 用程式直接放下的晶塊（儀式、靈液凝結、世界生成）也要接上已經在旁邊的晶塊。 */
        @Override
        protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
            super.onPlace(state, level, pos, oldState, movedByPiston);
            BlockState connected = connect(state, level, pos);
            if (connected != state) {
                level.setBlock(pos, connected, Block.UPDATE_CLIENTS);
            }
        }

        @Override
        protected void affectNeighborsAfterRemoval(BlockState state, ServerLevel level, BlockPos pos, boolean movedByPiston) {
            super.affectNeighborsAfterRemoval(state, level, pos, movedByPiston);
            if (!movedByPiston) {
                SpiritInteractions.releaseSouls(level, pos, 8);
                level.playSound(null, pos, SoundEvents.SOUL_ESCAPE.value(), SoundSource.BLOCKS, 1.2f, 1.0f);
            }
        }
    }

    public static void register() {
        pryuan05.pysift.item.SiftCreativeTabs.source(ModItems.BLOCKS_TAB_KEY, output -> output.accept(SOUL_CRYSTAL_BLOCK_ITEM));
        PySift.LOGGER.info("Registered soul crystal block");
    }
}
