package pryuan05.pysift.block.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Containers;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import pryuan05.pysift.block.RitualBlocks;
import pryuan05.pysift.block.RitualDiscs;
import pryuan05.pysift.block.SiftPortalRitual;

import java.util.ArrayList;
import java.util.List;

/**
 * 共鳴唱片盒：儀式的一個座位。存放入的唱片、這組 8 個唱片盒的位置、傳送門中心與框架軸向，
 * 以及給用戶端動畫用的時間點（出現、終曲閃光）。資料都會同步到用戶端（ResonantJukeboxRenderer）。
 */
public class ResonantJukeboxBlockEntity extends BlockEntity {
    private ItemStack disc = ItemStack.EMPTY;
    private BlockPos portalCentre;
    private boolean axisX = true;
    private boolean frame;
    private List<BlockPos> group = new ArrayList<>();
    private long placedAt;
    private long flashAt = -1000;

    public ResonantJukeboxBlockEntity(BlockPos pos, BlockState state) {
        super(RitualBlocks.RESONANT_JUKEBOX_ENTITY, pos, state);
    }

    // ------------------------------------------------------------------ ritual data
    public void setup(BlockPos portalCentre, boolean axisX, boolean frame, List<BlockPos> group, long now) {
        this.portalCentre = portalCentre;
        this.axisX = axisX;
        this.frame = frame;
        this.group = new ArrayList<>(group);
        this.placedAt = now;
        sync();
    }

    public ItemStack getDisc() {
        return disc;
    }

    public RitualDiscs.Disc getRitualDisc() {
        return disc.isEmpty() ? null : RitualDiscs.of(disc);
    }

    public void setDisc(ItemStack disc) {
        this.disc = disc.copyWithCount(1);
        sync();
    }

    public BlockPos getPortalCentre() {
        return portalCentre;
    }

    public boolean isAxisX() {
        return axisX;
    }

    public boolean isFrame() {
        return frame;
    }

    /** 由左到右第幾個（0~7）；不屬於任何一組時為 -1。 */
    public int seatIndex() {
        return group.indexOf(worldPosition);
    }

    /** 這個位置要的唱片。 */
    public RitualDiscs.Disc expectedDisc() {
        return RitualDiscs.forSeat(seatIndex());
    }

    public List<BlockPos> getGroup() {
        return group;
    }

    public long getPlacedAt() {
        return placedAt;
    }

    public long getFlashAt() {
        return flashAt;
    }

    public void flash(long now) {
        this.flashAt = now;
        sync();
    }

    private void sync() {
        setChanged();
        if (level != null && !level.isClientSide()) {
            level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), Block.UPDATE_CLIENTS);
        }
    }

    // ------------------------------------------------------------------ removal: drop the disc, close the portal
    @Override
    public void preRemoveSideEffects(BlockPos pos, BlockState state) {
        if (level instanceof ServerLevel server) {
            if (!disc.isEmpty()) {
                Containers.dropItemStack(server, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, disc);
                disc = ItemStack.EMPTY;
            }
            SiftPortalRitual.onJukeboxRemoved(server, this);
        }
        super.preRemoveSideEffects(pos, state);
    }

    // ------------------------------------------------------------------ save / sync
    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        if (!disc.isEmpty()) {
            output.store("Disc", ItemStack.CODEC, disc);
        }
        if (portalCentre != null) {
            output.store("PortalCentre", BlockPos.CODEC, portalCentre);
        }
        output.putBoolean("AxisX", axisX);
        output.putBoolean("Frame", frame);
        output.store("Group", BlockPos.CODEC.listOf(), group);
        output.putLong("PlacedAt", placedAt);
        output.putLong("FlashAt", flashAt);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        disc = input.read("Disc", ItemStack.CODEC).orElse(ItemStack.EMPTY);
        portalCentre = input.read("PortalCentre", BlockPos.CODEC).orElse(null);
        axisX = input.getBooleanOr("AxisX", true);
        frame = input.getBooleanOr("Frame", false);
        group = new ArrayList<>(input.read("Group", BlockPos.CODEC.listOf()).orElse(List.of()));
        placedAt = input.getLongOr("PlacedAt", 0L);
        flashAt = input.getLongOr("FlashAt", -1000L);
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        return saveCustomOnly(registries);
    }
}
