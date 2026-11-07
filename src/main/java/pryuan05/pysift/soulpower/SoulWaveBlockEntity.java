package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.Containers;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.particle.ModParticles;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 振波發送器／接收器的資料：頻率唱片，以及每個世界裡所有振波方塊的位置（找連線用，不用掃描整個範圍）。
 * 發送器運轉時，每條連線上都有一顆靈魂波球從發送器飛到接收器（距離越遠飛越久，只是外觀）。
 */
public class SoulWaveBlockEntity extends KineticBlockEntity {
    public static final int RANGE = 16;
    private static final Map<ResourceKey<Level>, Set<BlockPos>> WAVES = new HashMap<>();
    private ItemStack disc = ItemStack.EMPTY;
    private List<BlockPos> links = List.of();

    public SoulWaveBlockEntity(BlockPos pos, BlockState state) {
        super(SoulPower.SOUL_WAVE_ENTITY, pos, state);
    }

    public boolean isEmitter() {
        return getBlockState().getBlock() instanceof SoulWaveBlock wave && wave.emitter;
    }

    public ItemStack getDisc() {
        return disc;
    }

    public void setDisc(ItemStack disc) {
        this.disc = disc;
        setChanged();
        if (level != null && !level.isClientSide()) {
            level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), Block.UPDATE_CLIENTS);
        }
    }

    /** 同頻率、範圍內、視線上沒有隔絕振動方塊的另一種振波方塊（發送器找接收器，接收器找發送器）。 */
    public List<BlockPos> findLinks(ServerLevel level) {
        List<BlockPos> out = new ArrayList<>();
        if (!disc.isEmpty()) {
            for (BlockPos other : WAVES.getOrDefault(level.dimension(), Set.of())) {
                if (other.equals(worldPosition) || !other.closerThan(worldPosition, RANGE + 0.5)) {
                    continue;
                }
                if (level.getBlockEntity(other) instanceof SoulWaveBlockEntity wave && wave.isEmitter() != isEmitter()
                        && ItemStack.isSameItem(wave.disc, disc) && clearPath(level, worldPosition, other)) {
                    out.add(other);
                }
            }
        }
        links = out;
        return out;
    }

    /** 兩點之間沒有 #minecraft:occludes_vibration_signals（羊毛、地毯）。 */
    private static boolean clearPath(Level level, BlockPos from, BlockPos to) {
        Vec3 a = Vec3.atCenterOf(from), b = Vec3.atCenterOf(to);
        int steps = (int) Math.ceil(a.distanceTo(b) * 2);
        for (int i = 1; i < steps; i++) {
            BlockPos p = BlockPos.containing(a.lerp(b, (double) i / steps));
            if (!p.equals(from) && !p.equals(to) && level.getBlockState(p).is(BlockTags.OCCLUDES_VIBRATION_SIGNALS)) {
                return false;
            }
        }
        return true;
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, SoulWaveBlockEntity wave) {
        ServerLevel server = (ServerLevel) level;
        long now = level.getGameTime();
        if (now - wave.network.time() > SoulNetwork.INTERVAL * 3L && now % SoulNetwork.INTERVAL == 5) {
            wave.network = SoulNetwork.Result.IDLE;
            SoulNetwork.update(server, pos);
        }
        if (!wave.isEmitter() || wave.speed == 0 || now % 2 != 0) {
            return;
        }
        Vec3 a = Vec3.atCenterOf(pos);
        if (!wave.links.isEmpty() && (now + pos.hashCode()) % 40 == 0) {
            level.playSound(null, pos, pryuan05.pysift.sound.ModSounds.SOUL_WAVE_PULSE, net.minecraft.sounds.SoundSource.BLOCKS, 0.45f, 1.0f);
        }
        for (BlockPos link : wave.links) {
            Vec3 b = Vec3.atCenterOf(link);
            int period = Math.max(10, (int) (a.distanceTo(b) * 2));       // ~ 1 block per 2 ticks
            Vec3 p = a.lerp(b, (double) (now % period) / period);
            server.sendParticles(ModParticles.SOUL_TRAIL, p.x, p.y, p.z, 2, 0.05, 0.05, 0.05, 0.0);
        }
    }

    @Override
    public void setLevel(Level level) {
        super.setLevel(level);
        if (!level.isClientSide()) {
            WAVES.computeIfAbsent(level.dimension(), k -> new HashSet<>()).add(worldPosition.immutable());
        }
    }

    @Override
    public void setRemoved() {
        super.setRemoved();
        if (level != null && !level.isClientSide()) {
            Set<BlockPos> set = WAVES.get(level.dimension());
            if (set != null) {
                set.remove(worldPosition);
            }
        }
    }

    @Override
    public void preRemoveSideEffects(BlockPos pos, BlockState state) {
        if (level != null && !disc.isEmpty()) {
            Containers.dropItemStack(level, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, disc);
            disc = ItemStack.EMPTY;
        }
        super.preRemoveSideEffects(pos, state);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        if (!disc.isEmpty()) {
            output.store("Disc", ItemStack.CODEC, disc);
        }
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        disc = input.read("Disc", ItemStack.CODEC).orElse(ItemStack.EMPTY);
    }
}
