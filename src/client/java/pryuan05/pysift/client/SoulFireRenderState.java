package pryuan05.pysift.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.resources.model.sprite.SpriteId;
import net.minecraft.resources.Identifier;
import pryuan05.pysift.effect.SoulBurn;

/**
 * 加在 EntityRenderState 上（EntityRenderStateMixin）：這個實體身上燒的是靈魂火，
 * 火焰改用原版靈魂火的兩張貼圖（FlameFeatureRendererMixin）。
 */
public interface SoulFireRenderState {
    SpriteId SOUL_FIRE_0 = new SpriteId(TextureAtlas.LOCATION_BLOCKS, Identifier.withDefaultNamespace("block/soul_fire_0"));
    SpriteId SOUL_FIRE_1 = new SpriteId(TextureAtlas.LOCATION_BLOCKS, Identifier.withDefaultNamespace("block/soul_fire_1"));

    boolean pysift$soulFire();

    void pysift$setSoulFire(boolean soulFire);

    /** 自己（第一人稱）身上是否在燒靈魂火：螢幕下方的火焰也換成靈魂火（ScreenEffectRendererMixin）。 */
    static boolean localPlayerOnSoulFire() {
        var player = Minecraft.getInstance().player;
        return player != null && player.getAttachedOrElse(SoulBurn.FIRE, false);
    }
}
