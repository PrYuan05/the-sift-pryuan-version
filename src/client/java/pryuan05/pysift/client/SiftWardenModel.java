package pryuan05.pysift.client;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.monster.warden.WardenModel;
import net.minecraft.client.renderer.entity.state.WardenRenderState;
import net.minecraft.util.Mth;

/**
 * 隙浮守衛的模型：原版監守者，多一個「坐下等待」的姿勢（{@link SiftWardenRenderer.State#sit}，0 站 ~ 1 坐）。
 * 坐下時整隻往下沉、兩腿往前伸直平放在地上、身體微微前傾、雙手搭在膝上、頭稍微低下，觸鬚照常擺動。
 * 本體和五層發光層都用這個模型，姿勢才會一致。
 */
public class SiftWardenModel extends WardenModel {
    /** 髖部離地 13 格（腿長）；腿往前平放後腿的厚度一半是 3 格，所以往下沉 10 格。 */
    private static final float SINK = 10.0f;

    public SiftWardenModel(ModelPart root) {
        super(root);
    }

    @Override
    public void setupAnim(WardenRenderState state) {
        super.setupAnim(state);
        float sit = state instanceof SiftWardenRenderer.State s ? s.sit : 0.0f;
        if (sit <= 0.0f) {
            return;
        }
        float ease = sit * sit * (3.0f - 2.0f * sit);   // smoothstep
        bone.y += SINK * ease;
        leftLeg.xRot = Mth.lerp(ease, leftLeg.xRot, -Mth.HALF_PI);
        rightLeg.xRot = Mth.lerp(ease, rightLeg.xRot, -Mth.HALF_PI);
        leftLeg.yRot = Mth.lerp(ease, leftLeg.yRot, -0.12f);
        rightLeg.yRot = Mth.lerp(ease, rightLeg.yRot, 0.12f);
        body.xRot = Mth.lerp(ease, body.xRot, 0.22f);
        leftArm.xRot = Mth.lerp(ease, leftArm.xRot, -0.75f);
        rightArm.xRot = Mth.lerp(ease, rightArm.xRot, -0.75f);
        leftArm.zRot = Mth.lerp(ease, leftArm.zRot, -0.1f);
        rightArm.zRot = Mth.lerp(ease, rightArm.zRot, 0.1f);
        head.xRot = Mth.lerp(ease, head.xRot, head.xRot * 0.5f + 0.18f);
    }
}
