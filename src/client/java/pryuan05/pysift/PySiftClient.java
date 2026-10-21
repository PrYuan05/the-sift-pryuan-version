package pryuan05.pysift;

import pryuan05.pysift.client.VanillaGlowLayer;
import pryuan05.pysift.entity.mob.SculkMonstrosityEntity;
import pryuan05.pysift.entity.mob.SentinelEntity;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.BlockEntityRendererRegistry;
import pryuan05.pysift.block.entity.ModBlockEntities;
import pryuan05.pysift.client.render.SiftPortalBlockEntityRenderer;
import pryuan05.pysift.client.render.SiftArrowRenderer;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.NoopRenderer;
import net.minecraft.client.renderer.entity.ThrownItemRenderer;
import net.minecraft.world.entity.Entity;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import pryuan05.pysift.client.PysiftUniversalGeoRenderer;
import pryuan05.pysift.client.BlubRenderer;
import pryuan05.pysift.client.EchoGolemRenderer;
import pryuan05.pysift.client.MonarchRenderer;
import pryuan05.pysift.client.SiftClientVisuals;
import pryuan05.pysift.client.PysiftTooltips;
import pryuan05.pysift.client.SlabberRenderer;
import pryuan05.pysift.client.SiftPortalTransition;
import pryuan05.pysift.client.SoulDeprivationVision;
import pryuan05.pysift.client.SoulWillowWoodClient;
import pryuan05.pysift.client.particle.SoulParticlesClient;
import pryuan05.pysift.client.SoulFireShoulderLayer;
import pryuan05.pysift.entity.ModEntities;

