package pryuan05.pysift.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.ModBlocks;
import pryuan05.pysift.block.ModVegetation;
import pryuan05.pysift.block.SoulWillowWood;
import pryuan05.pysift.entity.BossMechanics;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.fluid.ModFluids;

import java.util.Optional;

/**
 * 專屬 Boss 競技場特徵（Specialized Boss Arenas）：
 * 針對 The Sift 每一隻主要 Boss 量身打造專屬的宏偉地景神殿與戰鬥場域：
 * <ul>
 *   <li><b>Monarch（沙皇 / 帝王）</b>：帝王日晷陵台（Imperial Sunken Ziggurat）——三層下沉式階梯鬥技場、十字日晷大道、中央高聳帝王寶座祭壇與四座宏偉對角方尖碑。</li>
 *   <li><b>Harmonizer（調和者）</b>：靈液環湖琴台（Resonant Spirit Lake Pavilion）——外層環繞深邃靈液湖泊、同心音律共振石環、四座跨湖聖橋、16 根風琴式起伏音律石柱與垂簾柳葉。</li>
 *   <li><b>Sculk Monstrosity（幽匿巨獸）</b>：深淵泰坦封印囚窟（The Abyssal Titan Crucible）——凹陷深谷鬥技場、四座拔高 10 格的泰坦禁錮堡壘、地下脈動的青藍靈魂晶塊能量導管與破裂中央封印。</li>
 * </ul>
 */
