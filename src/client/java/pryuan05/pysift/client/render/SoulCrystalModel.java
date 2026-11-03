package pryuan05.pysift.client.render;

import net.fabricmc.fabric.api.client.model.loading.v1.ModelLoadingPlugin;
import net.fabricmc.fabric.api.client.model.loading.v1.wrapper.WrapperBlockStateModel;
import net.fabricmc.fabric.api.client.renderer.v1.mesh.MutableQuadView;
import net.fabricmc.fabric.api.client.renderer.v1.mesh.QuadEmitter;
import net.fabricmc.fabric.api.util.TriState;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.client.renderer.block.dispatch.BlockStateModel;
import net.minecraft.client.renderer.chunk.ChunkSectionLayer;
import net.minecraft.client.resources.model.ModelBaker;
import net.minecraft.client.resources.model.ModelDebugName;
import net.minecraft.client.resources.model.sprite.Material;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.state.BlockState;
import org.jspecify.annotations.Nullable;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.SoulCrystal;

import java.util.function.Predicate;

/**
 * 靈魂晶塊的動態連接模型（Fabric Renderer API + Model Loading API）：
 * <ul>
 *   <li>繪製區段時直接讀取周圍 3×3×3（26 個鄰格，含斜對角）是否也是靈魂晶塊，無須占用任何 BlockState 屬性。</li>
 *   <li>外殼（Shell）：每個外露面切成 4 個 8×8 象限，依「水平鄰格 H、垂直鄰格 V、斜角鄰格 D」挑選 5 張 CTM 拼接圖之一，
 *       讓任意連接形狀都呈現緊密連貫的深青邊框與清澈內層。</li>
 *   <li>晶核（Core，內縮 1 px）：以 3×3×3 子方塊體素判定佔用（邊柱需 3 鄰格、角塊需 7 鄰格皆為晶塊才填滿），
 *       徹底補滿 2×2 與 2×2×2 交界中心的空洞，同時在 L 形內凹角維持 1 px 內縮。</li>
 *   <li>全亮自發光：設定 {@code emissive(true)}、{@code ambientOcclusion(TriState.FALSE)}、{@code shadeDirectionOverride(Direction.UP)}，
 *       消除側面與底面的方向陰影衰減，完整呈現由外而內、由深到淺的靈魂眩光色階。</li>
 * </ul>
 */
public final class SoulCrystalModel extends WrapperBlockStateModel {
    private static final float INSET = 1.0f / 16.0f;
    private static final Direction[] DIRECTIONS = Direction.values();
    private static final ModelDebugName DEBUG_NAME = () -> "pysift:soul_crystal_block";

    private final Material.Baked[] shellMaterials = new Material.Baked[5];
    private final Material.Baked[] coreMaterials = new Material.Baked[5];

    public SoulCrystalModel(BlockStateModel wrapped, ModelBaker baker) {
        super(wrapped);
        String base = "block/soul_crystal_block/soul_crystal_block_";
        for (int i = 0; i < 5; i++) {
            shellMaterials[i] = baker.materials().get(new Material(PySift.id(base + "shell_" + i), true), DEBUG_NAME);
            coreMaterials[i] = baker.materials().get(new Material(PySift.id(base + "core_" + i), false), DEBUG_NAME);
        }
    }

    public static void register() {
        ModelLoadingPlugin.register(pluginContext ->
                pluginContext.modifyBlockModelAfterBake().register((model, context) ->
                        context.state().is(SoulCrystal.SOUL_CRYSTAL_BLOCK)
                                ? new SoulCrystalModel(model, context.baker())
                                : model));
    }

    private record GeometryKey(int neighborMask) {
    }

    private static int idx(int dx, int dy, int dz) {
        return (dx + 1) * 9 + (dy + 1) * 3 + (dz + 1);
    }

    private static int sampleNeighbors(BlockAndTintGetter level, BlockPos pos) {
        BlockPos.MutableBlockPos mpos = new BlockPos.MutableBlockPos();
        int mask = 0;
        for (int dx = -1; dx <= 1; dx++) {
            for (int dy = -1; dy <= 1; dy++) {
                for (int dz = -1; dz <= 1; dz++) {
                    if (dx == 0 && dy == 0 && dz == 0) {
                        mask |= (1 << 13);
                    } else {
                        mpos.setWithOffset(pos, dx, dy, dz);
                        if (level.getBlockState(mpos).is(SoulCrystal.SOUL_CRYSTAL_BLOCK)) {
                            mask |= (1 << idx(dx, dy, dz));
                        }
                    }
                }
            }
        }
        return mask;
    }

