package pryuan05.pysift.worldgen;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Vec3i;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.packs.resources.Resource;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.StructureBlock;
import net.minecraft.world.level.block.entity.StructureBlockEntity;
import net.minecraft.world.level.block.state.properties.StructureMode;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.phys.AABB;
import pryuan05.pysift.PySift;

import java.io.Reader;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * 給使用者在遊戲裡修改結構的展示場：{@code /pysift_showcase [關鍵字]} 把 data/pysift/structure_showcase/landmarks.json
 * 列出的每個結構檔（地標、遺跡、到達傳送門、Boss 競技場）一個一個排在玩家旁邊，每個旁邊放一個已經設定好
 * 名稱、範圍、模式 = 儲存（SAVE）的結構方塊。改完後對結構方塊按「儲存」，檔案會存到世界資料夾的 generated/pysift/structure/，
 * 再用 tools/worldgen/import_structures.py 搬回模組。
 * 展示用的迴音傀儡不會動（NoAI），匯入時會拿掉。
 */
public final class StructureShowcase {
    private static final int GAP = 4;
    private static final int ROW_WIDTH = 140;

    private StructureShowcase() {
    }

    public static void register() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registries, environment) ->
                dispatcher.register(Commands.literal("pysift_showcase")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .executes(ctx -> lay(ctx.getSource().getLevel(), BlockPos.containing(ctx.getSource().getPosition()), "",
                                msg -> ctx.getSource().sendSuccess(() -> msg, false)))
                        .then(Commands.argument("filter", com.mojang.brigadier.arguments.StringArgumentType.word())
                                .executes(ctx -> lay(ctx.getSource().getLevel(), BlockPos.containing(ctx.getSource().getPosition()),
                                        com.mojang.brigadier.arguments.StringArgumentType.getString(ctx, "filter"),
                                        msg -> ctx.getSource().sendSuccess(() -> msg, false))))));
    }

    private static int lay(ServerLevel level, BlockPos at, String filter, java.util.function.Consumer<Component> say) {
        List<Identifier> ids = templates(level, filter);
        if (ids.isEmpty()) {
            say.accept(Component.literal("No templates match '" + filter + "'"));
            return 0;
        }
        int x = at.getX() + 3, z = at.getZ() + 3, rowDepth = 0, placed = 0;
        for (Identifier id : ids) {
            Optional<StructureTemplate> template = level.getStructureTemplateManager().get(id);
            if (template.isEmpty()) {
                say.accept(Component.literal("missing " + id));
                continue;
            }
            Vec3i size = template.get().getSize();
            if (x + size.getX() > at.getX() + ROW_WIDTH && placed > 0) {
                x = at.getX() + 3;
                z += rowDepth + GAP + 2;
                rowDepth = 0;
            }
            BlockPos corner = new BlockPos(x, at.getY(), z);
            // 先鋪滿結構空位：結構裡沒有方塊的位置維持空位，存檔時會被略過（世界生成時那些格子不動原本的地形）；
            // 結構裡的空氣照樣是空氣（會清出空間）。改建時想讓某格「不要動地形」，就放一個結構空位
            for (BlockPos p : BlockPos.betweenClosed(corner, corner.offset(size.getX() - 1, size.getY() - 1, size.getZ() - 1))) {
                level.setBlock(p, Blocks.STRUCTURE_VOID.defaultBlockState(), Block.UPDATE_CLIENTS);
            }
            template.get().placeInWorld(level, corner, corner, new StructurePlaceSettings(), level.getRandom(), Block.UPDATE_ALL);
            // 展示用的生物：不要走掉，不然存檔時就不在範圍裡了
            for (Mob mob : level.getEntitiesOfClass(Mob.class, new AABB(corner.getX(), corner.getY(), corner.getZ(),
                    corner.getX() + size.getX(), corner.getY() + size.getY(), corner.getZ() + size.getZ()))) {
                mob.setNoAi(true);
                mob.setSilent(true);
            }
            BlockPos blockPos = corner.offset(-1, -1, -1);
            level.setBlock(blockPos, Blocks.STRUCTURE_BLOCK.defaultBlockState().setValue(StructureBlock.MODE, StructureMode.SAVE), Block.UPDATE_ALL);
            if (level.getBlockEntity(blockPos) instanceof StructureBlockEntity structureBlock) {
                structureBlock.setStructureName(id);
                structureBlock.setStructurePos(new BlockPos(1, 1, 1));
                structureBlock.setStructureSize(size);
                structureBlock.setMode(StructureMode.SAVE);
                structureBlock.setIgnoreEntities(false);
                structureBlock.setShowBoundingBox(true);
                structureBlock.setChanged();
                level.sendBlockUpdated(blockPos, structureBlock.getBlockState(), structureBlock.getBlockState(), Block.UPDATE_ALL);
            }
            say.accept(Component.literal(id + " at " + corner.toShortString() + " size " + size.toShortString()));
            x += size.getX() + GAP;
            rowDepth = Math.max(rowDepth, size.getZ());
            placed++;
        }
        say.accept(Component.literal("Laid out " + placed + " templates. Edit them, then press SAVE on each structure block."));
        return placed;
    }

    private static List<Identifier> templates(ServerLevel level, String filter) {
        List<Identifier> out = new ArrayList<>();
        Optional<Resource> resource = level.getServer().getResourceManager().getResource(PySift.id("structure_showcase/landmarks.json"));
        if (resource.isEmpty()) {
            return out;
        }
        try (Reader reader = resource.get().openAsReader()) {
            for (JsonElement e : JsonParser.parseReader(reader).getAsJsonObject().getAsJsonArray("templates")) {
                String id = e.getAsString();
                if (filter.isEmpty() || id.contains(filter)) {
                    out.add(Identifier.parse(id));
                }
            }
        } catch (Exception e) {
            PySift.LOGGER.warn("Could not read the structure showcase list", e);
        }
        return out;
    }
}
