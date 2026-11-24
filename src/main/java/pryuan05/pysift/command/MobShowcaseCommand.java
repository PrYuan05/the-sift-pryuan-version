package pryuan05.pysift.command;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.ClimateVariant;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.entity.mob.BlubEntity;
import pryuan05.pysift.entity.mob.SlabberEntity;

import java.util.List;

/**
 * 生物展覽場指令：{@code /pysift_mobs} 在玩家前方鋪設平坦觀景台並一次召喚全模組所有生物與變種（共 56 隻，NoAI 站立方便檢視）。
 * {@code /pysift_mobs clear} 清除範圍內的展示生物。
 */
public final class MobShowcaseCommand {
    private static final String SHOWCASE_TAG = "pysift_showcase";

    private record ClimateEntry(String label, EntityType<? extends Mob> type) {}
    private record SimpleEntry(String label, EntityType<? extends Mob> type) {}

    private static final List<ClimateEntry> CLIMATE_MOBS = List.of(
            new ClimateEntry("Nuzzle", ModEntities.NUZZLE),
            new ClimateEntry("Lootkin", ModEntities.LOOTKIN),
            new ClimateEntry("Slabber", ModEntities.SLABBER),
            new ClimateEntry("Prickle", ModEntities.PRICKLE),
            new ClimateEntry("Dartback", ModEntities.DARTBACK),
            new ClimateEntry("Fusefly", ModEntities.FUSEFLY),
            new ClimateEntry("Wobble", ModEntities.WOBBLE),
            new ClimateEntry("Nester", ModEntities.NESTER),
            new ClimateEntry("Pollinator", ModEntities.POLLINATOR),
            new ClimateEntry("Seedling", ModEntities.SEEDLING),
            new ClimateEntry("Sprout", ModEntities.SPROUT),
            new ClimateEntry("Sentinel", ModEntities.SENTINEL)
    );

    private static final List<SimpleEntry> FRIENDLY_MOBS = List.of(
            new SimpleEntry("Echo Golem", ModEntities.ECHO_GOLEM),
            new SimpleEntry("Singer", ModEntities.SINGER),
            new SimpleEntry("Mourner", ModEntities.MOURNER),
            new SimpleEntry("Sift Warden", ModEntities.SIFT_WARDEN)
    );

    private static final List<SimpleEntry> HOSTILE_MOBS = List.of(
            new SimpleEntry("Hurler", ModEntities.HURLER),
            new SimpleEntry("Stalker", ModEntities.STALKER),
            new SimpleEntry("Scavenger", ModEntities.SCAVENGER),
            new SimpleEntry("Hunter", ModEntities.HUNTER),
            new SimpleEntry("Trapper", ModEntities.TRAPPER),
            new SimpleEntry("Tuner", ModEntities.TUNER),
            new SimpleEntry("Bloombud", ModEntities.BLOOMBUD),
            new SimpleEntry("Roamroot", ModEntities.ROAMROOT)
    );

    private static final List<SimpleEntry> BOSS_MOBS = List.of(
            new SimpleEntry("Harmonizer", ModEntities.HARMONIZER),
            new SimpleEntry("Monarch", ModEntities.MONARCH),
            new SimpleEntry("Sculk Monstrosity", ModEntities.SCULK_MONSTROSITY)
    );

    private MobShowcaseCommand() {
    }

