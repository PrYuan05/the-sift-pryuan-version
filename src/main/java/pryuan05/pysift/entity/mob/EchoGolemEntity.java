package pryuan05.pysift.entity.mob;

import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.tags.DamageTypeTags;
import com.geckolib.animatable.manager.AnimatableManager;
import com.geckolib.animation.AnimationController;
import com.geckolib.animation.RawAnimation;
import com.geckolib.animation.object.PlayState;
import pryuan05.pysift.block.SiftPortalRitual;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.UUIDUtil;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.level.ServerLevelAccessor;
import pryuan05.pysift.block.SoulCrystal;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.entity.PysiftGeoEntity;
import pryuan05.pysift.entity.ai.EchoPulseGoal;
import pryuan05.pysift.entity.ai.GroundSlamGoal;

/**
 * 迴音傀儡（中立的靈魂採集者）。
 * <ul>
 *   <li>中立：不主動攻擊，被打才反擊（揮拳 attack；目標 2.5 格內時砸地 slam，只傷害自己的目標；目標在 3.5~12 格且有視線時發射回音脈衝 pulse，造成音波傷害並緩速）。</li>
 *   <li>採集：每隔一段時間找 10 格內的靈魂沙／靈魂土走過去採集（動畫 pulse、靈魂粒子），不會破壞方塊；最多存 16 份靈魂。</li>
 *   <li>靈魂晶塊：頭頂那顆淡藍方塊是靈魂晶塊。附近 16 格沒有玩家時，傀儡會把它帶去送給 16 格內的歌者；
 *       玩家空手右鍵傀儡可以直接取下（得到一個靈魂晶塊）。取下後約 3 分鐘重新凝結。自然生成時一半機率帶 1 隻歌者。</li>
 *   <li>蒐集晶塊：每 2 秒找 16 格內的靈魂晶塊方塊（紫晶深板岩區會自然生成），走過去彎腰吸收（動畫 collect），
 *       頭上沒有晶塊時直接長回來，否則存起來（最多 3 個），送出或被取下後 5 秒就從存量補上。</li>
 *   <li>契約：玩家手持迴音碎片右鍵簽約（消耗 1 個）。簽約後主人在 24 格內時，每 30 秒把採集到的靈魂產物吐向主人：
 *       每 2 份靈魂換 1 個靈魂土或靈魂沙，另有 5% 機率附贈 1 個迴音碎片；主人離開超過 16 格時會往主人走。</li>
 * </ul>
 * <p>儀式工人（{@link #startRitualWork}）：由遠古城市的儀式歌者召喚。從地底爬出（emerge），抱著唱片盒（carry）走到位置，
 * 彎腰放下（place），全部放完後沉回地底（sink）並消失。工人模式下不受傷、不攻擊、不做其他事。
 */
public class EchoGolemEntity extends PysiftGeoEntity {
    private static final int MAX_SOULS = 16;
    private static final int DELIVER_INTERVAL = 600;
    private UUID contractOwner;
    private int souls;
    private int deliverTimer = DELIVER_INTERVAL;
    /** 頭頂有沒有靈魂晶塊（同步到客戶端，沒有時模型隱藏 crystal 骨骼）。 */
    private static final EntityDataAccessor<Boolean> DATA_CRYSTAL = SynchedEntityData.defineId(EchoGolemEntity.class, EntityDataSerializers.BOOLEAN);
    private static final int CRYSTAL_REGROW = 3600;
    private static final double GIFT_RANGE = 16.0;
    private int crystalTimer;
    private static final int MAX_STORED = 3;
    private static final int REFILL_TICKS = 100;
    /** 吸收來、還沒長到頭上的靈魂晶塊。 */
    private int storedCrystals;

    // ---------------------------------------------------------------- ritual worker
    private static final EntityDataAccessor<Integer> DATA_RITUAL_PHASE = SynchedEntityData.defineId(EchoGolemEntity.class, EntityDataSerializers.INT);
    private static final int PHASE_NONE = 0, PHASE_EMERGE = 1, PHASE_WORK = 2, PHASE_SINK = 3, PHASE_TOY = 4;
    /** 要和 animation.echo_golem.emerge / sink 的長度一致。 */
    private static final int EMERGE_TICKS = 50, SINK_TICKS = 40;
    private int phaseTicks;
    private List<BlockPos> ritualJobs = new ArrayList<>();
    private SiftPortalRitual.Plan ritualPlan;

