package pryuan05.pysift.entity.mob;

import java.util.ArrayList;
import java.util.List;

/**
 * 歌者用音符盒（笛聲＋鐘聲）哼的曲子：都是作曲版權早已過期的經典旋律，由這裡重新編成音符盒的音域（F#3～F#5 兩個八度）。
 * <p>
 * 曲譜寫法：每個音是「音名＋長度」，用空白隔開。音名 C D E F G A B，後面加 # 是升半音，加 ' 高八度、加 , 低八度；
 * R 是休止。長度以八分音符為單位（1 = 八分、2 = 四分、4 = 二分）。key 是 C 要對到的音符盒半音（0 = F#3），
 * 所以同一份譜換 key 就能整首移調。
 */
public final class SingerSongs {
    /** 一首曲子：每個八分音符一格，-1 = 休止或延長（不重新發聲）。onset[i] = 這格是不是新的音。 */
    public record Song(String name, int[] notes, boolean[] onset) {
        public int length() {
            return notes.length;
        }
    }

    /** 布拉姆斯《搖籃曲》（Wiegenlied, Op. 49 No. 4, 1868），F 大調。 */
    public static final Song LULLABY = parse("Brahms Lullaby", 11,
            "E1 E1 G4 E1 E1 G4 E1 G1 C'3 B2 A2 A1 G4 R2 "
          + "D1 E1 F2 D2 D1 E1 F4 D1 F1 B1 A1 G2 B2 C'4 R2 "
          + "C1 C1 C'4 A1 F1 G4 E1 C1 F2 G2 A2 G4 R2 "
          + "C1 C1 C'4 A1 F1 G4 E1 C1 F1 E1 D2 C4 R2");

    /** 貝多芬《快樂頌》（第九號交響曲終樂章主題，1824），F 大調。 */
    public static final Song ODE_TO_JOY = parse("Ode to Joy", 11,
            "E2 E2 F2 G2 G2 F2 E2 D2 C2 C2 D2 E2 E3 D1 D4 "
          + "E2 E2 F2 G2 G2 F2 E2 D2 C2 C2 D2 E2 D3 C1 C4 "
          + "D2 D2 E2 C2 D2 E1 F1 E2 C2 D2 E1 F1 E2 D2 C2 D2 G,4 "
          + "E2 E2 F2 G2 G2 F2 E2 D2 C2 C2 D2 E2 D3 C1 C4");

    /** 《小星星》（法國童謠 Ah! vous dirai-je, maman，莫札特變奏曲的主題），F 大調。 */
    public static final Song TWINKLE = parse("Twinkle Twinkle", 11,
            "C2 C2 G2 G2 A2 A2 G4 F2 F2 E2 E2 D2 D2 C4 "
          + "G2 G2 F2 F2 E2 E2 D4 G2 G2 F2 F2 E2 E2 D4 "
          + "C2 C2 G2 G2 A2 A2 G4 F2 F2 E2 E2 D2 D2 C4");

    /** 開門慶祝：快樂頌第一句。 */
    public static final Song CELEBRATION = parse("Ode to Joy (opening)", 11,
            "E2 E2 F2 G2 G2 F2 E2 D2 C2 C2 D2 E2 E3 D1 D4");

    /** 等唱片時輪流哼的曲子。 */
    public static final List<Song> WAITING = List.of(LULLABY, ODE_TO_JOY, TWINKLE);

    private SingerSongs() {
    }

    private static final String NAMES = "C D EF G A B";   // index = 相對 C 的半音

    static Song parse(String name, int key, String score) {
        List<Integer> notes = new ArrayList<>();
        List<Boolean> onset = new ArrayList<>();
        for (String token : score.trim().split("\\s+")) {
            int len = Character.getNumericValue(token.charAt(token.length() - 1));
            String pitch = token.substring(0, token.length() - 1);
            int note = -1;
            if (!pitch.equals("R")) {
                note = key + NAMES.indexOf(pitch.charAt(0));
                for (char c : pitch.substring(1).toCharArray()) {
                    note += switch (c) {
                        case '#' -> 1;
                        case '\'' -> 12;
                        case ',' -> -12;
                        default -> throw new IllegalArgumentException("bad note " + token + " in " + name);
                    };
                }
                if (note < 0 || note > 24) {
                    throw new IllegalArgumentException(token + " is outside the note block range in " + name);
                }
            }
            for (int i = 0; i < len; i++) {
                notes.add(note);
                onset.add(i == 0 && note >= 0);
            }
        }
        int[] n = notes.stream().mapToInt(Integer::intValue).toArray();
        boolean[] o = new boolean[onset.size()];
        for (int i = 0; i < o.length; i++) {
            o[i] = onset.get(i);
        }
        return new Song(name, n, o);
    }
}
