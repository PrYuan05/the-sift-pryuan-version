package pryuan05.pysift.entity.mob;

import java.util.List;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.ConversionParams;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.entity.PysiftAnimalEntity;
import pryuan05.pysift.fluid.SpiritInteractions;
import pryuan05.pysift.progression.StoryTriggers;

/**
 * 哀悼者（MODDING_ROADMAP §4.7）：屍化的歌者。困在沒有靈魂的主世界，毛髮脫落、哭著倒唱八音（{@link SingerSongs#MOURNING}）。
 * <ul>
 *   <li>中立：不攻擊，被打會逃。玩家走到 WEEP_RANGE 格內時，它停下來哭著唱一遍，DARK_RANGE 格內的玩家陷入黑暗。</li>
 *   <li>治癒：泡在靈液裡 CURE_TICKS，長回毛髮、變回歌者（{@link StoryTriggers#mournerCured}）。</li>
 *   <li>來源：主世界深暗之域稀有生成（{@code data/pysift/...} 的 biome modification，見 ModEntities），
 *       或歌者在主世界待太久（{@link SingerEntity} 的屍化計時）。</li>
 * </ul>
 * 模型與動畫沿用歌者（tools/models/build_mourner.py：動畫放慢 1.5 倍、頭垂低）。
 */
public class MournerEntity extends PysiftAnimalEntity {
    private static final double WEEP_RANGE = 6.0, DARK_RANGE = 12.0;
    private static final int WEEP_STEP = 7, WEEP_COOLDOWN = 600, CURE_TICKS = 200;
    private int weepTicks, weepCooldown, humTicks;
    private int cureTicks;

