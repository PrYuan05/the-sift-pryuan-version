package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.Property;

import java.util.List;

/**
 * 帶有表格定義狀態屬性的方塊。
 * <p>
 * createBlockStateDefinition 在父類別建構子內被呼叫，此時子類別欄位尚未初始化，
 * 所以屬性清單透過 {@link #PENDING} 在建構期間傳入；請一律使用 {@link #create} 建立。
 */
public class SiftStateBlock extends Block {
    static final ThreadLocal<List<Property<?>>> PENDING = ThreadLocal.withInitial(List::of);

    /** 方塊外形：一般立方體、具 axis 的柱狀、或具 facing 的六向可旋轉方塊（頂面朝向 facing）。 */
    public enum Shape {
        CUBE, PILLAR, FACING
    }

    private SiftStateBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        PENDING.get().forEach(builder::add);
    }

    /** 依外形與狀態屬性建立對應的方塊實例。預設狀態為各屬性的第一個值（柱狀 axis=y、六向 facing=up）。 */
    public static Block create(BlockBehaviour.Properties properties, Shape shape, List<Property<?>> stateProperties) {
        PENDING.set(stateProperties);
        try {
            return switch (shape) {
                case CUBE -> stateProperties.isEmpty() ? new Block(properties) : new SiftStateBlock(properties);
                case PILLAR -> stateProperties.isEmpty() ? new RotatedPillarBlock(properties) : new Pillar(properties);
                case FACING -> new Facing(properties);
            };
        } finally {
            PENDING.remove();
        }
    }

    /** 同時具有 axis 與其他狀態屬性的柱狀方塊（例如 peeling_log）。 */
    public static class Pillar extends RotatedPillarBlock {
        private Pillar(BlockBehaviour.Properties properties) {
            super(properties);
        }

        @Override
        protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
            super.createBlockStateDefinition(builder);
            PENDING.get().forEach(builder::add);
        }
    }

    /**
     * 六向可旋轉的複合面方塊（草方塊型）：模型的頂面朝向 facing，放置時朝向被點擊的面，
     * 所以貼在天花板上會變成頂面朝下。
     */
    public static class Facing extends Block {
        public static final EnumProperty<Direction> FACING = BlockStateProperties.FACING;

        private Facing(BlockBehaviour.Properties properties) {
            super(properties);
            registerDefaultState(defaultBlockState().setValue(FACING, Direction.UP));
        }

        @Override
        protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
            super.createBlockStateDefinition(builder);
            builder.add(FACING);
            PENDING.get().forEach(builder::add);
        }

        @Override
        public BlockState getStateForPlacement(BlockPlaceContext context) {
            // 地面方塊：不管點哪一面放置，覆蓋層一律朝上（使用者：頂面不可以跟著放置方向轉）。
            // FACING 屬性保留，指令或結構仍可指定其他方向。
            return defaultBlockState().setValue(FACING, Direction.UP);
        }

        @Override
        protected BlockState rotate(BlockState state, Rotation rotation) {
            return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
        }

        @Override
        protected BlockState mirror(BlockState state, Mirror mirror) {
            return state.rotate(mirror.getRotation(state.getValue(FACING)));
        }

        /** 自然生成的地表（{@link SurfaceDecay}）且頂面朝上時，被蓋住會退化成下方方塊。 */
        private Boolean surface;

        private boolean isSurface() {
            if (surface == null) {
                surface = SurfaceDecay.isSurface(this);
            }
            return surface;
        }

        @Override
        protected boolean isRandomlyTicking(BlockState state) {
            return state.getValue(FACING) == Direction.UP && isSurface();
        }

        @Override
        protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
            SurfaceDecay.randomTick(state, level, pos);
        }
    }

    /** 沒有狀態屬性的地表立方體（例如搖籃曲山丘的 void_capped_crimson_01）：被蓋住會退化成下方方塊（{@link SurfaceDecay}）。 */
    public static class SurfaceCube extends Block {
        public SurfaceCube(BlockBehaviour.Properties properties) {
            super(properties);
        }

        @Override
        protected boolean isRandomlyTicking(BlockState state) {
            return true;
        }

        @Override
        protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
            SurfaceDecay.randomTick(state, level, pos);
        }
    }
}
