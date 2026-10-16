package pryuan05.pysift.client.mixin;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.llamalad7.mixinextras.sugar.Local;
import net.minecraft.core.Direction;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.client.renderer.block.FluidModel;
import net.minecraft.client.renderer.block.FluidRenderer;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.resources.model.sprite.Material;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import pryuan05.pysift.fluid.ModFluids;

/**
 * 靈液靜止頂面改用世界座標 UV：still 貼圖是 8×8 格的大圖，每格只取其中對應座標的 1/8 × 1/8，
 * 整片池面因此連續、看不到格線（原版每格都貼整張 sprite）。
 * <ul>
 *   <li>靜止頂面：tesselate 裡「沒有流向」分支的 getU0/getV0/getV1/getU1（各自的第一次呼叫，u 沿 x、v 沿 z）。</li>
 *   <li>流動頂面（高度不滿、有流向）：原版改用流動貼圖並依流向旋轉 UV，每格方向不同所以看得出格線。
 *       靈液在這裡也換成靜止大貼圖（flowingMaterial 第一次呼叫），四組 getU(F)/getV(F)（ordinal 0~3，
 *       依序為角落 (x0,z0)、(x0,z1)、(x1,z1)、(x1,z0)）換成世界座標，斜面也和旁邊連成一片。</li>
 *   <li>底面：同靜止頂面（stillMaterial 第二次使用，getU0/getU1/getV0/getV1 的 ordinal 1）。</li>
 *   <li>側面（往下流的牆面、池邊）：原版每格貼整張流動貼圖。靈液改用靜止大貼圖，u 依面向沿世界 x 或 z、
 *       v 沿世界高度往下取 1/8 格（flowingMaterial 第二次呼叫、getU(F) ordinal 4~5、getV(F) ordinal 4~6），
 *       上下左右相鄰的牆面因此連成一片。貼著玻璃／樹葉時的 overlay 貼圖維持原版。</li>
 * </ul>
 * 其他液體不受影響。
 */
@Mixin(FluidRenderer.class)
public abstract class FluidRendererMixin {
    private static final int SPIRIT_TILE = 8;

    private static boolean pysift$isSpirit(FluidState fluidState) {
        return ModFluids.SPIRIT_LIQUID.isSame(fluidState.getType());
    }

