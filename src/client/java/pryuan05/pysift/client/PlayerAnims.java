package pryuan05.pysift.client;

import com.zigythebird.playeranim.animation.PlayerAnimResources;
import com.zigythebird.playeranim.animation.PlayerAnimationController;
import com.zigythebird.playeranim.api.PlayerAnimationAccess;
import com.zigythebird.playeranim.api.PlayerAnimationFactory;
import com.zigythebird.playeranimcore.animation.layered.modifier.AbstractFadeModifier;
import com.zigythebird.playeranimcore.easing.EasingType;
import com.zigythebird.playeranimcore.enums.PlayState;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import pryuan05.pysift.PySift;
import pryuan05.pysift.progression.SculkHammerItem;
import pryuan05.pysift.progression.SonicStaffItem;

import java.util.HashMap;
import java.util.Map;

/**
 * 玩家使用物品的全身動畫（第三人稱），由 Player Animation Library 播放；動畫檔是
 * assets/pysift/player_animations/weapons.json，由 tools/models/build_player_animations.py 產生。
 * <p>
 * 每個客戶端 tick 看每位玩家手上的武器與使用狀態，決定現在該播哪一段，換段時用 3 tick 淡入接起來（動作才連貫）：
 * <ul>
 *   <li>重錘：按住右鍵 → hammer_charge（先下沉再舉過頭，停在最後一格）→ 蓄滿 hammer_charged（發抖，循環）→
 *       放開 hammer_slam（整個人砸下去、彈一下、慢慢站起來）；左鍵 hammer_swing_right / _left 輪流。</li>
 *   <li>音波法杖：按住右鍵 staff_cast → 詠唱完成 staff_blast（後座力）；左鍵 staff_thrust。</li>
 *   <li>調音叉：敲響 fork_strike（往掌心一敲、舉著聽它嗡鳴）。靈魂標槍：javelin_charge → javelin_throw。
 *       衝刺護符：charm_dash（整個人平著往前刺）。</li>
 * </ul>
 * 第一人稱仍用 {@link WeaponPoses}（手上的物品姿勢是手調的）。這一層在播時，{@link WeaponPoses#thirdPerson} 不再疊上舊姿勢。
 */
public final class PlayerAnims {
    private static final Identifier LAYER = PySift.id("weapons");
    private static final int FADE_TICKS = 3;
    /** 實體 id → 目前的狀態（哪一段動畫），用來只在換段時觸發。 */
    private static final Map<Integer, String> STATE = new HashMap<>();
    /** 實體 id → 重錘揮了幾次（左右交替）。 */
    private static final Map<Integer, Integer> SWINGS = new HashMap<>();

    private PlayerAnims() {
    }

    public static void init() {
        PlayerAnimationFactory.ANIMATION_DATA_FACTORY.registerFactory(LAYER, pryuan05.pysift.client.compat.AnimCompat.layerPriority(),
                avatar -> new PlayerAnimationController(avatar, (controller, data, setter) -> PlayState.STOP));
        ClientTickEvents.END_CLIENT_TICK.register(PlayerAnims::tick);
    }

    private static PlayerAnimationController controller(Player player) {
        try {
            return PlayerAnimationAccess.getPlayerAnimationLayer(player, LAYER) instanceof PlayerAnimationController c ? c : null;
        } catch (RuntimeException e) {
            return null;   // 這個玩家還沒有動畫層（剛進入視野）
        }
    }

