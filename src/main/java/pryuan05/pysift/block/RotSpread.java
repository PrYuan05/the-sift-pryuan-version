package pryuan05.pysift.block;

import com.mojang.brigadier.arguments.BoolArgumentType;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;
import pryuan05.pysift.PySift;

/**
 * 腐爛會蔓延、也能停止（MODDING_ROADMAP §4.7 第三、五幕）。
 * <ul>
 *   <li>蔓延：赤紅幽匿收到隨機刻時，如果 ROT_RANGE 格內有隙浮傳送門（裂縫，主世界沒有靈魂的空氣從這裡倒灌），
 *       就有 ROT_CHANCE 的機率腐爛成原版的藍色幽匿。所以裂隙周圍的腐爛帶會慢慢往外長到 ROT_RANGE 格為止。</li>
 *   <li>止息：擊敗幽匿巨怪（腐爛的核心）後，這個世界記下 {@link State#stilled}；之後赤紅幽匿不再腐爛，
 *       反過來把身邊的藍色幽匿一塊一塊變回紅色（從腐爛帶外圈往門邊收回去）。</li>
 * </ul>
 * 測試指令：{@code /pysift_rot}（目前狀態）、{@code /pysift_rot stilled <true|false>}。
 */
public final class RotSpread {
    public static final int ROT_RANGE = 10;
    /** 變回紅色時冒出的粒子：赤紅幽匿的紅（腐爛時是藍色的 SCULK_SOUL）。 */
    private static final net.minecraft.core.particles.DustParticleOptions HEAL_DUST =
            new net.minecraft.core.particles.DustParticleOptions(0xD4566E, 1.1f);
    private static final float ROT_CHANCE = 0.35f, HEAL_CHANCE = 0.5f;

    private RotSpread() {
    }

    /** 赤紅幽匿：會隨機刻（腐爛或治癒）。 */
    public static class RedSculkBlock extends Block {
        public RedSculkBlock(BlockBehaviour.Properties properties) {
            super(properties.randomTicks());
        }

