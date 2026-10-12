package pryuan05.pysift.block;

import net.minecraft.util.StringRepresentable;

/**
 * 非數值型的方塊狀態屬性取值。序列化名稱必須與 blockstates/*.json 的鍵值一致，
 * 列舉順序的第一個值即為預設狀態。
 */
public final class SiftStateProperties {
    private SiftStateProperties() {
    }

    /** frost_veined_stone 的脈色。 */
    public enum Tint implements StringRepresentable {
        NONE("none"),
        VIOLET("violet"),
        CRIMSON("crimson");

        private final String name;

        Tint(String name) {
            this.name = name;
        }

        @Override
        public String getSerializedName() {
            return name;
        }
    }

    /** emerald_ore 的母岩。 */
    public enum Host implements StringRepresentable {
        MARBLE("marble"),
        SANDSTONE("sandstone");

        private final String name;

        Host(String name) {
            this.name = name;
        }

        @Override
        public String getSerializedName() {
            return name;
        }
    }

    /** 隨機池的色調標籤；各方塊只開放自己用到的子集（見 ModBlocks.Def#tones），第一個為預設。 */
    public enum Tone implements StringRepresentable {
        SMOOTH("smooth"),
        ROUGH("rough"),
        PANELED("paneled"),
        DARK("dark"),
        ROSE("rose"),
        MOTTLED("mottled"),
        CRIMSON("crimson"),
        PLUM("plum"),
        OLIVE("olive"),
        WARM("warm"),
        TEAL("teal"),
        LAVENDER("lavender"),
        VIOLET("violet"),
        LIGHT("light"),
        BLUE("blue"),
        PALE("pale"),
        CYAN("cyan"),
        DUSK("dusk"),
        SLATE("slate"),
        RUSTY("rusty"),
        GRAY("gray");

        private final String name;

        Tone(String name) {
            this.name = name;
        }

        @Override
        public String getSerializedName() {
            return name;
        }
    }
}
