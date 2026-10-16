package pryuan05.pysift.client.mixin;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.mojang.blaze3d.framegraph.FrameGraphBuilder;
import com.mojang.blaze3d.pipeline.RenderTarget;
import com.mojang.blaze3d.resource.ResourceHandle;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.renderpearl.api.buffers.GpuBuffer;
import com.mojang.renderpearl.api.buffers.GpuBufferSlice;
import com.mojang.renderpearl.api.device.GpuDevice;
import net.minecraft.client.renderer.PostPass;
import net.minecraft.resources.Identifier;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pryuan05.pysift.client.SoulDeprivationVision;

import java.nio.ByteBuffer;
import java.util.Map;
import java.util.function.Supplier;

/**
 * 讓靈魂剝奪的伏聆視野（pysift:post/sculk_vision）拿到每幀的相機資料。
 * 原版 post_effect 的 uniform 是 json 裡的固定值，緩衝區建立時只有 UNIFORM 用途、之後不能寫入。
 * <ul>
 *   <li>只對我們自己的 pass（pipeline 名稱含 pysift:）在建立緩衝區時多加 COPY_DST。</li>
 *   <li>每幀 addToFrame 開頭，把 SculkCamera（反投影矩陣、相機位置、強度、深度慣例）寫進去。</li>
 * </ul>
 * 其他（原版或別的 mod）的 post pass 完全不受影響。
 */
@Mixin(PostPass.class)
public abstract class PostPassMixin {
    @Shadow
    @Final
    private String name;

    @Shadow
    @Final
    private Map<String, GpuBuffer> customUniforms;

    @WrapOperation(method = "<init>", at = @At(value = "INVOKE",
            target = "Lcom/mojang/renderpearl/api/device/GpuDevice;createBuffer(Ljava/util/function/Supplier;ILjava/nio/ByteBuffer;)Lcom/mojang/renderpearl/api/buffers/GpuBuffer;"))
    private GpuBuffer pysift$writableUniforms(GpuDevice device, Supplier<String> label, int usage, ByteBuffer data,
                                              Operation<GpuBuffer> original) {
        boolean ours = this.name != null && this.name.contains("pysift");
        return original.call(device, label, ours ? usage | GpuBuffer.USAGE_COPY_DST : usage, data);
    }

    @Inject(method = "addToFrame", at = @At("HEAD"))
    private void pysift$updateSculkCamera(FrameGraphBuilder frame, Map<Identifier, ResourceHandle<RenderTarget>> targets,
                                          GpuBufferSlice shaderOrthoMatrix, CallbackInfo ci) {
        if (this.name == null || !this.name.contains("pysift")) {
            return;
        }
        GpuBuffer buffer = this.customUniforms.get(SoulDeprivationVision.UNIFORM_BLOCK);
        if (buffer == null || (buffer.usage() & GpuBuffer.USAGE_COPY_DST) == 0) {
            return;
        }
        ByteBuffer data = SoulDeprivationVision.cameraUniform();
        RenderSystem.getDevice().createCommandEncoder().writeToBuffer(buffer.slice(), data);
    }
}
