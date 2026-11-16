package pryuan05.pysift.block;

import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import java.util.List;

/**
 * 開門儀式要的 8 張唱片（各自來自不同的地方），顏色依「紅橙黃綠藍靛紫粉」的順序。
 * 唱片盒由左到右第 i 個只收第 i 張唱片，所以光柱永遠是彩虹順序。
 * 放入時響起的和弦音高是 C 大調音階（每張一個音），8 張剛好一個八度。
 */
public final class RitualDiscs {
    public record Disc(Item item, int color, int semitone, String where) {
        /** 音符盒音高：0.5（低 F#）～2.0（高 F#），C 大調。 */
        public float pitch() {
            return (float) Math.pow(2.0, (semitone - 6) / 12.0);
        }
    }

    public static final List<Disc> DISCS = List.of(
            new Disc(Items.MUSIC_DISC_PIGSTEP, 0xFFE0413A, 0, "bastion"),
            new Disc(Items.MUSIC_DISC_RELIC, 0xFFF08A2A, 2, "trail_ruins"),
            new Disc(Items.MUSIC_DISC_PRECIPICE, 0xFFF2D640, 4, "trial_chambers"),
            new Disc(Items.MUSIC_DISC_CREATOR, 0xFF7FD13B, 5, "ominous_vault"),
            new Disc(Items.MUSIC_DISC_5, 0xFF3D8BFF, 7, "ancient_city"),
            new Disc(Items.MUSIC_DISC_OTHERSIDE, 0xFF4B3FC0, 9, "stronghold"),
            new Disc(Items.MUSIC_DISC_13, 0xFFA050E0, 11, "dungeon"),
            new Disc(Items.MUSIC_DISC_TEARS, 0xFFF08CC8, 12, "ghast"));

    private RitualDiscs() {
    }

    /** 由左到右第 index 個唱片盒要的唱片。 */
    public static Disc forSeat(int index) {
        return index >= 0 && index < DISCS.size() ? DISCS.get(index) : null;
    }

    /** 唱片的歌名翻譯鍵（jukebox_song.minecraft.&lt;name&gt;）。 */
    public static String songKey(Disc disc) {
        String path = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(disc.item()).getPath();
        return "jukebox_song.minecraft." + path.replace("music_disc_", "");
    }

    /** 這張唱片是不是儀式要的；不是就回傳 null。 */
    public static Disc of(ItemStack stack) {
        for (Disc d : DISCS) {
            if (stack.is(d.item())) {
                return d;
            }
        }
        return null;
    }
}