    public static void register() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) ->
                dispatcher.register(Commands.literal("pysift_mobs")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .executes(ctx -> spawnAll(ctx.getSource()))
                        .then(Commands.literal("clear")
                                .executes(ctx -> clearAll(ctx.getSource())))));
    }

    private static int clearAll(CommandSourceStack source) {
        ServerLevel level = source.getLevel();
        Vec3 pos = source.getPosition();
        AABB box = new AABB(pos.x - 128, pos.y - 64, pos.z - 128, pos.x + 128, pos.y + 64, pos.z + 128);
        int removed = 0;
        for (Entity e : level.getEntitiesOfClass(Entity.class, box, e -> e.entityTags().contains(SHOWCASE_TAG))) {
            e.discard();
            removed++;
        }
        int count = removed;
        source.sendSuccess(() -> Component.literal("已清除 " + count + " 隻展示生物。").withStyle(ChatFormatting.YELLOW), false);
        return removed;
    }

    private static int spawnAll(CommandSourceStack source) {
        ServerLevel level = source.getLevel();
        // 先清掉附近舊的展示生物避免重疊
        clearAll(source);

        BlockPos origin = BlockPos.containing(source.getPosition());
        int baseX = origin.getX();
        int baseY = origin.getY();
        int baseZ = origin.getZ() + 4; // 全部排在玩家南方 (+Z)，面向北方 (-Z / yaw 180) 看著玩家

        // 鋪設寬敞的展示平台 (X: -24..+24, Z: -2..+50) 並清除上方 10 格障礙
        for (int dx = -24; dx <= 24; dx++) {
            for (int dz = -2; dz <= 50; dz++) {
                BlockPos floor = new BlockPos(baseX + dx, baseY - 1, baseZ + dz);
                boolean border = Math.abs(dx) == 24 || dz == -2 || dz == 50 || dz == 14 || dz == 28 || dz == 36 || dz == 42;
                level.setBlock(floor, (border ? Blocks.POLISHED_DEEPSLATE : Blocks.SMOOTH_STONE).defaultBlockState(), Block.UPDATE_CLIENTS);
                for (int dy = 0; dy <= 10; dy++) {
                    BlockPos air = new BlockPos(baseX + dx, baseY + dy, baseZ + dz);
                    if (!level.getBlockState(air).isAir()) {
                        level.setBlock(air, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
                    }
                }
            }
        }

        int total = 0;

        // 1. 12 種氣候變種生物：分為 4 排 × 每排 3 種生物，每種生物左→右為 [原版 | 熱帶 | 寒帶]
        int[] climateCodes = {ClimateVariant.NORMAL, ClimateVariant.TROPICAL, ClimateVariant.COLD};
        String[] climateLabels = {"", " (Tropical)", " (Cold)"};
        for (int i = 0; i < CLIMATE_MOBS.size(); i++) {
            ClimateEntry entry = CLIMATE_MOBS.get(i);
            int row = i / 3;          // 0..3
            int groupCol = i % 3;     // 0..2
            double groupCenterX = baseX + (groupCol - 1) * 14.0;
            double z = baseZ + 2.0 + row * 6.5;

            for (int c = 0; c < 3; c++) {
                double x = groupCenterX + (c - 1) * 3.0;
                Mob mob = createShowcaseMob(level, entry.type(), x + 0.5, baseY, z + 0.5, entry.label() + climateLabels[c]);
                if (mob != null) {
                    mob.setAttached(ClimateVariant.TYPE, climateCodes[c]);
                    if (mob instanceof SlabberEntity slabber) {
                        ItemStack flower = switch (climateCodes[c]) {
                            case ClimateVariant.TROPICAL -> new ItemStack(Items.TORCHFLOWER);
                            case ClimateVariant.COLD -> new ItemStack(Items.CORNFLOWER);
                            default -> new ItemStack(Items.POPPY);
                        };
                        slabber.setFlower(flower, SlabberEntity.MAX_GROWTH);
                    }
                    level.addFreshEntity(mob);
                    total++;
                }
            }
        }

        // 2. Blub 5 種生態變體（第 5 排, Z = baseZ + 31）
        BlubEntity.Variant[] blubVariants = BlubEntity.Variant.values();
        for (int i = 0; i < blubVariants.length; i++) {
            BlubEntity.Variant v = blubVariants[i];
            double x = baseX + (i - 2) * 4.0;
            Mob mob = createShowcaseMob(level, ModEntities.BLUB, x + 0.5, baseY, baseZ + 31.5, "Blub (" + v.getSerializedName() + ")");
            if (mob instanceof BlubEntity blub) {
                blub.setVariant(v);
                level.addFreshEntity(blub);
                total++;
            }
        }

        // 3. 友善／中立非變種生物 4 隻（左側, Z = baseZ + 38） + 野生敵對生物 8 隻（Z = baseZ + 38 & +43）
        for (int i = 0; i < FRIENDLY_MOBS.size(); i++) {
            SimpleEntry e = FRIENDLY_MOBS.get(i);
            double x = baseX - 18.0 + i * 4.5;
            Mob mob = createShowcaseMob(level, e.type(), x + 0.5, baseY, baseZ + 38.5, e.label());
            if (mob != null) {
                level.addFreshEntity(mob);
                total++;
            }
        }
        for (int i = 0; i < HOSTILE_MOBS.size(); i++) {
            SimpleEntry e = HOSTILE_MOBS.get(i);
            double x = baseX + 2.0 + (i % 4) * 5.0;
            double z = baseZ + (i < 4 ? 38.5 : 43.0);
            Mob mob = createShowcaseMob(level, e.type(), x + 0.5, baseY, z, e.label());
            if (mob != null) {
                level.addFreshEntity(mob);
                total++;
            }
        }

        // 4. 三大 Boss（最後一排大間距, Z = baseZ + 47.5）
        for (int i = 0; i < BOSS_MOBS.size(); i++) {
            SimpleEntry e = BOSS_MOBS.get(i);
            double x = baseX + (i - 1) * 12.0;
            Mob mob = createShowcaseMob(level, e.type(), x + 0.5, baseY, baseZ + 47.5, e.label());
            if (mob != null) {
                level.addFreshEntity(mob);
                total++;
            }
        }

        int finalTotal = total;
        source.sendSuccess(() -> Component.literal("已在前方展示台召喚全部 " + finalTotal + " 隻模組生物（含氣候變種、5 種 Blub 與三大 Boss）！輸入 /time set night 可檢視自發光。")
                .withStyle(ChatFormatting.AQUA), false);
        return total;
    }

    private static Mob createShowcaseMob(ServerLevel level, EntityType<? extends Mob> type, double x, double y, double z, String name) {
        Mob mob = type.create(level, EntitySpawnReason.COMMAND);
        if (mob == null) {
            return null;
        }
        mob.setPos(x, y, z);
        mob.setYRot(180.0F);
        mob.setYHeadRot(180.0F);
        mob.setYBodyRot(180.0F);
        mob.setNoAi(true);
        mob.setSilent(true);
        mob.setPersistenceRequired();
        mob.setCustomName(Component.literal(name));
        mob.setCustomNameVisible(true);
        mob.addTag(SHOWCASE_TAG);
        return mob;
    }
}
