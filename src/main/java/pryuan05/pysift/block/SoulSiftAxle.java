package pryuan05.pysift.block;

import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import pryuan05.pysift.PySift;
import pryuan05.pysift.item.ModItems;
import pryuan05.pysift.item.SiftCreativeTabs;

/**
 * 靈魂隙浮輪軸：歌者的工藝品，把漏到主世界、變質成幽匿的隙浮能量「篩」回乾淨的靈魂（世界觀見 MODDING_ROADMAP 4.7）。
 * <ul>
 *   <li>平時輪子慢慢轉；手持幽匿類方塊（{@link #SIFTABLE}）右鍵放進去，輪子加速轉 3 秒，篩出靈魂沙與機率掉落的靈魂精華。</li>
 *   <li>做法仿 Create 的「部分模型」：支架是一般的方塊模型（models/block/soul_sift_axle.json），會轉的輪子是另一個模型
 *       （models/block/soul_sift_axle_wheel.json，掛在沒有物品、不會被放置的 {@link #WHEEL} 方塊上），由用戶端的
 *       SoulSiftAxleRenderer 每一幀依角度旋轉後畫出。兩個模型都能直接用 Blockbench 修改。</li>
 *   <li>轉速在用戶端平滑變化（{@link Entity#clientTick}），開始與停下都有加減速。</li>
 * </ul>
 */
public final class SoulSiftAxle {
    /** 可以放進輪軸篩的方塊（幽匿、幽匿脈、感測器、尖嘯體、觸媒）。 */
    public static final TagKey<Item> SIFTABLE = TagKey.create(Registries.ITEM, PySift.id("soul_siftable"));
    public static final EnumProperty<Direction.Axis> AXIS = BlockStateProperties.HORIZONTAL_AXIS;
    public static final BooleanProperty ACTIVE = BooleanProperty.create("active");
    /** 篩一次的時間（tick）。 */
    public static final int SIFT_TICKS = 60;

