package pryuan05.pysift.soulpower.kinetic;

import net.fabricmc.loader.api.FabricLoader;
import pryuan05.pysift.PySift;

import java.io.IOException;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Properties;

/**
 * 機械擴充（傳動軸、齒輪、齒輪箱、離合器、換向器、手搖曲柄與轉速網路 {@link SoulNetwork}）的開關。
 * 基礎的靈魂紅石不需要它；這一層是給 Create 的擴充內容：
 * <ul>
 *   <li>auto（預設）：偵測到 Create 模組才啟用；</li>
 *   <li>on：強制啟用（測試用，Create 還沒有 26.x 版）；</li>
 *   <li>off：永遠不啟用。</li>
 * </ul>
 * 設定檔：config/pysift.properties 的 kinetic_addon。沒啟用時，擴充層的方塊完全不註冊。
 */
public final class KineticAddon {
    public static final String CREATE_MOD_ID = "create";
    private static final boolean ENABLED = decide();

    private KineticAddon() {
    }

    public static boolean enabled() {
        return ENABLED;
    }

    private static boolean decide() {
        String mode = "auto";
        Path file = FabricLoader.getInstance().getConfigDir().resolve("pysift.properties");
        try {
            if (Files.exists(file)) {
                Properties props = new Properties();
                try (Reader in = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
                    props.load(in);
                }
                mode = props.getProperty("kinetic_addon", "auto").trim().toLowerCase();
            } else {
                Files.createDirectories(file.getParent());
                Files.writeString(file, """
                        # The Sift (pysift)
                        # kinetic_addon: the mechanical add-on (soul shafts, cogwheels, gearbox, clutch, gearshift, hand crank).
                        #   auto = only when the Create mod is installed (default)
                        #   on   = always (for testing)
                        #   off  = never
                        kinetic_addon=auto
                        """, StandardCharsets.UTF_8);
            }
        } catch (IOException e) {
            PySift.LOGGER.warn("cannot read {}: {}", file, e.toString());
        }
        boolean create = FabricLoader.getInstance().isModLoaded(CREATE_MOD_ID);
        boolean enabled = mode.equals("on") || (mode.equals("auto") && create);
        PySift.LOGGER.info("Soul power kinetic add-on: {} (kinetic_addon={}, Create {})", enabled ? "enabled" : "disabled", mode,
                create ? "installed" : "not installed");
        return enabled;
    }
}
