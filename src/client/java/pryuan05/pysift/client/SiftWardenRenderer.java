package pryuan05.pysift.client;

import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.WardenRenderer;
import net.minecraft.client.renderer.entity.layers.LivingEntityEmissiveLayer;
import net.minecraft.client.renderer.entity.state.WardenRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.monster.warden.Warden;
import pryuan05.pysift.PySift;
import pryuan05.pysift.entity.mob.SiftWardenEntity;

/**
 * 隙浮守衛：原版監守者的模型與動作，換成 tools/models/build_sift_warden.py 畫的赤紅毛皮與粉洋紅的發光層。
 * 發光層和原版 WardenRenderer 的五層一樣（生物光、兩組脈動斑點、觸鬚、心臟），只是貼圖換掉。
 * 本體與發光層都換成 {@link SiftWardenModel}，多一個坐下等待的姿勢。
 */
public class SiftWardenRenderer extends WardenRenderer {
    private static final String DIR = "textures/entity/sift_warden/sift_warden";
    private static final Identifier TEXTURE = PySift.id(DIR + ".png");
    private static final Identifier BIOLUMINESCENT = PySift.id(DIR + "_bioluminescent_layer.png");
    private static final Identifier HEART = PySift.id(DIR + "_heart.png");
    private static final Identifier SPOTS_1 = PySift.id(DIR + "_pulsating_spots_1.png");
    private static final Identifier SPOTS_2 = PySift.id(DIR + "_pulsating_spots_2.png");

    /** 多帶坐下進度的渲染狀態。 */
    public static class State extends WardenRenderState {
        public float sit;
    }

    public SiftWardenRenderer(EntityRendererProvider.Context context) {
        super(context);
        this.model = new SiftWardenModel(context.bakeLayer(ModelLayers.WARDEN));
        this.layers.clear();
        this.addLayer(new LivingEntityEmissiveLayer<>(this, s -> BIOLUMINESCENT, (s, t) -> 1.0f,
                new SiftWardenModel(context.bakeLayer(ModelLayers.WARDEN_BIOLUMINESCENT)), RenderTypes::entityTranslucentEmissive, false));
        this.addLayer(new LivingEntityEmissiveLayer<>(this, s -> SPOTS_1, (s, t) -> Math.max(0.0f, Mth.cos(t * 0.045f) * 0.25f),
                new SiftWardenModel(context.bakeLayer(ModelLayers.WARDEN_PULSATING_SPOTS)), RenderTypes::entityTranslucentEmissive, false));
        this.addLayer(new LivingEntityEmissiveLayer<>(this, s -> SPOTS_2,
                (s, t) -> Math.max(0.0f, Mth.cos(t * 0.045f + (float) Math.PI) * 0.25f),
                new SiftWardenModel(context.bakeLayer(ModelLayers.WARDEN_PULSATING_SPOTS)), RenderTypes::entityTranslucentEmissive, false));
        this.addLayer(new LivingEntityEmissiveLayer<>(this, s -> TEXTURE, (s, t) -> s.tendrilAnimation,
                new SiftWardenModel(context.bakeLayer(ModelLayers.WARDEN_TENDRILS)), RenderTypes::entityTranslucentEmissive, false));
        this.addLayer(new LivingEntityEmissiveLayer<>(this, s -> HEART, (s, t) -> s.heartAnimation,
                new SiftWardenModel(context.bakeLayer(ModelLayers.WARDEN_HEART)), RenderTypes::entityTranslucentEmissive, false));
    }

    @Override
    public WardenRenderState createRenderState() {
        return new State();
    }

    @Override
    public void extractRenderState(Warden warden, WardenRenderState state, float partialTick) {
        super.extractRenderState(warden, state, partialTick);
        if (state instanceof State s) {
            s.sit = warden instanceof SiftWardenEntity sift ? sift.getSitAmount(partialTick) : 0.0f;
        }
    }

    @Override
    public Identifier getTextureLocation(WardenRenderState state) {
        return TEXTURE;
    }
}
