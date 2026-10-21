package pryuan05.pysift.progression;

import com.mojang.serialization.Codec;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.decoration.Mannequin;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.MultifaceBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.PySift;
import pryuan05.pysift.effect.ModEffects;
import pryuan05.pysift.effect.SoulBurn;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/**
 * 三把 Boss 武器（第 1 階段第 4 段），以及它們共用的規則：
 * <ul>
 *   <li>{@link #AWAKENED}：覺醒標記（鍛造台用另外兩隻 Boss 的碎片升級，配方在 build_progression.py）。</li>
 *   <li>{@link #soulDeprive}：對怪物施加靈魂剝奪。怪物版效果：受到的傷害 +30%（SoulDeprivationDamageMixin）、
 *       每秒流失約 1.25 點生命（ModEffects）。</li>
 *   <li>衝刺護符的分身與重錘的幽匿藤蔓都是限時的東西，由 {@link #tick} 統一倒數。</li>
 * </ul>
 */
public final class BossWeapons {
    public static final DataComponentType<Boolean> AWAKENED = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
            PySift.id("awakened"), DataComponentType.<Boolean>builder().persistent(Codec.BOOL).networkSynchronized(ByteBufCodecs.BOOL).build());

    public static final Item SONIC_STAFF = ModProgression.registerItem("sonic_staff", SonicStaffItem::new,
            new Item.Properties().sword(SiftiteGear.TOOL, 2.0f, -2.6f).durability(1500).rarity(Rarity.EPIC));
    public static final Item DASH_CHARM = ModProgression.registerItem("dash_charm", DashCharmItem::new,
            new Item.Properties().durability(600).rarity(Rarity.EPIC));
    public static final Item SCULK_HAMMER = ModProgression.registerItem("sculk_hammer", SculkHammerItem::new,
            new Item.Properties().sword(SiftiteGear.TOOL, 5.0f, -3.3f).durability(1500).rarity(Rarity.EPIC));

    /** 武器的靈魂剝奪持續時間（tick）。 */
    public static final int DEPRIVE_TICKS = 100;

    private static final List<Timed> TIMED = new ArrayList<>();

    private BossWeapons() {
    }

    public static boolean isAwakened(ItemStack stack) {
        return Boolean.TRUE.equals(stack.get(AWAKENED));
    }

    /** 可以被武器打到的目標：不是自己、不是玩家、不是使用者的寵物。 */
    public static boolean isFoe(LivingEntity user, Entity e) {
        return e instanceof LivingEntity living && e != user && living.isAlive() && !(e instanceof Player)
                && !(e instanceof Mannequin) && !(e instanceof TamableAnimal pet && pet.isOwnedBy(user));
    }

    public static void soulDeprive(LivingEntity target, LivingEntity source) {
        target.addEffect(new MobEffectInstance(ModEffects.SOUL_DEPRIVATION, DEPRIVE_TICKS, 0), source);
    }

    /** 靈魂連鎖：從 target 跳到附近 6 格內最近的 count 個敵人，各受 damage 點魔法傷害並附加靈魂剝奪（音波法杖、靈髓劍）。 */
    public static void chain(ServerLevel level, LivingEntity attacker, LivingEntity target, int count, float damage) {
        List<LivingEntity> next = level.getEntitiesOfClass(LivingEntity.class, target.getBoundingBox().inflate(6.0),
                e -> e != target && isFoe(attacker, e));
        next.sort((a, b) -> Double.compare(a.distanceToSqr(target), b.distanceToSqr(target)));
        Vec3 from = target.position().add(0, target.getBbHeight() * 0.5, 0);
        for (LivingEntity e : next.subList(0, Math.min(count, next.size()))) {
            Vec3 to = e.position().add(0, e.getBbHeight() * 0.5, 0);
            for (int i = 1; i < 8; i++) {                    // a crackling soul arc between the two
                Vec3 p = from.lerp(to, i / 8.0);
                level.sendParticles(ParticleTypes.SCULK_SOUL, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0);
            }
            if (e.hurtServer(level, level.damageSources().indirectMagic(attacker, attacker), damage)) {
                soulDeprive(e, attacker);
            }
            from = to;
        }
        if (!next.isEmpty()) {
            level.playSound(null, target.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.0f, 1.4f);
        }
    }

    /** 在玩家原地留下顯示他外觀的分身（{@link Mannequin}），lifetime tick 內吸引附近的怪物（衝刺護符、靈髓胸甲）。 */
    public static void spawnDecoy(ServerLevel level, Player player, int lifetime) {
        Mannequin decoy = net.minecraft.world.entity.EntityTypes.MANNEQUIN.create(level, net.minecraft.world.entity.EntitySpawnReason.TRIGGERED);
        if (decoy == null) {
            return;
        }
        decoy.snapTo(player.getX(), player.getY(), player.getZ(), player.getYRot(), 0.0f);
        decoy.setComponent(net.minecraft.core.component.DataComponents.PROFILE,
                net.minecraft.world.item.component.ResolvableProfile.createResolved(player.getGameProfile()));
        level.addFreshEntity(decoy);
        level.sendParticles(ParticleTypes.SOUL, player.getX(), player.getY(1.0), player.getZ(), 12, 0.3, 0.6, 0.3, 0.02);
        trackDecoy(level, player, decoy, lifetime);
    }

    // ------------------------------------------------------------ timed things (decoys, tendrils)
    private interface Timed {
        /** @return true when finished */
        boolean tick(long now);
    }

    /** 衝刺護符的分身 → 召喚它的玩家。分身不會受傷（{@link #load} 的 ALLOW_DAMAGE），但仍是有效的攻擊目標。 */
    private static final java.util.Map<Mannequin, Player> DECOYS = new java.util.HashMap<>();
    public static final double TAUNT_RADIUS = 20.0;

    /**
     * 衝刺護符的分身：存在期間每 5 tick 把附近正在追召喚者（或沒有目標）的怪物拉去追分身，時間到化成靈魂煙消失。
     * 怪物的目標 AI 會不斷重新鎖定玩家，所以要持續拉回來，只設定一次不夠。
     */
    static void trackDecoy(ServerLevel level, Player owner, Mannequin decoy, int lifetime) {
        long end = level.getGameTime() + lifetime;
        DECOYS.put(decoy, owner);
        TIMED.add(now -> {
            if (decoy.isRemoved()) {
                DECOYS.remove(decoy);
                return true;
            }
            if (now < end) {
                if (now % 5 == 0) {
                    for (Mob mob : level.getEntitiesOfClass(Mob.class, decoy.getBoundingBox().inflate(TAUNT_RADIUS),
                            m -> m.isAlive() && (m.getTarget() == owner || m.getTarget() == null && m instanceof net.minecraft.world.entity.monster.Enemy))) {
                        mob.setTarget(decoy);
                    }
                    level.sendParticles(ParticleTypes.SOUL, decoy.getX(), decoy.getY(0.5), decoy.getZ(), 1, 0.3, 0.5, 0.3, 0.01);
                }
                return false;
            }
            for (Mob mob : level.getEntitiesOfClass(Mob.class, decoy.getBoundingBox().inflate(TAUNT_RADIUS), m -> m.getTarget() == decoy)) {
                mob.setTarget(null);
            }
            level.sendParticles(ParticleTypes.SOUL, decoy.getX(), decoy.getY(1.0), decoy.getZ(), 20, 0.3, 0.6, 0.3, 0.02);
            level.playSound(null, decoy.blockPosition(), SoundEvents.ILLUSIONER_MIRROR_MOVE, SoundSource.PLAYERS, 1.0f, 1.2f);
            DECOYS.remove(decoy);
            decoy.discard();
            return true;
        });
    }

    /**
     * 重錘留下的幽匿藤蔓：在地面長出幽匿脈絡，{@code delay} tick 後爆炸（半徑 2.5，6 點傷害、靈魂剝奪），脈絡隨之消失。
     */
    static void plantTendril(ServerLevel level, BlockPos pos, LivingEntity owner, int delay) {
        BlockState vein = Blocks.SCULK_VEIN.defaultBlockState().setValue(MultifaceBlock.getFaceProperty(Direction.DOWN), true);
        boolean placed = level.getBlockState(pos).isAir() && level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP)
                && level.setBlock(pos, vein, 3);
        long end = level.getGameTime() + delay;
        Vec3 c = Vec3.atBottomCenterOf(pos).add(0, 0.3, 0);
        TIMED.add(now -> {
            if (now < end) {
                if (now % 4 == 0) {
                    level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, c.x, c.y, c.z, 2, 0.25, 0.1, 0.25, 0.01);
                }
                return false;
            }
            if (placed && level.getBlockState(pos).is(Blocks.SCULK_VEIN)) {
                level.removeBlock(pos, false);
            }
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(pos).inflate(2.5), e -> isFoe(owner, e))) {
                if (e.hurtServer(level, level.damageSources().indirectMagic(owner, owner), 6.0f)) {
                    soulDeprive(e, owner);
                }
            }
            level.sendParticles(ParticleTypes.SCULK_SOUL, c.x, c.y + 0.3, c.z, 12, 0.6, 0.4, 0.6, 0.05);
            level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.3, c.z, 1, 0, 0, 0, 0);
            level.playSound(null, pos, SoundEvents.SCULK_SHRIEKER_SHRIEK, SoundSource.PLAYERS, 0.6f, 1.6f);
            return true;
        });
    }

    private static void tick() {
        if (TIMED.isEmpty()) {
            return;
        }
        // 所有計時物件都在同一個伺服器上，用任一個世界的時間即可；各自用自己的 level 判斷
        Iterator<Timed> it = TIMED.iterator();
        List<Timed> done = new ArrayList<>();
        while (it.hasNext()) {
            Timed t = it.next();
            if (t.tick(currentTime)) {
                done.add(t);
            }
        }
        TIMED.removeAll(done);
    }

    private static long currentTime;

    /** 正在靈魂剝奪中的怪物：身上點著靈魂火（同步的 SoulBurn.FIRE 附件，和玩家一樣的藍色火焰），效果結束時熄滅。 */
    private static final java.util.Set<LivingEntity> BURNING = new java.util.HashSet<>();

    /** 由 ModEffects 在怪物身上的靈魂剝奪每次生效時呼叫（約每 4 tick）；重新載入的怪物也會在這裡被接回來。 */
    public static void markDeprived(LivingEntity e) {
        if (!e.getAttachedOrElse(SoulBurn.FIRE, false)) {
            e.setAttached(SoulBurn.FIRE, true);
        }
        BURNING.add(e);
    }

    private static void extinguish() {
        BURNING.removeIf(e -> {
            if (e.isRemoved() || !e.isAlive() || !e.hasEffect(ModEffects.SOUL_DEPRIVATION)) {
                if (!e.isRemoved()) {
                    e.setAttached(SoulBurn.FIRE, false);
                }
                return true;
            }
            return false;
        });
    }

    /** 怪物在靈魂剝奪期間是否被武器標記中（給 mixin 用）。 */
    public static boolean deprivedFoe(LivingEntity e) {
        return !(e instanceof Player) && e.hasEffect(ModEffects.SOUL_DEPRIVATION);
    }

    static void load() {
        // 分身吃下所有傷害但不會受傷（不能用「無敵」：無敵的實體不會被怪物當成目標）
        net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
            if (entity instanceof Mannequin decoy && DECOYS.containsKey(decoy)) {
                if (entity.level() instanceof ServerLevel level) {
                    level.sendParticles(ParticleTypes.SOUL, decoy.getX(), decoy.getY(0.7), decoy.getZ(), 3, 0.2, 0.3, 0.2, 0.02);
                }
                return false;
            }
            return true;
        });
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            currentTime = server.overworld().getGameTime();
            tick();
            if (currentTime % 4 == 0) {
                extinguish();
            }
        });
    }
}
