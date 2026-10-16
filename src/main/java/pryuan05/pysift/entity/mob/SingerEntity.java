package pryuan05.pysift.entity.mob;

import pryuan05.pysift.block.SoulCrystal;
import java.util.List;
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
 */
public class SingerEntity extends PysiftAnimalEntity {
    private static final double RANGE = 16.0;
    private int songCooldown;

    public SingerEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
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
