package pryuan05.pysift.block;

import net.minecraft.world.level.Level;

/**
 * 隙浮的三個時段（和 data/pysift/timeline/sift_day.json 一致，跟主世界共用時鐘）：
 * 晨間 23000~3000、日間 3500~11000、夜間 13500~22000，中間平滑過渡。
 * 給特效用（夜晚發光的傳送門、夜光植物的粒子）；兩端都能呼叫。
 */
public final class SiftDayPhase {
    private SiftDayPhase() {
    }

    /** 0 = 白天，1 = 深夜；黃昏 12000~13500 漸亮、黎明 22000~23300 漸暗。 */
    public static float night(Level level) {
        if (level == null) {
            return 0.0f;
        }
        long t = Math.floorMod(level.getDefaultClockTime(), 24000L);
        if (t >= 13500 && t <= 22000) {
            return 1.0f;
        }
        if (t > 12000 && t < 13500) {
            return smooth((t - 12000) / 1500.0f);
        }
        if (t > 22000 && t < 23300) {
            return 1.0f - smooth((t - 22000) / 1300.0f);
        }
        return 0.0f;
    }

    /** 0 = 不是早晨，1 = 清晨（23300~2000），之後到 3500 漸漸變成白天。 */
    public static float morning(Level level) {
        if (level == null) {
            return 0.0f;
        }
        long t = Math.floorMod(level.getDefaultClockTime(), 24000L);
        if (t >= 23300 || t <= 2000) {
            return 1.0f;
        }
        if (t > 2000 && t < 3500) {
            return 1.0f - smooth((t - 2000) / 1500.0f);
        }
        if (t > 22000 && t < 23300) {
            return smooth((t - 22000) / 1300.0f);
        }
        return 0.0f;
    }

    private static float smooth(float u) {
        u = Math.max(0.0f, Math.min(1.0f, u));
        return u * u * (3 - 2 * u);
    }
}
