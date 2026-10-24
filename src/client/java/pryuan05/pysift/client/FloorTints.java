package pryuan05.pysift.client;

import java.util.Map;

/**
 * 地板方塊 → 草色（ARGB）。由 tools/worldgen/make_floor_tints.py 產生，請改腳本後重跑，不要手改。
 * 每個地板取頂面貼圖平均色，依色相分家族：赤紅→淡桃紅、紫岩→紫／淡黃兩色（FloorTint 依位置分區混色）、
 * 青色頂面→青、粉壤→粉紅、沙→黃橙；顏色都偏淡，配合淺灰的草葉貼圖。
 */
public final class FloorTints {
    public static final Map<String, int[]> COLORS = Map.ofEntries(
            Map.entry("pysift:meadow_grass_block", new int[]{0xFFE6A394}),
            Map.entry("pysift:rich_dirt", new int[]{0xFFE0A095}),
            Map.entry("pysift:forest_floor", new int[]{0xFFE0C17B}),
            Map.entry("pysift:ash_capped_crimson_01", new int[]{0xFFECADA5}),
            Map.entry("pysift:crimson_strata", new int[]{0xFFE6A59B}),
            Map.entry("pysift:ash_capped_violet_01", new int[]{0xFFC2A0E7, 0xFFE9D685}),
            Map.entry("pysift:violet_strata", new int[]{0xFFB995E0, 0xFFE0CC7C}),
            Map.entry("pysift:crimson_capped_void_01", new int[]{0xFFEDA098}),
            Map.entry("pysift:crimson_capped_crimson_strata_3", new int[]{0xFFEDA098}),
            Map.entry("pysift:amber_sand", new int[]{0xFFEECC83}),
            Map.entry("pysift:pale_sand", new int[]{0xFFEFCD84}),
            Map.entry("pysift:crimson_capped_crimson_strata_2", new int[]{0xFFEEA399}),
            Map.entry("pysift:violet_capped_dark_slate", new int[]{0xFFB995E0, 0xFFE0CC7C}),
            Map.entry("pysift:capped_crimson_strata", new int[]{0xFF7BE0D4}),
            Map.entry("pysift:abyssal_strata", new int[]{0xFF7BE0D0}),
            Map.entry("pysift:dark_slate", new int[]{0xFFBA99E0, 0xFFE0CF7D}),
            Map.entry("pysift:silted_strata", new int[]{0xFF7BE0D2})
    );

    private FloorTints() {
    }
}