        @Override
        protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
            if (State.get(level.getServer()).stilled || nearSealed(level, pos)) {
                heal(level, pos, random);
            } else if (random.nextFloat() < ROT_CHANCE && nearRift(level, pos)) {
                level.setBlock(pos, Blocks.SCULK.defaultBlockState(), Block.UPDATE_ALL);
                level.sendParticles(ParticleTypes.SCULK_SOUL, pos.getX() + 0.5, pos.getY() + 1.1, pos.getZ() + 0.5, 2, 0.3, 0.1, 0.3, 0.01);
            }
        }
    }

    /** 這一格是藍色幽匿（或藍色脈絡）就變回紅色，冒出紅色粒子；回傳有沒有變。隙浮守衛、封印與止息都用它。 */
    public static boolean healOne(ServerLevel level, BlockPos n) {
        BlockState st = level.getBlockState(n);
        BlockState healed = null;
        if (st.is(Blocks.SCULK)) {
            healed = ModVegetation.RED_SCULK.defaultBlockState();
        } else if (st.is(Blocks.SCULK_VEIN)) {
            healed = ModVegetation.RED_SCULK_VEIN.withPropertiesOf(st);
        }
        if (healed == null) {
            return false;
        }
        level.setBlock(n, healed, Block.UPDATE_ALL);
        level.sendParticles(HEAL_DUST, n.getX() + 0.5, n.getY() + 1.1, n.getZ() + 0.5, 4, 0.3, 0.1, 0.3, 0.01);
        return true;
    }

    /** 隨便挑一個 2 格內的鄰居，是藍色幽匿（或藍色脈絡）就變回紅色。 */
    private static void heal(ServerLevel level, BlockPos pos, RandomSource random) {
        if (random.nextFloat() >= HEAL_CHANCE) {
            return;
        }
        BlockPos n = pos.offset(random.nextInt(5) - 2, random.nextInt(3) - 1, random.nextInt(5) - 2);
        BlockState st = level.getBlockState(n);
        BlockState healed = null;
        if (st.is(Blocks.SCULK)) {
            healed = ModVegetation.RED_SCULK.defaultBlockState();
        } else if (st.is(Blocks.SCULK_VEIN)) {
            healed = ModVegetation.RED_SCULK_VEIN.withPropertiesOf(st);
        }
        if (healed != null) {
            level.setBlock(n, healed, Block.UPDATE_ALL);
            level.sendParticles(HEAL_DUST, n.getX() + 0.5, n.getY() + 1.1, n.getZ() + 0.5, 4, 0.3, 0.1, 0.3, 0.01);
        }
    }

    /** 封印的裂隙方圓 SEAL_RANGE 格內：腐爛會被治癒。 */
    public static final int SEAL_RANGE = 12;

    public static boolean nearSealed(ServerLevel level, BlockPos pos) {
        if (level.dimension() != SiftPortalBlock.SIFT_DIM) {
            return false;
        }
        for (BlockPos s : State.get(level.getServer()).sealed) {
            if (Math.abs(s.getX() - pos.getX()) <= SEAL_RANGE && Math.abs(s.getZ() - pos.getZ()) <= SEAL_RANGE
                    && Math.abs(s.getY() - pos.getY()) <= 8) {
                return true;
            }
        }
        return false;
    }

    /** 封印一道裂隙：關掉傳送門、記下座標。回傳是否成功（附近要有傳送門）。 */
    public static boolean seal(ServerLevel level, BlockPos at) {
        if (SiftPortalBlock.clearPortal(level, at) == 0) {
            return false;
        }
        State s = State.get(level.getServer());
        s.sealed.add(at.immutable());
        s.setDirty();
        return true;
    }

    /** ROT_RANGE 格內（垂直 ±4）有隙浮傳送門。 */
    public static boolean nearRift(ServerLevel level, BlockPos pos) {
        for (BlockPos p : BlockPos.betweenClosed(pos.offset(-ROT_RANGE, -4, -ROT_RANGE), pos.offset(ROT_RANGE, 4, ROT_RANGE))) {
            if (level.getBlockState(p).is(ModBlocks.SIFT_PORTAL)) {
                return true;
            }
        }
        return false;
    }

    /**
     * 止息之後，就算裂隙周圍已經全部腐爛（沒有赤紅幽匿可以往回長），也要能慢慢變紅：每 5 tick 在隙浮裡每位玩家 HEAL_RADIUS 格內
     * 隨機挑 HEAL_SAMPLES 個地表柱，地表那幾格是藍色幽匿、而且附近有裂隙，就變回赤紅幽匿。一圈腐爛帶大約幾分鐘收完。
     */
    private static final int HEAL_RADIUS = 32, HEAL_SAMPLES = 5;

    public static void registerHealing() {
        net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(server -> {
            State state = State.get(server);
            if (server.getTickCount() % 5 != 0 || !state.stilled && state.sealed.isEmpty()) {
                return;
            }
            ServerLevel sift = server.getLevel(SiftPortalBlock.SIFT_DIM);
            if (sift == null) {
                return;
            }
            RandomSource random = sift.getRandom();
            for (ServerPlayer player : sift.players()) {
                for (int i = 0; i < HEAL_SAMPLES; i++) {
                    int x = player.getBlockX() + random.nextInt(HEAL_RADIUS * 2 + 1) - HEAL_RADIUS;
                    int z = player.getBlockZ() + random.nextInt(HEAL_RADIUS * 2 + 1) - HEAL_RADIUS;
                    if (!sift.hasChunkAt(new BlockPos(x, 0, z))) {
                        continue;
                    }
                    int top = sift.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.WORLD_SURFACE, x, z);
                    for (int y = top - 1; y >= top - 3; y--) {
                        BlockPos p = new BlockPos(x, y, z);
                        if (sift.getBlockState(p).is(Blocks.SCULK) && (state.stilled && nearRift(sift, p) || nearSealed(sift, p))) {
                            sift.setBlock(p, ModVegetation.RED_SCULK.defaultBlockState(), Block.UPDATE_ALL);
                            sift.sendParticles(HEAL_DUST, x + 0.5, y + 1.1, z + 0.5, 4, 0.3, 0.1, 0.3, 0.01);
                            break;
                        }
                    }
                }
            }
        });
    }

    /** 幽匿巨怪被擊敗：這個世界的腐爛停止。 */
    public static void still(ServerLevel level) {
        State s = State.get(level.getServer());
        if (!s.stilled) {
            s.stilled = true;
            s.setDirty();
            for (ServerPlayer p : level.getServer().getPlayerList().getPlayers()) {
                p.sendSystemMessage(Component.translatable("message.pysift.rot.stilled").withStyle(ChatFormatting.LIGHT_PURPLE));
                p.level().playSound(null, p.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.AMBIENT, 1.0f, 0.6f);
            }
        }
    }

    // ---------------------------------------------------------------- world state (kept in the Overworld's data storage)
    public static class State extends SavedData {
        boolean stilled;
        /** 用封印石關掉的裂隙（隙浮裡的座標）：附近的腐爛不再蔓延、而且會變回紅色。 */
        final java.util.List<BlockPos> sealed = new java.util.ArrayList<>();
        /** 終章送回隙浮、還沒在隙浮重逢的守衛數（Homecoming）。 */
        int homeward;

        public static final Codec<State> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.BOOL.optionalFieldOf("stilled", false).forGetter(s -> s.stilled),
                BlockPos.CODEC.listOf().optionalFieldOf("sealed", java.util.List.of()).forGetter(s -> s.sealed),
                Codec.INT.optionalFieldOf("homeward", 0).forGetter(s -> s.homeward)
        ).apply(i, (stilled, sealed, homeward) -> {
            State s = new State();
            s.stilled = stilled;
            s.sealed.addAll(sealed);
            s.homeward = homeward;
            return s;
        }));
        public static final SavedDataType<State> TYPE = new SavedDataType<>(PySift.id("sculk_rot"), State::new, CODEC, DataFixTypes.LEVEL);

        public static State get(MinecraftServer server) {
            return server.overworld().getDataStorage().computeIfAbsent(TYPE);
        }

        public boolean stilled() {
            return stilled;
        }

        public int homeward() {
            return homeward;
        }

        public void setHomeward(int n) {
            homeward = Math.max(0, n);
            setDirty();
        }
    }

    public static void registerCommand() {
        net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback.EVENT.register((dispatcher, registries, environment) ->
                dispatcher.register(Commands.literal("pysift_rot").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .executes(ctx -> {
                            boolean stilled = State.get(ctx.getSource().getServer()).stilled;
                            ctx.getSource().sendSuccess(() -> Component.literal("sculk rot stilled: " + stilled), false);
                            return stilled ? 1 : 0;
                        })
                        .then(Commands.literal("seal").then(Commands.argument("pos", net.minecraft.commands.arguments.coordinates.BlockPosArgument.blockPos()).executes(ctx -> {
                            BlockPos at = net.minecraft.commands.arguments.coordinates.BlockPosArgument.getBlockPos(ctx, "pos");
                            State s = State.get(ctx.getSource().getServer());
                            s.sealed.add(at.immutable());
                            s.setDirty();
                            ctx.getSource().sendSuccess(() -> Component.literal("sealed rift at " + at.toShortString()), true);
                            return 1;
                        })))
                        .then(Commands.literal("stilled").then(Commands.argument("value", BoolArgumentType.bool()).executes(ctx -> {
                            State s = State.get(ctx.getSource().getServer());
                            s.stilled = BoolArgumentType.getBool(ctx, "value");
                            s.setDirty();
                            ctx.getSource().sendSuccess(() -> Component.literal("sculk rot stilled: " + s.stilled), true);
                            return 1;
                        })))));
    }
}
