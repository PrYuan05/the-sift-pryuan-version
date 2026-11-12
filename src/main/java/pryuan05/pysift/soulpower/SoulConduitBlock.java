package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.util.RandomSource;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.DiodeBlock;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.RedstoneWireBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.redstone.Orientation;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.AutoConnect;

import java.util.EnumMap;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/**
 * 靈魂導線：一段活的赤紅幽匿脈，把歌聲（靈魂訊號）傳到遠處；也是原版紅石線的進階版。六個方向都能接（可以垂直、懸空、貼牆），
 * 訊號每 2 格才少 1 級，而且能帶著引擎的靈壓去推動靈魂機器（{@link SoulCircuit}）。
 * <ul>
 *   <li>對外的紅石強度（0–15）存在方塊實體裡（{@link Entity}），所以方塊狀態只管外觀。對原版元件來說導線就是訊號源：
 *       紅石粉會接上來，紅石燈、活塞、中繼器、漏斗都吃得到。</li>
 *   <li>LOOK：soul = 有靈魂訊號（赤紅發光，活的幽匿脈）；plain = 只有原版訊號（深藍微亮，和主世界枯死的幽匿同色）；
 *       off = 沒有訊號（暗灰）。</li>
 *   <li>每一面的接頭（{@link Side}）：wire = 接另一個靈魂元件；plug = 插在原版元件上（紅石燈、活塞、漏斗、拉桿、催化體…，
 *       末端多一圈銅綠的接環）；low = 往下彎到地面，接紅石粉、鐵軌、地上的中繼器與比較器（只有水平四面）。</li>
 * </ul>
 * 原版元件（拉桿、中繼器、比較器、紅石火把、紅石塊…）貼著導線就能把訊號送進來；紅石粉不行（見 SoulCircuit）。
 * <p>
 * 包覆：拿任何完整方塊對導線右鍵，導線就包成那個方塊的外觀（存在方塊實體 Cover，外框變成完整方塊，
 * 由 client/soulpower/ConduitRenderer 畫出來）；空手右鍵拆下來。訊號照樣通過。
 */
public class SoulConduitBlock extends Block implements SoulConductor, AutoConnect.Connecting, EntityBlock {
    public enum Side implements StringRepresentable {
        NONE, WIRE, PLUG, LOW;

        @Override
        public String getSerializedName() {
            return name().toLowerCase(Locale.ROOT);
        }
    }

    public enum Look implements StringRepresentable {
        OFF, PLAIN, SOUL;

        @Override
        public String getSerializedName() {
            return name().toLowerCase(Locale.ROOT);
        }
    }

    public static final EnumProperty<Look> LOOK = EnumProperty.create("look", Look.class);
    public static final Map<Direction, EnumProperty<Side>> SIDES = new EnumMap<>(Direction.class);
    /** 導線會插上去的原版元件（吃紅石訊號的方塊，以及貼著導線有作用的幽匿方塊）。訊號源不用列，本來就會接。 */
    public static final TagKey<Block> PLUGS = TagKey.create(Registries.BLOCK, PySift.id("soul_conduit_plugs"));
    /** 貼在地面上的元件：導線往下彎去接。中繼器與比較器不用列（只接它的前後兩端）。 */
    public static final TagKey<Block> LOW = TagKey.create(Registries.BLOCK, PySift.id("soul_conduit_low"));
    private static final VoxelShape CORE = Block.box(5.5, 5.5, 5.5, 10.5, 10.5, 10.5);
    private static final Map<Direction, VoxelShape> ARM = new EnumMap<>(Direction.class);
    private static final Map<Direction, VoxelShape> PLUG = new EnumMap<>(Direction.class);
    private static final Map<Direction, VoxelShape> DROP = new EnumMap<>(Direction.class);

    static {
        for (Direction d : Direction.values()) {
            SIDES.put(d, d.getAxis().isVertical()
                    ? EnumProperty.create(d.getName(), Side.class, Side.NONE, Side.WIRE, Side.PLUG)
                    : EnumProperty.create(d.getName(), Side.class));
            ARM.put(d, box(d, 6, 6, 0, 10, 10, 6));
            PLUG.put(d, Shapes.or(box(d, 6, 6, 0, 10, 10, 6), box(d, 5, 5, 0, 11, 11, 1.5)));
            if (d.getAxis().isHorizontal()) {
                DROP.put(d, Shapes.or(box(d, 6, 6, 2, 10, 10, 6), box(d, 6, 1, 0, 10, 10, 2), box(d, 5, 0, 0, 11, 1, 2)));
            }
        }
    }

    private final Map<BlockState, VoxelShape> shapes = new HashMap<>();

