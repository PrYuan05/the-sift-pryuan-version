package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Containers;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 共鳴核心（共鳴靈陣，第三階段）：核心上放一個「觸媒」，周圍八個共鳴台座（東南西北與四個斜角，距離 {@link #RING} 格，同一高度）
 * 放上材料；核心轉動時，合乎 {@link #RECIPES} 的組合會慢慢共鳴（32 RPM 時 {@link Recipe#time} tick），完成時台座上的東西消失、
 * 核心上的觸媒變成成品。共鳴時台座射出光束連到核心。
 * <p>
 * 範圍加成：運轉中的核心讓 {@link #AURA} 格內的研磨機與淨化篩快 50%。
 */
public class ResonanceCoreBlockEntity extends KineticBlockEntity {
    public static final int RING = 3;
    public static final int AURA = 8;
    private static final Map<ResourceKey<Level>, Set<BlockPos>> CORES = new HashMap<>();

    /** 共鳴配方：核心的觸媒、台座上的材料（不分順序，數量要剛好）、成品。 */
    public record Recipe(String core, List<String> pedestals, String result, int count, int time) {
    }

    public static final List<Recipe> RECIPES = new ArrayList<>();

    static {
        RECIPES.add(new Recipe("minecraft:amethyst_shard", List.of("minecraft:sculk", "minecraft:sculk", "minecraft:sculk",
                "minecraft:sculk", "pysift:soul_essence", "pysift:soul_essence", "pysift:soul_essence", "pysift:soul_essence"),
                "minecraft:echo_shard", 2, 200));
        RECIPES.add(new Recipe("minecraft:amethyst_cluster", List.of("pysift:soul_essence", "pysift:soul_essence",
                "pysift:soul_essence", "pysift:soul_essence"), "pysift:charoite", 4, 160));
        RECIPES.add(new Recipe("minecraft:deepslate", List.of("minecraft:bone_block", "minecraft:bone_block", "minecraft:bone_block",
                "minecraft:bone_block", "pysift:soul_crystal_block", "pysift:soul_crystal_block", "pysift:soul_crystal_block",
                "pysift:soul_crystal_block"), "minecraft:reinforced_deepslate", 1, 300));
        for (String disc : List.of("pigstep", "relic", "precipice", "creator", "5", "otherside", "13", "tears")) {
            String id = "minecraft:music_disc_" + disc;   // the resonant discs (block/RitualDiscs): copy one for wave frequencies
            RECIPES.add(new Recipe(id, List.of("minecraft:amethyst_shard", "minecraft:amethyst_shard", "minecraft:amethyst_shard",
                    "minecraft:amethyst_shard", "pysift:soul_essence", "pysift:soul_essence", "minecraft:note_block",
                    "minecraft:note_block"), id, 2, 240));
        }
    }

    private ItemStack item = ItemStack.EMPTY;
    private float progress;
    private boolean crafting;   // synced: the renderer draws the beams

    public ResonanceCoreBlockEntity(BlockPos pos, BlockState state) {
        super(SoulPower.RESONANCE_CORE_ENTITY, pos, state);
    }

    public ItemStack item() {
        return item;
    }

    public boolean crafting() {
        return crafting;
    }

    public void setItem(ItemStack stack) {
        item = stack;
        progress = 0;
        sync();
    }

    /** 八個台座的位置。 */
    public static List<BlockPos> ring(BlockPos core) {
        List<BlockPos> out = new ArrayList<>();
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                if (dx != 0 || dz != 0) {
                    out.add(core.offset(dx * RING, 0, dz * RING));
                }
            }
        }
        return out;
    }

    private static String id(ItemStack stack) {
        return BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
    }

    private Recipe match(Level level) {
        if (item.isEmpty()) {
            return null;
        }
        List<String> have = new ArrayList<>();
        for (BlockPos p : ring(worldPosition)) {
            if (level.getBlockEntity(p) instanceof ResonancePedestalBlock.Entity pedestal && !pedestal.item().isEmpty()) {
                have.add(id(pedestal.item()));
            }
        }
        for (Recipe r : RECIPES) {
            if (r.core().equals(id(item)) && r.pedestals().size() == have.size()) {
                List<String> left = new ArrayList<>(have);
                boolean ok = true;
                for (String need : r.pedestals()) {
                    ok &= left.remove(need);
                }
                if (ok) {
                    return r;
                }
            }
        }
        return null;
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, ResonanceCoreBlockEntity core) {
        ServerLevel server = (ServerLevel) level;
        long now = level.getGameTime();
        if (now - core.network.time() > SoulNetwork.INTERVAL * 3L && now % SoulNetwork.INTERVAL == 0) {
            core.network = SoulNetwork.Result.IDLE;
            SoulNetwork.update(server, pos);
        }
        Recipe recipe = core.speed == 0 || now % 5 != 0 && !core.crafting ? null : core.match(level);
        boolean was = core.crafting;
        core.crafting = recipe != null && core.speed != 0;
        if (core.crafting != was) {
            core.sync();
        }
        if (!core.crafting) {
            core.progress = 0;
            return;
        }
        core.progress += Math.abs(core.speed) / SoulNetwork.SPEED;
        if (now % 10 == 0) {
            for (BlockPos p : ring(pos)) {
                if (level.getBlockEntity(p) instanceof ResonancePedestalBlock.Entity pedestal && !pedestal.item().isEmpty()) {
                    Vec3 a = Vec3.atCenterOf(p).add(0, 0.6, 0), b = Vec3.atCenterOf(pos).add(0, 0.8, 0);
                    Vec3 m = a.lerp(b, level.getRandom().nextDouble());
                    server.sendParticles(ParticleTypes.SOUL, m.x, m.y, m.z, 1, 0.05, 0.05, 0.05, 0.0);
                }
            }
        }
        if (now % 40 == 0) {
            level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 1.0f, 0.6f + core.progress / recipe.time());
        }
        if (core.progress < recipe.time()) {
            return;
        }
        for (BlockPos p : ring(pos)) {
            if (level.getBlockEntity(p) instanceof ResonancePedestalBlock.Entity pedestal) {
                pedestal.setItem(ItemStack.EMPTY);
            }
        }
        Item result = BuiltInRegistries.ITEM.getValue(Identifier.parse(recipe.result()));
        core.setItem(new ItemStack(result, recipe.count()));
        core.crafting = false;
        core.sync();
        server.sendParticles(ParticleTypes.SONIC_BOOM, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 1, 0, 0, 0, 0);
        server.sendParticles(ParticleTypes.SOUL, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 20, 0.6, 0.4, 0.6, 0.05);
        level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.5f, 0.7f);
    }

    /** 範圍加成：pos 附近有運轉中的共鳴核心就回傳 1.5。 */
    public static float aura(Level level, BlockPos pos) {
        for (BlockPos p : CORES.getOrDefault(level.dimension(), Set.of())) {
            if (p.closerThan(pos, AURA + 0.5) && level.getBlockEntity(p) instanceof ResonanceCoreBlockEntity core && core.speed != 0) {
                return 1.5f;
            }
        }
        return 1f;
    }

    @Override
    public void setLevel(Level level) {
        super.setLevel(level);
        if (!level.isClientSide()) {
            CORES.computeIfAbsent(level.dimension(), k -> new HashSet<>()).add(worldPosition.immutable());
        }
    }

    @Override
    public void setRemoved() {
        super.setRemoved();
        if (level != null && !level.isClientSide()) {
            Set<BlockPos> set = CORES.get(level.dimension());
            if (set != null) {
                set.remove(worldPosition);
            }
        }
    }

    @Override
    public void preRemoveSideEffects(BlockPos pos, BlockState state) {
        if (level != null && !item.isEmpty()) {
            Containers.dropItemStack(level, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, item);
            item = ItemStack.EMPTY;
        }
        super.preRemoveSideEffects(pos, state);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        if (!item.isEmpty()) {
            output.store("Item", ItemStack.CODEC, item);
        }
        output.putFloat("Progress", progress);
        output.putBoolean("Crafting", crafting);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        item = input.read("Item", ItemStack.CODEC).orElse(ItemStack.EMPTY);
        progress = input.getFloatOr("Progress", 0f);
        crafting = input.getBooleanOr("Crafting", false);
    }
}