    private static boolean has(int mask, int dx, int dy, int dz) {
        return (mask & (1 << idx(dx, dy, dz))) != 0;
    }

    private static boolean hasDir(int mask, Direction d) {
        return has(mask, d.getStepX(), d.getStepY(), d.getStepZ());
    }

    private static boolean hasDir2(int mask, Direction d1, Direction d2) {
        return has(mask, d1.getStepX() + d2.getStepX(), d1.getStepY() + d2.getStepY(), d1.getStepZ() + d2.getStepZ());
    }

    /**
     * 子方塊 (sx, sy, sz) ∈ {-1, 0, +1}^3 是否被晶核填滿：
     * 所有非零軸向組合出的鄰格都必須是靈魂晶塊（中央恆為 true；面臂需 1 鄰；邊柱需 3 鄰；角塊需 7 鄰）。
     */
    private static boolean isSubCubeFilled(int mask, int sx, int sy, int sz) {
        for (int ix = 0; ix <= Math.abs(sx); ix++) {
            for (int iy = 0; iy <= Math.abs(sy); iy++) {
                for (int iz = 0; iz <= Math.abs(sz); iz++) {
                    if ((ix | iy | iz) != 0 && !has(mask, ix * sx, iy * sy, iz * sz)) {
                        return false;
                    }
                }
            }
        }
        return true;
    }

    /** 貼圖 UV Lock 下，每個面左半象限（u < 0.5）對應的世界方向。 */
    private static Direction leftDir(Direction face) {
        return switch (face) {
            case DOWN, UP, SOUTH -> Direction.WEST;
            case NORTH -> Direction.EAST;
            case WEST -> Direction.NORTH;
            case EAST -> Direction.SOUTH;
        };
    }

    /** 貼圖 UV Lock 下，每個面上半象限（v < 0.5）對應的世界方向。 */
    private static Direction upDir(Direction face) {
        return switch (face) {
            case DOWN -> Direction.SOUTH;
            case UP -> Direction.NORTH;
            case NORTH, SOUTH, WEST, EAST -> Direction.UP;
        };
    }

    /** 依 (H, V, D) 挑選 0..4 號 CTM 拼接圖。 */
    private static int selectTile(boolean h, boolean v, boolean d) {
        if (!h && !v) return 0;
        if (h && !v) return 1;
        if (!h && v) return 2;
        return d ? 4 : 3;
    }

    @Override
    public @Nullable Object createGeometryKey(BlockAndTintGetter level, BlockPos pos, BlockState state, RandomSource random) {
        if (!state.is(SoulCrystal.SOUL_CRYSTAL_BLOCK)) {
            return null;
        }
        return new GeometryKey(sampleNeighbors(level, pos));
    }

