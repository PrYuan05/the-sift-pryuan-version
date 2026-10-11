package pryuan05.pysift;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import pryuan05.pysift.client.render.PysiftMobRenderer;
import pryuan05.pysift.entity.ModEntities;

public class PySiftClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        EntityRendererRegistry.register(ModEntities.BLUB, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.ECHO_GOLEM, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.SINGER, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.NUZZLE, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.LOOTKIN, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.FUSEFLY, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.DARTBACK, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.HURLER, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.POLLINATOR, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.NESTER, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.SEEDLING, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.SPROUT, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.STALKER, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.SCAVENGER, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.SLABBER, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.PRICKLE, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.SENTINEL, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.TUNER, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.BLOOMBUD, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.ROAMROOT, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.WOBBLE, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.HARMONIZER, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.MONARCH, PysiftMobRenderer::new);
        EntityRendererRegistry.register(ModEntities.SCULK_MONSTROSITY, PysiftMobRenderer::new);
    }
}
