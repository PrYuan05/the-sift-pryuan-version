package pryuan05.pysift.progression;

import com.mojang.serialization.Codec;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.item.v1.ItemComponentTooltipProviderRegistry;
import net.minecraft.ChatFormatting;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import pryuan05.pysift.PySift;
import pryuan05.pysift.effect.ModEffects;
import pryuan05.pysift.effect.SoulBurn;

/**
 * 篩靈信標（終局，第 1 階段第 6 段）：三種 Boss 核心各一顆加紫龍晶合成<b>篩靈信標寶石</b>，
 * 在鍛造台鑲嵌到任一胸甲（保留附魔與紋飾，配方在 build_progression.py）。
 * 穿著鑲嵌胸甲的玩家周圍 {@link #RADIUS} 格內的所有玩家（含自己）：
 * 不會再被靈液點燃（{@link SoulWard#isImmune}），身上已有的靈魂剝奪也會被淨化、血量歸還（{@link SoulBurn#cure}）。
 */
public final class SiftBeacon {
    public static final double RADIUS = 8.0;

    public static final DataComponentType<Boolean> INLAID = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
            PySift.id("sift_beacon"), DataComponentType.<Boolean>builder().persistent(Codec.BOOL).networkSynchronized(ByteBufCodecs.BOOL).build());

    public static final Item GEM = ModProgression.registerItem("sift_beacon_gem",
            p -> new HintItem(p, "tooltip.pysift.sift_beacon_gem.0", "tooltip.pysift.sift_beacon_gem.1", "tooltip.pysift.sift_beacon.aura"),
            new Item.Properties().rarity(Rarity.EPIC).stacksTo(1).fireResistant());

    private SiftBeacon() {
    }

    public static boolean wearsBeacon(Player player) {
        return Boolean.TRUE.equals(player.getItemBySlot(EquipmentSlot.CHEST).get(INLAID));
    }

    /** 這位玩家在某個信標光環裡（自己或 RADIUS 格內的其他玩家穿著鑲嵌胸甲）。 */
    public static boolean inAura(ServerPlayer player) {
        if (wearsBeacon(player)) {
            return true;
        }
        for (ServerPlayer other : player.level().players()) {
            if (other != player && wearsBeacon(other) && other.distanceToSqr(player) <= RADIUS * RADIUS) {
                return true;
            }
        }
        return false;
    }

    static void load() {
        // 鑲嵌後的胸甲在物品說明欄顯示光環效果
        ItemComponentTooltipProviderRegistry.addLast(INLAID, inlaid -> (context, out, flag, components) -> {
            if (Boolean.TRUE.equals(inlaid)) {
                out.accept(Component.translatable("tooltip.pysift.sift_beacon.inlaid").withStyle(ChatFormatting.AQUA));
                out.accept(Component.translatable("tooltip.pysift.sift_beacon.aura").withStyle(ChatFormatting.GRAY));
            }
        });
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            if (server.getTickCount() % 10 != 0) {
                return;
            }
            for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                if (wearsBeacon(player) && player.level() instanceof ServerLevel level) {   // a soft ring of light around the wearer
                    double a = server.getTickCount() * 0.15;
                    level.sendParticles(ParticleTypes.END_ROD, player.getX() + Math.cos(a) * 1.2, player.getY() + 0.2,
                            player.getZ() + Math.sin(a) * 1.2, 1, 0, 0.05, 0, 0.0);
                }
                if (player.hasEffect(ModEffects.SOUL_DEPRIVATION) && inAura(player)) {
                    SoulBurn.cure(player);
                }
            }
        });
    }
}