public class PySiftClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        SiftClientVisuals.register();
        PysiftTooltips.register();   // 物品說明按住 Shift 才展開
        SoulDeprivationVision.register();   // 靈魂剝奪：伏聆色調的視野後製
        SiftPortalTransition.register();     // 篩靈界傳送門的過場動畫
        // 篩靈界傳送門：大面積珠光流光 + 邊緣破曉聖光
        BlockEntityRendererRegistry.register(ModBlockEntities.SIFT_PORTAL, context -> new SiftPortalBlockEntityRenderer());
        SoulWillowWoodClient.register();
        SoulParticlesClient.register();
        // 投射物：飛鏢用原版箭矢、碎石用鵝卵石物品的渲染器
        EntityRendererRegistry.register(ModEntities.DART, context -> new SiftArrowRenderer<>(context, "sift_dart", 1.0f));
        EntityRendererRegistry.register(ModEntities.HUNTER_JAVELIN, context -> new SiftArrowRenderer<>(context, "hunter_javelin", 2.0f));
        EntityRendererRegistry.register(ModEntities.THROWN_ROCK, ThrownItemRenderer::new);
        // Boss 招式的投射物：放大的幽匿塊（滾動方塊）、發光羽毛
        EntityRendererRegistry.register(ModEntities.SCULK_CUBE, context -> new PysiftUniversalGeoRenderer<>(context, "sculk_cube"));
        EntityRendererRegistry.register(ModEntities.MONARCH_FEATHER, context -> new ThrownItemRenderer<>(context, 1.5f, true));
        EntityRendererRegistry.register(ModEntities.TRAPPER_NET, context -> new ThrownItemRenderer<>(context, 1.6f, false));
        EntityRendererRegistry.register(ModEntities.SOUL_SNARE, NoopRenderer::new);   // 陷阱沒有模型，只有偶爾的靈魂微光
        EntityRendererRegistry.register(ModEntities.HUNTER, context -> new PysiftUniversalGeoRenderer<>(context, "hunter"));
        EntityRendererRegistry.register(ModEntities.TRAPPER, context -> new PysiftUniversalGeoRenderer<>(context, "trapper"));
        EntityRendererRegistry.register(ModEntities.BLUB, BlubRenderer::new);
        EntityRendererRegistry.register(ModEntities.ECHO_GOLEM, EchoGolemRenderer::new);
        EntityRendererRegistry.register(ModEntities.SINGER, context -> new PysiftUniversalGeoRenderer<>(context, "singer"));
        EntityRendererRegistry.register(ModEntities.NUZZLE, context -> new PysiftUniversalGeoRenderer<>(context, "nuzzle"));
        EntityRendererRegistry.register(ModEntities.LOOTKIN, context -> new PysiftUniversalGeoRenderer<>(context, "lootkin"));
        EntityRendererRegistry.register(ModEntities.FUSEFLY, context -> new PysiftUniversalGeoRenderer<>(context, "fusefly"));
        EntityRendererRegistry.register(ModEntities.DARTBACK, context -> new PysiftUniversalGeoRenderer<>(context, "dartback"));
        EntityRendererRegistry.register(ModEntities.HURLER, context -> new PysiftUniversalGeoRenderer<>(context, "hurler"));
        EntityRendererRegistry.register(ModEntities.POLLINATOR, context -> new PysiftUniversalGeoRenderer<>(context, "pollinator"));
        EntityRendererRegistry.register(ModEntities.NESTER, context -> new PysiftUniversalGeoRenderer<>(context, "nester"));
        EntityRendererRegistry.register(ModEntities.SEEDLING, context -> new PysiftUniversalGeoRenderer<>(context, "seedling"));
        EntityRendererRegistry.register(ModEntities.SPROUT, context -> new PysiftUniversalGeoRenderer<>(context, "sprout"));
        EntityRendererRegistry.register(ModEntities.STALKER, context -> new PysiftUniversalGeoRenderer<>(context, "stalker"));
        EntityRendererRegistry.register(ModEntities.SCAVENGER, context -> new PysiftUniversalGeoRenderer<>(context, "scavenger"));
        EntityRendererRegistry.register(ModEntities.SLABBER, SlabberRenderer::new);
        EntityRendererRegistry.register(ModEntities.PRICKLE, context -> new PysiftUniversalGeoRenderer<>(context, "prickle"));
        // Sentinel 的模型只有 0.89 格高，放大由實體的 SCALE 屬性負責（SentinelEntity.SCALE），和其他放大的生物一樣；
        // 先前用 renderer.withScale 放大時整隻畫成全黑。
        EntityRendererRegistry.register(ModEntities.SENTINEL, context -> new PysiftUniversalGeoRenderer<>(context, "sentinel"));
        EntityRendererRegistry.register(ModEntities.TUNER, context -> new PysiftUniversalGeoRenderer<>(context, "tuner"));
        EntityRendererRegistry.register(ModEntities.BLOOMBUD, context -> new PysiftUniversalGeoRenderer<>(context, "bloombud"));
        EntityRendererRegistry.register(ModEntities.ROAMROOT, context -> new PysiftUniversalGeoRenderer<>(context, "roamroot"));
        EntityRendererRegistry.register(ModEntities.WOBBLE, context -> new PysiftUniversalGeoRenderer<>(context, "wobble"));
        EntityRendererRegistry.register(ModEntities.HARMONIZER, context -> new PysiftUniversalGeoRenderer<>(context, "harmonizer"));
        EntityRendererRegistry.register(ModEntities.MONARCH, MonarchRenderer::new);   // 分身半透明
        EntityRendererRegistry.register(ModEntities.SCULK_MONSTROSITY, context -> new PysiftUniversalGeoRenderer<SculkMonstrosityEntity>(context, "sculk_monstrosity")
                .withRenderLayer(VanillaGlowLayer::new)     // 眼睛、青點：sculk_monstrosity_glowmask.png
                .withRenderLayer(renderer -> new SoulFireShoulderLayer<>(context, renderer, 1.25f,
                        "shoulder_flame_right", "shoulder_flame_left")));   // 肩上：原版靈魂火方塊（原版貼圖與動畫）
    }

    /** DartEntity 繼承 Arrow，原版箭矢渲染器可以直接畫它；只是泛型上需要轉型。 */
    @SuppressWarnings("unchecked")
    private static <T extends Entity> EntityRenderer<T, ?> castRenderer(EntityRenderer<?, ?> renderer) {
        return (EntityRenderer<T, ?>) renderer;
    }
}
