package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * 靈魂鑽頭（Create 的 mechanical drill）：背面接傳動，正面的鑽頭旋轉著挖掉正前方的方塊，掉落物（像用鐵鎬挖的一樣）噴在原地。
 * 挖的速度 = 硬度 × {@link #WORK_PER_HARDNESS} ÷（|RPM| ÷ 32），所以轉越快挖越快；基岩、黑曜石這類 Wither 免疫的方塊挖不動。
 * 正前方有生物時會被鑽傷。每 1 RPM 吃 2 SP。
 */
public class SoulDrillBlock extends SoulMachineBlock {
    public static final float WORK_PER_HARDNESS = 30f;
    private final VoxelShape[] shapes = new VoxelShape[6];

    public SoulDrillBlock(Properties properties) {
        super(true, properties);
        for (Direction d : Direction.values()) {
            shapes[d.ordinal()] = switch (d) {   // the casing; the bit sticks out of the front
                case UP -> Block.box(0, 0, 0, 16, 10, 16);
                case DOWN -> Block.box(0, 6, 0, 16, 16, 16);
                case NORTH -> Block.box(0, 0, 6, 16, 16, 16);
                case SOUTH -> Block.box(0, 0, 0, 16, 16, 10);
                case WEST -> Block.box(6, 0, 0, 16, 16, 16);
                case EAST -> Block.box(0, 0, 0, 10, 16, 16);
            };
        }
    }

    @Override
    public boolean connects(BlockState state, Direction side) {
        return side == state.getValue(FACING).getOpposite();
    }

    @Override
    public Direction.Axis axis(BlockState state) {
        return state.getValue(FACING).getAxis();
    }

    @Override
    public float impact(BlockState state) {
        return 2f;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shapes[state.getValue(FACING).ordinal()];
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new Entity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide() ? null : createTickerHelper(type, SoulPower.SOUL_DRILL_ENTITY, Entity::serverTick);
    }

    public static class Entity extends KineticBlockEntity {
        private float progress;
        private BlockPos target;

        public Entity(BlockPos pos, BlockState state) {
            super(SoulPower.SOUL_DRILL_ENTITY, pos, state);
        }

        static void serverTick(Level level, BlockPos pos, BlockState state, Entity drill) {
            ServerLevel server = (ServerLevel) level;
            long now = level.getGameTime();
            if (now - drill.network.time() > SoulNetwork.INTERVAL * 3L && now % SoulNetwork.INTERVAL == 0) {
                drill.network = SoulNetwork.Result.IDLE;
                SoulNetwork.update(server, pos);
            }
            BlockPos front = pos.relative(state.getValue(FACING));
            if (drill.speed == 0) {
                drill.reset(level);
                return;
            }
            if (now % 10 == 0) {
                for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(front))) {
                    e.hurtServer(server, server.damageSources().generic(), 3f);
                }
            }
            BlockState target = level.getBlockState(front);
            float hardness = target.getDestroySpeed(level, front);
            if (target.isAir() || hardness < 0 || target.is(BlockTags.WITHER_IMMUNE) || !target.getFluidState().isEmpty() && target.canBeReplaced()) {
                drill.reset(level);
                return;
            }
            if (!front.equals(drill.target)) {
                drill.reset(level);
                drill.target = front.immutable();
            }
            float work = Math.max(1f, hardness * WORK_PER_HARDNESS);
            drill.progress += Math.abs(drill.speed) / SoulNetwork.SPEED;
            int stage = (int) Math.min(9, drill.progress / work * 10);
            level.destroyBlockProgress(pos.hashCode(), front, stage);
            if (now % 4 == 0) {
                server.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, target), front.getX() + 0.5, front.getY() + 0.5,
                        front.getZ() + 0.5, 3, 0.3, 0.3, 0.3, 0.05);
            }
            if (drill.progress >= work) {
                // drops as if mined with an iron pickaxe (stone gives cobblestone, ores their raw item)
                Block.dropResources(target, level, front, level.getBlockEntity(front), null, new ItemStack(Items.IRON_PICKAXE));
                level.destroyBlock(front, false);
                drill.reset(level);
            }
        }

        private void reset(Level level) {
            if (target != null) {
                level.destroyBlockProgress(worldPosition.hashCode(), target, -1);
            }
            target = null;
            progress = 0;
        }

        @Override
        protected void saveAdditional(ValueOutput output) {
            super.saveAdditional(output);
            output.putFloat("Progress", progress);
        }

        @Override
        protected void loadAdditional(ValueInput input) {
            super.loadAdditional(input);
            progress = input.getFloatOr("Progress", 0f);
        }
    }
}
