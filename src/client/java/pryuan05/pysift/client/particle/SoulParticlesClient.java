package pryuan05.pysift.client.particle;

import net.fabricmc.fabric.api.client.particle.v1.ParticleProviderRegistry;
import net.minecraft.client.particle.SpriteSet;
import pryuan05.pysift.particle.ModParticles;

/** 靈魂粒子的客戶端註冊。貼圖清單在 assets/pysift/particles/*.json。 */
public final class SoulParticlesClient {
    /** soul_trail 的貼圖組；soul_wisp 產生光尾時要用。 */
    private static SpriteSet trailSprites;

    private SoulParticlesClient() {
    }

    public static void register() {
        ParticleProviderRegistry registry = ParticleProviderRegistry.getInstance();
        registry.register(ModParticles.SOUL_TRAIL, sprites -> {
            trailSprites = sprites;
            return (options, level, x, y, z, xd, yd, zd, random) ->
                    new SoulTrailParticle(level, x, y, z, sprites.first(), 0.12F, 0.6F, 0.9F, 1.0F, 0.85F, 20);
        });
        registry.register(ModParticles.SOUL_WISP, sprites -> (options, level, x, y, z, xd, yd, zd, random) ->
                new SoulWispParticle(level, x, y, z, xd, yd, zd, sprites.get(random), trailSprites));
    }
}