    @Override
    public void emitQuads(QuadEmitter emitter, BlockAndTintGetter level, BlockPos pos, BlockState state,
                          RandomSource random, Predicate<@Nullable Direction> cullTest) {
        if (!state.is(SoulCrystal.SOUL_CRYSTAL_BLOCK)) {
            super.emitQuads(emitter, level, pos, state, random, cullTest);
            return;
        }
        int mask = sampleNeighbors(level, pos);

        for (Direction face : DIRECTIONS) {
            Direction left = leftDir(face);
            Direction right = left.getOpposite();
            Direction up = upDir(face);
            Direction down = up.getOpposite();

            boolean cL = hasDir(mask, left);
            boolean cR = hasDir(mask, right);
            boolean cU = hasDir(mask, up);
            boolean cD = hasDir(mask, down);
            boolean cUL = hasDir2(mask, left, up);
            boolean cUR = hasDir2(mask, right, up);
            boolean cDL = hasDir2(mask, left, down);
            boolean cDR = hasDir2(mask, right, down);

            int tileTL = selectTile(cL, cU, cUL);
            int tileTR = selectTile(cR, cU, cUR);
            int tileBL = selectTile(cL, cD, cDL);
            int tileBR = selectTile(cR, cD, cDR);

            // 1. 外殼（Shell）：若該方向鄰格不是晶塊且未被遮擋，畫出 4 個象限的半透明外殼
            if (!hasDir(mask, face) && !cullTest.test(face)) {
                emitQuad(emitter, face, 0.0f, 0.5f, 0.0f, 0.5f, 0.0f, shellMaterials[tileTL], ChunkSectionLayer.TRANSLUCENT);
                emitQuad(emitter, face, 0.5f, 1.0f, 0.0f, 0.5f, 0.0f, shellMaterials[tileTR], ChunkSectionLayer.TRANSLUCENT);
                emitQuad(emitter, face, 0.0f, 0.5f, 0.5f, 1.0f, 0.0f, shellMaterials[tileBL], ChunkSectionLayer.TRANSLUCENT);
                emitQuad(emitter, face, 0.5f, 1.0f, 0.5f, 1.0f, 0.0f, shellMaterials[tileBR], ChunkSectionLayer.TRANSLUCENT);
            }

            // 2. 晶核（Core）：檢查法線軸 sn ∈ {0, -1} 兩層（sn = +1 的外側面緊貼鄰格晶核，屬內部接縫不畫）
            emitCoreLayerForFace(emitter, mask, face, left, right, up, down, 0, INSET,
                    tileTL, tileTR, tileBL, tileBR);
            emitCoreLayerForFace(emitter, mask, face, left, right, up, down, -1, 1.0f - INSET,
                    tileTL, tileTR, tileBL, tileBR);
        }
    }

    /** 繪製法線段 sn（sn=0 為深度 1/16 主晶核面，sn=-1 為深度 15/16 的內凹退縮側面）的晶核表面。 */
    private void emitCoreLayerForFace(QuadEmitter emitter, int mask, Direction face,
                                      Direction left, Direction right, Direction up, Direction down,
                                      int sn, float depth,
                                      int tileTL, int tileTR, int tileBL, int tileBR) {
        emitCoreQuadrant(emitter, mask, face, left, up, sn, depth, true, true, coreMaterials[tileTL]);
        emitCoreQuadrant(emitter, mask, face, right, up, sn, depth, false, true, coreMaterials[tileTR]);
        emitCoreQuadrant(emitter, mask, face, left, down, sn, depth, true, false, coreMaterials[tileBL]);
        emitCoreQuadrant(emitter, mask, face, right, down, sn, depth, false, false, coreMaterials[tileBR]);
    }

