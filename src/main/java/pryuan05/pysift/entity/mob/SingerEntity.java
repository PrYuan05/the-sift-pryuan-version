package pryuan05.pysift.entity.mob;

import pryuan05.pysift.block.SoulCrystal;
import java.util.List;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.core.particles.ParticleTypes;
import pryuan05.pysift.entity.ModEntities;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import pryuan05.pysift.block.SiftPortalRitual;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import pryuan05.pysift.entity.PysiftAnimalEntity;

/**
 * 歌者（音律神獸，被動）。16 格內有玩家吹響山羊角時，面向該玩家唱出和聲（動畫 sing），
 * 給周圍 16 格內所有玩家 30 秒抗性提升 I；每隻歌者冷卻 10 秒。體型是原本的 1.3 倍。
 * 會和迴音傀儡一起出現；傀儡附近沒有玩家時，會把頭頂的靈魂晶塊送給歌者（{@link #receiveSoulCrystal}）。
 * 出生時從地底爬出（{@link #startEmerging}，動畫 emerge，3 秒）：耳朵先冒出、再露出頭，雙手撐地把身體拉上來，最後抖掉泥土；
 * 爬出期間不能移動、不會受傷，腳下方塊噴出碎屑並發出挖掘聲。
 * <p>儀式歌者（在遠古城市吹山羊角召喚出來的，{@link #isRitual}）：固定站在原地不走動，
 * 手持迴音碎片右鍵它，它會召喚迴音傀儡擺放八音唱片盒（{@link SiftPortalRitual#startRitual}）。
 * 隙浮自然生成的歌者照常走動，不會觸發儀式。
 */
