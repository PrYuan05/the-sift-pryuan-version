package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import pryuan05.pysift.PySift;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 垂吊藤（v2.1.0 地底裝飾）：從洞穴天花板垂下來的藤蔓，用使用者重畫過的三種貼牆藤（綠隙浮藤、橙隙浮藤、甲殼藤）的樣子。
 * 像原版垂泣藤一樣畫在十字交叉的平面上；一串藤的最下面一格是尖端（tip=true，另一張貼圖），上面的都是藤身。
 * 只要上面是同一種藤，或是一個朝下的完整面就能掛著；上面的被打掉，下面整串跟著掉。可以攀爬（#minecraft:climbable），
 * 不會長。資源由 tools/worldgen/build_hanging_vines.py 產生，生成在 build_the_sift.py（原版的 block_column 特徵）。
 */
public final class HangingVines {
    /** 垂吊藤 id → 它照著畫的貼牆藤 id。 */
    public static final Map<String, String> VINES = new LinkedHashMap<>();
    public static final Map<String, Block> BLOCKS = new LinkedHashMap<>();

    static {
        VINES.put("hanging_green_sift_vine", "green_sift_vine");
        VINES.put("hanging_orange_sift_vine", "orange_sift_vine");
        VINES.put("hanging_carapace_vine", "carapace_vine");
    }

    private HangingVines() {
    }

    public static class HangingVineBlock extends Block {
        public static final BooleanProperty TIP = BlockStateProperties.BOTTOM;   // "bottom": the lowest block of the strand
        private static final VoxelShape BODY = Block.box(4.0, 0.0, 4.0, 12.0, 16.0, 12.0);
        private static final VoxelShape TIP_SHAPE = Block.box(4.0, 6.0, 4.0, 12.0, 16.0, 12.0);

        public HangingVineBlock(BlockBehaviour.Properties properties) {
            super(properties);
            registerDefaultState(stateDefinition.any().setValue(TIP, true));
        }

        @Override
        protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
            builder.add(TIP);
        }

        @Override
        protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
            return state.getValue(TIP) ? TIP_SHAPE : BODY;
        }

        @Override
        protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
            BlockPos above = pos.above();
            BlockState up = level.getBlockState(above);
            return up.is(this) || up.isFaceSturdy(level, above, Direction.DOWN);
        }

        @Override
        public BlockState getStateForPlacement(BlockPlaceContext context) {
            BlockState below = context.getLevel().getBlockState(context.getClickedPos().below());
            return defaultBlockState().setValue(TIP, !below.is(this));
        }

        @Override
        protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos, Direction direction,
                                         BlockPos neighborPos, BlockState neighbor, RandomSource random) {
            if (direction == Direction.UP && !canSurvive(state, level, pos)) {
                return Blocks.AIR.defaultBlockState();               // the strand above was cut: this part falls too
            }
            if (direction == Direction.DOWN) {
                return state.setValue(TIP, !neighbor.is(this));
            }
            return state;
        }
    }

    public static void register() {
        for (String id : VINES.keySet()) {
            ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(id));
            ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(id));
            Block block = new HangingVineBlock(BlockBehaviour.Properties.ofFullCopy(Blocks.WEEPING_VINES_PLANT).setId(blockKey));
            Registry.register(BuiltInRegistries.BLOCK, blockKey, block);
            Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().setId(itemKey)));
            ModBlocks.ALL_BLOCKS.add(block);
            BLOCKS.put(id, block);
        }
        PySift.LOGGER.debug("Registered {} hanging vines", BLOCKS.size());
    }
}