    private static float pysift$cell(int coord, int edge) {
        return (Math.floorMod(coord, SPIRIT_TILE) + edge) / (float) SPIRIT_TILE;
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getU0()F", ordinal = 0))
    private float pysift$stillU0(TextureAtlasSprite sprite, Operation<Float> original,
                                 BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getU(pysift$cell(pos.getX(), 0)) : original.call(sprite);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getU1()F", ordinal = 0))
    private float pysift$stillU1(TextureAtlasSprite sprite, Operation<Float> original,
                                 BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getU(pysift$cell(pos.getX(), 1)) : original.call(sprite);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getV0()F", ordinal = 0))
    private float pysift$stillV0(TextureAtlasSprite sprite, Operation<Float> original,
                                 BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getV(pysift$cell(pos.getZ(), 0)) : original.call(sprite);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getV1()F", ordinal = 0))
    private float pysift$stillV1(TextureAtlasSprite sprite, Operation<Float> original,
                                 BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getV(pysift$cell(pos.getZ(), 1)) : original.call(sprite);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/block/FluidModel;flowingMaterial()Lnet/minecraft/client/resources/model/sprite/Material$Baked;",
            ordinal = 0))
    private Material.Baked pysift$flowTopMaterial(FluidModel model, Operation<Material.Baked> original,
                                                  BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? model.stillMaterial() : original.call(model);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getU(F)F", ordinal = 0))
    private float pysift$flowTopU0(TextureAtlasSprite sprite, float f, Operation<Float> original,
                                   BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getU(pysift$cell(pos.getX(), 0)) : original.call(sprite, f);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getV(F)F", ordinal = 0))
    private float pysift$flowTopV0(TextureAtlasSprite sprite, float f, Operation<Float> original,
                                   BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getV(pysift$cell(pos.getZ(), 0)) : original.call(sprite, f);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getU(F)F", ordinal = 1))
    private float pysift$flowTopU1(TextureAtlasSprite sprite, float f, Operation<Float> original,
                                   BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getU(pysift$cell(pos.getX(), 0)) : original.call(sprite, f);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getV(F)F", ordinal = 1))
    private float pysift$flowTopV1(TextureAtlasSprite sprite, float f, Operation<Float> original,
                                   BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getV(pysift$cell(pos.getZ(), 1)) : original.call(sprite, f);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getU(F)F", ordinal = 2))
    private float pysift$flowTopU2(TextureAtlasSprite sprite, float f, Operation<Float> original,
                                   BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getU(pysift$cell(pos.getX(), 1)) : original.call(sprite, f);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getV(F)F", ordinal = 2))
    private float pysift$flowTopV2(TextureAtlasSprite sprite, float f, Operation<Float> original,
                                   BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getV(pysift$cell(pos.getZ(), 1)) : original.call(sprite, f);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getU(F)F", ordinal = 3))
    private float pysift$flowTopU3(TextureAtlasSprite sprite, float f, Operation<Float> original,
                                   BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getU(pysift$cell(pos.getX(), 1)) : original.call(sprite, f);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getV(F)F", ordinal = 3))
    private float pysift$flowTopV3(TextureAtlasSprite sprite, float f, Operation<Float> original,
                                   BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getV(pysift$cell(pos.getZ(), 0)) : original.call(sprite, f);
    }

    // ------------------------------------------------------------------ bottom face (stillMaterial 2nd use)
    // vertices: (x, z) u0 v0, (x+1, z) u1 v0, (x+1, z+1) u1 v1, (x, z+1) u0 v1 - same layout as the still top

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getU0()F", ordinal = 1))
    private float pysift$bottomU0(TextureAtlasSprite sprite, Operation<Float> original,
                                  BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getU(pysift$cell(pos.getX(), 0)) : original.call(sprite);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getU1()F", ordinal = 1))
    private float pysift$bottomU1(TextureAtlasSprite sprite, Operation<Float> original,
                                  BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getU(pysift$cell(pos.getX(), 1)) : original.call(sprite);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getV0()F", ordinal = 1))
    private float pysift$bottomV0(TextureAtlasSprite sprite, Operation<Float> original,
                                  BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getV(pysift$cell(pos.getZ(), 0)) : original.call(sprite);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getV1()F", ordinal = 1))
    private float pysift$bottomV1(TextureAtlasSprite sprite, Operation<Float> original,
                                  BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? sprite.getV(pysift$cell(pos.getZ(), 1)) : original.call(sprite);
    }

    // ------------------------------------------------------------------ side faces (the falling / edge walls)
    // Vanilla gives every side face the whole flowing sprite: u = getU(0) .. getU(0.5) across the face,
    // v = getV((1 - h) * 0.5) at the top corners (h = fluid height there) .. getV(0.5) at the bottom.
    // For spirit liquid the side uses the big still sprite instead, with world-space cells: u follows x (north/south
    // faces) or z (west/east faces), v follows the world height going down, so stacked and neighbouring walls join up.
    // The overlay sprite (next to glass / leaves) keeps vanilla UVs.

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/block/FluidModel;flowingMaterial()Lnet/minecraft/client/resources/model/sprite/Material$Baked;",
            ordinal = 1))
    private Material.Baked pysift$sideMaterial(FluidModel model, Operation<Material.Baked> original,
                                               BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState) {
        return pysift$isSpirit(fluidState) ? model.stillMaterial() : original.call(model);
    }

    /** Horizontal cell edge of a side face corner: which world axis and which end depends on the face direction. */
    private static float pysift$sideU(Direction direction, BlockPos pos, boolean firstCorner) {
        return switch (direction) {
            case NORTH -> pysift$cell(pos.getX(), firstCorner ? 0 : 1);
            case SOUTH -> pysift$cell(pos.getX(), firstCorner ? 1 : 0);
            case WEST -> pysift$cell(pos.getZ(), firstCorner ? 1 : 0);
            default -> pysift$cell(pos.getZ(), firstCorner ? 0 : 1);   // EAST
        };
    }

    /** Vertical cell coordinate: f = (1 - h) * 0.5 from vanilla, so 1 - h = 2f; cells count downwards in world y. */
    private static float pysift$sideV(BlockPos pos, float f) {
        return (Math.floorMod(-pos.getY() - 1, SPIRIT_TILE) + 2.0f * f) / SPIRIT_TILE;
    }

    private static boolean pysift$bigSide(FluidState fluidState, FluidModel model, TextureAtlasSprite sprite) {
        return pysift$isSpirit(fluidState) && sprite == model.stillMaterial().sprite();
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getU(F)F", ordinal = 4))
    private float pysift$sideU0(TextureAtlasSprite sprite, float f, Operation<Float> original,
                                BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState,
                                @Local Direction direction, @Local FluidModel model) {
        return pysift$bigSide(fluidState, model, sprite) ? sprite.getU(pysift$sideU(direction, pos, true)) : original.call(sprite, f);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getU(F)F", ordinal = 5))
    private float pysift$sideU1(TextureAtlasSprite sprite, float f, Operation<Float> original,
                                BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState,
                                @Local Direction direction, @Local FluidModel model) {
        return pysift$bigSide(fluidState, model, sprite) ? sprite.getU(pysift$sideU(direction, pos, false)) : original.call(sprite, f);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getV(F)F", ordinal = 4))
    private float pysift$sideVTop0(TextureAtlasSprite sprite, float f, Operation<Float> original,
                                   BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState,
                                   @Local FluidModel model) {
        return pysift$bigSide(fluidState, model, sprite) ? sprite.getV(pysift$sideV(pos, f)) : original.call(sprite, f);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getV(F)F", ordinal = 5))
    private float pysift$sideVTop1(TextureAtlasSprite sprite, float f, Operation<Float> original,
                                   BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState,
                                   @Local FluidModel model) {
        return pysift$bigSide(fluidState, model, sprite) ? sprite.getV(pysift$sideV(pos, f)) : original.call(sprite, f);
    }

    @WrapOperation(method = "tesselate", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/renderer/texture/TextureAtlasSprite;getV(F)F", ordinal = 6))
    private float pysift$sideVBottom(TextureAtlasSprite sprite, float f, Operation<Float> original,
                                     BlockAndTintGetter level, BlockPos pos, FluidRenderer.Output output, BlockState blockState, FluidState fluidState,
                                     @Local FluidModel model) {
        return pysift$bigSide(fluidState, model, sprite) ? sprite.getV(pysift$sideV(pos, f)) : original.call(sprite, f);
    }
}
