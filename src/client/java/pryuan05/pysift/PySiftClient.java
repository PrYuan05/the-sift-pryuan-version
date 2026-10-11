package pryuan05.pysift;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import pryuan05.pysift.client.PysiftUniversalGeoRenderer;
import pryuan05.pysift.entity.ModEntities;

public class PySiftClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        EntityRendererRegistry.register(ModEntities.BLUB, context -> new PysiftUniversalGeoRenderer<>(context, "blub"));
        EntityRendererRegistry.register(ModEntities.ECHO_GOLEM, context -> new PysiftUniversalGeoRenderer<>(context, "echo_golem"));
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
        EntityRendererRegistry.register(ModEntities.SLABBER, context -> new PysiftUniversalGeoRenderer<>(context, "slabber"));
        EntityRendererRegistry.register(ModEntities.PRICKLE, context -> new PysiftUniversalGeoRenderer<>(context, "prickle"));
        EntityRendererRegistry.register(ModEntities.SENTINEL, context -> new PysiftUniversalGeoRenderer<>(context, "sentinel"));
        EntityRendererRegistry.register(ModEntities.TUNER, context -> new PysiftUniversalGeoRenderer<>(context, "tuner"));
        EntityRendererRegistry.register(ModEntities.BLOOMBUD, context -> new PysiftUniversalGeoRenderer<>(context, "bloombud"));
        EntityRendererRegistry.register(ModEntities.ROAMROOT, context -> new PysiftUniversalGeoRenderer<>(context, "roamroot"));
        EntityRendererRegistry.register(ModEntities.WOBBLE, context -> new PysiftUniversalGeoRenderer<>(context, "wobble"));
        EntityRendererRegistry.register(ModEntities.HARMONIZER, context -> new PysiftUniversalGeoRenderer<>(context, "harmonizer"));
        EntityRendererRegistry.register(ModEntities.MONARCH, context -> new PysiftUniversalGeoRenderer<>(context, "monarch"));
        EntityRendererRegistry.register(ModEntities.SCULK_MONSTROSITY, context -> new PysiftUniversalGeoRenderer<>(context, "sculk_monstrosity"));
    }
}