    /** 這位玩家身上正在播我們的動畫嗎？（在播的時候舊的第三人稱姿勢讓開。） */
    public static boolean isActive(int entityId) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || !(mc.level.getEntity(entityId) instanceof Player player)) {
            return false;
        }
        PlayerAnimationController c = controller(player);
        return c != null && c.isActive();
    }

    private static void play(Player player, String name) {
        PlayerAnimationController c = controller(player);
        Identifier id = PySift.id(name);
        if (c == null || !PlayerAnimResources.hasAnimation(id)) {
            return;
        }
        if (c.isActive()) {
            c.replaceAnimationWithFade(AbstractFadeModifier.standardFadeIn(FADE_TICKS, EasingType.EASE_IN_OUT_SINE), id);
        } else {
            c.triggerAnimation(id);
        }
    }

    private static void tick(Minecraft mc) {
        if (mc.level == null) {
            if (!STATE.isEmpty() || !SWINGS.isEmpty() || !LAST_CHARGE.isEmpty()) {
                STATE.clear();
                SWINGS.clear();
                LAST_CHARGE.clear();
                WeaponPoses.clear();
            }
            return;
        }
        for (Player player : mc.level.players()) {
            String now = held(player);
            String before = STATE.put(player.getId(), now);
            if (now.equals(before)) {
                continue;
            }
            switch (now) {
                case "hammer_charge", "hammer_charged", "staff_cast", "javelin_charge" -> play(player, now);
                default -> {
                    // 放開：從蓄力接到出手的那一段；其他情況讓正在播的一次性動畫自己播完
                    if ("hammer_charge".equals(before) && usedLongEnough(player)) {
                        play(player, "hammer_slam");
                    } else if ("hammer_charged".equals(before)) {
                        play(player, "hammer_slam");
                    } else if ("staff_cast".equals(before)) {
                        play(player, "staff_blast");
                    } else if ("javelin_charge".equals(before)) {
                        if (LAST_CHARGE.getOrDefault(player.getId(), 0) >= pryuan05.pysift.progression.MobDrops.SoulJavelinItem.MIN_CHARGE) {
                            play(player, "javelin_throw");
                        } else {
                            stop(player);   // 蓄力不夠沒有丟出去：收手
                        }
                    }
                }
            }
        }
    }

    /** 放開重錘時蓄力夠不夠砸（不夠的話沒有效果，也不播砸地）。 */
    private static boolean usedLongEnough(Player player) {
        PlayerAnimationController c = controller(player);
        return c != null && c.isActive() && LAST_CHARGE.getOrDefault(player.getId(), 0) >= SculkHammerItem.MIN_CHARGE;
    }

    private static final Map<Integer, Integer> LAST_CHARGE = new HashMap<>();

    /** 這位玩家現在的持續狀態：蓄力中的哪一段，或 idle。 */
    private static String held(Player player) {
        if (!player.isUsingItem()) {
            return "idle";
        }
        ItemStack stack = player.getUseItem();
        int ticks = player.getTicksUsingItem();
        if (stack.getItem() instanceof SculkHammerItem) {
            LAST_CHARGE.put(player.getId(), ticks);
            return ticks >= SculkHammerItem.FULL_CHARGE ? "hammer_charged" : "hammer_charge";
        }
        if (stack.getItem() instanceof SonicStaffItem) {
            return "staff_cast";
        }
        if (stack.getItem() instanceof pryuan05.pysift.progression.MobDrops.SoulJavelinItem) {
            LAST_CHARGE.put(player.getId(), ticks);
            return "javelin_charge";
        }
        return "idle";
    }

    /** 揮擊（LivingEntitySwingMixin → WeaponPoses.onSwing）：左鍵的那一下。 */
    public static void onSwing(int entityId) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || !(mc.level.getEntity(entityId) instanceof Player player) || player.isUsingItem()) {
            return;
        }
        ItemStack stack = player.getMainHandItem();
        if (stack.getItem() instanceof SculkHammerItem) {
            int n = SWINGS.merge(entityId, 1, Integer::sum);
            play(player, n % 2 == 1 ? "hammer_swing_right" : "hammer_swing_left");
        } else if (stack.getItem() instanceof SonicStaffItem) {
            play(player, "staff_thrust");
        } else if (stack.getItem() instanceof pryuan05.pysift.progression.MobDrops.TuningForkItem) {
            play(player, "fork_strike");
        }
    }

    /** 衝刺護符衝出去的那一下（伺服器的 DashPosePayload → WeaponPoses.markDash）。 */
    public static void onDash(int entityId) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level != null && mc.level.getEntity(entityId) instanceof Player player) {
            play(player, "charm_dash");
        }
    }

    private static void stop(Player player) {
        PlayerAnimationController c = controller(player);
        if (c != null && c.isActive()) {
            c.stop();
        }
    }
}
