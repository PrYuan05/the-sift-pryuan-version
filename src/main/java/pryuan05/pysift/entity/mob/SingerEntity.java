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
import pryuan05.pysift.entity.PysiftAnimalEntity;

/**
 * 歌者（音律神獸，被動）。16 格內有玩家吹響山羊角時，面向該玩家唱出和聲（動畫 sing），
 * 給周圍 16 格內所有玩家 30 秒抗性提升 I；每隻歌者冷卻 10 秒。體型是原本的 1.3 倍。
 * 會和迴音傀儡一起出現；傀儡附近沒有玩家時，會把頭頂的靈魂晶塊送給歌者（{@link #receiveSoulCrystal}）。
 * 出生時從地底爬出（{@link #startEmerging}，動畫 emerge，3 秒）：耳朵先冒出、再露出頭，雙手撐地把身體拉上來，最後抖掉泥土；
 * 爬出期間不能移動、不會受傷，腳下方塊噴出碎屑並發出挖掘聲。
 */
public class SingerEntity extends PysiftAnimalEntity {
    private static final double RANGE = 16.0;
    /** 從地底爬出的時間（tick），要和 animation.singer.emerge 的長度一致。 */
    private static final int EMERGE_TICKS = 60;
    private static final EntityDataAccessor<Boolean> DATA_EMERGING = SynchedEntityData.defineId(SingerEntity.class, EntityDataSerializers.BOOLEAN);
    private int songCooldown;
    private int emergeTicks;

    public SingerEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_EMERGING, false);
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
        return isEmerging() ? "emerge" : null;
    }

    /** 爬出期間不跑 AI、不移動。 */
    @Override
    protected boolean isImmobile() {
        return isEmerging() || super.isImmobile();
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (isEmerging() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
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

    /** 手持迴音碎片、靈魂沙、靈魂土或山羊角右鍵：共鳴開啟篩靈界傳送門（見 SiftPortalRitual）。 */
    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (isEmerging()) {
            return InteractionResult.PASS;
        }
        if (stack.is(Items.ECHO_SHARD) || stack.is(Items.SOUL_SAND) || stack.is(Items.SOUL_SOIL) || stack.is(Items.GOAT_HORN)
                || stack.is(SoulCrystal.SOUL_CRYSTAL_BLOCK_ITEM)) {
            if (this.level() instanceof ServerLevel) {
                this.getLookControl().setLookAt(player, 60.0f, 60.0f);
                this.triggerAnim("skill", "sing");
                SiftPortalRitual.resonate(this, player);
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
    protected List<String> skillAnimations() {
        return List.of("sing");
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
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