    public EchoGolemEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PathfinderMob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 40.0)
                .add(Attributes.MOVEMENT_SPEED, 0.22)
                .add(Attributes.ATTACK_DAMAGE, 6.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.6)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(0, new PlaceJukeboxGoal());
        this.goalSelector.addGoal(1, new GroundSlamGoal(this, "slam", 12, 20, 60, 2.5, 3.0, 8.0f, 0.5, e -> false));
        this.goalSelector.addGoal(1, new EchoPulseGoal(this, "pulse", 12, 22, 100, 3.5, 12.0, 5.0f, 60, 1));
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.0, true));
        this.goalSelector.addGoal(3, new FollowContractOwnerGoal());
        this.goalSelector.addGoal(4, new CollectCrystalGoal());
        this.goalSelector.addGoal(5, new GiveCrystalToSingerGoal());
        this.goalSelector.addGoal(6, new HarvestSoulGoal());
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 6.0f));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));

        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("attack", "slam", "pulse", "collect", "place");
    }

    @Override
    protected String meleeAnimation() {
        return "attack";
    }

    @Override
    protected boolean hasDeathAnimation() {
        return true;
    }

    // ---------------------------------------------------------------- soul crystal
    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_CRYSTAL, true);
        builder.define(DATA_RITUAL_PHASE, PHASE_NONE);
    }

    // ---------------------------------------------------------------- ritual worker
    public boolean isRitualWorker() {
        return this.entityData.get(DATA_RITUAL_PHASE) != PHASE_NONE;
    }

    /** 儀式工人與小傀儡不產生震動（不會引來伏守者）。 */
    @Override
    public boolean dampensVibrations() {
        return isRitualWorker() || super.dampensVibrations();
    }

    @Override
    public boolean isSteppingCarefully() {
        return isRitualWorker() || super.isSteppingCarefully();
    }

    private int ritualPhase() {
        return this.entityData.get(DATA_RITUAL_PHASE);
    }

    private void setRitualPhase(int phase, int ticks) {
        this.entityData.set(DATA_RITUAL_PHASE, phase);
        this.phaseTicks = ticks;
    }

    /** 由 SiftPortalRitual 呼叫：從地底爬出，然後把唱片盒放到 jobs 的每個位置。 */
    public void startRitualWork(List<BlockPos> jobs, SiftPortalRitual.Plan plan) {
        this.ritualJobs = new ArrayList<>(jobs);
        this.ritualPlan = plan;
        this.setPersistenceRequired();
        this.setDropChance(EquipmentSlot.MAINHAND, 0.0f);
        this.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(Items.JUKEBOX));
        setRitualPhase(PHASE_EMERGE, EMERGE_TICKS);
    }

    /** 歌者等太久時抱在懷裡的小傀儡：縮小、不受傷、不做事；被放下就沉回地底。 */
    public void becomeToy() {
        var scale = this.getAttribute(Attributes.SCALE);
        if (scale != null) {
            scale.setBaseValue(0.4);
        }
        this.setPersistenceRequired();
        setRitualPhase(PHASE_TOY, 0);
    }

    /** 沉回地底消失（儀式工人放完、或小傀儡被放下）。 */
    public void sinkAway() {
        if (ritualPhase() != PHASE_SINK) {
            this.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
            setRitualPhase(PHASE_SINK, SINK_TICKS);
            this.playSound(SoundEvents.WARDEN_DIG, 0.6f, 1.6f);
        }
    }

    /** 抱著唱片盒時，手臂改播 carry（用戶端依同步的手持物品判斷）。 */
    public boolean isCarryingJukebox() {
        return ritualPhase() == PHASE_WORK && this.getMainHandItem().is(Items.JUKEBOX);
    }

    @Override
    protected String heldMovementAnimation() {
        int phase = ritualPhase();
        return phase == PHASE_EMERGE ? "emerge" : phase == PHASE_SINK ? "sink" : null;
    }

    @Override
    protected boolean isImmobile() {
        int phase = ritualPhase();
        return phase == PHASE_EMERGE || phase == PHASE_SINK || super.isImmobile();
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (isRitualWorker() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    public void tick() {
        super.tick();
        if (!(this.level() instanceof ServerLevel level) || !isRitualWorker()) {
            return;
        }
        int phase = ritualPhase();
        if (phase == PHASE_TOY && !this.isPassenger() && this.tickCount > 5) {
            sinkAway();
            return;
        }
        if (phase == PHASE_EMERGE || phase == PHASE_SINK) {
            BlockState ground = level.getBlockState(this.blockPosition().below());
            if (ground.isAir()) {
                ground = Blocks.DEEPSLATE.defaultBlockState();
            }
            if (this.tickCount % 2 == 0) {
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), this.getX(), this.getY() + 0.1, this.getZ(),
                        8, 0.6, 0.05, 0.6, 0.15);
            }
            if (this.tickCount % 8 == 0) {
                this.playSound(ground.getSoundType().getBreakSound(), 1.0f, 0.5f);
            }
            if (--phaseTicks <= 0) {
                if (phase == PHASE_EMERGE) {
                    setRitualPhase(PHASE_WORK, 0);
                    this.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 1.2f, 0.7f);
                } else {
                    level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 0.3, this.getZ(), 20, 0.6, 0.2, 0.6, 0.02);
                    this.discard();
                }
            }
        }
    }

    public boolean hasCrystal() {
        return this.entityData.get(DATA_CRYSTAL);
    }

    private void setCrystal(boolean crystal) {
        this.entityData.set(DATA_CRYSTAL, crystal);
        crystalTimer = 0;
    }

    /** 自然生成時一半機率帶 1 隻歌者在身邊。 */
    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason, SpawnGroupData data) {
        SpawnGroupData result = super.finalizeSpawn(level, difficulty, reason, data);
        if (reason == EntitySpawnReason.NATURAL || reason == EntitySpawnReason.CHUNK_GENERATION) {
            int count = this.random.nextFloat() < 0.5f ? 1 : 0;   // 一半的傀儡帶一隻歌者（歌者不要太多）
            for (int i = 0; i < count; i++) {
                SingerEntity singer = ModEntities.SINGER.create(level.getLevel(), reason);
                if (singer == null) {
                    continue;
                }
                double angle = this.random.nextDouble() * Math.PI * 2;
                singer.snapTo(new Vec3(this.getX() + Math.cos(angle) * 3, this.getY(), this.getZ() + Math.sin(angle) * 3),
                        this.random.nextFloat() * 360, 0);
                singer.finalizeSpawn(level, difficulty, reason, null);
                level.addFreshEntity(singer);
            }
        }
        return result;
    }

    // ---------------------------------------------------------------- contract
    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (stack.isEmpty() && hand == InteractionHand.MAIN_HAND && hasCrystal()) {   // 取下頭頂的靈魂晶塊
            if (this.level() instanceof ServerLevel level) {
                setCrystal(false);
                if (!player.getInventory().add(new ItemStack(SoulCrystal.SOUL_CRYSTAL_BLOCK_ITEM))) {
                    spit(level, player, new ItemStack(SoulCrystal.SOUL_CRYSTAL_BLOCK_ITEM));
                }
                this.triggerAnim("skill", "pulse");
                this.playSound(SoundEvents.AMETHYST_BLOCK_BREAK, 1.0f, 1.0f);
                level.sendParticles(ParticleTypes.GLOW, this.getX(), this.getY() + this.getBbHeight(), this.getZ(), 15, 0.4, 0.3, 0.4, 0.02);
            }
            return InteractionResult.SUCCESS;
        }
        if (stack.is(Items.ECHO_SHARD) && !player.getUUID().equals(contractOwner)) {
            stack.consume(1, player);
            if (this.level() instanceof ServerLevel level) {
                contractOwner = player.getUUID();
                this.setTarget(null);
                this.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 1.0f, 0.8f);
                level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 1.8, this.getZ(), 20, 0.5, 0.6, 0.5, 0.02);
            }
            return InteractionResult.SUCCESS;
        }
        return super.mobInteract(player, hand);
    }

    private Player contractPlayer() {
        return contractOwner == null ? null : this.level().getPlayerByUUID(contractOwner);
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (!hasCrystal() && ++crystalTimer >= (storedCrystals > 0 ? REFILL_TICKS : CRYSTAL_REGROW)) {   // 從存量補上，或重新凝結
            if (storedCrystals > 0) {
                storedCrystals--;
            }
            setCrystal(true);
            this.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 1.0f, 1.2f);
            level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + this.getBbHeight(), this.getZ(), 12, 0.4, 0.3, 0.4, 0.02);
        }
        if (--deliverTimer > 0) {
            return;
        }
        deliverTimer = DELIVER_INTERVAL;
        Player owner = contractPlayer();
        if (owner == null || souls < 2 || this.distanceTo(owner) > 24) {
            return;
        }
        int count = souls / 2;
        souls -= count * 2;
        spit(level, owner, new ItemStack(this.random.nextBoolean() ? Items.SOUL_SOIL : Items.SOUL_SAND, count));
        if (this.random.nextFloat() < 0.05f) {
            spit(level, owner, new ItemStack(Items.ECHO_SHARD));
        }
        this.triggerAnim("skill", "pulse");
        this.playSound(SoundEvents.ALLAY_THROW, 1.0f, 0.7f);
    }

    private void spit(ServerLevel level, Player owner, ItemStack stack) {
        Vec3 from = this.getEyePosition();
        ItemEntity item = new ItemEntity(level, from.x, from.y, from.z, stack);
        Vec3 v = owner.getEyePosition().subtract(from).normalize().scale(0.35);
        item.setDeltaMovement(v.x, v.y + 0.2, v.z);
        item.setDefaultPickUpDelay();
        level.addFreshEntity(item);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (ritualPhase() == PHASE_TOY) {
            output.putBoolean("RitualToy", true);
        }
        if (isRitualWorker() && ritualPlan != null) {
            output.putInt("RitualPhase", ritualPhase());
            output.putInt("RitualPhaseTicks", phaseTicks);
            output.store("RitualJobs", BlockPos.CODEC.listOf(), ritualJobs);
            output.store("RitualCentre", BlockPos.CODEC, ritualPlan.portalCentre());
            output.putBoolean("RitualAxisX", ritualPlan.axisX());
            output.putBoolean("RitualFrame", ritualPlan.frame());
            output.store("RitualGroup", BlockPos.CODEC.listOf(), ritualPlan.group());
        }
        if (contractOwner != null) {
            output.store("ContractOwner", UUIDUtil.CODEC, contractOwner);
        }
        output.putInt("Souls", souls);
        output.putBoolean("HasCrystal", hasCrystal());
        output.putInt("CrystalTimer", crystalTimer);
        output.putInt("StoredCrystals", storedCrystals);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        contractOwner = input.read("ContractOwner", UUIDUtil.CODEC).orElse(null);
        souls = input.getIntOr("Souls", 0);
        this.entityData.set(DATA_CRYSTAL, input.getBooleanOr("HasCrystal", true));
        crystalTimer = input.getIntOr("CrystalTimer", 0);
        storedCrystals = input.getIntOr("StoredCrystals", 0);
        if (input.getBooleanOr("RitualToy", false)) {
            setRitualPhase(PHASE_TOY, 0);
        }
        int phase = input.getIntOr("RitualPhase", PHASE_NONE);
        BlockPos centre = input.read("RitualCentre", BlockPos.CODEC).orElse(null);
        if (phase != PHASE_NONE && centre != null) {
            ritualJobs = new ArrayList<>(input.read("RitualJobs", BlockPos.CODEC.listOf()).orElse(List.of()));
            ritualPlan = new SiftPortalRitual.Plan(centre, input.getBooleanOr("RitualAxisX", true), input.getBooleanOr("RitualFrame", false),
                    input.read("RitualGroup", BlockPos.CODEC.listOf()).orElse(List.of()));
            setRitualPhase(phase, input.getIntOr("RitualPhaseTicks", 0));
        }
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        super.registerControllers(controllers);
        // 抱著唱片盒走路：只蓋過手臂（排在 movement 之後）
        controllers.add(new AnimationController<EchoGolemEntity>("arms", 4, state -> isCarryingJukebox()
                ? state.setAndContinue(RawAnimation.begin().thenLoop(anim("carry"))) : PlayState.STOP));
    }

    /** 走到下一個位置 → 彎腰（place）→ 第 12 tick 放下唱片盒 → 下一個；全部放完就沉回地底。 */
    private class PlaceJukeboxGoal extends Goal {
        private static final int PLACE_AT = 12, PLACE_END = 26, STUCK_LIMIT = 200;
        private BlockPos target;
        private int placing = -1;
        private int walking;

        PlaceJukeboxGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            return ritualPhase() == PHASE_WORK && ritualPlan != null;
        }

        @Override
        public boolean canContinueToUse() {
            return ritualPhase() == PHASE_WORK;
        }

        @Override
        public void start() {
            next();
        }

        private void next() {
            placing = -1;
            walking = 0;
            target = ritualJobs.isEmpty() ? null : ritualJobs.getFirst();
            if (target == null) {
                setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
                getNavigation().stop();
                setRitualPhase(PHASE_SINK, SINK_TICKS);
                playSound(SoundEvents.WARDEN_DIG, 0.8f, 1.3f);
                return;
            }
            setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(Items.JUKEBOX));
            getNavigation().moveTo(target.getX() + 0.5, target.getY(), target.getZ() + 0.5, 1.0);
        }

        @Override
        public void tick() {
            if (target == null || !(level() instanceof ServerLevel level)) {
                return;
            }
            getLookControl().setLookAt(Vec3.atCenterOf(target));
            if (placing >= 0) {
                placing++;
                if (placing == PLACE_AT) {
                    setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
                    if (!level.getBlockState(target).is(pryuan05.pysift.block.RitualBlocks.RESONANT_JUKEBOX)) {
                        SiftPortalRitual.placeJukebox(level, target, ritualPlan);
                    }
                    ritualJobs.removeFirst();
                }
                if (placing >= PLACE_END) {
                    next();
                }
                return;
            }
            double dist = distanceToSqr(Vec3.atBottomCenterOf(target));
            if (dist < 2.6 * 2.6) {
                getNavigation().stop();
                if (!SiftPortalRitual.previousSeatsReady(level, ritualPlan, target)) {
                    walking = 0;   // 左邊的還沒放好：抱著唱片盒等
                    return;
                }
                placing = 0;
                triggerAnim("skill", "place");
                playSound(SoundEvents.WARDEN_STEP, 0.8f, 1.2f);
                return;
            }
            if (++walking > STUCK_LIMIT) {   // 走不過去：直接瞬移到旁邊
                Vec3 beside = Vec3.atBottomCenterOf(target).add(Vec3.atLowerCornerOf(Direction.Plane.HORIZONTAL.getRandomDirection(getRandom()).getUnitVec3i()).scale(1.5));
                level.sendParticles(ParticleTypes.SCULK_SOUL, getX(), getY() + 1, getZ(), 12, 0.4, 0.6, 0.4, 0.02);
                teleportTo(beside.x, target.getY(), beside.z);
                walking = 0;
            } else if (getNavigation().isDone()) {
                getNavigation().moveTo(target.getX() + 0.5, target.getY(), target.getZ() + 0.5, 1.0);
            }
        }
    }

    private static boolean isSoulBlock(BlockState state) {
        return state.is(Blocks.SOUL_SAND) || state.is(Blocks.SOUL_SOIL);
    }

    // ---------------------------------------------------------------- goals
    /** 每隔 10~20 秒找附近的靈魂方塊，走過去採集一份靈魂。 */
    private class HarvestSoulGoal extends Goal {
        private BlockPos targetPos;
        private int nextSearch = 100;
        private int harvestTicks;

        HarvestSoulGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (souls >= MAX_SOULS || getTarget() != null || --nextSearch > 0) {
                return false;
            }
            nextSearch = 200 + random.nextInt(200);
            BlockPos c = blockPosition();
            targetPos = BlockPos.betweenClosedStream(c.offset(-10, -4, -10), c.offset(10, 4, 10))
                    .filter(p -> isSoulBlock(level().getBlockState(p)) && level().getBlockState(p.above()).isAir())
                    .min(java.util.Comparator.comparingDouble(p -> p.distSqr(c)))
                    .map(BlockPos::immutable).orElse(null);
            return targetPos != null;
        }

        @Override
        public boolean canContinueToUse() {
            return targetPos != null && harvestTicks < 30 && getTarget() == null && isSoulBlock(level().getBlockState(targetPos));
        }

        @Override
        public void start() {
            harvestTicks = 0;
            getNavigation().moveTo(targetPos.getX() + 0.5, targetPos.getY() + 1, targetPos.getZ() + 0.5, 0.9);
        }

        @Override
        public void tick() {
            getLookControl().setLookAt(Vec3.atCenterOf(targetPos));
            if (distanceToSqr(Vec3.atCenterOf(targetPos)) > 6.25) {
                if (getNavigation().isDone()) {
                    getNavigation().moveTo(targetPos.getX() + 0.5, targetPos.getY() + 1, targetPos.getZ() + 0.5, 0.9);
                }
                return;
            }
            getNavigation().stop();
            if (harvestTicks++ == 0) {
                triggerAnim("skill", "pulse");
                playSound(SoundEvents.SOUL_ESCAPE.value(), 1.0f, 1.0f);
            }
            if (level() instanceof ServerLevel level) {
                level.sendParticles(ParticleTypes.SOUL, targetPos.getX() + 0.5, targetPos.getY() + 1.1, targetPos.getZ() + 0.5, 2, 0.3, 0.1, 0.3, 0.03);
            }
            if (harvestTicks == 30) {
                souls = Math.min(MAX_SOULS, souls + 1);
            }
        }

        @Override
        public void stop() {
            targetPos = null;
        }
    }

    /** 每 2 秒找 16 格內露出的靈魂晶塊方塊，走過去彎腰吸收（動畫 collect，第 COLLECT_TICK tick 吸收）。 */
    private class CollectCrystalGoal extends Goal {
        private static final int COLLECT_TICK = 20;
        private static final int SEARCH_RADIUS = 16;
        /** 在這個距離內就能把晶塊的靈魂吸過來（不必走到正上方，台地上下也行）。 */
        private static final double REACH = 4.5;
        private BlockPos targetPos;
        private int nextSearch;
        private int collectTicks;
        private int walkTicks;

        CollectCrystalGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        private boolean wantsMore() {
            return !hasCrystal() || storedCrystals < MAX_STORED;
        }

        private boolean isCrystal(BlockPos pos) {
            return level().getBlockState(pos).is(SoulCrystal.SOUL_CRYSTAL_BLOCK);
        }

        @Override
        public boolean canUse() {
            if (getTarget() != null || !wantsMore() || --nextSearch > 0) {
                return false;
            }
            nextSearch = 40;
            BlockPos c = blockPosition();
            targetPos = BlockPos.betweenClosedStream(c.offset(-SEARCH_RADIUS, -6, -SEARCH_RADIUS), c.offset(SEARCH_RADIUS, 6, SEARCH_RADIUS))
                    .filter(p -> isCrystal(p) && (level().getBlockState(p.above()).isAir() || level().getBlockState(p.north()).isAir()
                            || level().getBlockState(p.south()).isAir() || level().getBlockState(p.east()).isAir()
                            || level().getBlockState(p.west()).isAir()))
                    .map(BlockPos::immutable)
                    .sorted(java.util.Comparator.comparingDouble(p -> p.distSqr(c)))
                    .limit(6)
                    .filter(this::reachable)              // 只挑走得到（或已經夠近）的晶塊，不會卡在台地邊
                    .findFirst().orElse(null);
            return targetPos != null;
        }

        private boolean reachable(BlockPos pos) {
            if (distanceToSqr(Vec3.atCenterOf(pos)) <= REACH * REACH) {
                return true;
            }
            net.minecraft.world.level.pathfinder.Path path = getNavigation().createPath(pos, 3);
            return path != null && path.canReach();
        }

        @Override
        public boolean canContinueToUse() {
            return targetPos != null && getTarget() == null && walkTicks < 300
                    && (collectTicks > COLLECT_TICK ? collectTicks < 30 : isCrystal(targetPos));
        }

        @Override
        public void start() {
            collectTicks = 0;
            walkTicks = 0;
            getNavigation().moveTo(targetPos.getX() + 0.5, targetPos.getY() + 1, targetPos.getZ() + 0.5, 1.0);
        }

        @Override
        public void tick() {
            getLookControl().setLookAt(Vec3.atCenterOf(targetPos));
            if (collectTicks == 0 && distanceToSqr(Vec3.atCenterOf(targetPos)) > REACH * REACH) {
                walkTicks++;
                if (getNavigation().isDone() || walkTicks % 40 == 0) {
                    getNavigation().moveTo(targetPos.getX() + 0.5, targetPos.getY() + 1, targetPos.getZ() + 0.5, 1.0);
                }
                return;
            }
            getNavigation().stop();
            if (collectTicks++ == 0) {
                triggerAnim("skill", "collect");
                playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 1.0f, 0.7f);
            }
            if (level() instanceof ServerLevel level) {
                if (collectTicks < COLLECT_TICK) {     // 晶塊的碎光被吸向傀儡頭頂
                    level.sendParticles(ParticleTypes.GLOW, targetPos.getX() + 0.5, targetPos.getY() + 0.8, targetPos.getZ() + 0.5,
                            2, 0.3, 0.3, 0.3, 0.02);
                } else if (collectTicks == COLLECT_TICK && isCrystal(targetPos)) {
                    level.destroyBlock(targetPos, false, EchoGolemEntity.this);
                    level.sendParticles(ParticleTypes.SCULK_SOUL, getX(), getY() + getBbHeight(), getZ(), 15, 0.4, 0.3, 0.4, 0.03);
                    playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 1.5f, 1.0f);
                    if (!hasCrystal()) {
                        setCrystal(true);
                    } else {
                        storedCrystals = Math.min(MAX_STORED, storedCrystals + 1);
                    }
                }
            }
        }

        @Override
        public void stop() {
            targetPos = null;
            getNavigation().stop();
        }
    }

    /** 附近 16 格沒有玩家、而有歌者時，帶著頭頂的靈魂晶塊走過去送給歌者。 */
    private class GiveCrystalToSingerGoal extends Goal {
        private SingerEntity singer;
        private int nextCheck;

        GiveCrystalToSingerGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (!hasCrystal() || getTarget() != null || --nextCheck > 0) {
                return false;
            }
            nextCheck = 100;
            if (level().getNearestPlayer(EchoGolemEntity.this, GIFT_RANGE) != null) {
                return false;
            }
            singer = level().getEntitiesOfClass(SingerEntity.class, getBoundingBox().inflate(GIFT_RANGE), SingerEntity::isAlive)
                    .stream().min(java.util.Comparator.comparingDouble(EchoGolemEntity.this::distanceToSqr)).orElse(null);
            return singer != null;
        }

        @Override
        public boolean canContinueToUse() {
            return singer != null && singer.isAlive() && hasCrystal() && getTarget() == null;
        }

        @Override
        public void tick() {
            getLookControl().setLookAt(singer);
            if (distanceToSqr(singer) > 3.0 * 3.0) {
                if (getNavigation().isDone() || tickCount % 20 == 0) {
                    getNavigation().moveTo(singer, 0.9);
                }
                return;
            }
            getNavigation().stop();
            setCrystal(false);
            triggerAnim("skill", "pulse");
            singer.receiveSoulCrystal(EchoGolemEntity.this);
        }

        @Override
        public void stop() {
            singer = null;
        }
    }

    /** 簽約後主人離開 16 格以上時往主人走，靠近到 6 格內停下。 */
    private class FollowContractOwnerGoal extends Goal {
        private Player owner;

        FollowContractOwnerGoal() {
            this.setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            owner = contractPlayer();
            return owner != null && getTarget() == null && !owner.isSpectator() && distanceToSqr(owner) > 16 * 16;
        }

        @Override
        public boolean canContinueToUse() {
            return owner != null && owner.isAlive() && getTarget() == null && distanceToSqr(owner) > 6 * 6;
        }

        @Override
        public void tick() {
            if (getNavigation().isDone() || tickCount % 20 == 0) {
                getNavigation().moveTo(owner, 1.0);
            }
        }

        @Override
        public void stop() {
            owner = null;
            getNavigation().stop();
        }
    }
}
