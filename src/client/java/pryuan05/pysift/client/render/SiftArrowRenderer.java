package pryuan05.pysift.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.ArrowRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.ArrowRenderState;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import pryuan05.pysift.PySift;

/**
 * 用原版箭矢模型、換成自己貼圖的投擲物渲染器（貼圖版面同原版 arrow.png，可以是 32x32 或兩倍解析度 64x64）。
 * scale 放大整支箭（標槍用 2 倍）。貼圖由使用者繪製，見 tools/items/install_projectile_art.py。
 */
public class SiftArrowRenderer<T extends AbstractArrow> extends ArrowRenderer<T, ArrowRenderState> {
    private final Identifier texture;
    private final float scale;

    public SiftArrowRenderer(EntityRendererProvider.Context context, String texture, float scale) {
        super(context);
        this.texture = PySift.id("textures/entity/projectiles/" + texture + ".png");
        this.scale = scale;
    }

    @Override
    protected Identifier getTextureLocation(ArrowRenderState state) {
        return texture;
    }

    @Override
    public ArrowRenderState createRenderState() {
        return new ArrowRenderState();
    }

    @Override
    public void submit(ArrowRenderState state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        poseStack.pushPose();
        poseStack.scale(scale, scale, scale);
        super.submit(state, poseStack, collector, camera);
        poseStack.popPose();
    }
}
