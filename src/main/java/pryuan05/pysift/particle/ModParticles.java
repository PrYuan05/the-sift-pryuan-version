package pryuan05.pysift.particle;

import net.fabricmc.fabric.api.particle.v1.FabricParticleTypes;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.BuiltInRegistries;
import pryuan05.pysift.PySift;

/**
 * 粒子類型。外觀與行為在客戶端（client/particle/），貼圖由 tools/worldgen/make_soul_wisp_textures.py 產生。
 * <ul>
 *   <li>soul_wisp：從靈液冒出、螺旋上升的靈魂（藍白發光的小鬼臉），會在身後拖出光尾。</li>
 *   <li>soul_trail：光尾與光暈的柔光點（靈魂粒子在客戶端自己產生，也可以用 /particle 單獨叫出）。</li>
 * </ul>
 */
public final class ModParticles {
    public static final SimpleParticleType SOUL_WISP = register("soul_wisp");
    public static final SimpleParticleType SOUL_TRAIL = register("soul_trail");

    private ModParticles() {
    }

    private static SimpleParticleType register(String name) {
        return Registry.register(BuiltInRegistries.PARTICLE_TYPE, PySift.id(name), FabricParticleTypes.simple(false));
    }

    public static void register() {
        PySift.LOGGER.info("Registered particles {}, {}", BuiltInRegistries.PARTICLE_TYPE.getKey(SOUL_WISP),
                BuiltInRegistries.PARTICLE_TYPE.getKey(SOUL_TRAIL));
    }
}
