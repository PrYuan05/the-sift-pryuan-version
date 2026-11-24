package pryuan05.pysift.entity;

import com.mojang.serialization.Codec;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentSyncPredicate;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.biome.Biome;
import pryuan05.pysift.PySift;

import java.util.Set;

/**
 * 動物的氣候變體（使用者，2026-11-24）：熱帶＝毛較少、身上有明顯的花、顏色較鮮豔；寒帶＝毛較多、顏色較冷。
 * <ul>
 *   <li>出生（第一次載入世界）時依所在生態域的溫度決定，存在實體上（Fabric 附加資料，會存檔、會同步給用戶端）。</li>
 *   <li>隙浮：溫度 ≥ 1.4 是熱帶（琥珀沙丘、赤紅峽谷、靈魂火山口、靈液深淵），≤ 0.7 是寒帶（紫晶深板岩區、
 *       枯萎窪地），其餘為溫帶（靈魂柳林、搖籃曲山丘、紅區洞穴、迴音穹窟）。其他維度用原版溫度：≥ 0.95 熱帶，≤ 0.3 寒帶。</li>
 *   <li>貼圖：textures/entity/&lt;生物&gt;_tropical.png、_cold.png（PysiftUniversalGeoModel 依變體換貼圖）。</li>
 *   <li>只有 {@link #MOBS} 裡的生物有變體；每做完一種生物的貼圖才把它加進來，不會出現缺貼圖的紫黑方塊。</li>
 * </ul>
 */
public final class ClimateVariant {
    public static final int NORMAL = 0, TROPICAL = 1, COLD = 2;

    public static final AttachmentType<Integer> TYPE = AttachmentRegistry.create(PySift.id("climate_variant"),
            builder -> builder.persistent(Codec.INT).syncWith(ByteBufCodecs.VAR_INT, AttachmentSyncPredicate.all()));

    /** 有氣候變體的生物（實體 ID 的路徑）。 */
    public static final Set<String> MOBS = Set.of("nuzzle", "lootkin", "slabber", "prickle", "dartback", "fusefly", "wobble", "nester", "pollinator", "seedling", "sprout", "sentinel");
    /** 熱帶、寒帶另外有模型（geckolib/models/entity/&lt;生物&gt;_tropical.geo.json、_cold.geo.json，骨骼與原模型相同）的生物。 */
    public static final Set<String> VARIANT_MODELS = Set.of("nuzzle", "lootkin", "slabber", "prickle", "dartback", "fusefly", "wobble", "nester", "pollinator", "seedling", "sprout", "sentinel");

    private ClimateVariant() {
    }

    public static String suffix(int variant) {
        return switch (variant) {
            case TROPICAL -> "_tropical";
            case COLD -> "_cold";
            default -> "";
        };
    }

    public static boolean hasVariants(Entity entity) {
        var key = BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType());
        return key.getNamespace().equals(PySift.MOD_ID) && MOBS.contains(key.getPath());
    }

    public static int of(Entity entity) {
        return entity.getAttachedOrElse(TYPE, NORMAL);
    }

    static int pick(ServerLevel level, BlockPos pos) {
        Holder<Biome> biome = level.getBiome(pos);
        float t = biome.value().getBaseTemperature();
        boolean sift = biome.unwrapKey().map(k -> k.identifier().getNamespace().equals(PySift.MOD_ID)).orElse(false);
        if (sift) {
            return t >= 1.4F ? TROPICAL : t <= 0.7F ? COLD : NORMAL;
        }
        return t >= 0.95F ? TROPICAL : t <= 0.3F ? COLD : NORMAL;
    }

    public static void register() {
        ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
            if (!entity.hasAttached(TYPE) && hasVariants(entity)) {
                entity.setAttached(TYPE, pick(level, entity.blockPosition()));
            }
        });
    }
}