public class SingerEntity extends PysiftAnimalEntity {
    private static final double RANGE = 16.0;
    /** 從地底爬出的時間（tick），要和 animation.singer.emerge 的長度一致。 */
    private static final int EMERGE_TICKS = 60;
    private static final EntityDataAccessor<Boolean> DATA_EMERGING = SynchedEntityData.defineId(SingerEntity.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> DATA_RITUAL = SynchedEntityData.defineId(SingerEntity.class, EntityDataSerializers.BOOLEAN);
    /** 儀式歌者現在的動作（同步到用戶端，由 "ritual" 動畫控制器播放）：無／招手／召喚／終曲。 */
    private static final EntityDataAccessor<Integer> DATA_ACTION = SynchedEntityData.defineId(SingerEntity.class, EntityDataSerializers.INT);
    /** 目前動作開始時的遊戲時間（用戶端用來把懷裡的小傀儡擺在和動畫一致的位置）。 */
    private static final EntityDataAccessor<Integer> DATA_ACTION_START = SynchedEntityData.defineId(SingerEntity.class, EntityDataSerializers.INT);
    /** 抱小傀儡轉圈前的朝向：轉完一圈後回到這個方向。 */
    private float playBaseYaw;
    /** 吹山羊角時就算好的儀式配置（門的中點、哪一側、唱片盒那一排的位置）；之後召喚與擺放都沿用它。 */
    private pryuan05.pysift.block.SiftPortalRitual.Site ritualSite;
    public static final int ACTION_NONE = 0, ACTION_BECKON = 1, ACTION_SUMMON = 2, ACTION_FINALE = 3, ACTION_SWEEP = 4, ACTION_PLAY = 5,
            ACTION_AWAIT = 6, ACTION_CELEBRATE = 7;
    /** 招手多久沒人理（tick）就抱起小傀儡轉圈圈，之後每隔多久再玩一次。 */
    private static final int BORED_AFTER = 400, PLAY_TICKS = 120, PLAY_AGAIN = 1200;
    private int beckonTicks;
    /** 玩完小傀儡之後要回到的等待動作（招手或等唱片）。 */
    private int waitAction = ACTION_BECKON;
    /**
     * 哼歌（曲目見 {@link SingerSongs}）：等唱片時把 WAITING 的曲子一首接一首完整哼完，每首之間休息 SONG_REST tick；
     * 開門慶祝時哼 CELEBRATION。每格八分音符 HUM_STEP tick（慶祝時 CELEBRATE_STEP，比較輕快）。
     */
    private static final int HUM_STEP = 5, CELEBRATE_STEP = 3, SONG_REST = 40;
    private int humTicks;
    private int songIndex;
    /** 召喚（summon 2 秒）與終曲（sing 1.5 秒）播完後回到無動作。 */
    private int actionTicks;
    /** 開門後鑽回地底離開（動畫 burrow）。 */
    private static final EntityDataAccessor<Boolean> DATA_LEAVING = SynchedEntityData.defineId(SingerEntity.class, EntityDataSerializers.BOOLEAN);
    /**
     * 要和 animation.singer.burrow 的長度一致（5.5 秒）：鞠躬 → 單手揮別 → 蹲低（剩 79 tick）→ 跳起 → 第 2.5 秒開始用 2 秒
     * 慢慢轉一圈鑽進地底（剩 BURROW_DIVE tick）→ 第 4.5 秒完全沒入，再等 1 秒才移除，讓用戶端的動畫一定播得完。
     */
    private static final int BURROW_TICKS = 110, BURROW_DIVE = 60, BURROW_UNDER = 20;
    private int burrowTicks;
    private int songCooldown;
    private int emergeTicks;
    /**
     * 認出監守者（§4.7）：24 格內有監守者時，歌者先不安地發抖（UNEASE_TICKS），再面向它倒唱八音（{@link SingerSongs#MOURNING}），
     * 唱完監守者平靜 SOOTHE_TICKS（{@link pryuan05.pysift.entity.WardenSoothing}）。每隻歌者之後要隔 MOURN_COOLDOWN 才會再唱。
     */
    public static final double WARDEN_RANGE = 24.0;
    private static final int UNEASE_TICKS = 40, MOURN_STEP = 5, SOOTHE_TICKS = 600, MOURN_COOLDOWN = 400;
    private net.minecraft.world.entity.monster.warden.Warden mournFor;
    private int mournTicks, mournCooldown;
    /**
     * 屍化（§4.7）：歌者在主世界待著，附近 SHELTER 格內沒有靈魂晶塊或靈液時，每 tick 累積一點；累積到 HOLLOW_TICKS（5 分鐘）
     * 就變成哀悼者（{@link MournerEntity}）。有靈魂晶塊或靈液的地方會慢慢恢復。儀式歌者不會屍化（開門後就回去了）。
     * 存檔欄位 OverworldTicks，測試可以用 /data merge 直接設定。
     */
    public static final int HOLLOW_TICKS = 6000, SHELTER = 6;
    private int overworldTicks;
    private boolean sheltered;
    /** 搖籃曲香爐（LullabyCenserBlock）照顧到哪個遊戲時間為止。 */
    private long shelteredUntil;

    public void shelter(long until) {
        shelteredUntil = Math.max(shelteredUntil, until);
    }

    public SingerEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_EMERGING, false);
        builder.define(DATA_RITUAL, false);
        builder.define(DATA_ACTION, ACTION_NONE);
        builder.define(DATA_ACTION_START, 0);
        builder.define(DATA_LEAVING, false);
    }

    /** 還在等玩家給迴音碎片：一直招手。 */
    public void setWaiting(boolean waiting) {
        setAction(waiting ? ACTION_BECKON : ACTION_NONE);
    }

    public boolean isWaiting() {
        return ritualAction() == ACTION_BECKON;
    }

    public int ritualAction() {
        return this.entityData.get(DATA_ACTION);
    }

    /** 播放儀式動作；召喚與終曲會自己結束。 */
    public void setAction(int action) {
        if (ritualAction() == ACTION_PLAY && action != ACTION_PLAY) {   // 中途被打斷：轉回原本的方向
            faceYaw(playBaseYaw);
        }
        if (action == ACTION_AWAIT && ritualAction() != ACTION_PLAY) {   // 剛開始等唱片：重新計算多久會無聊
            beckonTicks = 0;
        }
        if (action == ACTION_AWAIT || action == ACTION_CELEBRATE) {   // 旋律從頭唱
            humTicks = 0;
        }
        this.entityData.set(DATA_ACTION, action);
        this.entityData.set(DATA_ACTION_START, (int) this.level().getGameTime());
        this.actionTicks = switch (action) {
            case ACTION_SUMMON -> 40;
            case ACTION_FINALE -> 200;    // 正常情況下開門時就會換成 celebrate；門沒開成（唱片盒被打破）就回去等唱片
            case ACTION_CELEBRATE -> 100;   // 快樂頌第一句（32 格 × 3 tick）唱完再退場
            case ACTION_SWEEP -> 50;
            case ACTION_PLAY -> PLAY_TICKS;
            default -> 0;
        };
        if (action != ACTION_PLAY) {
            releaseToy();
        }
    }

    // ---------------------------------------------------------------- bored: hug a tiny Echo Golem and spin around
    private void startPlaying(ServerLevel level) {
        EchoGolemEntity toy = ModEntities.ECHO_GOLEM.create(level, EntitySpawnReason.TRIGGERED);
        if (toy == null) {
            return;
        }
        toy.snapTo(this.getX(), this.getY(), this.getZ(), this.getYRot() + 180, 0);
        toy.becomeToy();
        level.addFreshEntity(toy);
        toy.startRiding(this, true, true);
        playBaseYaw = this.getYRot();
        setAction(ACTION_PLAY);
        voice(pryuan05.pysift.sound.ModSounds.SINGER_GIGGLE, 1.5f, "giggle");
        level.sendParticles(ParticleTypes.HEART, this.getX(), this.getY() + this.getBbHeight() + 0.3, this.getZ(), 4, 0.5, 0.2, 0.5, 0);
        level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 1.4, this.getZ(), 16, 0.4, 0.4, 0.4, 0.02);
    }

    /** 把懷裡的小傀儡放回地底。 */
    private void releaseToy() {
        for (net.minecraft.world.entity.Entity passenger : List.copyOf(this.getPassengers())) {
            passenger.stopRiding();
            if (passenger instanceof EchoGolemEntity toy) {
                toy.sinkAway();
            }
        }
    }

    // 抱小傀儡（animation.singer.play，6 秒）：0~1.2 秒彎腰撈起抱到胸前 → 1.2~2.2 秒高舉過頭 → 2.2~4.4 秒抱在胸前轉一圈
    // → 4.4~6 秒放回地上。小傀儡的位置用同一條時間曲線算（用戶端與伺服器一致）。
    private static final double[][] TOY_KEYS = {   // {秒, 前方距離, 高度}（以原始體型 1.456 為準）
            {0.0, 0.95, 0.0}, {0.6, 0.9, 0.15}, {1.2, 0.45, 1.05}, {2.2, 0.15, 2.65}, {2.6, 0.5, 1.25},
            {4.4, 0.5, 1.25}, {5.2, 0.9, 0.2}, {6.0, 0.95, 0.0}};

    private static double toyKey(double t, int field) {
        for (int i = 1; i < TOY_KEYS.length; i++) {
            if (t <= TOY_KEYS[i][0]) {
                double a = TOY_KEYS[i - 1][0], b = TOY_KEYS[i][0];
                double u = (t - a) / (b - a);
                u = u * u * (3 - 2 * u);   // smoothstep
                return TOY_KEYS[i - 1][field] + (TOY_KEYS[i][field] - TOY_KEYS[i - 1][field]) * u;
            }
        }
        return TOY_KEYS[TOY_KEYS.length - 1][field];
    }

    @Override
    protected void positionRider(net.minecraft.world.entity.Entity passenger, net.minecraft.world.entity.Entity.MoveFunction move) {
        double t = Math.max(0, (this.level().getGameTime() - this.entityData.get(DATA_ACTION_START)) / 20.0);
        double k = this.getScale() / 1.456;
        double yaw = Math.toRadians(this.yBodyRot);
        double reach = toyKey(t, 1) * k, height = toyKey(t, 2) * k;
        move.accept(passenger, this.getX() - Math.sin(yaw) * reach, this.getY() + height, this.getZ() + Math.cos(yaw) * reach);
        passenger.setYRot(this.yBodyRot + 180.0f);
        if (passenger instanceof net.minecraft.world.entity.LivingEntity living) {
            living.setYBodyRot(this.yBodyRot + 180.0f);
            living.setYHeadRot(this.yBodyRot + 180.0f);
        }
    }

    private void faceYaw(float yaw) {
        this.setYRot(yaw);
        this.setYBodyRot(yaw);
        this.setYHeadRot(yaw);
    }

    // ---------------------------------------------------------------- ritual site (decided once, when the horn is blown)
    public pryuan05.pysift.block.SiftPortalRitual.Site getRitualSite() {
        return ritualSite;
    }

    public void setRitualSite(pryuan05.pysift.block.SiftPortalRitual.Site site) {
        this.ritualSite = site;
    }

    public boolean isLeaving() {
        return this.entityData.get(DATA_LEAVING);
    }

    /** 門開了：揮手道別（sing），然後鑽回地底消失。 */
    public void startLeaving() {
        if (isLeaving() || isRemoved()) {
            return;
        }
        setAction(ACTION_NONE);
        this.entityData.set(DATA_LEAVING, true);
        this.burrowTicks = BURROW_TICKS;
        this.playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 1.5f, 1.4f);
    }

    /** 遠古城市儀式召喚的歌者：固定不動，不會消失。 */
    public void setRitual(boolean ritual) {
        this.entityData.set(DATA_RITUAL, ritual);
        if (ritual) {
            this.setPersistenceRequired();
            setWaiting(true);
        }
    }

    public boolean isRitual() {
        return this.entityData.get(DATA_RITUAL);
    }

    /** 儀式歌者不產生震動（腳步、動作都不會被幽匿感測器聽到）。 */
    @Override
    public boolean dampensVibrations() {
        return isRitual() || super.dampensVibrations();
    }

    @Override
    public boolean isSteppingCarefully() {
        return isRitual() || super.isSteppingCarefully();
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Ritual", isRitual());
        output.putInt("OverworldTicks", overworldTicks);
        if (ritualSite != null) {
            ritualSite.save(output);
        }
        output.putBoolean("Waiting", isWaiting());
        output.putBoolean("AwaitDiscs", ritualAction() == ACTION_AWAIT || ritualAction() == ACTION_PLAY && waitAction == ACTION_AWAIT);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.entityData.set(DATA_RITUAL, input.getBooleanOr("Ritual", false));
        overworldTicks = input.getIntOr("OverworldTicks", 0);
        ritualSite = pryuan05.pysift.block.SiftPortalRitual.Site.load(input);
        if (input.getBooleanOr("AwaitDiscs", false)) {
            setAction(ACTION_AWAIT);
        } else {
            setWaiting(input.getBooleanOr("Waiting", false));
        }
    }

    /** 自然生成、生怪蛋、/summon 都會經過這裡：出生時從地底爬出。 */
    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason, SpawnGroupData data) {
        SpawnGroupData result = super.finalizeSpawn(level, difficulty, reason, data);
        if (reason != EntitySpawnReason.CHUNK_GENERATION) {   // 區塊生成時沒有人在看，直接站在地上
            startEmerging();
        }
        return result;
    }

    /** 開始從地底爬出（伺服器端）。 */
    public void startEmerging() {
        this.emergeTicks = EMERGE_TICKS;
        this.entityData.set(DATA_EMERGING, true);
    }

    public boolean isEmerging() {
        return this.entityData.get(DATA_EMERGING);
    }

    @Override
    protected String heldMovementAnimation() {
        return isEmerging() ? "emerge" : isLeaving() ? "burrow" : null;
    }

    /** 爬出期間不跑 AI、不移動。 */
    @Override
    protected boolean isImmobile() {
        return isEmerging() || isLeaving() || isRitual() || super.isImmobile();   // 儀式歌者不跑 AI：頭與視角都不轉
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if ((isEmerging() || isLeaving() || isRitual()) && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    public void tick() {
        super.tick();
        if (this.emergeTicks > 0 && this.level() instanceof ServerLevel level) {
            tickEmerge(level, EMERGE_TICKS - this.emergeTicks);
            if (--this.emergeTicks == 0) {
                this.entityData.set(DATA_EMERGING, false);
            }
        }
        if (this.level() instanceof ServerLevel server && isRitual() && !isEmerging() && !isLeaving()) {
            int action = ritualAction();
            if (action == ACTION_BECKON && this.tickCount % 140 == 0) {   // 招手時偶爾呼喚一聲
                voice(pryuan05.pysift.sound.ModSounds.SINGER_BECKON, 1.4f, "beckon");
            }
            if ((action == ACTION_BECKON || action == ACTION_AWAIT) && ++beckonTicks >= BORED_AFTER) {   // 等太久：抱起小傀儡轉圈圈
                beckonTicks = BORED_AFTER - PLAY_AGAIN;
                waitAction = action;
                startPlaying(server);
            } else if (action == ACTION_PLAY) {
                int elapsed = PLAY_TICKS - actionTicks;   // 2.2~4.4 秒：抱著轉一圈；其他時間面向原本的方向
                faceYaw(elapsed >= 44 && elapsed < 88 ? playBaseYaw + 360.0f * (elapsed - 44) / 44.0f : playBaseYaw);
                if (this.tickCount % 20 == 0) {
                    server.sendParticles(ParticleTypes.NOTE, this.getX(), this.getY() + this.getBbHeight() + 0.2, this.getZ(), 2, 0.6, 0.2, 0.6, 1.0);
                }
            }
            if (mournTicks > 0) {
                // 正在對監守者唱歌：等唱片的哼歌先停下來
            } else if (ritualAction() == ACTION_AWAIT) {
                if (tickSong(server, SingerSongs.WAITING.get(songIndex), HUM_STEP, SONG_REST)) {   // 一首唱完換下一首
                    songIndex = (songIndex + 1) % SingerSongs.WAITING.size();
                }
            } else if (ritualAction() == ACTION_CELEBRATE) {
                tickSong(server, SingerSongs.CELEBRATION, CELEBRATE_STEP, 1000);
            }
        }
        if (this.level() instanceof ServerLevel server && !isEmerging() && !isLeaving()) {
            tickMourning(server);
            tickHollowing(server);
            tickChoir(server);
            tickLineSong(server);
        }
        if (this.actionTicks > 0 && !this.level().isClientSide() && --this.actionTicks == 0) {
            // 玩夠了回去繼續等；召喚完傀儡之後，儀式歌者改成等玩家放唱片（await）
            int done = ritualAction();
            if (done == ACTION_CELEBRATE) {   // 慶祝完：揮手道別、鑽回地底
                startLeaving();
            } else {
                setAction(done == ACTION_PLAY ? waitAction
                        : (done == ACTION_SUMMON || done == ACTION_FINALE) && isRitual() ? ACTION_AWAIT : ACTION_NONE);
            }
        }
        if (this.burrowTicks > 0 && this.level() instanceof ServerLevel level) {
            int left = this.burrowTicks;
            if (left == 79) {   // 蹲低準備起跳：「再——見」兩個下行音
                hum(level, 19, true);
            } else if (left == 75) {
                hum(level, 12, true);
            }
            if (left == BURROW_DIVE) {   // 跳起轉圈、開始往下鑽：爆出一圈靈魂與音符
                level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 0.5, this.getZ(), 30, 0.8, 0.4, 0.8, 0.05);
                level.sendParticles(ParticleTypes.NOTE, this.getX(), this.getY() + this.getBbHeight(), this.getZ(), 8, 1.0, 0.5, 1.0, 1.0);
                this.playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 1.5f, 1.8f);
            }
            if (left <= BURROW_DIVE && left > BURROW_UNDER) {   // 只有往下鑽的那 2 秒有碎屑與挖掘聲
                tickEmerge(level, Math.min(EMERGE_TICKS - 7, left));
            }
            if (--this.burrowTicks == 0) {
                level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 0.3, this.getZ(), 20, 0.6, 0.2, 0.6, 0.02);
                this.discard();
            }
        }
    }

    // ---------------------------------------------------------------- recognising a Warden (its kin, starved in the Overworld)
    private void tickMourning(ServerLevel level) {
        if (mournCooldown > 0) {
            mournCooldown--;
        }
        if (mournTicks == 0) {
            if (mournCooldown > 0 || this.tickCount % 20 != 0) {
                return;
            }
            var wardens = level.getEntitiesOfClass(net.minecraft.world.entity.monster.warden.Warden.class,
                    this.getBoundingBox().inflate(WARDEN_RANGE), w -> w.isAlive() && !pryuan05.pysift.entity.WardenSoothing.isSoothed(w));
            if (wardens.isEmpty()) {
                return;
            }
            mournFor = wardens.stream().min(java.util.Comparator.comparingDouble(this::distanceToSqr)).get();
            mournTicks = UNEASE_TICKS + SingerSongs.MOURNING.length() * MOURN_STEP;
            humTicks = 0;
            this.getNavigation().stop();
            this.playSound(SoundEvents.WARDEN_HEARTBEAT, 1.2f, 1.4f);
            voice(pryuan05.pysift.sound.ModSounds.SINGER_UNEASE, 1.3f, "unease");
            return;
        }
        if (mournFor == null || !mournFor.isAlive()) {   // 監守者不見了：停下來
            mournTicks = 0;
            mournCooldown = 100;
            return;
        }
        this.getNavigation().stop();
        this.getLookControl().setLookAt(mournFor, 30.0f, 30.0f);
        int sung = UNEASE_TICKS + SingerSongs.MOURNING.length() * MOURN_STEP - mournTicks;
        if (sung < UNEASE_TICKS) {   // 不安：發抖、心跳、靈魂從身上飄散
            if (!isRitual()) {
                this.setYBodyRot(this.yBodyRot + (this.random.nextFloat() - 0.5f) * 12.0f);
            }
            if (sung % 10 == 0) {
                level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + this.getBbHeight() * 0.6, this.getZ(), 3, 0.4, 0.4, 0.4, 0.01);
            }
            if (sung == UNEASE_TICKS - 1) {
                this.triggerAnim("skill", "sing");
                this.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 1.6f, 0.6f);
            }
        } else {
            tickSong(level, SingerSongs.MOURNING, MOURN_STEP, 0);
            if (sung % 8 == 0) {   // 歌聲飄向監守者
                double dx = mournFor.getX() - this.getX(), dy = mournFor.getEyeY() - this.getEyeY(), dz = mournFor.getZ() - this.getZ();
                double len = Math.max(1.0, Math.sqrt(dx * dx + dy * dy + dz * dz));
                level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getEyeY(), this.getZ(), 0, dx / len, dy / len, dz / len, 0.4);
            }
        }
        if (--mournTicks == 0) {
            pryuan05.pysift.entity.WardenSoothing.soothe(level, mournFor, SOOTHE_TICKS);
            level.sendParticles(ParticleTypes.SCULK_SOUL, mournFor.getX(), mournFor.getY() + 1.5, mournFor.getZ(), 30, 0.6, 0.8, 0.6, 0.02);
            level.playSound(null, mournFor.blockPosition(), SoundEvents.WARDEN_LISTENING, SoundSource.HOSTILE, 1.5f, 0.6f);
            for (Player p : level.getEntitiesOfClass(Player.class, this.getBoundingBox().inflate(WARDEN_RANGE))) {
                if (p instanceof net.minecraft.server.level.ServerPlayer sp) {
                    pryuan05.pysift.progression.StoryTriggers.wardenSoothed(sp);
                }
            }
            mournFor = null;
            mournCooldown = MOURN_COOLDOWN;
        }
    }

    // ---------------------------------------------------------------- the echo den choir (§4.7「回音窟」)
    /**
     * 回音窟舞台上的領唱（結構裡帶 pysift_den_lead 標籤）：CHOIR_RANGE 格內有玩家時，每 CHOIR_PERIOD tick（20 秒）帶頭唱一次正確的八音
     * （{@link SingerSongs#OPENING}，替篩網「調音」），其他合唱的歌者（pysift_den_choir）一起做合唱動作（choir，嘴巴隨每個音張合），唱三度／五度和聲。
     * 合唱期間附近被驚醒的守衛會平靜下來（DenGuard.calm）。
     */
    public static final String DEN_LEAD = "pysift_den_lead", DEN_CHOIR = "pysift_den_choir";
    private static final int CHOIR_PERIOD = 400;
    /** 合唱團其他歌者對主旋律唱的和聲（半音）：三度、五度輪流。 */
    private static final int[] CHOIR_HARMONY = {4, 7, -5};
    private static final double CHOIR_RANGE = 24.0;

    private void tickChoir(ServerLevel level) {
        if (!this.entityTags().contains(DEN_LEAD) || mournTicks > 0 || (this.tickCount + this.getId()) % CHOIR_PERIOD != 0
                || level.getNearestPlayer(this, CHOIR_RANGE) == null) {
            return;
        }
        var choir = level.getEntitiesOfClass(SingerEntity.class, this.getBoundingBox().inflate(16.0),
                s -> s.isAlive() && s.entityTags().contains(DEN_CHOIR));
        // OPENING：8 個音、每音 2 格 × 8 tick = 6.4 秒，和 animation.singer.choir 一樣長（每 0.8 秒張嘴唱一個音）
        pryuan05.pysift.progression.StoryItems.play(level, this, SingerSongs.OPENING, 8, i -> {
            int note = SingerSongs.OPENING.notes()[i];
            int k = 0;
            for (SingerEntity s : choir) {
                if (i == 0) {
                    s.triggerAnim("skill", "choir");
                }
                if (s != this) {   // 領唱的主旋律由 play() 發聲；其他人唱和聲
                    float pitch = (float) Math.pow(2.0, (note + CHOIR_HARMONY[k++ % CHOIR_HARMONY.length] - 12) / 12.0);
                    pitch = Math.max(0.5f, Math.min(2.0f, pitch));
                    level.playSound(null, s.getX(), s.getEyeY(), s.getZ(), pryuan05.pysift.sound.ModSounds.SINGER_VOICE, SoundSource.NEUTRAL, 0.7f, pitch);
                    level.playSound(null, s.getX(), s.getEyeY(), s.getZ(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.NEUTRAL, 0.5f, pitch);
                }
                level.sendParticles(ParticleTypes.NOTE, s.getX(), s.getY() + s.getBbHeight() + 0.3, s.getZ(), 0, (i * 3) / 24.0, 0, 0, 1.0);
            }
            if (i == 0) {
                for (SiftWardenEntity w : level.getEntitiesOfClass(SiftWardenEntity.class, this.getBoundingBox().inflate(CHOIR_RANGE))) {
                    pryuan05.pysift.entity.DenGuard.calm(w);
                }
            }
        }, null);
    }

    // ---------------------------------------------------------------- hollowing: starving in the soulless Overworld
    private void tickHollowing(ServerLevel level) {
        if (isRitual() || isRemoved()) {
            return;
        }
        if (level.dimension() != Level.OVERWORLD) {
            overworldTicks = Math.max(0, overworldTicks - 4);
            return;
        }
        if (this.tickCount % 40 == 0) {
            sheltered = nearSoul(level);
        }
        if (sheltered || level.getGameTime() < shelteredUntil) {
            overworldTicks = Math.max(0, overworldTicks - 2);
            return;
        }
        overworldTicks++;
        if (overworldTicks > HOLLOW_TICKS - 600 && this.tickCount % 10 == 0) {   // 最後 30 秒：發抖、毛一直掉
            level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + this.getBbHeight() * 0.6, this.getZ(), 2, 0.4, 0.5, 0.4, 0.02);
            if (this.tickCount % 40 == 0) {
                this.playSound(SoundEvents.WARDEN_HEARTBEAT, 0.8f, 1.6f);
                if (this.tickCount % 120 == 0) {
                    voice(pryuan05.pysift.sound.ModSounds.SINGER_STARVE, 1.0f, "starve");
                }
            }
        }
        if (overworldTicks >= HOLLOW_TICKS) {
            MournerEntity mourner = this.convertTo(ModEntities.MOURNER,
                    net.minecraft.world.entity.ConversionParams.single(this, false, false), m -> { });
            if (mourner != null) {
                mourner.playSound(pryuan05.pysift.sound.ModSounds.SINGER_HOLLOW, 1.6f, 1.0f);
                level.sendParticles(ParticleTypes.SCULK_SOUL, mourner.getX(), mourner.getY() + 1.5, mourner.getZ(), 40, 0.6, 0.8, 0.6, 0.03);
            }
        }
    }

    /** SHELTER 格內有靈魂晶塊或靈液。 */
    private boolean nearSoul(ServerLevel level) {
        for (net.minecraft.core.BlockPos p : net.minecraft.core.BlockPos.betweenClosed(
                this.blockPosition().offset(-SHELTER, -SHELTER, -SHELTER), this.blockPosition().offset(SHELTER, SHELTER, SHELTER))) {
            BlockState st = level.getBlockState(p);
            if (st.is(SoulCrystal.SOUL_CRYSTAL_BLOCK) || pryuan05.pysift.fluid.SpiritInteractions.isSpirit(st.getFluidState())) {
                return true;
            }
        }
        return false;
    }

    public int getOverworldTicks() {
        return overworldTicks;
    }

    public boolean isMourning() {
        return mournTicks > 0;
    }

    // ---------------------------------------------------------------- singing into a soul conduit (soul redstone)
    /** 對著導線唱歌：LINE_RANGE 格內有靈魂導線時站定唱完一整套歌（{@link SingerSongs#LINE}），唱完休息 LINE_REST tick。 */
    private static final int LINE_RANGE = 3, LINE_REST = 600, LINE_GAP = 20;
    private net.minecraft.core.BlockPos lineConduit;
    private int lineSong, lineRest;

    public boolean isSingingToConduit() {
        return lineConduit != null;
    }

    /**
     * 歌聲就是靈魂訊號：歌者唱歌的期間，那段導線是訊號源（強度 15、{@link pryuan05.pysift.soulpower.SoulCircuit#SINGER_CAPACITY} SP）。
     * 儀式歌者、回音窟的合唱團與正在對監守者唱歌的歌者不唱這套歌。
     */
    private void tickLineSong(ServerLevel level) {
        if (isRitual() || mournTicks > 0 || this.entityTags().contains(DEN_CHOIR) || this.entityTags().contains(DEN_LEAD)) {
            lineConduit = null;
            return;
        }
        if (lineRest > 0) {
            lineRest--;
            return;
        }
        if (lineConduit == null) {
            if ((this.tickCount + this.getId()) % 40 != 0) {
                return;
            }
            lineConduit = pryuan05.pysift.soulpower.SoulCircuit.conduitNear(level, this.blockPosition(), LINE_RANGE);
            if (lineConduit == null) {
                return;
            }
            humTicks = 0;
            lineSong = 0;
            this.triggerAnim("skill", "sing");
        }
        if (!(level.getBlockState(lineConduit).getBlock() instanceof pryuan05.pysift.soulpower.SoulConduitBlock)
                || !lineConduit.closerThan(this.blockPosition(), LINE_RANGE + 3)) {
            lineConduit = null;     // 導線被拆了，或歌者被推開了
            return;
        }
        this.getNavigation().stop();
        this.getLookControl().setLookAt(lineConduit.getX() + 0.5, lineConduit.getY() + 0.5, lineConduit.getZ() + 0.5, 30.0f, 30.0f);
        if (this.tickCount % 10 == 0) {
            pryuan05.pysift.soulpower.SoulCircuit.feed(level, lineConduit, 30, pryuan05.pysift.soulpower.SoulCircuit.SINGER_CAPACITY, true);
        }
        if (this.tickCount % 20 == 0) {     // 音符從歌者飄向導線
            level.sendParticles(ParticleTypes.NOTE, (this.getX() + lineConduit.getX() + 0.5) / 2, this.getY() + this.getBbHeight() * 0.8,
                    (this.getZ() + lineConduit.getZ() + 0.5) / 2, 1, 0.3, 0.2, 0.3, 1.0);
        }
        if (tickSong(level, SingerSongs.LINE.get(lineSong), HUM_STEP, LINE_GAP) && ++lineSong >= SingerSongs.LINE.size()) {
            lineSong = 0;
            lineRest = LINE_REST;
            lineConduit = null;
        }
    }

    /**
     * 哼一首曲子（每個八分音符 step tick），唱完休息 rest tick；回傳 true 表示這一首（含休息）剛好結束。
     * 每小節的強拍（每 4 格的第一格）再疊一聲鐘聲。
     */
    private boolean tickSong(ServerLevel level, SingerSongs.Song song, int step, int rest) {
        int t = humTicks++;
        if (humTicks >= song.length() * step + rest) {
            humTicks = 0;
            return true;
        }
        int i = t / step;
        if (t % step == 0 && i < song.length() && song.onset()[i]) {
            hum(level, song.notes()[i], i % 4 == 0);
        }
        return false;
    }

    // ---------------------------------------------------------------- 聲音（tools/audio/build_sounds.py 合成）
    @Override
    protected net.minecraft.sounds.SoundEvent getAmbientSound() {
        return isRitual() || isLeaving() || isEmerging() ? null : pryuan05.pysift.sound.ModSounds.SINGER_AMBIENT;
    }

    @Override
    public int getAmbientSoundInterval() {
        return 240;   // 偶爾哼一小段，不要太吵
    }

    @Override
    protected net.minecraft.sounds.SoundEvent getHurtSound(net.minecraft.world.damagesource.DamageSource source) {
        return pryuan05.pysift.sound.ModSounds.SINGER_HURT;
    }

    @Override
    protected net.minecraft.sounds.SoundEvent getDeathSound() {
        return pryuan05.pysift.sound.ModSounds.SINGER_DEATH;
    }

    /** 終曲時跟著唱片盒唱同一個音（pitch = 音符盒的音高倍率）。 */
    public void humNote(float pitch) {
        if (this.level() instanceof ServerLevel level) {
            hum(level, (int) Math.round(12 + 12 * Math.log(pitch) / Math.log(2)), true);
        }
    }

    /** 笛聲唱一個音（音符盒半音 0~24），可以疊一聲輕輕的鐘聲；頭上冒出對應顏色的音符。 */
    private void hum(ServerLevel level, int note, boolean chime) {
        float pitch = (float) Math.pow(2.0, (note - 12) / 12.0);
        level.playSound(null, this.getX(), this.getY() + 1.5, this.getZ(), pryuan05.pysift.sound.ModSounds.SINGER_VOICE, SoundSource.NEUTRAL, 0.9f, pitch);
        int action = ritualAction();
        if (action != ACTION_AWAIT && action != ACTION_FINALE && action != ACTION_CELEBRATE) {   // 這幾個動作自己會張嘴
            this.triggerAnim("face", "face_note");
        }
        if (chime) {
            level.playSound(null, this.getX(), this.getY() + 1.5, this.getZ(), SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.NEUTRAL, 0.35f, pitch);
        }
        // 音符粒子：count 0 時 xSpeed 是顏色（和音符盒一樣 note / 24）
        level.sendParticles(ParticleTypes.NOTE, this.getX(), this.getY() + this.getBbHeight() + 0.3, this.getZ(), 0, note / 24.0, 0.0, 0.0, 1.0);
    }

    /** 門開了：雙手往上拋、跳兩下轉一圈（celebrate 5 秒，只播一次），哼快樂頌第一句；播完自己開始退場（{@link #startLeaving}）。 */
    public void celebrate() {
        setAction(ACTION_CELEBRATE);
        this.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 2.0f, 1.4f);
        voice(pryuan05.pysift.sound.ModSounds.SINGER_CHEER, 1.8f, "cheer");
    }

    /** 腳下方塊的碎屑與挖掘聲；身體越出來，碎屑越往上噴。t = 已經爬了幾 tick。 */
    private void tickEmerge(ServerLevel level, int t) {
        BlockState ground = level.getBlockState(this.blockPosition().below());
        if (ground.isAir()) {
            ground = Blocks.DIRT.defaultBlockState();
        }
        double w = this.getBbWidth() * 0.5;
        if (t % 2 == 0 && t < EMERGE_TICKS - 6) {
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), this.getX(), this.getY() + 0.1, this.getZ(),
                    6 + t / 6, w, 0.05, w, 0.15 + t * 0.004);
        }
        if (t % 8 == 0 && t < EMERGE_TICKS - 6) {
            this.playSound(ground.getSoundType().getBreakSound(), 1.0f, 0.6f + this.random.nextFloat() * 0.2f);
        }
        if (t == 0) {
            this.playSound(SoundEvents.WARDEN_EMERGE, 0.6f, 1.6f);
        }
        if (t == EMERGE_TICKS - 8) {   // 抖掉泥土
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), this.getX(), this.getY() + this.getBbHeight() * 0.6, this.getZ(),
                    30, w, this.getBbHeight() * 0.3, w, 0.2);
            this.playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 1.5f, 1.0f);
            if (!isLeaving()) {
                voice(pryuan05.pysift.sound.ModSounds.SINGER_GREET, 1.5f, "greet");
            }
        }
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftAnimalEntity.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 30.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.SCALE, 1.456); // 原本 1.12 再放大 1.3 倍：頭頂約 3.5 格（耳朵尖約 3.9 格）
    }

    /** 儀式歌者：手持迴音碎片右鍵，召喚迴音傀儡擺放八音唱片盒（消耗 1 個迴音碎片，見 SiftPortalRitual）。 */
    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (isEmerging()) {
            return InteractionResult.PASS;
        }
        if (isRitual() && stack.is(Items.ECHO_SHARD)) {
            if (this.level() instanceof ServerLevel && SiftPortalRitual.startRitual(this, player)) {
                stack.consume(1, player);
            }
            return InteractionResult.SUCCESS;
        }
        return super.mobInteract(player, hand);
    }

    /** 迴音傀儡把頭頂的靈魂晶塊送給歌者：歌者轉向傀儡唱歌、回滿血，冒出晶光。 */
    public void receiveSoulCrystal(EchoGolemEntity golem) {
        if (!(this.level() instanceof ServerLevel level)) {
            return;
        }
        this.getLookControl().setLookAt(golem, 60.0f, 60.0f);
        this.triggerAnim("skill", "sing");
        this.heal(this.getMaxHealth());
        this.playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 1.5f, 0.8f);
        voice(pryuan05.pysift.sound.ModSounds.SINGER_THANKS, 1.4f, "thanks");
        level.sendParticles(ParticleTypes.GLOW, this.getX(), this.getY() + this.getBbHeight() * 0.8, this.getZ(),
                20, 0.5, 0.5, 0.5, 0.03);
    }

    @Override
    public void registerControllers(com.geckolib.animatable.manager.AnimatableManager.ControllerRegistrar controllers) {
        super.registerControllers(controllers);
        // 儀式動作：等迴音碎片時招手（循環）→ 召喚傀儡（summon）→ 等玩家放唱片時打拍子哼歌（await，循環）→ 終曲跟著唱片盒越指越高（finale）→ 開門慶祝（celebrate）。排在最後，蓋過 idle／walk。
        controllers.add(new com.geckolib.animation.AnimationController<SingerEntity>("ritual", 4, state -> {
            // 退場也由這個控制器播：它排在最後，若只回傳 STOP，前一個「播完停在最後一格」的動作（celebrate）
            // 會一直蓋住 held 控制器的 burrow，歌者就會原地站著直接消失
            if (isLeaving()) {
                return state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenPlayAndHold(anim("burrow")));
            }
            if (isEmerging()) {
                return com.geckolib.animation.object.PlayState.STOP;
            }
            return switch (ritualAction()) {
                case ACTION_BECKON -> state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenLoop(anim("beckon")));
                case ACTION_SUMMON -> state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenPlayAndHold(anim("summon")));
                case ACTION_FINALE -> state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenPlayAndHold(anim("finale")));
                case ACTION_CELEBRATE -> state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenPlayAndHold(anim("celebrate")));
                case ACTION_SWEEP -> state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenLoop(anim("sweep")));
                case ACTION_PLAY -> state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenPlayAndHold(anim("play")));
                case ACTION_AWAIT -> state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenLoop(anim("await")));
                default -> com.geckolib.animation.object.PlayState.STOP;
            };
        }));
        var face = new com.geckolib.animation.AnimationController<SingerEntity>("face", 2, state -> com.geckolib.animation.object.PlayState.STOP);
        for (String name : FACES) {
            face.triggerableAnim("face_" + name, com.geckolib.animation.RawAnimation.begin().thenPlay(anim("face_" + name)));
        }
        controllers.add(face);
    }

    /** 表情（嘴巴與耳朵）：每段人聲各有一個 face_* 動畫（tools/models/singer_faces.py），排在最後，蓋過身體動作的嘴和耳朵。 */
    private static final List<String> FACES = List.of("greet", "beckon", "call", "sweep", "summon", "gasp", "cheer", "giggle",
            "thanks", "unease", "starve", "hurt", "ambient", "note", "reborn");

    /** 說一句話：播放人聲，同時做出對應的表情。 */
    public void voice(net.minecraft.sounds.SoundEvent sound, float volume, String face) {
        this.playSound(sound, volume, 1.0f);
        this.triggerAnim("face", "face_" + face);
    }

    @Override
    public void playAmbientSound() {
        super.playAmbientSound();
        if (getAmbientSound() != null) {
            this.triggerAnim("face", "face_ambient");
        }
    }

    @Override
    protected void playHurtSound(DamageSource source) {
        super.playHurtSound(source);
        this.triggerAnim("face", "face_hurt");
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("sing", "summon", "choir");
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (isRitual() || this.entityTags().contains(DEN_CHOIR)) {   // 儀式歌者與回音窟的合唱團站在原地（仍會轉頭看玩家）
            this.getNavigation().stop();
            this.setDeltaMovement(0.0, this.getDeltaMovement().y, 0.0);
        }
        if (songCooldown > 0) {
            songCooldown--;
            return;
        }
        if (this.tickCount % 5 != 0) {
            return;
        }
        for (Player horn : level.getEntitiesOfClass(Player.class, this.getBoundingBox().inflate(RANGE),
                p -> p.isUsingItem() && p.getUseItem().is(Items.GOAT_HORN))) {
            sing(level, horn);
            return;
        }
    }

    private void sing(ServerLevel level, Player horn) {
        songCooldown = 200;
        this.getNavigation().stop();
        this.getLookControl().setLookAt(horn, 60.0f, 60.0f);
        this.triggerAnim("skill", "sing");
        this.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 2.0f, 1.2f);
        voice(pryuan05.pysift.sound.ModSounds.SINGER_CALL, 2.0f, "call");
        level.sendParticles(ParticleTypes.NOTE, this.getX(), this.getY() + this.getBbHeight() + 0.3, this.getZ(), 12, 0.8, 0.4, 0.8, 1.0);
        for (Player p : level.getEntitiesOfClass(Player.class, this.getBoundingBox().inflate(RANGE))) {
            p.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 600, 0), this);
        }
    }
}
