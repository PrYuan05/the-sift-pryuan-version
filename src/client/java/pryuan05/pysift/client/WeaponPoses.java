package pryuan05.pysift.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import pryuan05.pysift.progression.BossWeapons;
import pryuan05.pysift.progression.SculkHammerItem;
import pryuan05.pysift.progression.SonicStaffItem;

import java.util.HashMap;
import java.util.Map;

/**
 * Boss 武器的自訂姿勢（使用者：不要用原版的拉弓、三叉戟姿勢）。物品的 getUseAnimation 是 NONE，
 * 姿勢全部在這裡算，由 HumanoidModelMixin（第三人稱）與 FirstPersonHandsMixin（第一人稱）套上。
 * <ul>
 *   <li>音波法杖「詠唱」（按住右鍵）：持杖的手把法杖越舉越高、指向天空，另一隻手往前伸出（施法）；
 *       「戳刺」（左鍵）：發光的晶球朝前，從靠近自己的地方往前戳一小段（攻擊距離比一般武器遠，BossWeapons 的 ATTACK_RANGE）。</li>
 *   <li>重錘「蓄力」（按住右鍵）：雙手把錘子舉過頭頂、越蓄越往後拉，蓄滿後發抖；
 *       「左錘右錘」（左鍵）：雙手從頭頂斜劈下來，一次從右上劈到左下、下一次從左上劈到右下，輪流交替。</li>
 *   <li>衝刺護符「前刺」（衝刺後 {@link #DASH_TICKS} tick，伺服器送 DashPosePayload）：雙手握著羽刃往前刺、身體前傾。</li>
 * </ul>
 */
public final class WeaponPoses {
    public enum Kind { STAFF, HAMMER, CHARM }

    private static final int DASH_TICKS = 8;
    /** 實體 id → 最近一次衝刺的時間（客戶端世界時間）。 */
    private static final Map<Integer, Long> DASH = new HashMap<>();
    /** 實體 id → 揮了幾次（重錘左右交替用）。 */
    private static final Map<Integer, Integer> SWINGS = new HashMap<>();

    private WeaponPoses() {
    }

    public static Kind kind(ItemStack stack) {
        if (stack.is(BossWeapons.SONIC_STAFF)) {
            return Kind.STAFF;
        }
        if (stack.is(BossWeapons.SCULK_HAMMER)) {
            return Kind.HAMMER;
        }
        return stack.is(BossWeapons.DASH_CHARM) ? Kind.CHARM : null;
    }

    public static void markDash(int entityId) {
        var level = Minecraft.getInstance().level;
        if (level != null) {
            DASH.put(entityId, level.getGameTime());
        }
    }

    public static void onSwing(int entityId) {
        SWINGS.merge(entityId, 1, Integer::sum);
    }

    /** 這一次揮擊從哪一邊開始：1 = 右上往左下，-1 = 左上往右下。 */
    private static float hammerSide(int entityId) {
        return SWINGS.getOrDefault(entityId, 0) % 2 == 0 ? 1.0f : -1.0f;
    }

    /** 衝刺後經過的比例 0～1；不在衝刺姿勢中回傳 -1。 */
    private static float dashProgress(int entityId) {
        var mc = Minecraft.getInstance();
        Long start = DASH.get(entityId);
        if (start == null || mc.level == null) {
            return -1;
        }
        float t = mc.level.getGameTime() - start + mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
        if (t > DASH_TICKS) {
            DASH.remove(entityId);
            return -1;
        }
        return t / DASH_TICKS;
    }

    /** 0（剛開始）～1（詠唱完成／蓄滿）。 */
    private static float progress(Kind kind, float ticks) {
        float full = kind == Kind.STAFF ? SonicStaffItem.CAST_TICKS : SculkHammerItem.FULL_CHARGE;
        return Mth.clamp(ticks / full, 0.0f, 1.0f);
    }

    /**
     * 戳刺的前後位置（使用者：發光的晶球在前面，從靠近自己的地方往前一小段）：
     * 0～0.35 從靠近自己處快速往前戳，停一下，0.6 之後收回。0 = 靠近自己、1 = 戳到最前面。
     */
    private static float poke(float x) {
        if (x < 0.35f) {
            return easeOut(x / 0.35f);
        }
        if (x < 0.6f) {
            return 1.0f;
        }
        return 1 - (x - 0.6f) / 0.4f;
    }

    private static float easeOut(float x) {
        return 1 - (1 - x) * (1 - x);
    }