public record BossArenaFeature(
        String arenaType,
        EntityType<?> boss,
        int radius,
        Holder<BlockStateProvider> floor,
        Holder<BlockStateProvider> wall,
        Holder<BlockStateProvider> pillar,
        int pillarHeight,
        int pillarCount,
        Optional<Holder<BlockStateProvider>> moat,
        int moatWidth
) implements Feature {

    private static final int MAX_FOOTING = 16;
    private static final int CLEAR_HEIGHT = 20;

    public static final MapCodec<BossArenaFeature> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            Codec.STRING.optionalFieldOf("arena_type", "").forGetter(BossArenaFeature::arenaType),
            BuiltInRegistries.ENTITY_TYPE.byNameCodec().fieldOf("boss").forGetter(BossArenaFeature::boss),
            Codec.intRange(6, 22).fieldOf("radius").forGetter(BossArenaFeature::radius),
            BlockStateProvider.CODEC.fieldOf("floor").forGetter(BossArenaFeature::floor),
            BlockStateProvider.CODEC.fieldOf("wall").forGetter(BossArenaFeature::wall),
            BlockStateProvider.CODEC.fieldOf("pillar").forGetter(BossArenaFeature::pillar),
            Codec.intRange(2, 16).optionalFieldOf("pillar_height", 6).forGetter(BossArenaFeature::pillarHeight),
            Codec.intRange(0, 24).optionalFieldOf("pillar_count", 8).forGetter(BossArenaFeature::pillarCount),
            BlockStateProvider.CODEC.optionalFieldOf("moat").forGetter(BossArenaFeature::moat),
            Codec.intRange(0, 8).optionalFieldOf("moat_width", 0).forGetter(BossArenaFeature::moatWidth)
    ).apply(instance, BossArenaFeature::new));

    public static final MapCodec<BossArenaFeature> TYPE = Registry.register(
            BuiltInRegistries.FEATURE_TYPE, PySift.id("boss_arena"), CODEC);

    @Override
    public MapCodec<BossArenaFeature> codec() {
        return CODEC;
    }

    private static Block getBlock(String name) {
        Block b = ModBlocks.BY_NAME.get(name);
        if (b != null) {
            return b;
        }
        return BuiltInRegistries.BLOCK.getValue(PySift.id(name));
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        BlockPos center = origin.below();
        if (boss.create(level.getLevel(), EntitySpawnReason.CHUNK_GENERATION) instanceof Mob mob) {
            String type = arenaType;
            if (type == null || type.isEmpty()) {
                if (boss == ModEntities.MONARCH) {
                    type = "monarch";
                } else if (boss == ModEntities.HARMONIZER) {
                    type = "harmonizer";
                } else if (boss == ModEntities.SCULK_MONSTROSITY) {
                    type = "sculk_monstrosity";
                }
            }

            switch (type) {
                case "monarch" -> buildMonarchArena(level, random, center, mob);
                case "harmonizer" -> buildHarmonizerArena(level, random, center, mob);
                case "sculk_monstrosity" -> buildSculkMonstrosityArena(level, random, center, mob);
                default -> buildGenericArena(level, random, center, mob);
            }

            mob.setYRot(random.nextFloat() * 360);
            BossMechanics.setArena(mob, center.above());
            mob.finalizeSpawn(level, level.getCurrentDifficultyAt(center), EntitySpawnReason.CHUNK_GENERATION, null);
            level.addFreshEntityWithPassengers(mob);
            BossArenaSavedData.record(level.getLevel(), type, BuiltInRegistries.ENTITY_TYPE.getKey(boss).toString(), center);
            return true;
        }
        return false;
    }

    public static boolean generateArenaDirectly(net.minecraft.server.level.ServerLevel level, String type, BlockPos center) {
        EntityType<?> bossType = switch (type.toLowerCase()) {
            case "monarch" -> ModEntities.MONARCH;
            case "harmonizer" -> ModEntities.HARMONIZER;
            case "sculk_monstrosity" -> ModEntities.SCULK_MONSTROSITY;
            default -> null;
        };
        if (bossType == null) {
            return false;
        }
        BossArenaFeature feature = new BossArenaFeature(
                type.toLowerCase(), bossType, 16,
                BlockStateProvider.holderOf(Blocks.STONE),
                BlockStateProvider.holderOf(Blocks.STONE),
                BlockStateProvider.holderOf(Blocks.STONE),
                6, 8, Optional.empty(), 0
        );
        return feature.place(level, level.getChunkSource().getGenerator(), level.getRandom(), center.above());
    }

    // =========================================================================================================
    // 1. Monarch: 帝王日晷陵台（Imperial Sunken Ziggurat & Sun Altar）
    // =========================================================================================================
    private void buildMonarchArena(WorldGenLevel level, RandomSource random, BlockPos center, Mob bossMob) {
        Block sandstone = getBlock("bleached_sandstone");
        Block sandstoneBricks = getBlock("bleached_sandstone_bricks");
        Block chiseledBricks = getBlock("chiseled_bleached_sandstone_bricks");
        Block brickWall = getBlock("bleached_sandstone_brick_wall");
        Block cracked = getBlock("cracked_sandstone");
        Block amberSand = getBlock("amber_sand");
        Block glyph = getBlock("glyph_block");

        int r = Math.min(radius, 16);
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();

        // 1. 清空上方空間 & 往下填實地基
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                double d = Math.sqrt(dx * dx + dz * dz);
                if (d > r + 0.5) continue;
                int x = center.getX() + dx, z = center.getZ() + dz;
                for (int y = 1; y <= CLEAR_HEIGHT; y++) {
                    setBlock(level, pos.set(x, center.getY() + y, z), Blocks.AIR.defaultBlockState());
                }
                fillDown(level, random, pos.set(x, center.getY() - 1, z), sandstone);
            }
        }

        // 2. 三層階梯式下沉露天鬥技場 (Stepped Sunken Ziggurat)
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                double d = Math.sqrt(dx * dx + dz * dz);
                if (d > r + 0.5) continue;
                int x = center.getX() + dx, z = center.getZ() + dz;

                boolean isRay = Math.abs(dx) <= 1 || Math.abs(dz) <= 1; // 十字軸線日晷大道

                if (d > 12.5) {
                    // 外層高台 (Y = center.Y + 1)
                    BlockState st = (isRay || random.nextFloat() < 0.7f) ? sandstoneBricks.defaultBlockState() : cracked.defaultBlockState();
                    setBlock(level, pos.set(x, center.getY() + 1, z), st);
                    // 外圍護欄矮牆（十字路口留出缺口當入口）
                    if (d > 15.0 && !isRay) {
                        setBlock(level, pos.set(x, center.getY() + 2, z), brickWall.defaultBlockState());
                    }
                } else if (d > 7.5) {
                    // 中層下沉環形沙槽 (Y = center.Y)
                    if (isRay) {
                        setBlock(level, pos.set(x, center.getY(), z), chiseledBricks.defaultBlockState());
                    } else {
                        BlockState st = random.nextFloat() < 0.6f ? amberSand.defaultBlockState() : cracked.defaultBlockState();
                        setBlock(level, pos.set(x, center.getY(), z), st);
                    }
                } else {
                    // 內圈底層鬥技場 (Y = center.Y - 1)
                    BlockState st = isRay ? chiseledBricks.defaultBlockState() : sandstoneBricks.defaultBlockState();
                    setBlock(level, pos.set(x, center.getY() - 1, z), st);
                }
            }
        }

        // 3. 中央高聳的日晷帝王祭壇 (Raised 7x7 Sun Throne Dais)
        for (int dx = -3; dx <= 3; dx++) {
            for (int dz = -3; dz <= 3; dz++) {
                int x = center.getX() + dx, z = center.getZ() + dz;
                setBlock(level, pos.set(x, center.getY() + 1, z), chiseledBricks.defaultBlockState());
                setBlock(level, pos.set(x, center.getY(), z), sandstoneBricks.defaultBlockState());
            }
        }

        // 祭壇四面踏階
        for (int step = -2; step <= 2; step++) {
            setBlock(level, pos.set(center.getX() + step, center.getY(), center.getZ() - 4), sandstoneBricks.defaultBlockState());
            setBlock(level, pos.set(center.getX() + step, center.getY(), center.getZ() + 4), sandstoneBricks.defaultBlockState());
            setBlock(level, pos.set(center.getX() - 4, center.getY(), center.getZ() + step), sandstoneBricks.defaultBlockState());
            setBlock(level, pos.set(center.getX() + 4, center.getY(), center.getZ() + step), sandstoneBricks.defaultBlockState());
        }

        // 4. 祭壇後方的帝王石座 (Imperial Sandstone Throne)
        int tx = center.getX(), tz = center.getZ() + 3, ty = center.getY() + 2;
        setBlock(level, pos.set(tx - 1, ty, tz), brickWall.defaultBlockState());
        setBlock(level, pos.set(tx - 1, ty + 1, tz), brickWall.defaultBlockState());
        setBlock(level, pos.set(tx + 1, ty, tz), brickWall.defaultBlockState());
        setBlock(level, pos.set(tx + 1, ty + 1, tz), brickWall.defaultBlockState());
        setBlock(level, pos.set(tx, ty, tz), chiseledBricks.defaultBlockState());
        setBlock(level, pos.set(tx, ty + 1, tz), chiseledBricks.defaultBlockState());
        setBlock(level, pos.set(tx, ty + 2, tz), glyph.defaultBlockState());

        // 5. 四座宏偉的對角古埃及日晷方尖碑 (4 Corner Obelisks)
        int[][] obelisks = {{-11, -11}, {11, -11}, {-11, 11}, {11, 11}};
        for (int[] ob : obelisks) {
            int ox = center.getX() + ob[0], oz = center.getZ() + ob[1], oy = center.getY() + 2;
            for (int odx = -1; odx <= 1; odx++) {
                for (int odz = -1; odz <= 1; odz++) {
                    setBlock(level, pos.set(ox + odx, oy, oz + odz), chiseledBricks.defaultBlockState());
                }
            }
            for (int h = 1; h <= 8; h++) {
                setBlock(level, pos.set(ox, oy + h, oz), chiseledBricks.defaultBlockState());
                setBlock(level, pos.set(ox + 1, oy + h, oz), brickWall.defaultBlockState());
                setBlock(level, pos.set(ox - 1, oy + h, oz), brickWall.defaultBlockState());
                setBlock(level, pos.set(ox, oy + h, oz + 1), brickWall.defaultBlockState());
                setBlock(level, pos.set(ox, oy + h, oz - 1), brickWall.defaultBlockState());
            }
            setBlock(level, pos.set(ox, oy + 9, oz), glyph.defaultBlockState());
        }

        // 6. 外圍殘破柱廊 (Ruined Colonnade)
        for (int i = 0; i < 12; i++) {
            float angle = Mth.TWO_PI * i / 12.0f;
            int px = center.getX() + Math.round(Mth.cos(angle) * 14.5f);
            int pz = center.getZ() + Math.round(Mth.sin(angle) * 14.5f);
            if (Math.abs(px - center.getX()) <= 2 || Math.abs(pz - center.getZ()) <= 2) continue;
            int ph = 3 + random.nextInt(4);
            for (int h = 1; h <= ph; h++) {
                setBlock(level, pos.set(px, center.getY() + 1 + h, pz), chiseledBricks.defaultBlockState());
            }
        }

        bossMob.snapTo(center.getX() + 0.5, center.getY() + 2, center.getZ() + 0.5);
    }

    // =========================================================================================================
    // 2. Harmonizer: 靈液環湖琴台（The Resonant Spirit Lake Pavilion）
    // =========================================================================================================
    private void buildHarmonizerArena(WorldGenLevel level, RandomSource random, BlockPos center, Mob bossMob) {
        Block bricks = getBlock("abyssal_strata_bricks");
        Block chiseled = getBlock("chiseled_abyssal_strata_bricks");
        Block wall = getBlock("abyssal_strata_brick_wall");
        Block liquid = ModFluids.SPIRIT_LIQUID_BLOCK;
        Block leaves = ModVegetation.SOUL_WILLOW_LEAVES;
        Block glowingLeaves = ModVegetation.GLOWING_SOUL_WILLOW_LEAVES;
        Block vine = ModVegetation.SOUL_WILLOW_VINE;
        Block glowingVine = ModVegetation.GLOWING_SOUL_WILLOW_VINE;

        int r = Math.min(radius + 2, 17);
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();

        // 1. 清空空間
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                double d = Math.sqrt(dx * dx + dz * dz);
                if (d > r + 0.5) continue;
                int x = center.getX() + dx, z = center.getZ() + dz;
                for (int y = 1; y <= CLEAR_HEIGHT; y++) {
                    setBlock(level, pos.set(x, center.getY() + y, z), Blocks.AIR.defaultBlockState());
                }
            }
        }

        // 2. 同心音律水環與跨湖聖橋 (Concentric Acoustic Liquid Rings & Bridges)
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                double d = Math.sqrt(dx * dx + dz * dz);
                if (d > r + 0.5) continue;
                int x = center.getX() + dx, z = center.getZ() + dz;
                boolean isBridge = Math.abs(dx) <= 1 || Math.abs(dz) <= 1;

                if (d > 13.0) {
                    // 外圍靈液湖泊 (深 3 格)
                    if (isBridge) {
                        setBlock(level, pos.set(x, center.getY(), z), bricks.defaultBlockState());
                        setBlock(level, pos.set(x, center.getY() + 1, z), wall.defaultBlockState());
                        fillDown(level, random, pos.set(x, center.getY() - 1, z), bricks);
                    } else {
                        setBlock(level, pos.set(x, center.getY(), z), liquid.defaultBlockState());
                        setBlock(level, pos.set(x, center.getY() - 1, z), liquid.defaultBlockState());
                        setBlock(level, pos.set(x, center.getY() - 2, z), liquid.defaultBlockState());
                        fillDown(level, random, pos.set(x, center.getY() - 3, z), bricks);
                    }
                } else if (d > 8.0) {
                    // 音律共振石磚外環
                    BlockState st = (d > 10.0 && d < 11.5) ? chiseled.defaultBlockState() : bricks.defaultBlockState();
                    setBlock(level, pos.set(x, center.getY(), z), st);
                    fillDown(level, random, pos.set(x, center.getY() - 1, z), bricks);
                } else if (d > 4.5) {
                    // 內層水波溝槽
                    if (isBridge) {
                        setBlock(level, pos.set(x, center.getY(), z), chiseled.defaultBlockState());
                        fillDown(level, random, pos.set(x, center.getY() - 1, z), bricks);
                    } else {
                        setBlock(level, pos.set(x, center.getY(), z), liquid.defaultBlockState());
                        fillDown(level, random, pos.set(x, center.getY() - 1, z), bricks);
                    }
                } else {
                    // 中央共振琴台 (加高一層)
                    setBlock(level, pos.set(x, center.getY() + 1, z), chiseled.defaultBlockState());
                    setBlock(level, pos.set(x, center.getY(), z), bricks.defaultBlockState());
                    fillDown(level, random, pos.set(x, center.getY() - 1, z), bricks);
                }
            }
        }

        // 3. 風琴式音律石柱群與柳藤涼棚 (Organ Pipe Chime Spires & Willow Pergolas)
        for (int i = 0; i < 16; i++) {
            float angle = Mth.TWO_PI * i / 16.0f;
            int px = center.getX() + Math.round(Mth.cos(angle) * 10.5f);
            int pz = center.getZ() + Math.round(Mth.sin(angle) * 10.5f);
            if (Math.abs(px - center.getX()) <= 1 || Math.abs(pz - center.getZ()) <= 1) continue;

            int h = 4 + Math.round(3.5f * Mth.sin(angle * 2.0f) + 1.0f);
            for (int y = 1; y <= h; y++) {
                BlockState st = (y == h || y % 2 == 0) ? chiseled.defaultBlockState() : bricks.defaultBlockState();
                setBlock(level, pos.set(px, center.getY() + y, pz), st);
            }

            if (h >= 6) {
                int topY = center.getY() + h + 1;
                Block leafBlock = random.nextFloat() < 0.25f ? glowingLeaves : leaves;
                setBlock(level, pos.set(px, topY, pz), leafBlock.defaultBlockState());
                setBlock(level, pos.set(px + 1, topY, pz), leafBlock.defaultBlockState());
                setBlock(level, pos.set(px - 1, topY, pz), leafBlock.defaultBlockState());
                setBlock(level, pos.set(px, topY, pz + 1), leafBlock.defaultBlockState());
                setBlock(level, pos.set(px, topY, pz - 1), leafBlock.defaultBlockState());

                Block vBlock = random.nextFloat() < 0.35f ? glowingVine : vine;
                int vLen = 2 + random.nextInt(3);
                for (int v = 1; v <= vLen; v++) {
                    BlockPos vp = pos.set(px, topY - v, pz);
                    if (level.getBlockState(vp).isAir()) {
                        setBlock(level, vp, vBlock.defaultBlockState());
                    }
                }
            }
        }

        bossMob.snapTo(center.getX() + 0.5, center.getY() + 2, center.getZ() + 0.5);
    }

    // =========================================================================================================
    // 3. Sculk Monstrosity: 深淵泰坦封印囚窟（The Abyssal Titan Crucible）
    // =========================================================================================================
    private void buildSculkMonstrosityArena(WorldGenLevel level, RandomSource random, BlockPos center, Mob bossMob) {
        Block darkBricks = getBlock("dark_slate_bricks");
        Block chiseledDark = getBlock("chiseled_dark_slate_bricks");
        Block pillar = getBlock("dark_slate_pillar");
        Block wall = getBlock("dark_slate_brick_wall");
        Block corrupted = getBlock("corrupted_slate_bricks");
        Block crystal = getBlock("soul_crystal_block");
        Block rune = getBlock("rune_slate");
        Block voidStone = getBlock("void_stone");

        int r = Math.min(radius + 2, 18);
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();

        // 1. 清空空間
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                double d = Math.sqrt(dx * dx + dz * dz);
                if (d > r + 0.5) continue;
                int x = center.getX() + dx, z = center.getZ() + dz;
                for (int y = -3; y <= CLEAR_HEIGHT; y++) {
                    setBlock(level, pos.set(x, center.getY() + y, z), Blocks.AIR.defaultBlockState());
                }
            }
        }

        // 2. 巨大深淵凹坑 (Sunken Abyssal Crucible)
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                double d = Math.sqrt(dx * dx + dz * dz);
                if (d > r + 0.5) continue;
                int x = center.getX() + dx, z = center.getZ() + dz;

                if (d > 14.5) {
                    // 外圈守衛台 (Y = center.Y + 1)
                    BlockState st = random.nextFloat() < 0.7f ? darkBricks.defaultBlockState() : corrupted.defaultBlockState();
                    setBlock(level, pos.set(x, center.getY() + 1, z), st);
                    fillDown(level, random, pos.set(x, center.getY(), z), darkBricks);
                    // 巨石齒尖圍牆
                    if (d > 16.5 && (Math.abs(dx) % 3 == 0 || Math.abs(dz) % 3 == 0)) {
                        int spikeH = 2 + random.nextInt(4);
                        for (int h = 1; h <= spikeH; h++) {
                            setBlock(level, pos.set(x, center.getY() + 1 + h, z), wall.defaultBlockState());
                        }
                    }
                } else if (d > 8.0) {
                    // 中層環廊 (Y = center.Y - 1)
                    BlockState st = (d > 11.0 && d < 12.0) ? rune.defaultBlockState() : darkBricks.defaultBlockState();
                    setBlock(level, pos.set(x, center.getY() - 1, z), st);
                    fillDown(level, random, pos.set(x, center.getY() - 2, z), darkBricks);
                } else {
                    // 底層破碎封印坑 (Y = center.Y - 3)
                    BlockState st = random.nextFloat() < 0.4f ? corrupted.defaultBlockState()
                            : (random.nextFloat() < 0.2f ? voidStone.defaultBlockState() : darkBricks.defaultBlockState());
                    setBlock(level, pos.set(x, center.getY() - 3, z), st);
                    fillDown(level, random, pos.set(x, center.getY() - 4, z), darkBricks);
                }
            }
        }

        // 3. 四條發光靈魂晶塊能量導管 (Glowing Soul Crystal Power Conduits)
        int[][] conduitTargets = {{-10, -10}, {10, -10}, {-10, 10}, {10, 10}};
        for (int[] t : conduitTargets) {
            int cx = t[0], cz = t[1];
            for (int step = 2; step <= 9; step++) {
                int px = center.getX() + Math.round((float) cx * step / 10.0f);
                int pz = center.getZ() + Math.round((float) cz * step / 10.0f);
                setBlock(level, pos.set(px, center.getY() - 3, pz), crystal.defaultBlockState());
                setBlock(level, pos.set(px, center.getY() - 4, pz), darkBricks.defaultBlockState());
            }
        }

        // 4. 四座巨大 3x3 泰坦禁錮堡壘 (4 Colossal Containment Bastions)
        for (int[] t : conduitTargets) {
            int bx = center.getX() + t[0], bz = center.getZ() + t[1];
            for (int bdx = -1; bdx <= 1; bdx++) {
                for (int bdz = -1; bdz <= 1; bdz++) {
                    int x = bx + bdx, z = bz + bdz;
                    fillDown(level, random, pos.set(x, center.getY() - 2, z), darkBricks);
                    for (int h = -1; h <= 9; h++) {
                        BlockState st = (bdx == 0 && bdz == 0) ? pillar.defaultBlockState()
                                : (h % 3 == 0 ? chiseledDark.defaultBlockState() : corrupted.defaultBlockState());
                        setBlock(level, pos.set(x, center.getY() + h, z), st);
                    }
                }
            }
            setBlock(level, pos.set(bx, center.getY() + 10, bz), wall.defaultBlockState());
            setBlock(level, pos.set(bx, center.getY() + 11, bz), wall.defaultBlockState());
        }

        // 5. 中央被撕裂的封印陣 (The Shattered Seal Dais)
        for (int dx = -3; dx <= 3; dx++) {
            for (int dz = -3; dz <= 3; dz++) {
                int x = center.getX() + dx, z = center.getZ() + dz;
                BlockState st = (dx == 0 && dz == 0) ? crystal.defaultBlockState()
                        : (Math.abs(dx) == 3 || Math.abs(dz) == 3 ? rune.defaultBlockState() : chiseledDark.defaultBlockState());
                setBlock(level, pos.set(x, center.getY() - 2, z), st);
            }
        }

        bossMob.snapTo(center.getX() + 0.5, center.getY() - 1, center.getZ() + 0.5);
    }

    // =========================================================================================================
    // Generic fallback arena
    // =========================================================================================================
    private void buildGenericArena(WorldGenLevel level, RandomSource random, BlockPos center, Mob mob) {
        int outer = radius + 1 + (moat.isPresent() ? moatWidth : 0);
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int dx = -outer; dx <= outer; dx++) {
            for (int dz = -outer; dz <= outer; dz++) {
                double d = Math.sqrt(dx * dx + dz * dz);
                if (d > outer + 0.5) continue;
                int x = center.getX() + dx, z = center.getZ() + dz;
                if (d <= radius + 1.5) {
                    for (int y = 1; y <= CLEAR_HEIGHT; y++) {
                        setBlock(level, pos.set(x, center.getY() + y, z), Blocks.AIR.defaultBlockState());
                    }
                    fillDown(level, random, pos.set(x, center.getY() - 1, z), floor.value().getState(level, random, pos).getBlock());
                    setBlock(level, pos.set(x, center.getY(), z), floor.value().getState(level, random, pos));
                    if (d <= 3.5) {
                        setBlock(level, pos.set(x, center.getY() + 1, z), floor.value().getState(level, random, pos));
                    }
                    if (d > radius + 0.5) {
                        boolean gate = Math.abs(dx) <= 1 || Math.abs(dz) <= 1;
                        if (!gate) {
                            setBlock(level, pos.set(x, center.getY() + 1, z), wall.value().getState(level, random, pos));
                        }
                    }
                } else if (moat.isPresent()) {
                    for (int y = 1; y <= CLEAR_HEIGHT; y++) {
                        setBlock(level, pos.set(x, center.getY() + y, z), Blocks.AIR.defaultBlockState());
                    }
                    BlockState liquid = moat.get().value().getState(level, random, pos.set(x, center.getY(), z));
                    setBlock(level, pos, liquid);
                    setBlock(level, pos.set(x, center.getY() - 1, z), liquid);
                    fillDown(level, random, pos.set(x, center.getY() - 2, z), floor.value().getState(level, random, pos).getBlock());
                }
            }
        }
        for (int i = 0; i < pillarCount; i++) {
            float angle = Mth.TWO_PI * (i + 0.5f) / pillarCount;
            int x = center.getX() + Math.round(Mth.cos(angle) * (radius + 1));
            int z = center.getZ() + Math.round(Mth.sin(angle) * (radius + 1));
            int height = pillarHeight - random.nextInt(3);
            for (int y = 1; y <= height; y++) {
                setBlock(level, pos.set(x, center.getY() + y, z), pillar.value().getState(level, random, pos));
            }
        }
        mob.snapTo(center.getX() + 0.5, center.getY() + 2, center.getZ() + 0.5);
    }

    private void fillDown(WorldGenLevel level, RandomSource random, BlockPos.MutableBlockPos pos, Block material) {
        for (int i = 0; i < MAX_FOOTING; i++) {
            BlockState current = level.getBlockState(pos);
            if (current.isSolidRender() && level.getFluidState(pos).isEmpty()) {
                return;
            }
            if (current.is(Blocks.BEDROCK)) {
                return;
            }
            setBlock(level, pos, material.defaultBlockState());
            pos.move(0, -1, 0);
        }
    }

    public static void register() {
        PySift.LOGGER.info("Registered feature type {}", BuiltInRegistries.FEATURE_TYPE.getKey(TYPE));
    }
}
