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
 * 篩靈界自然生成的歌者照常走動，不會觸發儀式。
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
            ACTION_AWAIT = 6;
    /** 招手多久沒人理（tick）就抱起小傀儡轉圈圈，之後每隔多久再玩一次。 */
    private static final int BORED_AFTER = 400, PLAY_TICKS = 120, PLAY_AGAIN = 1200;
    private int beckonTicks;
    /** 玩完小傀儡之後要回到的等待動作（招手或等唱片）。 */
    private int waitAction = ACTION_BECKON;
    /** 召喚（summon 2 秒）與終曲（sing 1.5 秒）播完後回到無動作。 */
    private int actionTicks;
    /** 開門後鑽回地底離開（動畫 burrow）。 */
    private static final EntityDataAccessor<Boolean> DATA_LEAVING = SynchedEntityData.defineId(SingerEntity.class, EntityDataSerializers.BOOLEAN);
    /** 要和 animation.singer.burrow 的長度一致。 */
    private static final int BURROW_TICKS = 50;
    private int burrowTicks;
    private int songCooldown;
    private int emergeTicks;

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
        this.entityData.set(DATA_ACTION, action);
        this.entityData.set(DATA_ACTION_START, (int) this.level().getGameTime());
        this.actionTicks = switch (action) {
            case ACTION_SUMMON -> 40;
            case ACTION_FINALE -> 30;
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
        this.playSound(SoundEvents.ALLAY_AMBIENT_WITH_ITEM, 1.5f, 0.9f);
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
        }
        if (this.actionTicks > 0 && !this.level().isClientSide() && --this.actionTicks == 0) {
            // 玩夠了回去繼續等；召喚完傀儡之後，儀式歌者改成等玩家放唱片（await）
            int done = ritualAction();
            setAction(done == ACTION_PLAY ? waitAction : done == ACTION_SUMMON && isRitual() ? ACTION_AWAIT : ACTION_NONE);
        }
        if (this.burrowTicks > 0 && this.level() instanceof ServerLevel level) {
            tickEmerge(level, Math.min(EMERGE_TICKS - 7, this.burrowTicks));   // 同樣的碎屑與挖掘聲
            if (--this.burrowTicks == 0) {
                level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 0.3, this.getZ(), 20, 0.6, 0.2, 0.6, 0.02);
                this.discard();
            }
        }
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
        level.sendParticles(ParticleTypes.GLOW, this.getX(), this.getY() + this.getBbHeight() * 0.8, this.getZ(),
                20, 0.5, 0.5, 0.5, 0.03);
    }

    @Override
    public void registerControllers(com.geckolib.animatable.manager.AnimatableManager.ControllerRegistrar controllers) {
        super.registerControllers(controllers);
        // 儀式動作：等迴音碎片時招手（循環）→ 召喚傀儡（summon）→ 等玩家放唱片時打拍子哼歌（await，循環）→ 開門時唱終曲（sing）。排在最後，蓋過 idle／walk。
        controllers.add(new com.geckolib.animation.AnimationController<SingerEntity>("ritual", 4, state -> {
            if (isEmerging() || isLeaving()) {
                return com.geckolib.animation.object.PlayState.STOP;
            }
            return switch (ritualAction()) {
                case ACTION_BECKON -> state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenLoop(anim("beckon")));
                case ACTION_SUMMON -> state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenPlayAndHold(anim("summon")));
                case ACTION_FINALE -> state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenPlayAndHold(anim("sing")));
                case ACTION_SWEEP -> state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenLoop(anim("sweep")));
                case ACTION_PLAY -> state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenPlayAndHold(anim("play")));
                case ACTION_AWAIT -> state.setAndContinue(com.geckolib.animation.RawAnimation.begin().thenLoop(anim("await")));
                default -> com.geckolib.animation.object.PlayState.STOP;
            };
        }));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("sing", "summon");
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (isRitual()) {   // 儀式歌者站在原地（仍會轉頭看玩家）
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
        this.playSound(SoundEvents.NOTE_BLOCK_CHIME.value(), 2.0f, 1.0f);
        level.sendParticles(ParticleTypes.NOTE, this.getX(), this.getY() + this.getBbHeight() + 0.3, this.getZ(), 12, 0.8, 0.4, 0.8, 1.0);
        for (Player p : level.getEntitiesOfClass(Player.class, this.getBoundingBox().inflate(RANGE))) {
            p.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 600, 0), this);
        }
    }
}
