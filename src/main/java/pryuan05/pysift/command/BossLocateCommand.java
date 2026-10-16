package pryuan05.pysift.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.datafixers.util.Pair;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.Heightmap;
import pryuan05.pysift.PySift;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.worldgen.BossArenaFeature;
import pryuan05.pysift.worldgen.BossArenaSavedData;

import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.Optional;

/**
 * Boss 定位指令：
 * 支援三種指令入口：
 * <ul>
 *   <li>/locate boss &lt;monarch|harmonizer|sculk_monstrosity&gt; [find|biome|spawn]</li>
 *   <li>/locateboss [monarch|harmonizer|sculk_monstrosity] [find|biome|spawn]</li>
 *   <li>/pysift locate boss &lt;monarch|harmonizer|sculk_monstrosity&gt; [find|biome|spawn]</li>
 * </ul>
 * 搜尋三層機制：
 * <ol>
 *   <li>活體實體搜尋：掃描當前維度已載入的活躍 Boss 實體。</li>
 *   <li>已生成神殿搜尋：透過 {@link BossArenaSavedData} 跨區塊查詢世界中任何已生成的專屬神殿競技場。</li>
 *   <li>原生生態域搜尋：若世界尚未生成，利用生態域噪聲圖快速定位最近的原生生態域，並提供一鍵傳送與直接召喚神殿按鈕。</li>
 * </ol>
 */
public final class BossLocateCommand {

    public enum BossInfo {
        MONARCH("monarch", "帝王 (Monarch)", ModEntities.MONARCH,
                ResourceKey.create(Registries.BIOME, PySift.id("amber_dunes")),
                "黃琥珀沙丘 (Amber Dunes)",
                "帝王日晷陵台 (Imperial Sunken Ziggurat)",
                ChatFormatting.GOLD),
        HARMONIZER("harmonizer", "調和者 (Harmonizer)", ModEntities.HARMONIZER,
                ResourceKey.create(Registries.BIOME, PySift.id("willow_grove")),
                "靈魂柳林 (Willow Grove)",
                "靈液環湖琴台 (Resonant Spirit Lake Pavilion)",
                ChatFormatting.AQUA),
        SCULK_MONSTROSITY("sculk_monstrosity", "幽匿巨獸 (Sculk Monstrosity)", ModEntities.SCULK_MONSTROSITY,
                ResourceKey.create(Registries.BIOME, PySift.id("violet_slate_abyss")),
                "紫板岩深淵 (Violet Slate Abyss)",
                "深淵泰坦封印囚窟 (Abyssal Titan Crucible)",
                ChatFormatting.DARK_AQUA);

        public final String id;
        public final String displayName;
        public final EntityType<?> entityType;
        public final ResourceKey<Biome> biomeKey;
        public final String biomeName;
        public final String arenaName;
        public final ChatFormatting color;

        BossInfo(String id, String displayName, EntityType<?> entityType, ResourceKey<Biome> biomeKey,
                 String biomeName, String arenaName, ChatFormatting color) {
            this.id = id;
            this.displayName = displayName;
            this.entityType = entityType;
            this.biomeKey = biomeKey;
            this.biomeName = biomeName;
            this.arenaName = arenaName;
            this.color = color;
        }

        public static Optional<BossInfo> fromString(String name) {
            if (name == null) return Optional.empty();
            String clean = name.trim().toLowerCase(Locale.ROOT);
            for (BossInfo b : values()) {
                if (b.id.equals(clean) || b.name().toLowerCase(Locale.ROOT).equals(clean)) {
                    return Optional.of(b);
                }
            }
            return Optional.empty();
        }

        public static List<String> getIds() {
            return Arrays.stream(values()).map(b -> b.id).toList();
        }
    }

    private static final List<String> ACTIONS = List.of("find", "biome", "spawn");

    private BossLocateCommand() {
    }

