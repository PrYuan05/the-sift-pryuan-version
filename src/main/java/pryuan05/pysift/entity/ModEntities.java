package pryuan05.pysift.entity;

import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import pryuan05.pysift.PySift;
import pryuan05.pysift.entity.mob.*;

public class ModEntities {
    // 1. Friendly & Neutral Mobs
    public static final EntityType<BlubEntity> BLUB = register(
            "blub", BlubEntity::new, MobCategory.CREATURE, 0.8f, 0.8f
    );
    public static final EntityType<EchoGolemEntity> ECHO_GOLEM = register(
            "echo_golem", EchoGolemEntity::new, MobCategory.CREATURE, 1.2f, 1.8f
    );
    public static final EntityType<SingerEntity> SINGER = register(
            "singer", SingerEntity::new, MobCategory.CREATURE, 1.0f, 1.5f
    );
    public static final EntityType<NuzzleEntity> NUZZLE = register(
            "nuzzle", NuzzleEntity::new, MobCategory.CREATURE, 0.7f, 0.7f
    );
    public static final EntityType<LootkinEntity> LOOTKIN = register(
            "lootkin", LootkinEntity::new, MobCategory.CREATURE, 0.6f, 0.8f
    );

    // 2. Aerial & Ranged Mobs
    public static final EntityType<FuseflyEntity> FUSEFLY = register(
            "fusefly", FuseflyEntity::new, MobCategory.MONSTER, 0.6f, 0.6f
    );
    public static final EntityType<DartbackEntity> DARTBACK = register(
            "dartback", DartbackEntity::new, MobCategory.MONSTER, 0.9f, 1.2f
    );
    public static final EntityType<HurlerEntity> HURLER = register(
            "hurler", HurlerEntity::new, MobCategory.MONSTER, 1.0f, 1.6f
    );
    public static final EntityType<PollinatorEntity> POLLINATOR = register(
            "pollinator", PollinatorEntity::new, MobCategory.CREATURE, 0.7f, 0.7f
    );

    // 3. Hive & Minion Mobs
    public static final EntityType<NesterEntity> NESTER = register(
            "nester", NesterEntity::new, MobCategory.MONSTER, 1.2f, 1.4f
    );
    public static final EntityType<SeedlingEntity> SEEDLING = register(
            "seedling", SeedlingEntity::new, MobCategory.MONSTER, 0.5f, 0.5f
    );
    public static final EntityType<SproutEntity> SPROUT = register(
            "sprout", SproutEntity::new, MobCategory.MONSTER, 0.6f, 0.6f
    );

    // 4. Wild Predators & Guards
    public static final EntityType<StalkerEntity> STALKER = register(
            "stalker", StalkerEntity::new, MobCategory.MONSTER, 0.8f, 1.8f
    );
    public static final EntityType<ScavengerEntity> SCAVENGER = register(
            "scavenger", ScavengerEntity::new, MobCategory.MONSTER, 0.9f, 1.4f
    );
    public static final EntityType<SlabberEntity> SLABBER = register(
            "slabber", SlabberEntity::new, MobCategory.MONSTER, 1.2f, 1.0f
    );
    public static final EntityType<PrickleEntity> PRICKLE = register(
            "prickle", PrickleEntity::new, MobCategory.MONSTER, 0.8f, 0.8f
    );
    public static final EntityType<SentinelEntity> SENTINEL = register(
            "sentinel", SentinelEntity::new, MobCategory.MONSTER, 1.4f, 2.2f
    );
    public static final EntityType<TunerEntity> TUNER = register(
            "tuner", TunerEntity::new, MobCategory.MONSTER, 0.8f, 1.4f
    );
    public static final EntityType<BloombudEntity> BLOOMBUD = register(
            "bloombud", BloombudEntity::new, MobCategory.MONSTER, 0.8f, 1.2f
    );
    public static final EntityType<RoamrootEntity> ROAMROOT = register(
            "roamroot", RoamrootEntity::new, MobCategory.MONSTER, 0.9f, 1.1f
    );
    public static final EntityType<WobbleEntity> WOBBLE = register(
            "wobble", WobbleEntity::new, MobCategory.MONSTER, 0.7f, 1.0f
    );

    // 5. Boss Mobs
    public static final EntityType<HarmonizerEntity> HARMONIZER = register(
            "harmonizer", HarmonizerEntity::new, MobCategory.MONSTER, 2.0f, 2.8f
    );
    public static final EntityType<MonarchEntity> MONARCH = register(
            "monarch", MonarchEntity::new, MobCategory.MONSTER, 2.2f, 3.2f
    );
    public static final EntityType<SculkMonstrosityEntity> SCULK_MONSTROSITY = register(
            "sculk_monstrosity", SculkMonstrosityEntity::new, MobCategory.MONSTER, 2.5f, 3.5f
    );

    private static <T extends Entity> EntityType<T> register(
            String name, EntityType.EntityFactory<T> factory, MobCategory category, float width, float height
    ) {
        ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, PySift.id(name));
        EntityType<T> type = EntityType.Builder.of(factory, category)
                .sized(width, height)
                .build(key);
        return Registry.register(BuiltInRegistries.ENTITY_TYPE, key, type);
    }

    public static void registerModEntities() {
        PySift.LOGGER.info("Registering Entities and Default Attributes for {}", PySift.MOD_ID);

        FabricDefaultAttributeRegistry.register(BLUB, BlubEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(ECHO_GOLEM, EchoGolemEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(SINGER, SingerEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(NUZZLE, NuzzleEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(LOOTKIN, LootkinEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(FUSEFLY, FuseflyEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(DARTBACK, DartbackEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(HURLER, HurlerEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(POLLINATOR, PollinatorEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(NESTER, NesterEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(SEEDLING, SeedlingEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(SPROUT, SproutEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(STALKER, StalkerEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(SCAVENGER, ScavengerEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(SLABBER, SlabberEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(PRICKLE, PrickleEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(SENTINEL, SentinelEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(TUNER, TunerEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(BLOOMBUD, BloombudEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(ROAMROOT, RoamrootEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(WOBBLE, WobbleEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(HARMONIZER, HarmonizerEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(MONARCH, MonarchEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(SCULK_MONSTROSITY, SculkMonstrosityEntity.createAttributes());
    }
}