    public MournerEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftAnimalEntity.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 30.0)
                .add(Attributes.MOVEMENT_SPEED, 0.17)
                .add(Attributes.SCALE, 1.456);   // 和歌者一樣大
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("sing");
    }

    @Override
    public void tick() {
        super.tick();
        if (!(this.level() instanceof ServerLevel level) || !this.isAlive()) {
            return;
        }
        tickCure(level);
        if (weepCooldown > 0) {
            weepCooldown--;
        }
        if (weepTicks > 0) {
            tickWeep(level);
        } else if (weepCooldown == 0 && this.tickCount % 20 == 0) {
            Player near = level.getNearestPlayer(this, WEEP_RANGE);
            if (near != null && !near.isSpectator()) {
                startWeeping(level, near);
            }
        }
        if (this.tickCount % 40 == 0 && this.random.nextInt(3) == 0) {   // 一直在掉毛、漏出靈魂
            level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + this.getBbHeight() * 0.5, this.getZ(), 1, 0.4, 0.5, 0.4, 0.01);
        }
    }

    private void startWeeping(ServerLevel level, Player near) {
        weepTicks = SingerSongs.MOURNING.length() * WEEP_STEP;
        humTicks = 0;
        this.getNavigation().stop();
        this.getLookControl().setLookAt(near, 30.0f, 30.0f);
        this.triggerAnim("skill", "sing");
        voice(pryuan05.pysift.sound.ModSounds.MOURNER_WAIL, 1.4f, "wail");
        for (Player p : level.getEntitiesOfClass(Player.class, this.getBoundingBox().inflate(DARK_RANGE), p -> !p.isSpectator())) {
            p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 160, 0), this);
        }
    }

    private void tickWeep(ServerLevel level) {
        this.getNavigation().stop();
        int t = humTicks++;
        int i = t / WEEP_STEP;
        SingerSongs.Song song = SingerSongs.MOURNING;
        if (t % WEEP_STEP == 0 && i < song.length() && song.onset()[i]) {
            float pitch = (float) Math.pow(2.0, (song.notes()[i] - 12) / 12.0) * 0.94f;   // 稍微走音
            level.playSound(null, this.getX(), this.getY() + 1.5, this.getZ(), pryuan05.pysift.sound.ModSounds.MOURNER_VOICE, SoundSource.NEUTRAL, 0.8f, pitch);
            if (i > 0) {   // 第一個音和哀號同時，不要打斷哀號的表情
                this.triggerAnim("face", "face_note");
            }
            level.playSound(null, this.getX(), this.getY() + 1.5, this.getZ(), SoundEvents.SOUL_ESCAPE.value(), SoundSource.NEUTRAL, 0.9f, 0.7f);
            level.sendParticles(ParticleTypes.FALLING_WATER, this.getX(), this.getY() + this.getBbHeight() * 0.85, this.getZ(), 4, 0.25, 0.1, 0.25, 0);
            level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + this.getBbHeight() + 0.2, this.getZ(), 2, 0.3, 0.2, 0.3, 0.01);
        }
        if (--weepTicks == 0) {
            weepCooldown = WEEP_COOLDOWN;
        }
    }

    /** 泡在靈液裡：毛慢慢長回來，CURE_TICKS 後變回歌者。離開靈液就從頭算。 */
    private void tickCure(ServerLevel level) {
        boolean soaking = SpiritInteractions.isSpirit(level.getFluidState(this.blockPosition()))
                || SpiritInteractions.isSpirit(level.getFluidState(this.blockPosition().above()));
        if (!soaking) {
            cureTicks = 0;
            return;
        }
        cureTicks++;
        if (cureTicks % 10 == 0) {
            level.sendParticles(ParticleTypes.GLOW, this.getX(), this.getY() + this.getBbHeight() * 0.6, this.getZ(), 4 + cureTicks / 20, 0.5, 0.6, 0.5, 0.02);
        }
        if (cureTicks % 40 == 0) {
            this.playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 1.2f, 0.6f + cureTicks / 200.0f);
        }
        if (cureTicks % 60 == 20) {   // 被靈液安慰：鬆一口氣，聲音一次比一次亮
            this.playSound(pryuan05.pysift.sound.ModSounds.MOURNER_SOOTHE, 1.2f, 0.9f + cureTicks / 1000.0f);
            this.triggerAnim("face", "face_soothe");
        }
        if (cureTicks >= CURE_TICKS) {
            cure(level);
        }
    }

    /** 搖籃曲香爐的歌（LullabyCenserBlock）：累積 WARM_TICKS 也會變回歌者，不必泡靈液。 */
    public static final int WARM_TICKS = 1200;
    private int warmTicks;

    public void warmBy(ServerLevel level, int ticks) {
        if (!this.isAlive()) {
            return;
        }
        warmTicks += ticks;
        hush(ticks * 2);
        if (this.random.nextInt(3) == 0) {   // 香爐的歌：偶爾鬆一口氣
            this.playSound(pryuan05.pysift.sound.ModSounds.MOURNER_SOOTHE, 1.0f, 0.9f + warmTicks / 4000.0f);
            this.triggerAnim("face", "face_soothe");
        }
        level.sendParticles(ParticleTypes.GLOW, this.getX(), this.getY() + this.getBbHeight() * 0.6, this.getZ(), 2 + warmTicks / 200, 0.5, 0.6, 0.5, 0.02);
        if (warmTicks >= WARM_TICKS) {
            cure(level);
        }
    }

    /** 長回毛，變回歌者。 */
    public SingerEntity cure(ServerLevel level) {
        SingerEntity singer = this.convertTo(ModEntities.SINGER, ConversionParams.single(this, false, false), s -> {
            s.addTag(pryuan05.pysift.fluid.SpiritFluid.REBORN);   // 10 秒內爬出靈液池，不會一長回毛就被撐傷
            s.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 2.0f, 1.2f);
            s.voice(pryuan05.pysift.sound.ModSounds.SINGER_REBORN, 1.8f, "reborn");
        });
        if (singer != null) {
            level.sendParticles(ParticleTypes.NOTE, singer.getX(), singer.getY() + singer.getBbHeight() + 0.3, singer.getZ(), 12, 0.8, 0.4, 0.8, 1.0);
            level.sendParticles(ParticleTypes.SCULK_SOUL, singer.getX(), singer.getY() + 1.5, singer.getZ(), 30, 0.6, 0.8, 0.6, 0.03);
            StoryTriggers.mournerCured(level, singer.position());
        }
        return singer;
    }

    /** 被哀悼號角安撫：ticks 內不再哭。 */
    public void hush(int ticks) {
        if (weepTicks > 0) {   // 正在哭：哭聲漸漸收住
            voice(pryuan05.pysift.sound.ModSounds.MOURNER_HUSH, 1.2f, "hush");
        }
        weepTicks = 0;
        weepCooldown = Math.max(weepCooldown, ticks);
    }

    public int getCureTicks() {
        return cureTicks;
    }

    // ---------------------------------------------------------------- 表情（tools/models/singer_faces.py 的 MOURNER_FACES）
    private static final List<String> FACES = List.of("ambient", "wail", "note", "hurt", "soothe", "hush");

    /** 發出聲音，同時做出對應的表情。 */
    private void voice(net.minecraft.sounds.SoundEvent sound, float volume, String face) {
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
    protected void playHurtSound(net.minecraft.world.damagesource.DamageSource source) {
        super.playHurtSound(source);
        this.triggerAnim("face", "face_hurt");
    }

    @Override
    public void registerControllers(com.geckolib.animatable.manager.AnimatableManager.ControllerRegistrar controllers) {
        super.registerControllers(controllers);
        var face = new com.geckolib.animation.AnimationController<MournerEntity>("face", 2, state -> com.geckolib.animation.object.PlayState.STOP);
        for (String name : FACES) {
            face.triggerableAnim("face_" + name, com.geckolib.animation.RawAnimation.begin().thenPlay(anim("face_" + name)));
        }
        controllers.add(face);
    }

    // ---------------------------------------------------------------- 聲音（tools/audio/build_sounds.py 合成）
    @Override
    protected net.minecraft.sounds.SoundEvent getAmbientSound() {
        return weepTicks > 0 ? null : pryuan05.pysift.sound.ModSounds.MOURNER_AMBIENT;   // 正在哭著唱歌時不另外啜泣
    }

    @Override
    public int getAmbientSoundInterval() {
        return 300;
    }

    @Override
    protected net.minecraft.sounds.SoundEvent getHurtSound(net.minecraft.world.damagesource.DamageSource source) {
        return pryuan05.pysift.sound.ModSounds.MOURNER_HURT;
    }

    @Override
    protected net.minecraft.sounds.SoundEvent getDeathSound() {
        return pryuan05.pysift.sound.ModSounds.MOURNER_DEATH;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("WeepCooldown", weepCooldown);
        output.putInt("WarmTicks", warmTicks);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        weepCooldown = input.getIntOr("WeepCooldown", 0);
        warmTicks = input.getIntOr("WarmTicks", 0);
    }
}