    public static void register() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> registerCommands(dispatcher));
    }

    private static void registerCommands(CommandDispatcher<CommandSourceStack> dispatcher) {
        // 1. /locateboss [boss] [action]
        dispatcher.register(Commands.literal("locateboss")
                .executes(context -> showDashboard(context.getSource()))
                .then(Commands.argument("boss", StringArgumentType.word())
                        .suggests((context, builder) -> SharedSuggestionProvider.suggest(BossInfo.getIds(), builder))
                        .executes(context -> locate(context.getSource(), StringArgumentType.getString(context, "boss"), "find"))
                        .then(Commands.argument("action", StringArgumentType.word())
                                .suggests((context, builder) -> SharedSuggestionProvider.suggest(ACTIONS, builder))
                                .executes(context -> locate(context.getSource(),
                                        StringArgumentType.getString(context, "boss"),
                                        StringArgumentType.getString(context, "action"))))));

        // 2. /locate boss <boss> [action]（無縫注入原版 /locate 體系）
        dispatcher.register(Commands.literal("locate")
                .then(Commands.literal("boss")
                        .executes(context -> showDashboard(context.getSource()))
                        .then(Commands.argument("boss", StringArgumentType.word())
                                .suggests((context, builder) -> SharedSuggestionProvider.suggest(BossInfo.getIds(), builder))
                                .executes(context -> locate(context.getSource(), StringArgumentType.getString(context, "boss"), "find"))
                                .then(Commands.argument("action", StringArgumentType.word())
                                        .suggests((context, builder) -> SharedSuggestionProvider.suggest(ACTIONS, builder))
                                        .executes(context -> locate(context.getSource(),
                                                StringArgumentType.getString(context, "boss"),
                                                StringArgumentType.getString(context, "action")))))));

        // 3. /pysift locate boss <boss> [action] & /pysift spawnarena <boss>
        dispatcher.register(Commands.literal("pysift")
                .then(Commands.literal("locate")
                        .then(Commands.literal("boss")
                                .executes(context -> showDashboard(context.getSource()))
                                .then(Commands.argument("boss", StringArgumentType.word())
                                        .suggests((context, builder) -> SharedSuggestionProvider.suggest(BossInfo.getIds(), builder))
                                        .executes(context -> locate(context.getSource(), StringArgumentType.getString(context, "boss"), "find"))
                                        .then(Commands.argument("action", StringArgumentType.word())
                                                .suggests((context, builder) -> SharedSuggestionProvider.suggest(ACTIONS, builder))
                                                .executes(context -> locate(context.getSource(),
                                                        StringArgumentType.getString(context, "boss"),
                                                        StringArgumentType.getString(context, "action")))))))
                .then(Commands.literal("spawnarena")
                        .then(Commands.argument("boss", StringArgumentType.word())
                                .suggests((context, builder) -> SharedSuggestionProvider.suggest(BossInfo.getIds(), builder))
                                .executes(context -> locate(context.getSource(), StringArgumentType.getString(context, "boss"), "spawn")))));
    }

    private static int showDashboard(CommandSourceStack source) {
        source.sendSuccess(() -> Component.literal("§6========================================"), false);
        source.sendSuccess(() -> Component.literal("§6[The Sift] §eBoss 智能定位導航面板§r"), false);
        source.sendSuccess(() -> Component.literal("§7點擊下方選項快速定位或傳送至該 Boss：§r"), false);

        for (BossInfo b : BossInfo.values()) {
            MutableComponent line = Component.literal("➤ ").withStyle(ChatFormatting.DARK_GRAY);
            line.append(Component.literal(b.displayName).withStyle(b.color, ChatFormatting.BOLD));
            line.append(Component.literal("  "));

            line.append(createActionButton("[尋找 Boss]", "/locateboss " + b.id + " find",
                    "點擊自動搜尋活動中的實體或已生成的專屬神殿", ChatFormatting.GREEN));
            line.append(Component.literal(" "));

            line.append(createActionButton("[尋找生態域]", "/locateboss " + b.id + " biome",
                    "點擊搜尋此 Boss 的棲息原生生態域（" + b.biomeName + "）", ChatFormatting.AQUA));
            line.append(Component.literal(" "));

            line.append(createActionButton("[召喚神殿]", "/locateboss " + b.id + " spawn",
                    "點擊於當前位置立即生成專屬神殿與 Boss（需要管理員權限）", ChatFormatting.GOLD));

            source.sendSuccess(() -> line, false);
        }
        source.sendSuccess(() -> Component.literal("§6========================================"), false);
        return 1;
    }

    private static int locate(CommandSourceStack source, String bossName, String action) {
        Optional<BossInfo> opt = BossInfo.fromString(bossName);
        if (opt.isEmpty()) {
            source.sendFailure(Component.literal("§c[The Sift] 未知的 Boss 名稱「" + bossName + "」！可用：monarch, harmonizer, sculk_monstrosity"));
            return 0;
        }

        BossInfo boss = opt.get();
        ServerLevel level = source.getLevel();
        BlockPos origin = BlockPos.containing(source.getPosition());

        if ("spawn".equalsIgnoreCase(action)) {
            return handleSpawn(source, level, boss, origin);
        }

        if ("biome".equalsIgnoreCase(action)) {
            return handleBiomeSearch(source, level, boss, origin, false);
        }

        // 預設 "find"：三層搜尋機制
        // 1. 活體實體搜尋
        LivingEntity nearestEntity = null;
        double minLiveDist = Double.MAX_VALUE;
        for (Entity e : level.getAllEntities()) {
            if (e.getType() == boss.entityType && e.isAlive() && e instanceof LivingEntity l) {
                double d = e.distanceToSqr(source.getPosition());
                if (d < minLiveDist) {
                    minLiveDist = d;
                    nearestEntity = l;
                }
            }
        }

        if (nearestEntity != null) {
            int x = nearestEntity.getBlockX();
            int y = nearestEntity.getBlockY();
            int z = nearestEntity.getBlockZ();
            int dist = (int) Math.sqrt(minLiveDist);

            MutableComponent msg = Component.literal("§6[The Sift]§r 在目前世界找到正在活動的 ")
                    .append(Component.literal(boss.displayName).withStyle(boss.color, ChatFormatting.BOLD))
                    .append(Component.literal("！\n§7座標：§a[" + x + ", " + y + ", " + z + "]§r §7(距離: §b" + dist + "§7 格)§r  "))
                    .append(createActionButton("[點擊傳送至該 Boss]", "/tp @s " + x + " " + y + " " + z,
                            "立即傳送至該 Boss 身旁", ChatFormatting.GREEN));
            source.sendSuccess(() -> msg, false);
            return 1;
        }

        // 2. 跨區塊記錄神殿搜尋
        Optional<BossArenaSavedData.ArenaRecord> arenaRecord = BossArenaSavedData.get(level).findNearest(boss.id, origin);
        if (arenaRecord.isPresent()) {
            BlockPos arenaPos = arenaRecord.get().pos();
            int dist = (int) Math.sqrt(arenaPos.distSqr(origin));

            MutableComponent msg = Component.literal("§6[The Sift]§r 雖無活動中實體，但已定位到先前生成的專屬神殿 ")
                    .append(Component.literal(boss.arenaName).withStyle(boss.color, ChatFormatting.BOLD))
                    .append(Component.literal("！\n§7座標：§a[" + arenaPos.getX() + ", " + arenaPos.getY() + ", " + arenaPos.getZ() + "]§r §7(距離: §b" + dist + "§7 格)§r  "))
                    .append(createActionButton("[點擊傳送至神殿]", "/tp @s " + arenaPos.getX() + " " + (arenaPos.getY() + 1) + " " + arenaPos.getZ(),
                            "立即傳送至神殿中央", ChatFormatting.GREEN));
            source.sendSuccess(() -> msg, false);
            return 1;
        }

        // 3. 原生生態域噪聲搜尋
        return handleBiomeSearch(source, level, boss, origin, true);
    }

    private static int handleBiomeSearch(CommandSourceStack source, ServerLevel level, BossInfo boss, BlockPos origin, boolean fromFindFallback) {
        Pair<BlockPos, Holder<Biome>> result = level.findClosestBiome3d(holder -> holder.is(boss.biomeKey), origin, 6400, 32, 64);
        if (result == null) {
            MutableComponent msg = Component.literal("§c[The Sift] 在半徑 6400 格內未探測到 " + boss.displayName + " 的棲息生態域。§r  ")
                    .append(createActionButton("[在此處直接生成專屬神殿]", "/locateboss " + boss.id + " spawn",
                            "立即在此處生成專屬神殿與 Boss", ChatFormatting.GOLD));
            source.sendSuccess(() -> msg, false);
            return 1;
        }

        BlockPos biomePos = result.getFirst();
        int surfaceY = level.getHeight(Heightmap.Types.WORLD_SURFACE, biomePos.getX(), biomePos.getZ());
        BlockPos targetPos = new BlockPos(biomePos.getX(), surfaceY, biomePos.getZ());
        int dist = (int) Math.sqrt(origin.distSqr(targetPos));

        MutableComponent msg = Component.literal("§6[The Sift]§r ");
        if (fromFindFallback) {
            msg.append(Component.literal("目前區域尚未生成該 Boss。已為您定位其原生生態域 "));
        } else {
            msg.append(Component.literal("已成功定位到 "));
        }
        msg.append(Component.literal(boss.biomeName).withStyle(boss.color, ChatFormatting.BOLD))
                .append(Component.literal("！\n§7生態域座標：§a[" + targetPos.getX() + ", " + targetPos.getY() + ", " + targetPos.getZ() + "]§r §7(距離: §b" + dist + "§7 格)§r  "))
                .append(createActionButton("[點擊傳送至生態域]", "/tp @s " + targetPos.getX() + " " + (targetPos.getY() + 1) + " " + targetPos.getZ(),
                        "傳送至生態域地表", ChatFormatting.AQUA))
                .append(Component.literal("  "))
                .append(createActionButton("[在此生成專屬神殿]", "/locateboss " + boss.id + " spawn",
                        "立即在目標或當前位置生成神殿與 Boss", ChatFormatting.GOLD));

        source.sendSuccess(() -> msg, false);
        return 1;
    }

    private static int handleSpawn(CommandSourceStack source, ServerLevel level, BossInfo boss, BlockPos origin) {
        if (!Commands.LEVEL_GAMEMASTERS.check(source.permissions())) {
            source.sendFailure(Component.literal("§c[The Sift] 召喚神殿需要管理員權限 (Game Master / OP)！"));
            return 0;
        }

        boolean success = BossArenaFeature.generateArenaDirectly(level, boss.id, origin);
        if (success) {
            MutableComponent msg = Component.literal("§6[The Sift]§r 已成功於 §a[" + origin.getX() + ", " + origin.getY() + ", " + origin.getZ() + "]§r 召喚 ")
                    .append(Component.literal(boss.displayName).withStyle(boss.color, ChatFormatting.BOLD))
                    .append(Component.literal(" 與其專屬神殿 "))
                    .append(Component.literal(boss.arenaName).withStyle(ChatFormatting.YELLOW, ChatFormatting.BOLD))
                    .append(Component.literal("！"));
            source.sendSuccess(() -> msg, true);
            return 1;
        } else {
            source.sendFailure(Component.literal("§c[The Sift] 召喚專屬神殿失敗，請確認該位置是否可容納建築。"));
            return 0;
        }
    }

    private static MutableComponent createActionButton(String label, String command, String hoverText, ChatFormatting color) {
        return Component.literal(label).withStyle(style -> style
                .withColor(color)
                .withUnderlined(true)
                .withClickEvent(new ClickEvent.RunCommand(command))
                .withHoverEvent(new HoverEvent.ShowText(Component.literal(hoverText))));
    }
}