    /**
     * 針對單一 8×8 象限，檢查其 2×2 子區間（內側 7×7、水平外緣 1×7、垂直外緣 7×1、外角 1×1）哪些朝向 face 露出，
     * 並自動合併為最少數量的矩形 Quad。
     */
    private void emitCoreQuadrant(QuadEmitter emitter, int mask, Direction face,
                                  Direction dirH, Direction dirV, int sn, float depth,
                                  boolean isLeft, boolean isTop, Material.Baked mat) {
        boolean e00 = isSubFaceExposed(mask, face, dirH, dirV, 0, 0, sn);   // 內側 7×7
        boolean e10 = isSubFaceExposed(mask, face, dirH, dirV, 1, 0, sn);   // 水平外緣 1×7
        boolean e01 = isSubFaceExposed(mask, face, dirH, dirV, 0, 1, sn);   // 垂直外緣 7×1
        boolean e11 = isSubFaceExposed(mask, face, dirH, dirV, 1, 1, sn);   // 角落 1×1

        if (!e00 && !e10 && !e01 && !e11) {
            return;
        }

        // U 軸與 V 軸上的內側區間 [uIn0, uIn1] 與外緣區間 [uRim0, uRim1]
        float uIn0 = isLeft ? INSET : 0.5f;
        float uIn1 = isLeft ? 0.5f : 1.0f - INSET;
        float uRim0 = isLeft ? 0.0f : 1.0f - INSET;
        float uRim1 = isLeft ? INSET : 1.0f;
        float uFull0 = isLeft ? 0.0f : 0.5f;
        float uFull1 = isLeft ? 0.5f : 1.0f;

        float vIn0 = isTop ? INSET : 0.5f;
        float vIn1 = isTop ? 0.5f : 1.0f - INSET;
        float vRim0 = isTop ? 0.0f : 1.0f - INSET;
        float vRim1 = isTop ? INSET : 1.0f;
        float vFull0 = isTop ? 0.0f : 0.5f;
        float vFull1 = isTop ? 0.5f : 1.0f;

        // 常見情況快速合併：整塊象限（或水平/垂直延伸）合為單一 Quad
        if (e00 && e10 && e01 && e11) {
            emitQuad(emitter, face, uFull0, uFull1, vFull0, vFull1, depth, mat, ChunkSectionLayer.SOLID);
            return;
        }
        if (e00 && !e10 && !e01 && !e11) {
            emitQuad(emitter, face, uIn0, uIn1, vIn0, vIn1, depth, mat, ChunkSectionLayer.SOLID);
            return;
        }
        if (e00 && e10 && !e01 && !e11) {
            emitQuad(emitter, face, uFull0, uFull1, vIn0, vIn1, depth, mat, ChunkSectionLayer.SOLID);
            return;
        }
        if (e00 && !e10 && e01 && !e11) {
            emitQuad(emitter, face, uIn0, uIn1, vFull0, vFull1, depth, mat, ChunkSectionLayer.SOLID);
            return;
        }
        if (e00 && e10 && e01 && !e11) {
            // L 形內凹轉角：主塊 (uIn × vFull) + 水平側邊條 (uRim × vIn)
            emitQuad(emitter, face, uIn0, uIn1, vFull0, vFull1, depth, mat, ChunkSectionLayer.SOLID);
            emitQuad(emitter, face, uRim0, uRim1, vIn0, vIn1, depth, mat, ChunkSectionLayer.SOLID);
            return;
        }

        // 其他局部邊緣露出的組合（例如連接臂的 1 px 側面）逐格合併繪製
        if (e00) emitQuad(emitter, face, uIn0, uIn1, vIn0, vIn1, depth, mat, ChunkSectionLayer.SOLID);
        if (e10 && e11) {
            emitQuad(emitter, face, uRim0, uRim1, vFull0, vFull1, depth, mat, ChunkSectionLayer.SOLID);
        } else {
            if (e10) emitQuad(emitter, face, uRim0, uRim1, vIn0, vIn1, depth, mat, ChunkSectionLayer.SOLID);
            if (e11) emitQuad(emitter, face, uRim0, uRim1, vRim0, vRim1, depth, mat, ChunkSectionLayer.SOLID);
        }
        if (e01) emitQuad(emitter, face, uIn0, uIn1, vRim0, vRim1, depth, mat, ChunkSectionLayer.SOLID);
    }

    /**
     * 檢查子方塊 (sh along dirH, sv along dirV, sn along face) 是否填滿，且其在 +face 方向的鄰接子方塊未填滿。
     */
    private static boolean isSubFaceExposed(int mask, Direction face, Direction dirH, Direction dirV,
                                            int sh, int sv, int sn) {
        int sx = sh * dirH.getStepX() + sv * dirV.getStepX() + sn * face.getStepX();
        int sy = sh * dirH.getStepY() + sv * dirV.getStepY() + sn * face.getStepY();
        int sz = sh * dirH.getStepZ() + sv * dirV.getStepZ() + sn * face.getStepZ();
        if (!isSubCubeFilled(mask, sx, sy, sz)) {
            return false;
        }
        int nx = sx + face.getStepX();
        int ny = sy + face.getStepY();
        int nz = sz + face.getStepZ();
        return !isSubCubeFilled(mask, nx, ny, nz);
    }

    private static void emitQuad(QuadEmitter emitter, Direction face,
                                 float u0, float u1, float v0, float v1, float depth,
                                 Material.Baked material, ChunkSectionLayer layer) {
        emitter.square(face, u0, 1.0f - v1, u1, 1.0f - v0, depth)
                .materialBake(material, MutableQuadView.BAKE_LOCK_UV)
                .chunkLayer(layer)
                .emissive(true)
                .ambientOcclusion(TriState.FALSE)
                .shadeDirectionOverride(Direction.UP)
                .emit();
    }
}
