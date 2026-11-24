package pryuan05.pysift.client.particle;

import net.fabricmc.fabric.api.client.particle.v1.ParticleProviderRegistry;
import pryuan05.pysift.particle.ModParticles;

/** 靈魂粒子的客戶端註冊（包含連續曲線光帶渲染器 SoulWispRenderer）。貼圖清單在 assets/pysift/particles/*.json。 */
public final class SoulParticlesClient {
    private SoulParticlesClient() {
    }

    public static void register() {
        SoulWispRenderer.register();
        ParticleProviderRegistry registry = ParticleProviderRegistry.getInstance();
        registry.register(ModParticles.SOUL_TRAIL, sprites -> (options, level, x, y, z, xd, yd, zd, random) -> {
            float size = 0.026F + random.nextFloat() * 0.022F;
            boolean bright = random.nextInt(3) == 0;
            float r = bright ? 0.72F : 0.24F;
            float g = bright ? 0.98F : 0.90F;
            float b = 1.0F;
            int life = 16 + random.nextInt(16);
            return new SoulTrailParticle(level, x, y, z, xd, yd, zd, sprites.first(), size, r, g, b, 0.92F, life);
        });
        registry.register(ModParticles.SOUL_WISP, sprites -> (options, level, x, y, z, xd, yd, zd, random) ->
                new SoulWispParticle(level, x, y, z, xd, yd, zd, sprites.get(random)));
    }
}