    // ------------------------------------------------------------------ third person
    public static void thirdPerson(HumanoidModel<?> model, HumanoidRenderState state, int entityId) {
        if (state.isUsingItem && state.useItemHand != null && using(model, state)) {
            return;
        }
        ItemStack main = state.mainArm == HumanoidArm.RIGHT ? state.rightHandItemStack : state.leftHandItemStack;
        Kind kind = kind(main);
        if (kind == null) {
            return;
        }
        float inward = state.mainArm == HumanoidArm.RIGHT ? -1.0f : 1.0f;    // yRot toward the body's centre for the main arm
        ModelPart arm = state.mainArm == HumanoidArm.RIGHT ? model.rightArm : model.leftArm;
        ModelPart other = state.mainArm == HumanoidArm.RIGHT ? model.leftArm : model.rightArm;
        if (kind == Kind.CHARM) {
            float d = dashProgress(entityId);
            if (d >= 0) {   // both hands thrust the blade forward, leaning in, then ease back
                float k = d < 0.3f ? d / 0.3f : 1 - (d - 0.3f) / 0.7f;
                for (ModelPart a : new ModelPart[]{model.rightArm, model.leftArm}) {
                    float in = a == model.rightArm ? -1.0f : 1.0f;
                    a.xRot = Mth.lerp(k, a.xRot, -1.45f);
                    a.yRot = Mth.lerp(k, a.yRot, in * 0.55f);
                    a.zRot = Mth.lerp(k, a.zRot, 0.0f);
                }
                model.body.xRot = 0.3f * k;
            }
            return;
        }
        float s = state.swingAnimation;
        if (s <= 0) {
            return;
        }
        if (kind == Kind.STAFF) {   // poke: hand low at the hip, staff level with the crystal ahead, a short jab forward
            float k = poke(s);
            arm.xRot = Mth.lerp(k, -0.15f, -0.6f) + model.head.xRot * 0.5f;
            arm.yRot = inward * 0.35f + model.head.yRot;
            arm.zRot = 0.0f;
            other.xRot = Mth.lerp(k, -0.5f, -0.9f) + model.head.xRot * 0.5f;    // the free hand guides the shaft
            other.yRot = -inward * 0.4f + model.head.yRot;
            model.body.yRot = -inward * Mth.lerp(k, 0.15f, -0.1f);
        } else {                    // two-handed diagonal chop, alternating sides
            float side = hammerSide(entityId) * -inward;
            float e = s * s * (3 - 2 * s);
            for (ModelPart a : new ModelPart[]{model.rightArm, model.leftArm}) {
                float in = a == model.rightArm ? -1.0f : 1.0f;
                a.xRot = Mth.lerp(e, -2.9f, -0.5f);
                a.yRot = in * 0.3f + side * Mth.lerp(e, 0.55f, -0.45f);
                a.zRot = 0.0f;
            }
            model.body.yRot = side * Mth.lerp(e, 0.3f, -0.35f);
            model.body.xRot = 0.25f * Mth.sin(s * Mth.PI);
        }
    }

    /** 右鍵使用中的姿勢（詠唱、蓄力）；有套用回傳 true。 */
    private static boolean using(HumanoidModel<?> model, HumanoidRenderState state) {
        HumanoidArm useArm = state.useItemHand == InteractionHand.MAIN_HAND ? state.mainArm : state.mainArm.getOpposite();
        ItemStack stack = useArm == HumanoidArm.RIGHT ? state.rightHandItemStack : state.leftHandItemStack;
        Kind kind = kind(stack);
        if (kind == null || kind == Kind.CHARM) {
            return false;
        }
        float t = state.ticksUsingItem;
        float p = progress(kind, t);
        ModelPart use = useArm == HumanoidArm.RIGHT ? model.rightArm : model.leftArm;
        ModelPart other = useArm == HumanoidArm.RIGHT ? model.leftArm : model.rightArm;
        float inward = useArm == HumanoidArm.RIGHT ? -1.0f : 1.0f;
        if (kind == Kind.STAFF) {
            float sway = Mth.sin(t * 0.6f) * 0.05f;
            use.xRot = Mth.lerp(p, -1.7f, -2.8f) + model.head.xRot * 0.3f + sway;   // forward -> raised to the sky
            use.yRot = model.head.yRot * 0.5f;
            use.zRot = -inward * Mth.lerp(p, 0.05f, 0.2f);
            other.xRot = -1.45f + model.head.xRot * 0.5f - sway;                     // the free hand reaches out
            other.yRot = -inward * 0.45f + model.head.yRot;
            other.zRot = inward * 0.1f;
        } else {
            float shake = p >= 1.0f ? Mth.sin(t * 2.7f) * 0.05f : 0.0f;
            float lift = Mth.lerp(p, -2.5f, -3.05f) + shake;                         // overhead, pulled back as it charges
            for (ModelPart arm : new ModelPart[]{model.rightArm, model.leftArm}) {
                float in = arm == model.rightArm ? -1.0f : 1.0f;
                arm.xRot = lift;
                arm.yRot = in * 0.3f;                                                 // both hands on the handle
                arm.zRot = -in * 0.05f + shake;
            }
            model.body.xRot = -0.08f * p;                                             // leans back a little
        }
        return true;
    }

