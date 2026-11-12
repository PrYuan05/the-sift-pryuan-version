package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.PipeBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import pryuan05.pysift.fluid.ModFluids;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * 靈液泵：轉動時吸走正前方的靈液源頭（存進 {@link #CAPACITY} mB 的槽），每 {@link #PUSH_INTERVAL} tick 沿著背面的靈液管
 * 送 {@link #PUSH} mB 給管網上還裝得下的靈液引擎。送不出去、管網又有漏口（只接一頭、另一頭空著的管子）時，
 * 靈液從漏口漏出來：漏口前留下一灘靈液，正下方的泥土與草地被汙染成靈魂土。
 */
public class SpiritPumpBlockEntity extends KineticBlockEntity {
    public static final int CAPACITY = 4000;
    public static final int PUSH = 250;
    public static final int PUSH_INTERVAL = 10;
    public static final int PUMP_WORK = 40;   // ticks per bucket at 32 RPM
    private static final int MAX_PIPES = 128;
    private int tank;
    private float work;
    private int leakCooldown;

    public SpiritPumpBlockEntity(BlockPos pos, BlockState state) {
        super(SoulPower.SPIRIT_PUMP_ENTITY, pos, state);
    }

    public int tank() {
        return tank;
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, SpiritPumpBlockEntity pump) {
        ServerLevel server = (ServerLevel) level;
        long now = level.getGameTime();
        if (now - pump.network.time() > SoulSignal.INTERVAL * 3L && now % SoulSignal.INTERVAL == 0) {
            pump.network = SoulSignal.Result.IDLE;
            SoulSignal.poll(server, pos);
        }
        if (pump.leakCooldown > 0) {
            pump.leakCooldown--;
        }
        Direction facing = state.getValue(SoulMachineBlock.FACING);
        // 吸：正前方是靈液源頭就抽走一桶
        if (pump.speed != 0 && pump.tank <= CAPACITY - 1000) {
            pump.work += Math.abs(pump.speed) / SoulSignal.SPEED;
            if (pump.work >= PUMP_WORK) {
                pump.work = 0;
                BlockPos intake = pos.relative(facing);
                if (level.getFluidState(intake).isSourceOfType(ModFluids.SPIRIT_LIQUID)) {
                    level.setBlock(intake, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
                    pump.tank += 1000;
                    level.playSound(null, pos, SoundEvents.BUCKET_FILL, SoundSource.BLOCKS, 0.6f, 0.8f);
                    pump.setChanged();
                }
            }
        }
        // 送：每隔一段時間沿著管子送給引擎；送不出去就從漏口漏
        if (pump.tank >= PUSH && (now + pos.hashCode()) % PUSH_INTERVAL == 0) {
            Net net = network(level, pos.relative(facing.getOpposite()), facing.getOpposite());
            for (SpiritEngineBlockEntity engine : net.engines) {
                if (engine.acceptLiquid(PUSH)) {
                    pump.tank -= PUSH;
                    pump.setChanged();
                    return;
                }
            }
            if (!net.leaks.isEmpty() && pump.leakCooldown == 0) {
                BlockPos[] leak = net.leaks.get(level.getRandom().nextInt(net.leaks.size()));
                spill(server, leak[0], leak[1]);
                pump.tank -= PUSH;
                pump.leakCooldown = 40;
                pump.setChanged();
            }
        }
    }

    /** 漏：漏口前放一灘靈液（不是源頭），正下方的泥土類方塊變成靈魂土。 */
    private static void spill(ServerLevel level, BlockPos pipe, BlockPos out) {
        if (level.getBlockState(out).canBeReplaced()) {
            level.setBlock(out, ModFluids.FLOWING_SPIRIT_LIQUID.getFlowing(7, false).createLegacyBlock(), Block.UPDATE_ALL);
        }
        for (int dy = 1; dy <= 3; dy++) {
            BlockPos ground = out.below(dy);
            BlockState g = level.getBlockState(ground);
            if (g.is(BlockTags.DIRT) || g.is(BlockTags.SAND)) {
                level.setBlock(ground, Blocks.SOUL_SOIL.defaultBlockState(), Block.UPDATE_ALL);
                break;
            }
            if (g.canOcclude()) {
                break;   // something solid that is not soil: the spill stops here
            }
        }
        level.sendParticles(ParticleTypes.DRIPPING_DRIPSTONE_WATER, out.getX() + 0.5, out.getY() + 0.6, out.getZ() + 0.5, 6, 0.2, 0.2, 0.2, 0);
        level.sendParticles(ParticleTypes.SOUL, out.getX() + 0.5, out.getY() + 0.5, out.getZ() + 0.5, 2, 0.2, 0.2, 0.2, 0.02);
        level.playSound(null, pipe, SoundEvents.BUCKET_EMPTY, SoundSource.BLOCKS, 0.4f, 1.3f);
    }

    /** 管網：接在 start 的管子（以及它們連到的引擎），還有漏口（管子、往外的那一格）。 */
    private record Net(List<SpiritEngineBlockEntity> engines, List<BlockPos[]> leaks) {
    }

    static Net network(Level level, BlockPos start, Direction from) {
        List<SpiritEngineBlockEntity> engines = new ArrayList<>();
        List<BlockPos[]> leaks = new ArrayList<>();
        if (level.getBlockEntity(start) instanceof SpiritEngineBlockEntity direct) {
            engines.add(direct);
            return new Net(engines, leaks);
        }
        if (!(level.getBlockState(start).getBlock() instanceof SpiritPipeBlock)) {
            return new Net(engines, leaks);
        }
        Set<BlockPos> seen = new HashSet<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        seen.add(start);
        queue.add(start);
        while (!queue.isEmpty() && seen.size() < MAX_PIPES) {
            BlockPos pos = queue.poll();
            BlockState state = level.getBlockState(pos);
            int links = 0;
            for (Direction d : Direction.values()) {
                if (state.getValue(PipeBlock.PROPERTY_BY_DIRECTION.get(d))) {
                    links++;
                    BlockPos n = pos.relative(d);
                    if (level.getBlockEntity(n) instanceof SpiritEngineBlockEntity engine && !engines.contains(engine)) {
                        engines.add(engine);
                    } else if (level.getBlockState(n).getBlock() instanceof SpiritPipeBlock && seen.add(n)) {
                        queue.add(n);
                    }
                }
            }
            if (links == 1) {   // a dead end: it leaks out of the side opposite its only connection
                for (Direction d : Direction.values()) {
                    if (state.getValue(PipeBlock.PROPERTY_BY_DIRECTION.get(d))) {
                        BlockPos out = pos.relative(d.getOpposite());
                        if (level.getBlockState(out).canBeReplaced()) {
                            leaks.add(new BlockPos[]{pos, out});
                        }
                    }
                }
            }
        }
        return new Net(engines, leaks);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        output.putInt("Tank", tank);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        tank = input.getIntOr("Tank", 0);
    }
}