    /** 以「朝北」寫的方塊（往 -z 伸出去），轉到 dir 那一面。 */
    private static VoxelShape box(Direction dir, double x1, double y1, double z1, double x2, double y2, double z2) {
        return switch (dir) {
            case NORTH -> Block.box(x1, y1, z1, x2, y2, z2);
            case SOUTH -> Block.box(16 - x2, y1, 16 - z2, 16 - x1, y2, 16 - z1);
            case WEST -> Block.box(z1, y1, 16 - x2, z2, y2, 16 - x1);
            case EAST -> Block.box(16 - z2, y1, x1, 16 - z1, y2, x2);
            case DOWN -> Block.box(x1, z1, 16 - y2, x2, z2, 16 - y1);
            case UP -> Block.box(x1, 16 - z2, y1, x2, 16 - z1, y2);
        };
    }

    public SoulConduitBlock(Properties properties) {
        super(properties);
        BlockState s = stateDefinition.any().setValue(LOOK, Look.OFF);
        for (EnumProperty<Side> p : SIDES.values()) {
            s = s.setValue(p, Side.NONE);
        }
        registerDefaultState(s);
        for (BlockState state : stateDefinition.getPossibleStates()) {
            VoxelShape shape = CORE;
            for (Direction d : Direction.values()) {
                shape = switch (state.getValue(SIDES.get(d))) {
                    case NONE -> shape;
                    case WIRE -> Shapes.or(shape, ARM.get(d));
                    case PLUG -> Shapes.or(shape, PLUG.get(d));
                    case LOW -> Shapes.or(shape, DROP.get(d));
                };
            }
            shapes.put(state.setValue(LOOK, Look.OFF), shape);
        }
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(LOOK);
        for (Direction d : Direction.values()) {
            builder.add(SIDES.get(d));
        }
    }

    /** 這一面要用哪一種接頭去接隔壁的方塊。 */
    private static Side side(BlockGetter level, BlockPos neighbor, Direction towards) {
        BlockState ns = level.getBlockState(neighbor);
        if (ns.getBlock() instanceof SoulConductor other) {
            return other.conducts(ns, towards.getOpposite()) ? Side.WIRE : Side.NONE;
        }
        boolean horizontal = towards.getAxis().isHorizontal();
        if (ns.getBlock() instanceof DiodeBlock) {      // 中繼器、比較器：只接它的輸入與輸出那兩端
            return horizontal && ns.getValue(DiodeBlock.FACING).getAxis() == towards.getAxis() ? Side.LOW : Side.NONE;
        }
        if (ns.getBlock() instanceof RedstoneWireBlock || ns.is(LOW) || ns.is(BlockTags.RAILS)) {
            return horizontal ? Side.LOW : Side.PLUG;
        }
        return ns.isSignalSource() || ns.is(PLUGS) ? Side.PLUG : Side.NONE;
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockState state = defaultBlockState();
        for (Direction d : Direction.values()) {
            state = state.setValue(SIDES.get(d), side(context.getLevel(), context.getClickedPos().relative(d), d));
        }
        return state;
    }

