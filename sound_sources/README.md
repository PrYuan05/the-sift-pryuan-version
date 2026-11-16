# 音效素材清單（sound_sources）

這個資料夾放**下載的原始素材**，不進 git（只有這份 README 會 commit）。
`tools/audio/build_sounds.py` 會讀這裡的檔案，裁切、變調、混上合成的音色後，輸出到 `assets/pysift/sounds/`。

## 怎麼放
- 每隻生物一個資料夾：`sound_sources/<生物 id>/`，生態域放 `sound_sources/ambient/<生態域 id>/`。
- 檔名開頭寫用途，後面隨意：例如 `hurt_bear_growl.mp3`、`ambient_whale.wav`。
  用途：`ambient`（平常叫聲）、`hurt`、`death`、`step`、`attack`、`special`（技能）。
- mp3 / wav / ogg 都可以；不必先剪，我來剪。
- **來源與授權**：在同一個資料夾放一個 `sources.txt`，每行貼「檔名 + 下載網址」。發版時會整理成 `assets/pysift/sounds/CREDITS.md`。

## 可以用的來源
| 來源 | 授權 | 說明 |
| :-- | :-- | :-- |
| [Pixabay Sound Effects](https://pixabay.com/sound-effects/) | Pixabay Content License | 可以改、可以放進模組；不可把原檔單獨散布（我們一律加工過才用） |
| [Freesound](https://freesound.org/)（篩選 **CC0**） | CC0 | 最安全，不用標示也行 |
| [Kenney Audio](https://kenney.nl/assets/category:Audio) | CC0 | 介面、腳步、衝擊類很好用 |
| ~~Epidemic Sound~~ | 訂閱授權 | **不能用**：授權不允許把音檔本身散布在模組裡 |

## 圖例
- **合成** = 全部用程式做，不用下載。
- **素材** = 需要下載，括號裡是建議的英文搜尋關鍵字（2～3 個候選檔就夠，我會挑、會混）。
- ★ = 第一批試做。

---

## 一、試做（先做這三樣）
| ★ | 對象 | 聲音 | 做法 |
| :-- | :-- | :-- | :-- |
| ★ | 歌者 `singer` | 平常哼唱、受傷、死亡 | **合成**：類人聲的母音合成（formant）＋水晶泛音。不用下載 |
| ★ | 哀悼者 `mourner` | 哭泣、受傷、死亡 | 合成（歌者的音色往下移、加顫抖）＋**素材**：一段低沉哀鳴（`wind howl`、`low moan`、`whale call`） |
| ★ | 柳絮林地 `willow_grove` | 環境底噪、偶爾的低鳴 | **合成**：風聲雜訊＋遠處的水晶和聲。不用下載 |

所以試做只需要你下載 **1 類素材**：放進 `sound_sources/mourner/`，檔名開頭 `ambient_`。

---

## 二、生物（第二批）
| 對象 | 個性 | 需要的聲音 | 做法 |
| :-- | :-- | :-- | :-- |
| 迴音傀儡 `echo_golem` | 中立、搬運靈魂的石像 | 平常、受傷、死亡、腳步 | 合成（低沉共鳴）＋**素材**：石頭摩擦（`stone grinding`、`rock scrape`） |
| 蹭蹭怪 `nuzzle` | 溫和、會蹭人 | 平常、被打的尖叫、死亡 | **素材**：小動物咕嚕與尖叫（`small animal purr`、`squeak`、`guinea pig`） |
| 泥板獸 `slabber` | 隙浮的牛 | 平常、受傷、死亡、腳步 | **素材**：低沉哞叫或喘氣（`cow moo`、`yak grunt`、`snort`） |
| 授粉者 `pollinator` | 會螫人的蟲 | 嗡嗡聲、螫、死亡 | 合成（翅膀嗡鳴）＋**素材**：昆蟲（`insect buzz`、`cicada`） |
| 漫遊根 `roamroot` | 緩慢的植物巨人 | 平常、跺地、受傷、死亡 | **素材**：木頭吱嘎與低吼（`tree creak`、`wood crack`、`deep groan`） |
| 盛開花苞 `bloombud` | 偽裝成花苞，會咬合 | 合上、張開 | **素材**：濕黏的咬合聲（`squelch`、`venus flytrap`、`wet snap`） |
| 哨兵 `sentinel` | 拿重劍的遺跡戰士 | 平常、蓄力劈砍、受傷、死亡 | 合成（金屬共鳴）＋**素材**：盔甲與劍（`armor clank`、`sword swing heavy`） |
| 追蹤者 `stalker` | 黑暗中隱形、繞背 | 平常（很小聲）、偷襲、死亡 | **素材**：呼吸與嘶聲（`creature breath`、`hiss`） |
| 調音器 `tuner` | 只會幫別的怪物加持 | 平常、施法、死亡 | **合成**：調頻和弦與音叉聲 |
| 獵人 `hunter` | 君王的士兵、丟標槍 | 平常、投擲、受傷、死亡 | **素材**：低吼與喊叫（`goblin grunt`、`creature growl`） |
| 飛鏢背 `dartback` | 有殼、射刺、衝撞 | 平常、射擊、衝撞、受傷、死亡 | **素材**：甲殼與爬蟲（`crab clicking`、`lizard hiss`） |
| 引信蠅 `fusefly` | 會飛、死後爆炸 | 飛行嗡嗡、引信嘶嘶、死亡 | 合成（嗡鳴＋引信嘶聲）。爆炸沿用原版 |
| 刺球 `prickle` | 帶刺、會反傷 | 平常、射刺、受傷、死亡 | **素材**：刺蝟或豪豬（`hedgehog`、`porcupine`、`rattle`） |
| 築巢者 `nester` | 會召喚幼體的母獸 | 平常、呼喚、受傷、死亡 | **素材**：低沉的母獸叫聲（`bird call deep`、`animal call`） |
| 幼苗、萌芽 `seedling` `sprout` | 築巢者的幼體 | 平常、受傷、死亡 | 用築巢者的素材**變高音**，不用另外下載 |
| 清道夫 `scavenger` | 腐食獵手、咬人流血 | 平常、咬、受傷、死亡 | **素材**：鬣狗或禿鷹（`hyena laugh`、`vulture`、`jackal`） |
| 投擲者 `hurler` | 從地上挖石頭丟人 | 平常、挖起、投擲、受傷、死亡 | **素材**：猩猩低吼（`gorilla grunt`、`ape`）；挖石沿用原版 |
| 搖晃怪 `wobble` | 傻乎乎的 | 平常、受傷、死亡 | **素材**：滑稽的果凍聲（`jelly wobble`、`boing`、`cartoon`） |
| 陷阱師 `trapper` | 君王的僕從、丟網 | 平常、丟網、受傷、死亡 | 用獵人的素材換音色，不用另外下載 |
| 掠奪精 `lootkin` | 很快、會逃跑 | 平常（叮噹）、逃跑、死亡 | 合成（金幣叮噹）＋**素材**：小生物笑聲（`goblin giggle`、`small creature laugh`） |
| 布魯布 `blub` | 已有自己的音檔 | — | **保留現有的，不動** |
| 隙浮守衛 `sift_warden` | 原版監守者的音效 | — | 維持原版，只調音高（已經做了） |

## 三、Boss（第三批）
| 對象 | 需要的聲音 | 做法 |
| :-- | :-- | :-- |
| 調和者 `harmonizer` | 平常、技能、受傷、死亡 | **合成**：巨大的和弦合唱、聲波。不用下載 |
| 君王 `monarch` | 平常、召喚、受傷、死亡 | **素材**：大型猛禽叫聲（`eagle screech`、`hawk`）＋合成的王者回音 |
| 幽匿巨怪 `sculk_monstrosity` | 平常、咆哮、受傷、死亡 | 合成（低頻心跳與轟鳴）＋**素材**：巨獸咆哮（`monster roar`、`dinosaur`、`lion roar`） |

## 四、生態域環境音（7 個）
全部都可以**純合成**（底噪＋偶爾一聲低鳴＋零星的小聲音）。想更自然的話，可以補下面的素材：
| 生態域 | 氣氛 | 可補的素材 |
| :-- | :-- | :-- |
| 柳絮林地 `willow_grove` ★ | 柔和、垂柳、靈液池 | （試做：純合成） |
| 赤紅沉積峽谷 `crimson_strata_canyon` | 乾燥遼闊 | `canyon wind`、`desert wind` |
| 紫晶深板岩區 `violet_slate_abyss` | 幽暗、深淵 | `cave drips`、`deep cave ambience` |
| 琥珀沙丘 `amber_dunes` | 溫暖、沙 | `sand wind`、`dune` |
| 紅區洞穴 `red_zone_caves` | 低沉、壓迫 | `cave rumble`、`underground` |
| 搖籃曲山丘 `lullaby_hills` | 溫柔、遠處的歌聲 | （純合成：遠處歌者的哼唱） |
| 靈魂火山高原 `soul_caldera` | 火山、靈魂 | `lava bubbling`、`fire crackle`、`volcano rumble` |
