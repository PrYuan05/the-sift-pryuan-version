package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.chunk.LevelChunkSection;

import java.util.function.Predicate;

/**
 * 「這個範圍裡有沒有某種方塊」的快速版：先看每段 16×16×16 區塊的調色盤（{@link LevelChunkSection#maybeHas}），
 * 調色盤裡根本沒有的段落整段跳過，只在可能有的段落逐格讀。結果和逐格掃 {@code BlockPos.betweenClosed} 一樣，
 * 但絕大多數情況一格都不用讀；而且只看已載入的區塊，不會為了找方塊去載入或生成區塊。
 */
public final class BlockScan {
    private BlockScan() {
    }

    /** min～max（含）之間有沒有符合 test 的方塊（只看已載入的區塊）。 */
    public static boolean any(ServerLevel level, BlockPos min, BlockPos max, Predicate<BlockState> test) {
        int x0 = min.getX(), y0 = Math.max(min.getY(), level.getMinY()), z0 = min.getZ();
        int x1 = max.getX(), y1 = Math.min(max.getY(), level.getMaxY()), z1 = max.getZ();
        if (y0 > y1) {
            return false;
        }
        for (int cx = x0 >> 4; cx <= x1 >> 4; cx++) {
            for (int cz = z0 >> 4; cz <= z1 >> 4; cz++) {
                LevelChunk chunk = level.getChunkSource().getChunkNow(cx, cz);
                if (chunk == null) {
                    continue;
                }
                for (int sy = y0 >> 4; sy <= y1 >> 4; sy++) {
                    int index = level.getSectionIndexFromSectionY(sy);
                    if (index < 0 || index >= chunk.getSectionsCount()) {
                        continue;
                    }
                    LevelChunkSection section = chunk.getSection(index);
                    if (section.hasOnlyAir() && !test.test(net.minecraft.world.level.block.Blocks.AIR.defaultBlockState())
                            || !section.maybeHas(test)) {
                        continue;
                    }
                    int ax = Math.max(x0, cx << 4), bx = Math.min(x1, (cx << 4) + 15);
                    int ay = Math.max(y0, sy << 4), by = Math.min(y1, (sy << 4) + 15);
                    int az = Math.max(z0, cz << 4), bz = Math.min(z1, (cz << 4) + 15);
                    for (int x = ax; x <= bx; x++) {
                        for (int y = ay; y <= by; y++) {
                            for (int z = az; z <= bz; z++) {
                                if (test.test(section.getBlockState(x & 15, y & 15, z & 15))) {
                                    return true;
                                }
                            }
                        }
                    }
                }
            }
        }
        return false;
    }
}
