package pryuan05.pysift.client.compat;

import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import pryuan05.pysift.PySift;
import pryuan05.pysift.client.PlayerAnims;
import pryuan05.pysift.client.WeaponPoses;
import pryuan05.pysift.progression.MobDrops;

import java.io.Reader;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import java.util.Properties;
import java.util.function.Function;
import java.util.function.Predicate;

/**
 * 和其他玩家動畫模組共存（見 docs/COMPAT.md）。
 * <p>
 * 設定：config/pysift.properties 的 {@code animation_priority}
 * <ul>
 *   <li>{@code override}（預設）：拿著／使用 The Sift 的武器時，我們的動畫優先；會告訴 Punchy! 與 Punchy! Moves 讓開，
 *       Player Animation Library 的圖層優先度提高，手寫的第三人稱姿勢也在其他模組之後再套一次。</li>
 *   <li>{@code yield}：讓其他模組優先（不登記任何讓開的要求，圖層優先度降低）。</li>
 * </ul>
 * 對 Punchy 只用它公開的 API（{@code punchy.api.PunchyApi}、{@code punchymoves.api.client.AnimationIntent}），
 * 用反射呼叫，所以沒裝 Punchy 時什麼都不做、也不會崩潰。
 */
public final class AnimCompat {
    public static final String PUNCHY = "punchy";
    public static final String PUNCHY_MOVES = "punchy_moves";
    private static final String OWNER = PySift.MOD_ID;

    private static boolean override = true;
    private static boolean loaded;

    private AnimCompat() {
    }

    /** 我們的動畫要不要壓過其他模組。 */
    public static boolean override() {
        load();
        return override;
    }

    /** Player Animation Library 圖層優先度：override 時壓在 Better Combat／Emotecraft 等常見圖層之上，yield 時墊在下面。 */
    public static int layerPriority() {
        return override() ? 5000 : 100;
    }

    /** 有沒有其他會在 PlayerModel.setupAnim 之後改姿勢的模組（需要把手寫姿勢晚一點再套一次）。 */
    public static boolean latePose() {
        return override() && FabricLoader.getInstance().isModLoaded(PUNCHY_MOVES);
    }

    /** 這個物品是不是 The Sift 自己有動畫的武器。 */
    public static boolean ours(ItemStack stack) {
        return stack != null && !stack.isEmpty() && (WeaponPoses.kind(stack) != null
                || stack.getItem() instanceof MobDrops.TuningForkItem
                || stack.getItem() instanceof MobDrops.SoulJavelinItem);
    }

    /** 這位玩家現在是不是由我們的動畫負責（在播全身動畫、或拿著我們的武器）。 */
    public static boolean claims(Player player) {
        return PlayerAnims.isActive(player.getId()) || ours(player.getMainHandItem()) || ours(player.getOffhandItem())
                || (player.isUsingItem() && ours(player.getUseItem()));
    }

    public static void init() {
        load();
        if (!override) {
            return;
        }
        if (FabricLoader.getInstance().isModLoaded(PUNCHY)) {
            punchy();
        }
        if (FabricLoader.getInstance().isModLoaded(PUNCHY_MOVES)) {
            punchyMoves();
        }
    }

    /** Punchy!（第一人稱）：我們的武器交給原版的第一人稱繪製，FirstPersonHandsMixin 的姿勢才會出現。 */
    private static void punchy() {
        try {
            Class<?> api = Class.forName("punchy.api.PunchyApi");
            Predicate<Object> leave = o -> o instanceof ItemStack s && ours(s);
            api.getMethod("leaveItemsToMinecraft", String.class, Predicate.class).invoke(null, OWNER, leave);
            Class<?> cond = Class.forName("punchy.api.PunchyApi$HandCondition");
            Object hands = Proxy.newProxyInstance(cond.getClassLoader(), new Class<?>[]{cond}, (proxy, m, args) -> {
                if (m.getDeclaringClass() == Object.class) {
                    return switch (m.getName()) {
                        case "hashCode" -> System.identityHashCode(proxy);
                        case "equals" -> proxy == args[0];
                        default -> "pysift hand condition";
                    };
                }
                return args != null && args.length > 0 && args[0] instanceof ItemStack s && ours(s);
            });
            api.getMethod("leaveHandsToMinecraft", String.class, cond).invoke(null, OWNER, hands);
            PySift.LOGGER.info("Punchy! detected: The Sift weapons are left to vanilla first-person rendering");
        } catch (ReflectiveOperationException | LinkageError | RuntimeException e) {
            PySift.LOGGER.warn("Punchy! detected but its API could not be used: {}", e.toString());
        }
    }

    /** Punchy! Moves（第三人稱）：拿著我們的武器時回報 SPECIAL_ACTION，讓它把身體交給我們。 */
    @SuppressWarnings({"unchecked", "rawtypes"})
    private static void punchyMoves() {
        try {
            Class<?> intent = Class.forName("punchymoves.api.client.AnimationIntent");
            Class<? extends Enum> kind = (Class<? extends Enum>) Class.forName("punchymoves.api.client.AnimationIntent$Kind");
            Object special = Enum.valueOf(kind, "SPECIAL_ACTION");
            Object unspecified = Enum.valueOf(kind, "UNSPECIFIED");
            Function<Object, Object> reader = p -> p instanceof Player player && claims(player) ? special : unspecified;
            Method register = intent.getMethod("register", Function.class);
            register.invoke(null, reader);
            PySift.LOGGER.info("Punchy! Moves detected: it yields to The Sift weapon animations");
        } catch (ReflectiveOperationException | LinkageError | RuntimeException e) {
            PySift.LOGGER.warn("Punchy! Moves detected but its API could not be used: {}", e.toString());
        }
    }

    private static void load() {
        if (loaded) {
            return;
        }
        loaded = true;
        Path file = FabricLoader.getInstance().getConfigDir().resolve("pysift.properties");
        try {
            if (Files.exists(file)) {
                Properties props = new Properties();
                try (Reader in = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
                    props.load(in);
                }
                String mode = props.getProperty("animation_priority", "override").trim().toLowerCase(Locale.ROOT);
                override = !"yield".equals(mode);
                if (props.getProperty("animation_priority") == null) {
                    Files.writeString(file, """

                            # animation_priority: when another player-animation mod (Punchy!, Punchy! Moves, Better Combat,
                            # Emotecraft, Not Enough Animations) is installed, whose animation wins while you hold a Sift weapon.
                            #   override = The Sift's weapon animations win (default)
                            #   yield    = the other mod wins
                            animation_priority=override
                            """, StandardCharsets.UTF_8, java.nio.file.StandardOpenOption.APPEND);
                }
            }
        } catch (Exception e) {
            PySift.LOGGER.warn("cannot read animation_priority from {}: {}", file, e.toString());
        }
    }

    /** 給 mixin 用：目前世界裡這個實體是不是玩家且由我們負責。 */
    public static boolean claims(int entityId) {
        Minecraft mc = Minecraft.getInstance();
        return mc.level != null && mc.level.getEntity(entityId) instanceof Player p && claims(p);
    }
}
