package pryuan05.pysift.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.PySift;

/**
 * 第一人稱的「手持物理」：隙浮的物品拿在手上有重量。
 * <ul>
 *   <li>轉動視角時，手上的東西落在後面、再像彈簧一樣追上來，最後微微回彈（欠阻尼的彈簧，阻尼比 0.55）。</li>
 *   <li>左右平移時往移動方向的反側傾斜一點。</li>
 *   <li>{@link #kick}：出手的反作用（重錘砸地往下一沉、法杖發射往後一頓、標槍丟出往前一甩）。</li>
 * </ul>
 * 只套在隙浮自己的物品上（方塊除外），不改原版物品，也不跟其他第一人稱動畫模組搶原版物品。
 * 每一幀更新一次（兩隻手共用同一個狀態），用實際經過的時間積分，所以和幀率無關。
 */
public final class HandMotion {
    private static final float STIFFNESS = 140.0f;
    private static final float DAMPING = 2.0f * (float) Math.sqrt(STIFFNESS) * 0.55f;
    private static final float LIMIT = 0.16f;

    private static boolean started;
    private static long lastFrame;
    private static float lastYaw, lastPitch;
    /** 偏移（方塊）與速度：x 右正、y 上正；roll（度）。 */
    private static float x, y, vx, vy, roll, vroll;

    private HandMotion() {
    }

    /** 隙浮的物品（不是方塊）才有手持物理。 */
    public static boolean applies(ItemStack stack) {
        return !stack.isEmpty() && !(stack.getItem() instanceof BlockItem)
                && BuiltInRegistries.ITEM.getKey(stack.getItem()).getNamespace().equals(PySift.MOD_ID);
    }

    /** 出手的反作用：給彈簧一個速度（方塊／秒與度／秒）。 */
    public static void kick(float dx, float dy, float droll) {
        vx += dx;
        vy += dy;
        vroll += droll;
    }

    /** 把這一幀的偏移套到手上（在原版把物品移到手上之後呼叫）。 */
    public static void apply(PoseStack pose, Player player, float partial, float side) {
        update(player, partial);
        pose.translate(x, y, 0.0f);
        pose.rotateDegrees(Axis.ZP, roll + x * 55.0f);   // lagging sideways also tilts the blade a little
        pose.rotateDegrees(Axis.XP, -y * 70.0f);
    }

    private static void update(Player player, float partial) {
        long now = System.nanoTime();
        if (started && now - lastFrame < 1_000_000L) {
            return;   // the other hand of the same frame
        }
        float dt = started ? Math.min((now - lastFrame) / 1.0e9f, 0.05f) : 0.0f;
        lastFrame = now;
        float yaw = player.getViewYRot(partial);
        float pitch = player.getViewXRot(partial);
        if (!started) {
            lastYaw = yaw;
            lastPitch = pitch;
            started = true;
            return;
        }
        float dyaw = Mth.wrapDegrees(yaw - lastYaw);
        float dpitch = pitch - lastPitch;
        lastYaw = yaw;
        lastPitch = pitch;
        if (dt <= 0.0f) {
            return;
        }
        // turning drags the item the other way; strafing leans it
        vx += -dyaw * 0.012f;
        vy += dpitch * 0.010f;
        Vec3 move = player.getDeltaMovement();
        Vec3 right = Vec3.directionFromRotation(0.0f, yaw + 90.0f);
        float strafe = (float) (move.x * right.x + move.z * right.z);
        float targetRoll = Mth.clamp(-strafe * 60.0f, -6.0f, 6.0f);
        // one spring per axis, integrated with the real frame time
        vx += (-STIFFNESS * x - DAMPING * vx) * dt;
        vy += (-STIFFNESS * y - DAMPING * vy) * dt;
        vroll += (-STIFFNESS * (roll - targetRoll) - DAMPING * vroll) * dt;
        x = Mth.clamp(x + vx * dt, -LIMIT, LIMIT);
        y = Mth.clamp(y + vy * dt, -LIMIT, LIMIT);
        roll = Mth.clamp(roll + vroll * dt, -25.0f, 25.0f);
    }

    /** 換世界時歸零。 */
    public static void reset() {
        started = false;
        x = y = vx = vy = roll = vroll = 0.0f;
    }
}
