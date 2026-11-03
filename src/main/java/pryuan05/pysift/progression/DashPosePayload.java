package pryuan05.pysift.progression;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;
import pryuan05.pysift.PySift;

/** 伺服器 → 客戶端：這個玩家剛用衝刺護符衝刺，客戶端播雙手前刺的姿勢（WeaponPoses）。 */
public record DashPosePayload(int entityId) implements CustomPacketPayload {
    public static final Type<DashPosePayload> TYPE = new Type<>(PySift.id("dash_pose"));
    public static final StreamCodec<RegistryFriendlyByteBuf, DashPosePayload> CODEC =
            ByteBufCodecs.VAR_INT.map(DashPosePayload::new, DashPosePayload::entityId).cast();

    @Override
    public Type<DashPosePayload> type() {
        return TYPE;
    }

    static void register() {
        PayloadTypeRegistry.clientboundPlay().register(TYPE, CODEC);
    }

    /** 送給衝刺的玩家本人和看得到他的玩家。 */
    static void broadcast(ServerPlayer player) {
        DashPosePayload payload = new DashPosePayload(player.getId());
        ServerPlayNetworking.send(player, payload);
        for (ServerPlayer other : PlayerLookup.tracking(player)) {
            if (other != player) {
                ServerPlayNetworking.send(other, payload);
            }
        }
    }
}
