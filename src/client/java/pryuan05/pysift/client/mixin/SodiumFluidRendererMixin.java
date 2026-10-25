package pryuan05.pysift.client.mixin;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.llamalad7.mixinextras.sugar.Local;
import net.caffeinemc.mods.sodium.client.model.quad.ModelQuadViewMutable;
import net.caffeinemc.mods.sodium.client.render.chunk.compile.pipeline.DefaultFluidRenderer;
import net.minecraft.client.renderer.block.FluidModel;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.resources.model.sprite.Material;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.material.FluidState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import pryuan05.pysift.fluid.ModFluids;

/**
 * Sodium 版的靈液世界座標 UV（原版路徑見 {@link FluidRendererMixin}）。裝了 Sodium 時區塊網格由
 * Sodium 的 DefaultFluidRenderer 產生，原版 FluidRenderer 的 mixin 不會被用到，靈液每格都會貼一整張 32×32 格的大貼圖。
 * <ul>
 *   <li>流動頂面、側面的 flowingMaterial 換成 stillMaterial（大貼圖），和原版路徑一樣。</li>
 *   <li>所有頂點都經過 setVertex(quad, i, x, y, z, u, v)，x/y/z 是格內座標：頂面、底面的 u 沿世界 x、v 沿世界 z；
 *       側面的頂點，固定那一軸是 0.001 / 0.999（貼著格邊），變動那一軸剛好是 0 或 1，
 *       所以 x 不是 0/1 時是東西向的面（u 沿 z），否則是南北向的面（u 沿 x）；v 沿世界高度往下。</li>
 *   <li>貼著玻璃／樹葉的 overlay 貼圖不是大貼圖，維持 Sodium 原本的 UV。</li>
 * </ul>
 * {@code @Pseudo} + {@code require = 0}：沒裝 Sodium 時整個 mixin 略過；Sodium 改版、注入點找不到時退回 Sodium 原本的畫法，不會當機。
 */
@Pseudo
@Mixin(value = DefaultFluidRenderer.class, remap = false)
public abstract class SodiumFluidRendererMixin {
    private static final int SPIRIT_TILE = 32;   // blocks per still-texture tile (512 px; tools/texture_pipeline/spirit_liquid.py)

    private static boolean pysift$isSpirit(FluidState fluidState) {
        return ModFluids.SPIRIT_LIQUID.isSame(fluidState.getType());
    }

    /** (world cell in the 32x32 tile + offset inside the block 0..1) / 32; never leaves the sprite. */
    private static float pysift$cell(int coord, float local) {
        return (Math.floorMod(coord, SPIRIT_TILE) + local) / SPIRIT_TILE;
    }

    private static boolean pysift$onEdge(float c) {
        return c == 0.0f || c == 1.0f;
    }

    @WrapOperation(method = "render", require = 0, at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/block/FluidModel;flowingMaterial()Lnet/minecraft/client/resources/model/sprite/Material$Baked;"))
    private Material.Baked pysift$bigSprite(FluidModel model, Operation<Material.Baked> original,
                                            @Local(argsOnly = true) FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? model.stillMaterial() : original.call(model);
    }

    @WrapOperation(method = "render", require = 0, at = @At(value = "INVOKE",
            target = "Lnet/caffeinemc/mods/sodium/client/render/chunk/compile/pipeline/DefaultFluidRenderer;setVertex(Lnet/caffeinemc/mods/sodium/client/model/quad/ModelQuadViewMutable;IFFFFF)V"))
    private void pysift$worldUv(ModelQuadViewMutable quad, int i, float x, float y, float z, float u, float v,
                                Operation<Void> original,
                                @Local(argsOnly = true) FluidState fluidState, @Local(argsOnly = true, ordinal = 0) BlockPos pos,
                                @Local(argsOnly = true) FluidModel model) {
        TextureAtlasSprite sprite = quad.getSprite();
        if (pysift$isSpirit(fluidState) && sprite != null && sprite == model.stillMaterial().sprite()) {
            if (pysift$onEdge(x) && pysift$onEdge(z)) {                                   // top (incl. sloped) and bottom faces
                u = sprite.getU(pysift$cell(pos.getX(), x));
                v = sprite.getV(pysift$cell(pos.getZ(), z));
            } else {                                       // walls: u along the face, v down the world height
                u = pysift$onEdge(x) ? sprite.getU(pysift$cell(pos.getX(), x)) : sprite.getU(pysift$cell(pos.getZ(), z));
                v = sprite.getV(pysift$cell(-pos.getY() - 1, 1.0f - y));
            }
        }
        original.call(quad, i, x, y, z, u, v);
    }
}