    // ------------------------------------------------------------------ first person
    /** 第一人稱：已經把物品移到手上（applyItemArmTransform）之後再加上姿勢。 */
    public static void firstPerson(PoseStack pose, HumanoidArm arm, ItemStack stack) {
        Kind kind = kind(stack);
        Player player = Minecraft.getInstance().player;
        if (kind == null || player == null) {
            return;
        }
        float side = arm == HumanoidArm.RIGHT ? 1.0f : -1.0f;
        if (kind == Kind.CHARM) {
            float d = dashProgress(player.getId());
            if (d >= 0) {   // held with both hands in the middle and thrust forward
                float k = d < 0.3f ? d / 0.3f : 1 - (d - 0.3f) / 0.7f;
                pose.translate(-0.3f * side * k, 0.05f * k, -0.35f * k);
                pose.rotateDegrees(Axis.YP, side * 35.0f * k);
                pose.rotateDegrees(Axis.XP, -25.0f * k);
            }
            return;
        }
        if (!player.isUsingItem() || !player.getUseItem().equals(stack)) {
            return;
        }
        float t = player.getTicksUsingItem(Minecraft.getInstance().getDeltaTracker().getGameTimeDeltaPartialTick(false));
        float p = progress(kind, t);
        if (kind == Kind.STAFF) {
            float tremble = p > 0.7f ? Mth.sin(t * 3.1f) * 0.006f * (p - 0.7f) / 0.3f : 0.0f;
            pose.translate(-0.22f * side * p + tremble, 0.10f + 0.20f * p, -0.12f * p);   // to the middle, rising
            pose.rotateDegrees(Axis.ZP, side * 28.0f * p);                      // stood upright
            pose.rotateDegrees(Axis.XP, -10.0f * p);
        } else {
            float shake = p >= 1.0f ? Mth.sin(t * 2.7f) : 0.0f;
            pose.translate(-0.05f * side * p, 0.22f * p, 0.18f * p);                       // up and back over the shoulder
            pose.rotateDegrees(Axis.XP, -55.0f * p);
            pose.rotateDegrees(Axis.ZP, side * (12.0f * p + shake * 2.0f));
        }
    }

    /**
     * 第一人稱的左鍵揮擊（取代原版的 applyItemArmAttackTransform）；不是這幾把武器就回傳 false，照原版揮。
     * swing = 0～1 的揮擊進度。
     */
    public static boolean firstPersonSwing(PoseStack pose, HumanoidArm arm, ItemStack stack, float swing) {
        Kind kind = kind(stack);
        Player player = Minecraft.getInstance().player;
        if (kind == null || kind == Kind.CHARM || player == null) {
            return false;
        }
        float side = arm == HumanoidArm.RIGHT ? 1.0f : -1.0f;
        if (kind == Kind.STAFF) {   // poke: crystal pointing into the screen, from close to you a short way forward
            float k = poke(swing);
            float aim = Math.min(1.0f, swing * 6.0f) * (1 - Math.max(0.0f, swing - 0.8f) / 0.2f);   // turn to point ahead, then relax
            pose.translate(-0.18f * side * aim, -0.08f * aim, Mth.lerp(k, 0.1f, -0.25f) * aim);
            pose.rotateDegrees(Axis.YP, side * 8.0f * aim);
            pose.rotateDegrees(Axis.XP, -75.0f * aim);
        } else {                    // diagonal chop, alternating: upper right -> lower left, then upper left -> lower right
            float dir = hammerSide(player.getId()) * side;
            float e = swing * swing * (3 - 2 * swing);
            pose.translate(dir * Mth.lerp(e, 0.15f, -0.25f), Mth.lerp(e, 0.25f, -0.25f), -0.1f * Mth.sin(swing * Mth.PI));
            pose.rotateDegrees(Axis.ZP, dir * Mth.lerp(e, -35.0f, 40.0f));
            pose.rotateDegrees(Axis.XP, Mth.lerp(e, -50.0f, 35.0f));
        }
        return true;
    }
}
