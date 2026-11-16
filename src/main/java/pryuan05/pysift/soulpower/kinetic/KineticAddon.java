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
 * 機械層（傳動軸、齒輪、齒輪箱、離合器、換向器、手搖曲柄與轉速網路 {@link SoulNetwork}）的開關。
 * 基礎的靈魂紅石不需要它。裝了 Create 時，傳動用的是 Create 自己的軸與齒輪，隙浮只在上面疊加能力
 * （compat/create/CreateBridge，規格在 docs/CREATE_ADDON.md），所以隙浮自己的軸與齒輪預設不出現：
 * <ul>
 *   <li>auto（預設）：不註冊隙浮自己的軸與齒輪；有 Create 時啟用橋接；</li>
 *   <li>on：註冊隙浮自己的軸與齒輪（獨立的機械層，用來測試轉速網路；Create 還沒有 26.x 版）；</li>
 *   <li>off：兩者都不啟用。</li>
 * </ul>
 * 設定檔：config/pysift.properties 的 kinetic_addon。沒啟用時，機械層的方塊完全不註冊。
 */
public final class KineticAddon {
    public static final String CREATE_MOD_ID = "create";
    private static boolean bridge;
    private static final boolean ENABLED = decide();

    private KineticAddon() {
    }

    /** 隙浮自己的軸與齒輪有沒有註冊。 */
    public static boolean enabled() {
        return ENABLED;
    }

    /** Create 已安裝而且沒有被設定檔關掉：橋接（compat/create/CreateBridge）可以啟用。 */
    public static boolean createBridge() {
        return bridge;
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
                        # kinetic_addon: The Sift's own mechanical parts (soul shafts, cogwheels, gearbox, clutch, gearshift,
                        # hand crank). Soul redstone does not need them, and with Create installed you use Create's.
                        #   auto = off; the Create bridge is used when Create is installed (default)
                        #   on   = register them (a stand-alone mechanical layer, for testing)
                        #   off  = off, and no Create bridge either
                        kinetic_addon=auto
                        """, StandardCharsets.UTF_8);
            }
        } catch (IOException e) {
            PySift.LOGGER.warn("cannot read {}: {}", file, e.toString());
        }
        boolean create = FabricLoader.getInstance().isModLoaded(CREATE_MOD_ID);
        boolean enabled = mode.equals("on");
        bridge = create && !mode.equals("off");
        PySift.LOGGER.info("Soul power mechanical parts: {} (kinetic_addon={}, Create {})", enabled ? "enabled" : "disabled", mode,
                create ? "installed" : "not installed");
        return enabled;
    }
}