    @Override
    protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos, Direction dir,
                                     BlockPos neighborPos, BlockState neighbor, RandomSource random) {
        return state.setValue(SIDES.get(dir), side(level, neighborPos, dir));
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        if (level.getBlockEntity(pos) instanceof Entity conduit && conduit.cover != null) {
            return Shapes.block();
        }
        return shapes.get(state.setValue(LOOK, Look.OFF));
    }

    // ---------------------------------------------------------------- 包覆
    /** 可以拿來包導線的方塊：外框是完整方塊、沒有方塊實體、不是靈魂元件。 */
    private static BlockState coverOf(ItemStack stack, Level level, BlockPos pos) {
        if (!(stack.getItem() instanceof BlockItem item)) {
            return null;
        }
        BlockState cover = item.getBlock().defaultBlockState();
        if (cover.getBlock() instanceof SoulConductor || cover.hasBlockEntity() || !cover.isCollisionShapeFullBlock(level, pos)) {
            return null;
        }
        return cover;
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          InteractionHand hand, BlockHitResult hit) {
        if (!(level.getBlockEntity(pos) instanceof Entity conduit) || conduit.cover != null) {
            return InteractionResult.TRY_WITH_EMPTY_HAND;
        }
        BlockState cover = coverOf(stack, level, pos);
        if (cover == null) {
            return InteractionResult.TRY_WITH_EMPTY_HAND;
        }
        if (!level.isClientSide()) {
            conduit.setCover(cover);
            level.playSound(null, pos, cover.getSoundType().getPlaceSound(), SoundSource.BLOCKS, 1.0f, 0.9f);
            if (!player.getAbilities().instabuild) {
                stack.shrink(1);
            }
        }
        return InteractionResult.SUCCESS;
    }

    /** 空手右鍵：把包覆的方塊拆下來。 */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!(level.getBlockEntity(pos) instanceof Entity conduit) || conduit.cover == null) {
            return InteractionResult.PASS;
        }
        if (!level.isClientSide()) {
            BlockState cover = conduit.cover;
            conduit.setCover(null);
            level.playSound(null, pos, cover.getSoundType().getBreakSound(), SoundSource.BLOCKS, 1.0f, 0.9f);
            if (!player.getAbilities().instabuild) {
                Block.popResource(level, pos, new ItemStack(cover.getBlock()));
            }
        }
        return InteractionResult.SUCCESS;
    }

    // ---------------------------------------------------------------- 原版紅石：這是一個訊號源
    @Override
    protected boolean isSignalSource(BlockState state) {
        return true;
    }

    @Override
    protected int getSignal(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
        return state.getValue(LOOK) == Look.OFF ? 0 : power(level, pos);
    }

    /** 這段導線對外的紅石強度。 */
    public static int power(BlockGetter level, BlockPos pos) {
        return level.getBlockEntity(pos) instanceof Entity conduit ? conduit.power : 0;
    }

    /** 迴路算完之後寫回強度與外觀；有變才通知旁邊的原版元件。 */
    static void apply(ServerLevel level, BlockPos pos, BlockState state, int power, boolean soul) {
        Look look = power <= 0 ? Look.OFF : soul ? Look.SOUL : Look.PLAIN;
        boolean changed = false;
        if (level.getBlockEntity(pos) instanceof Entity conduit && conduit.power != power) {
            conduit.power = power;
            conduit.setChanged();
            changed = true;
        }
        if (state.getValue(LOOK) != look) {
            level.setBlock(pos, state.setValue(LOOK, look), Block.UPDATE_ALL);
        } else if (changed) {
            level.updateNeighborsAt(pos, state.getBlock(), null);
        }
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new Entity(pos, state);
    }

    // ---------------------------------------------------------------- 迴路
    @Override
    protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
        super.onPlace(state, level, pos, oldState, movedByPiston);
        if (level instanceof ServerLevel server && !oldState.is(this)) {
            SoulSignal.update(server, pos);
        }
    }

    @Override
    protected void affectNeighborsAfterRemoval(BlockState state, ServerLevel level, BlockPos pos, boolean movedByPiston) {
        super.affectNeighborsAfterRemoval(state, level, pos, movedByPiston);
        if (!level.getBlockState(pos).is(this)) {
            level.updateNeighborsAt(pos, this, null);
            SoulSignal.updateAround(level, pos);
        }
    }

    /** 旁邊的原版元件變了（拉桿扳動、中繼器輸出改變）：下一個 tick 重算，同一個 tick 的多次通知只算一次。 */
    @Override
    protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block block, Orientation orientation, boolean movedByPiston) {
        if (level instanceof ServerLevel server) {
            for (Direction d : Direction.values()) {
                BlockState ns = level.getBlockState(pos.relative(d));
                if (ns.is(Blocks.SCULK_CATALYST) && ns.getValue(BlockStateProperties.BLOOM)) {
                    SoulCircuit.charge(server, pos);    // 生物死在催化體旁：放出來的靈魂流進導線
                }
            }
            if (!level.getBlockTicks().hasScheduledTick(pos, this)) {
                level.scheduleTick(pos, this, 1);
            }
        }
    }

    @Override
    protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        SoulSignal.poll(level, pos);
        if (SoulCircuit.charged(level, pos)) {
            level.scheduleTick(pos, this, SoulSignal.INTERVAL);     // 催化體的靈魂用完之前定期重算，時間到就熄掉
        } else if (state.getValue(LOOK) == Look.SOUL && level.getBlockState(pos).is(this)) {
            SoulSignal.update(level, pos);
        }
    }

    /** 記對外的紅石強度，以及包覆的方塊（同步給用戶端，渲染器要畫）。不 tick。 */
    public static class Entity extends BlockEntity {
        int power;
        BlockState cover;

        public BlockState cover() {
            return cover;
        }

        void setCover(BlockState cover) {
            this.cover = cover;
            setChanged();
            if (level != null && !level.isClientSide()) {
                level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), Block.UPDATE_ALL);
            }
        }

        @Override
        public void preRemoveSideEffects(BlockPos pos, BlockState state) {
            if (level != null && cover != null) {
                Block.popResource(level, pos, new ItemStack(cover.getBlock()));
                cover = null;
            }
            super.preRemoveSideEffects(pos, state);
        }

        @Override
        public Packet<ClientGamePacketListener> getUpdatePacket() {
            return ClientboundBlockEntityDataPacket.create(this);
        }

        @Override
        public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
            return saveCustomOnly(registries);
        }

        public Entity(BlockPos pos, BlockState state) {
            super(SoulPower.SOUL_CONDUIT_ENTITY, pos, state);
        }

        @Override
        protected void saveAdditional(ValueOutput output) {
            super.saveAdditional(output);
            output.putInt("Power", power);
            if (cover != null) {
                output.store("Cover", BlockState.CODEC, cover);
            }
        }

        @Override
        protected void loadAdditional(ValueInput input) {
            super.loadAdditional(input);
            power = input.getIntOr("Power", 0);
            cover = input.read("Cover", BlockState.CODEC).orElse(null);
        }
    }
}
