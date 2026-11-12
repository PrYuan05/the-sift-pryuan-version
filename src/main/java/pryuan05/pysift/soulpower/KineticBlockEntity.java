package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * 每個靈魂動力方塊的方塊實體（和 Create 一樣，會轉的東西都有）：記住網路狀態與自己的轉速，
 * 轉速、過載或負載改變時同步給用戶端，用戶端依「遊戲時間 × 轉速」算出角度（{@link #angle}），
 * 所以整個網路的齒輪、傳動軸完全同步，重新載入也不會錯位。
 */
public class KineticBlockEntity extends BlockEntity implements SoulKinetic.Member {
    protected SoulSignal.Result network = SoulSignal.Result.IDLE;
    protected float speed;
    private SoulSignal.Result circuit = SoulSignal.Result.IDLE;
    private SoulSignal.Result kinetic = SoulSignal.Result.IDLE;
    private float circuitSpeed;
    private float kineticSpeed;
    /** 只在用戶端有意義（從同步資料讀來）。 */
    private boolean overloaded;
    private boolean conflict;
    private float load;

    public KineticBlockEntity(BlockEntityType<?> type, BlockPos pos, BlockState state) {
        super(type, pos, state);
    }

    public KineticBlockEntity(BlockPos pos, BlockState state) {
        this(SoulPower.SOUL_KINETIC_ENTITY, pos, state);
    }

    /** 機械擴充的轉速網路算出來的結果（沒啟用擴充時不會被呼叫）。 */
    @Override
    public void setNetwork(SoulSignal.Result result, float speed) {
        kinetic = result;
        kineticSpeed = speed;
        apply();
    }

    /** 靈魂迴路（{@link SoulCircuit}）算出來的結果：speed 由靈魂訊號強度換算。 */
    public void setCircuit(SoulSignal.Result result, float speed) {
        circuit = result;
        circuitSpeed = speed;
        apply();
    }

    /**
     * 兩邊都有動力源時（只有機械層啟用才會發生，例如引擎同時接著傳動軸和導線），聽負載比較重的那一邊；
     * 只有一邊有動力源就聽那一邊。
     */
    private void apply() {
        boolean mechanical = kinetic.capacity() > 0 && (circuit.capacity() == 0 || kinetic.stress() >= circuit.stress());
        SoulSignal.Result result = mechanical ? kinetic : circuit;
        float speed = mechanical ? kineticSpeed : circuitSpeed;
        boolean changed = Math.abs(this.speed - speed) > 1e-3f || network.overloaded() != result.overloaded()
                || network.conflict() != result.conflict() || Math.abs(network.load() - result.load()) > 0.02f;
        this.network = result;
        this.speed = speed;
        BlockState state = getBlockState();
        boolean powered = speed != 0;
        if (level != null && !level.isClientSide() && state.hasProperty(SoulKinetic.POWERED) && state.getValue(SoulKinetic.POWERED) != powered) {
            level.setBlock(worldPosition, state.setValue(SoulKinetic.POWERED, powered), 2);
        }
        onState(result, speed);
        if (changed) {
            sync();
        }
    }

    /** 狀態更新之後（靈壓計用來通知比較器）。 */
    protected void onState(SoulSignal.Result result, float speed) {
    }

    /** 靈魂訊號強度 0–15（由速度換算；機械動力直接帶動時可能更快，這裡封頂）。 */
    public int strength() {
        return Math.min(SoulSignal.MAX_STRENGTH, SoulSignal.strength(speed));
    }

    /** 存檔並把方塊實體資料送給用戶端。 */
    protected void sync() {
        setChanged();
        if (level != null && !level.isClientSide()) {
            level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), Block.UPDATE_CLIENTS);
        }
    }

    public SoulSignal.Result network() {
        return network;
    }

    public float speed() {
        return speed;
    }

    public boolean isOverloaded() {
        return level != null && level.isClientSide() ? overloaded : network.overloaded();
    }

    public boolean isConflicted() {
        return level != null && level.isClientSide() ? conflict : network.conflict();
    }

    /** 負載比例（需求 ÷ 容量，可以超過 1）。 */
    public float load() {
        return level != null && level.isClientSide() ? load : network.load();
    }

    /** 轉動的角度（度），time 是遊戲時間加 partialTick。1 RPM = 每 tick 0.3°。 */
    public float angle(double time) {
        return (float) ((time * speed * 0.3) % 360.0);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        output.putFloat("Speed", speed);
        output.putBoolean("Overloaded", network.overloaded());
        output.putBoolean("Conflict", network.conflict());
        output.putFloat("Load", network.load());
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        speed = input.getFloatOr("Speed", 0f);
        overloaded = input.getBooleanOr("Overloaded", false);
        conflict = input.getBooleanOr("Conflict", false);
        load = input.getFloatOr("Load", 0f);
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
