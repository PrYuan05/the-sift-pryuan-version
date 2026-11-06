package pryuan05.pysift.progression;

import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.PySift;

/**
 * 故事線（MODDING_ROADMAP §4.7）的成就：都是 minecraft:impossible 條件，由遊戲事件在這裡頒發。
 * 成就 JSON 與語系由 tools/progression/build_story.py 產生。
 */
public final class StoryTriggers {
    private StoryTriggers() {
    }

    /** 歌者倒唱八音、安撫了監守者。 */
    public static void wardenSoothed(ServerPlayer player) {
        award(player, "warden_soothed");
    }

    /** 哀悼者泡在靈液裡變回歌者。 */
    public static void mournerCured(ServerLevel level, Vec3 at) {
        nearby(level, at, "mourner_cured");
    }

    /** 監守者在隙浮或靈液裡長回皮毛，變成隙浮守衛。 */
    public static void wardenCured(ServerLevel level, Vec3 at) {
        nearby(level, at, "warden_cured");
    }

    /** 擊敗幽匿巨怪後，這個世界的腐爛開始退去。 */
    public static void rotStilled(ServerLevel level, Vec3 at) {
        nearby(level, at, "rot_stilled");
    }

    private static void nearby(ServerLevel level, Vec3 at, String name) {
        for (ServerPlayer p : level.getEntitiesOfClass(ServerPlayer.class, new AABB(at, at).inflate(32.0))) {
            award(p, name);
        }
    }

    public static void award(ServerPlayer player, String name) {
        AdvancementHolder adv = player.level().getServer().getAdvancements().get(PySift.id("story/" + name));
        if (adv != null) {
            player.getAdvancements().award(adv, "done");
        }
    }
}
