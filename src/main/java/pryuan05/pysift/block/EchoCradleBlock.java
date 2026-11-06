package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.entity.mob.EchoGolemEntity;
import pryuan05.pysift.entity.mob.SingerEntity;

/**
 * 回音晶簇（回音窟的晶洞裡）：歌者的歌聲在晶體裡反覆回響，回音慢慢凝結，滿了就生出一隻迴音傀儡（§4.7「回音窟」）。
 * 附近 {@link #SINGER_RANGE} 格內有歌者、而且 {@link #GOLEM_RANGE} 格內的傀儡少於 {@link #MAX_GOLEMS} 隻時，每次隨機刻
 * 共鳴 +1；餵迴音碎片也會 +1（不需要歌者）。共鳴到 {@link #FULL} 時生出傀儡並歸零。
 */
public class EchoCradleBlock extends Block {
    public static final int FULL = 3;
    public static final IntegerProperty RESONANCE = IntegerProperty.create("resonance", 0, FULL);
    static final double SINGER_RANGE = 8.0, GOLEM_RANGE = 16.0;
    static final int MAX_GOLEMS = 4;
    private static final VoxelShape SHAPE = Block.box(3, 0, 3, 13, 12, 13);

    public EchoCradleBlock(Properties properties) {
        super(properties);
        this.registerDefaultState(this.stateDefinition.any().setValue(RESONANCE, 0));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(RESONANCE);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE;
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        BlockPos below = pos.below();
        return level.getBlockState(below).isFaceSturdy(level, below, Direction.UP);
    }

    @Override
    protected BlockState updateShape(BlockState state, LevelReader level, net.minecraft.world.level.ScheduledTickAccess ticks, BlockPos pos,
                                     Direction direction, BlockPos neighborPos, BlockState neighborState, RandomSource random) {
        return direction == Direction.DOWN && !state.canSurvive(level, pos) ? net.minecraft.world.level.block.Blocks.AIR.defaultBlockState()
                : super.updateShape(state, level, ticks, pos, direction, neighborPos, neighborState, random);
    }

    @Override
    protected boolean isRandomlyTicking(BlockState state) {
        return true;
    }

    @Override
    protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (level.getEntitiesOfClass(SingerEntity.class, new net.minecraft.world.phys.AABB(pos).inflate(SINGER_RANGE), SingerEntity::isAlive).isEmpty()) {
            return;
        }
        resonate(state, level, pos);
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          InteractionHand hand, BlockHitResult hit) {
        if (!stack.is(Items.ECHO_SHARD)) {
            return super.useItemOn(stack, state, level, pos, player, hand, hit);
        }
        if (level instanceof ServerLevel server) {
            if (resonate(state, server, pos)) {
                stack.consume(1, player);
            }
        }
        return InteractionResult.SUCCESS;
    }

    /** 共鳴 +1；滿了就生出傀儡。傀儡已經夠多時什麼都不做，回傳 false。 */
    static boolean resonate(BlockState state, ServerLevel level, BlockPos pos) {
        int golems = level.getEntitiesOfClass(EchoGolemEntity.class, new net.minecraft.world.phys.AABB(pos).inflate(GOLEM_RANGE),
                EchoGolemEntity::isAlive).size();
        if (golems >= MAX_GOLEMS) {
            return false;
        }
        int next = state.getValue(RESONANCE) + 1;
        double x = pos.getX() + 0.5, y = pos.getY() + 0.5, z = pos.getZ() + 0.5;
        if (next < FULL) {
            level.setBlock(pos, state.setValue(RESONANCE, next), Block.UPDATE_ALL);
            level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 1.0f, 0.7f + 0.15f * next);
            level.sendParticles(ParticleTypes.NOTE, x, y + 0.6, z, 2 + next, 0.3, 0.2, 0.3, 1.0);
            level.sendParticles(ParticleTypes.SCULK_SOUL, x, y, z, 2, 0.25, 0.25, 0.25, 0.01);
            return true;
        }
        EchoGolemEntity golem = ModEntities.ECHO_GOLEM.create(level, EntitySpawnReason.MOB_SUMMONED);
        if (golem == null) {
            return false;
        }
        golem.snapTo(x, pos.getY() + 1.0, z, level.getRandom().nextFloat() * 360f, 0f);
        golem.setPersistenceRequired();
        level.addFreshEntity(golem);
        level.setBlock(pos, state.setValue(RESONANCE, 0), Block.UPDATE_ALL);
        level.playSound(null, pos, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.BLOCKS, 1.2f, 0.6f);
        level.playSound(null, pos, SoundEvents.SCULK_SHRIEKER_SHRIEK, SoundSource.BLOCKS, 0.6f, 1.8f);
        level.sendParticles(ParticleTypes.SONIC_BOOM, x, y + 1.0, z, 1, 0, 0, 0, 0);
        level.sendParticles(ParticleTypes.NOTE, x, y + 1.5, z, 12, 0.8, 0.6, 0.8, 1.0);
        level.sendParticles(ParticleTypes.SCULK_SOUL, x, y + 1.0, z, 16, 0.6, 0.8, 0.6, 0.03);
        return true;
    }

    /** 光度隨共鳴變亮（3 / 6 / 9 / 12）。 */
    public static int light(BlockState state) {
        return 3 + 3 * state.getValue(RESONANCE);
    }
}
