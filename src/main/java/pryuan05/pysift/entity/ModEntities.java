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
import pryuan05.pysift.entity.projectile.DartEntity;
import pryuan05.pysift.entity.projectile.ThrownRockEntity;
import pryuan05.pysift.entity.projectile.SculkCubeEntity;
import pryuan05.pysift.entity.projectile.MonarchFeatherEntity;
import pryuan05.pysift.entity.projectile.TrapperNetEntity;
import pryuan05.pysift.entity.projectile.HunterJavelinEntity;
import pryuan05.pysift.entity.misc.SoulSnareEntity;

public class ModEntities {
    // 1. Friendly & Neutral Mobs
    public static final EntityType<BlubEntity> BLUB = register(
            "blub", BlubEntity::new, MobCategory.CREATURE, 0.8f, 0.8f
    );
    public static final EntityType<EchoGolemEntity> ECHO_GOLEM = register(
            "echo_golem", EchoGolemEntity::new, MobCategory.CREATURE, 1.4f, 2.6f
    );
    public static final EntityType<SingerEntity> SINGER = register(
            "singer", SingerEntity::new, MobCategory.CREATURE, 1.0f, 2.7f
    );
    public static final EntityType<NuzzleEntity> NUZZLE = register(
            "nuzzle", NuzzleEntity::new, MobCategory.CREATURE, 1.0f, 1.3f
    );
    public static final EntityType<LootkinEntity> LOOTKIN = register(
            "lootkin", LootkinEntity::new, MobCategory.CREATURE, 0.6f, 0.8f
    );

    // 2. Aerial & Ranged Mobs
    public static final EntityType<FuseflyEntity> FUSEFLY = register(
            "fusefly", FuseflyEntity::new, MobCategory.MONSTER, 0.6f, 1.0f
    );
    public static final EntityType<DartbackEntity> DARTBACK = register(
            "dartback", DartbackEntity::new, MobCategory.MONSTER, 0.6f, 0.53f
    );
    public static final EntityType<HurlerEntity> HURLER = register(
            "hurler", HurlerEntity::new, MobCategory.MONSTER, 1.0f, 1.0f
    );
    public static final EntityType<PollinatorEntity> POLLINATOR = register(
            "pollinator", PollinatorEntity::new, MobCategory.CREATURE, 0.8f, 1.5f
    );

    // 3. Hive & Minion Mobs
    public static final EntityType<NesterEntity> NESTER = register(
            "nester", NesterEntity::new, MobCategory.MONSTER, 0.6f, 1.08f
    );
    public static final EntityType<SeedlingEntity> SEEDLING = register(
            "seedling", SeedlingEntity::new, MobCategory.MONSTER, 0.6f, 0.8f
    );
    public static final EntityType<SproutEntity> SPROUT = register(
            "sprout", SproutEntity::new, MobCategory.MONSTER, 0.7f, 1.6f
    );

    // 4. Wild Predators & Guards
    public static final EntityType<StalkerEntity> STALKER = register(
            "stalker", StalkerEntity::new, MobCategory.MONSTER, 0.8f, 1.3f
    );
    public static final EntityType<ScavengerEntity> SCAVENGER = register(
            "scavenger", ScavengerEntity::new, MobCategory.MONSTER, 1.0f, 1.6f
    );
    /** Monarch 麾下：遠程標槍手（模型約 2.1 格高）。 */
    public static final EntityType<HunterEntity> HUNTER = register(
            "hunter", HunterEntity::new, MobCategory.MONSTER, 0.8f, 2.1f
    );
    /** Monarch 麾下：佈陷阱、丟網（模型約 1.75 格高，微駝）。 */
    public static final EntityType<TrapperEntity> TRAPPER = register(
            "trapper", TrapperEntity::new, MobCategory.MONSTER, 0.9f, 1.75f
    );
    public static final EntityType<SlabberEntity> SLABBER = register(
            "slabber", SlabberEntity::new, MobCategory.CREATURE, 1.4f, 1.7f
    );
    public static final EntityType<PrickleEntity> PRICKLE = register(
            "prickle", PrickleEntity::new, MobCategory.MONSTER, 0.6f, 0.8f
    );
    public static final EntityType<SentinelEntity> SENTINEL = register(
            "sentinel", SentinelEntity::new, MobCategory.MONSTER, 0.6f, 0.89f   // 模型原尺寸；SCALE 2.02 → 1.2 × 1.8 格
    );
    public static final EntityType<TunerEntity> TUNER = register(
            "tuner", TunerEntity::new, MobCategory.MONSTER, 0.7f, 1.3f
    );
    public static final EntityType<BloombudEntity> BLOOMBUD = register(
            "bloombud", BloombudEntity::new, MobCategory.MONSTER, 0.9f, 2.4f
    );
    public static final EntityType<RoamrootEntity> ROAMROOT = register(
            "roamroot", RoamrootEntity::new, MobCategory.MONSTER, 1.1f, 2.4f
    );
    public static final EntityType<WobbleEntity> WOBBLE = register(
            "wobble", WobbleEntity::new, MobCategory.MONSTER, 0.8f, 0.85f
    );

    // 5. Boss Mobs
    public static final EntityType<HarmonizerEntity> HARMONIZER = register(
            "harmonizer", HarmonizerEntity::new, MobCategory.MONSTER, 2.4f, 3.8f
    );
    public static final EntityType<MonarchEntity> MONARCH = register(
            "monarch", MonarchEntity::new, MobCategory.MONSTER, 1.2f, 3.6f
    );
    public static final EntityType<SculkMonstrosityEntity> SCULK_MONSTROSITY = register(
            "sculk_monstrosity", SculkMonstrosityEntity::new, MobCategory.MONSTER, 3.2f, 4.25f
    );

    // 5. Projectiles（外觀沿用原版渲染器）
    public static final EntityType<DartEntity> DART = register(
            "dart", DartEntity::new, MobCategory.MISC, 0.5f, 0.5f
    );
    public static final EntityType<ThrownRockEntity> THROWN_ROCK = register(
            "thrown_rock", ThrownRockEntity::new, MobCategory.MISC, 0.4f, 0.4f
    );
    public static final EntityType<SculkCubeEntity> SCULK_CUBE = register(
            "sculk_cube", SculkCubeEntity::new, MobCategory.MISC, 0.8f, 0.8f
    );
    public static final EntityType<MonarchFeatherEntity> MONARCH_FEATHER = register(
            "monarch_feather", MonarchFeatherEntity::new, MobCategory.MISC, 0.4f, 0.4f
    );
    public static final EntityType<HunterJavelinEntity> HUNTER_JAVELIN = register(
            "hunter_javelin", HunterJavelinEntity::new, MobCategory.MISC, 0.5f, 0.5f
    );
    public static final EntityType<TrapperNetEntity> TRAPPER_NET = register(
            "trapper_net", TrapperNetEntity::new, MobCategory.MISC, 0.5f, 0.5f
    );
    public static final EntityType<SoulSnareEntity> SOUL_SNARE = register(
            "soul_snare", SoulSnareEntity::new, MobCategory.MISC, 0.9f, 0.2f
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
        FabricDefaultAttributeRegistry.register(HUNTER, HunterEntity.createAttributes());
        FabricDefaultAttributeRegistry.register(TRAPPER, TrapperEntity.createAttributes());
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