    private static final ResourceKey<Block> AXLE_KEY = ResourceKey.create(Registries.BLOCK, PySift.id("soul_sift_axle"));
    public static final Block AXLE = Registry.register(BuiltInRegistries.BLOCK, AXLE_KEY,
            new AxleBlock(BlockBehaviour.Properties.ofFullCopy(Blocks.GRINDSTONE).lightLevel(s -> s.getValue(ACTIVE) ? 9 : 4)
                    .noOcclusion().setId(AXLE_KEY)));
    /** 只拿來掛輪子模型給渲染器用，不會出現在世界裡。 */
    private static final ResourceKey<Block> WHEEL_KEY = ResourceKey.create(Registries.BLOCK, PySift.id("soul_sift_axle_wheel"));
    public static final Block WHEEL = Registry.register(BuiltInRegistries.BLOCK, WHEEL_KEY,
            new Block(BlockBehaviour.Properties.of().noLootTable().noOcclusion().setId(WHEEL_KEY)));
    private static final ResourceKey<Item> ITEM_KEY = ResourceKey.create(Registries.ITEM, PySift.id("soul_sift_axle"));
    public static final Item ITEM = Registry.register(BuiltInRegistries.ITEM, ITEM_KEY,
            new BlockItem(AXLE, new Item.Properties().useBlockDescriptionPrefix().setId(ITEM_KEY)));
    public static final BlockEntityType<Entity> ENTITY = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("soul_sift_axle"),
            FabricBlockEntityTypeBuilder.create(Entity::new, AXLE).build());

    private SoulSiftAxle() {
    }

    public static void register() {
        SiftCreativeTabs.source(ModItems.BLOCKS_TAB_KEY, output -> output.accept(ITEM));
    }

    public static class AxleBlock extends Block implements EntityBlock {
        private static final VoxelShape SHAPE = Block.box(0, 0, 0, 16, 15, 16);

        public AxleBlock(Properties properties) {
            super(properties);
            registerDefaultState(defaultBlockState().setValue(AXIS, Direction.Axis.X).setValue(ACTIVE, false));
        }

        @Override
        protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
            builder.add(AXIS, ACTIVE);
        }

        /** The wheel faces the player: the axle runs left-right. */
        @Override
        public BlockState getStateForPlacement(BlockPlaceContext context) {
            return defaultBlockState().setValue(AXIS, context.getHorizontalDirection().getClockWise().getAxis());
        }

        @Override
        protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
            return SHAPE;
        }

        @Override
        public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
            return new Entity(pos, state);
        }

        @Override
        @SuppressWarnings("unchecked")
        public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
            if (type != ENTITY) {
                return null;
            }
            return level.isClientSide()
                    ? (l, p, s, be) -> ((Entity) be).clientTick()
                    : (l, p, s, be) -> ((Entity) be).serverTick((ServerLevel) l, p, s);
        }

        @Override
        protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                              InteractionHand hand, BlockHitResult hit) {
            if (!stack.is(SIFTABLE)) {
                return InteractionResult.TRY_WITH_EMPTY_HAND;
            }
            if (!(level.getBlockEntity(pos) instanceof Entity axle) || axle.siftTicks > 0) {
                return InteractionResult.FAIL;
            }
            if (!level.isClientSide()) {
                axle.start(stack.copyWithCount(1));
                stack.consume(1, player);
                level.setBlock(pos, state.setValue(ACTIVE, true), Block.UPDATE_ALL);
                level.playSound(null, pos, SoundEvents.GRINDSTONE_USE, SoundSource.BLOCKS, 0.8F, 0.7F);
                level.playSound(null, pos, SoundEvents.SCULK_BLOCK_BREAK, SoundSource.BLOCKS, 1.0F, 0.8F);
            }
            return InteractionResult.SUCCESS;
        }
    }

    public static class Entity extends BlockEntity {
        /** Ticks left of the current sifting, 0 = idle. */
        int siftTicks;
        private ItemStack input = ItemStack.EMPTY;
        // client-side animation (degrees): angle now and last tick, current speed per tick
        private float angle;
        private float prevAngle;
        private float speed;

        public Entity(BlockPos pos, BlockState state) {
            super(ENTITY, pos, state);
        }

        void start(ItemStack stack) {
            input = stack;
            siftTicks = SIFT_TICKS;
            setChanged();
        }

        void serverTick(ServerLevel level, BlockPos pos, BlockState state) {
            if (siftTicks <= 0) {
                return;
            }
            siftTicks--;
            if (siftTicks % 5 == 0) {
                level.sendParticles(ParticleTypes.SCULK_SOUL, pos.getX() + 0.5, pos.getY() + 0.7, pos.getZ() + 0.5, 2, 0.25, 0.2, 0.25, 0.02);
            }
            if (siftTicks == 0) {
                for (ItemStack out : results(input, level)) {
                    Block.popResourceFromFace(level, pos, Direction.UP, out);
                }
                input = ItemStack.EMPTY;
                level.setBlock(pos, state.setValue(ACTIVE, false), Block.UPDATE_ALL);
                level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.2F, 0.6F);
                level.sendParticles(ParticleTypes.SOUL, pos.getX() + 0.5, pos.getY() + 0.8, pos.getZ() + 0.5, 8, 0.3, 0.2, 0.3, 0.03);
            }
            setChanged();
        }

        /** What one sifted block gives: the purified soul (soul sand / soil) and a chance of soul essence. */
        private static java.util.List<ItemStack> results(ItemStack input, ServerLevel level) {
            java.util.List<ItemStack> out = new java.util.ArrayList<>();
            Item soulEssence = BuiltInRegistries.ITEM.getValue(PySift.id("soul_essence"));
            float essenceChance;
            if (input.is(Items.SCULK_VEIN)) {
                essenceChance = 0.15F;                            // a thin vein: no soul sand
            } else if (input.is(Items.SCULK_CATALYST)) {
                out.add(new ItemStack(Items.SOUL_SOIL, 2));
                out.add(new ItemStack(soulEssence, 2));
                essenceChance = 0.5F;
            } else if (input.is(Items.SCULK_SENSOR) || input.is(Items.CALIBRATED_SCULK_SENSOR) || input.is(Items.SCULK_SHRIEKER)) {
                out.add(new ItemStack(Items.SOUL_SAND));
                essenceChance = 0.6F;
            } else {
                out.add(new ItemStack(Items.SOUL_SAND));
                essenceChance = 0.25F;
            }
            if (level.getRandom().nextFloat() < essenceChance) {
                out.add(new ItemStack(soulEssence));
            }
            return out;
        }

        void clientTick() {
            boolean active = getBlockState().getValue(ACTIVE);
            float target = active ? 18.0F : 1.5F;                 // degrees per tick: fast while sifting, a slow idle turn
            speed += (target - speed) * (active ? 0.12F : 0.05F);  // spin up quickly, run down slowly
            prevAngle = angle;
            angle += speed;
            if (angle >= 360.0F) {
                angle -= 360.0F;
                prevAngle -= 360.0F;
            }
        }

        /** Wheel angle in degrees, interpolated for this frame. */
        public float angle(float partialTick) {
            return Mth.lerp(partialTick, prevAngle, angle);
        }

        @Override
        protected void saveAdditional(ValueOutput output) {
            super.saveAdditional(output);
            output.putInt("sift_ticks", siftTicks);
            if (!input.isEmpty()) {
                output.store("input", ItemStack.CODEC, input);
            }
        }

        @Override
        protected void loadAdditional(ValueInput input) {
            super.loadAdditional(input);
            siftTicks = input.getIntOr("sift_ticks", 0);
            this.input = input.read("input", ItemStack.CODEC).orElse(ItemStack.EMPTY);
        }

        @Override
        public Packet<ClientGamePacketListener> getUpdatePacket() {
            return ClientboundBlockEntityDataPacket.create(this);
        }
    }
}
