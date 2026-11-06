package pryuan05.pysift.block;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.minecraft.ChatFormatting;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.entity.ResonantJukeboxBlockEntity;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.entity.mob.EchoGolemEntity;
import pryuan05.pysift.entity.mob.SingerEntity;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.Iterator;
import java.util.List;

/**
 * 遠古城市「伏守者巨口」× 歌者的八音開門儀式。
 * <ol>
 *   <li>在強化深板岩附近（16 格內）吹響山羊角：24 格內沒有歌者時，在玩家面前召喚一隻「儀式歌者」（從地底爬出，之後固定不動）。</li>
 *   <li>手持迴音碎片右鍵儀式歌者：歌者召喚兩隻迴音傀儡，把 8 個共鳴唱片盒擺在框架前（找不到封閉框架時，
 *       改在歌者前方預留一道裂隙門的位置，唱片盒排在它前面）。</li>
 *   <li>玩家把 8 張儀式唱片（{@link RitualDiscs}）由左到右照「紅橙黃綠藍靛紫粉」放進唱片盒：每放一張就射出該顏色的光柱。</li>
 *   <li>8 張放滿：唱片盒由左到右依序奏出八音、歌者跟著唱。全部放對：8 道光柱匯聚到門中心，框架填滿傳送門（或開出裂隙門）；
 *       歌者揮手道別、鑽回地底離開。</li>
 *   <li>放錯任何一張（唱片可以放進任何一個盒子）：那一格走調，畫面一暗，門被撕開又閃爍，深色幽匿從門前爆開，
 *       歌者倒著唱出旋律把門闔上（哀悼者的歌），唱片全部彈出來，要重新放（世界觀 4.7：遠古人就是這樣放錯的）。</li>
 *   <li>唱片盒就是門的鑰匙：打破任一個，門就關閉，唱片掉出來。</li>
 * </ol>
 * 隙浮裡沒有遠古城市：用靈魂晶塊蓋一個封閉框架，手持迴音碎片右鍵框架，就能填出回主世界的傳送門。
 */
public final class SiftPortalRitual {
    /** 這次儀式的配置：門中心、框架軸向、是否有框架、8 個唱片盒的位置。 */
    public record Plan(BlockPos portalCentre, boolean axisX, boolean frame, List<BlockPos> group) {
    }

    /**
     * 儀式的位置（吹山羊角時算一次，存在歌者身上）：門中心、框架軸向、有沒有框架、唱片盒在哪一側、
     * 門寬方向的正中點（世界座標，一定是某一格的中心）、唱片盒那一排離門幾格與高度。
     */
    public record Site(BlockPos portalCentre, boolean axisX, boolean frame, Direction side, double middle, int rowDist, int floorY) {
        public void save(net.minecraft.world.level.storage.ValueOutput out) {
            out.store("SitePortalCentre", BlockPos.CODEC, portalCentre);
            out.putBoolean("SiteAxisX", axisX);
            out.putBoolean("SiteFrame", frame);
            out.putInt("SiteSide", side.get3DDataValue());
            out.putDouble("SiteMiddle", middle);
            out.putInt("SiteRowDist", rowDist);
            out.putInt("SiteFloorY", floorY);
        }

        public static Site load(net.minecraft.world.level.storage.ValueInput in) {
            BlockPos centre = in.read("SitePortalCentre", BlockPos.CODEC).orElse(null);
            if (centre == null) {
                return null;
            }
            return new Site(centre, in.getBooleanOr("SiteAxisX", true), in.getBooleanOr("SiteFrame", false),
                    Direction.from3DDataValue(in.getIntOr("SiteSide", 3)), in.getDoubleOr("SiteMiddle", centre.getX() + 0.5),
                    in.getIntOr("SiteRowDist", ROW_GAP), in.getIntOr("SiteFloorY", centre.getY()));
        }

        /** 中點那條線上、離門 dist 格、高度 y 的位置（方塊）。 */
        BlockPos onMiddle(int dist, int y) {
            BlockPos base = new BlockPos(portalCentre.getX(), y, portalCentre.getZ()).relative(side, dist);
            int m = (int) Math.floor(middle);
            return axisX ? new BlockPos(m, y, base.getZ()) : new BlockPos(base.getX(), y, m);
        }
    }

    private record Task(ServerLevel level, long at, Runnable run) {
    }

    private static final List<Task> TASKS = new ArrayList<>();
    private static final int SEATS = 8;
    private static final int FINALE_STEP = 6;
    /** 歌者站在唱片盒那一排後面幾格；框架前面沒有更低的地面時，唱片盒排在離門幾格。 */
    private static final int SINGER_GAP = 2, ROW_GAP = 4;

    /** 唱片盒那一排離門幾格、在哪個高度。 */
    private record Layout(int rowDist, int floorY) {
    }

    /**
     * 遠古城市的傳送門框架架在高台上：從門口往外走，找到框架下方的地面（比門底低 2 格以上），唱片盒排在那片地面上，
     * 離高台邊緣一格。找不到更低的地面（例如自己蓋在平地上的框架）就排在門前 4 格、門底的高度。
     */
    private static Layout layout(ServerLevel level, BlockPos centre, int bottomY, Direction side) {
        for (int d = 1; d <= 12; d++) {
            BlockPos column = new BlockPos(centre.getX(), bottomY, centre.getZ()).relative(side, d);
            Integer ground = groundY(level, column, bottomY + 2, bottomY - 14);
            if (ground != null && ground <= bottomY - 2) {
                return new Layout(d + 1, ground);
            }
            if (ground == null || ground > bottomY + 1) {
                break;   // 前面是牆
            }
        }
        return new Layout(ROW_GAP, bottomY);
    }

    /** 框架兩側哪一邊比較寬敞：數門前 3~12 格、門寬 ±10 格範圍內站得住的位置（門底往下 14 格內）。 */
    private static Direction roomierSide(ServerLevel level, SiftPortalBlock.Frame frame, BlockPos centre) {
        boolean axisX = frame.axis() == Direction.Axis.X;
        Direction normal = axisX ? Direction.SOUTH : Direction.EAST;
        Direction along = axisX ? Direction.EAST : Direction.SOUTH;
        int best = -1;
        Direction bestSide = normal;
        for (Direction side : new Direction[]{normal, normal.getOpposite()}) {
            int open = 0;
            for (int d = 3; d <= 12; d++) {
                for (int a = -10; a <= 10; a += 2) {
                    BlockPos column = new BlockPos(centre.getX(), frame.bottomY(), centre.getZ()).relative(side, d).relative(along, a);
                    if (groundY(level, column, frame.bottomY() + 2, frame.bottomY() - 14) != null) {
                        open++;
                    }
                }
            }
            if (open > best) {
                best = open;
                bestSide = side;
            }
        }
        return bestSide;
    }

    /**
     * 門寬方向的正中格：先取框架內部最左到最右的中點；門寬是偶數格時中點落在兩格之間，
     * 再比較門前地面（唱片盒那一排前後）左右的高低是否對稱，選比較對稱的那一格當中心
     * （遠古城市的巨口框架比前面的 5 格中央台階偏了半格，靠這個對回台階正中）。
     */
    private static double pickMiddle(ServerLevel level, SiftPortalBlock.Frame frame, Direction side, Layout layout) {
        double m = frame.alongMiddle();
        if (Math.abs(m - Math.floor(m) - 0.5) < 1e-6) {
            return m;   // 已經是某一格的中心
        }
        boolean axisX = frame.axis() == Direction.Axis.X;
        BlockPos centre = BlockPos.containing(frame.centre());
        double best = m - 0.5;
        int bestScore = Integer.MIN_VALUE;
        for (double c : new double[]{m - 0.5, m + 0.5}) {
            int score = 0;
            for (int d = Math.max(1, layout.rowDist() - 2); d <= layout.rowDist() + 5; d++) {
                BlockPos row = new BlockPos(centre.getX(), layout.floorY(), centre.getZ()).relative(side, d);
                for (int k = 1; k <= 12; k++) {
                    int a = (int) Math.floor(c - k), b = (int) Math.floor(c + k);
                    Integer ha = groundY(level, axisX ? new BlockPos(a, 0, row.getZ()) : new BlockPos(row.getX(), 0, a),
                            layout.floorY() + 4, layout.floorY() - 6);
                    Integer hb = groundY(level, axisX ? new BlockPos(b, 0, row.getZ()) : new BlockPos(row.getX(), 0, b),
                            layout.floorY() + 4, layout.floorY() - 6);
                    if (java.util.Objects.equals(ha, hb)) {
                        score++;
                    }
                }
            }
            if (score > bestScore) {
                bestScore = score;
                best = c;
            }
        }
        return best;
    }

    /** 吹山羊角時決定整個儀式的位置。有框架：中點、比較寬敞的一側、框架下方的地面；沒有框架：歌者面前預留裂隙門。 */
    private static Site computeSite(ServerLevel level, BlockPos near, Vec3 facingFrom, float facingYaw) {
        SiftPortalBlock.Frame frame = SiftPortalBlock.findFrame(level, near, 16, Blocks.REINFORCED_DEEPSLATE);
        if (frame != null) {
            boolean axisX = frame.axis() == Direction.Axis.X;
            BlockPos centre = BlockPos.containing(frame.centre());
            Direction side = roomierSide(level, frame, centre);
            Layout layout = layout(level, centre, frame.bottomY(), side);
            return new Site(centre, axisX, true, side, pickMiddle(level, frame, side, layout), layout.rowDist(), layout.floorY());
        }
        Vec3 fwd = Vec3.directionFromRotation(0, facingYaw);
        Direction facing = Direction.getApproximateNearest(fwd.x, 0, fwd.z);
        boolean axisX = facing.getAxis() == Direction.Axis.Z;
        BlockPos base = standingSpot(level, BlockPos.containing(facingFrom).relative(facing, ROW_GAP + SINGER_GAP + 2));
        double middle = axisX ? base.getX() + 0.5 : base.getZ() + 0.5;
        return new Site(base.above(1), axisX, false, facing.getOpposite(), middle, ROW_GAP, base.getY());
    }

    /** 不是完整方塊（蠟燭、地毯、幽匿脈絡、骷髏頭……）：找地面時當成空的，打掃時會清掉。 */
    private static boolean passable(ServerLevel level, BlockPos p) {
        BlockState s = level.getBlockState(p);
        return s.canBeReplaced() || !s.isCollisionShapeFullBlock(level, p);
    }

    /** column 從 top 往下到 bottom，第一個站得住的高度（腳下實心、身體兩格沒有完整方塊）。 */
    private static Integer groundY(ServerLevel level, BlockPos column, int top, int bottom) {
        for (int y = top; y >= bottom; y--) {
            BlockPos p = new BlockPos(column.getX(), y, column.getZ());
            if (passable(level, p) && passable(level, p.above())
                    && level.getBlockState(p.below()).isFaceSturdy(level, p.below(), Direction.UP)) {
                return y;
            }
        }
        return null;
    }

    private SiftPortalRitual() {
    }

    public static void register() {
        RitualBlocks.load();
        pryuan05.pysift.worldgen.WildRiftFeature.register();
        registerCommand();
        UseItemCallback.EVENT.register((player, level, hand) -> {
            if (level instanceof ServerLevel server && player.getItemInHand(hand).is(Items.GOAT_HORN)) {
                summonSinger(server, player);
            }
            return InteractionResult.PASS;   // 山羊角照常吹響
        });
        // 隙浮：靈魂晶塊框架 + 迴音碎片 → 回主世界的傳送門
        UseBlockCallback.EVENT.register((player, level, hand, hit) -> {
            ItemStack stack = player.getItemInHand(hand);
            if (!stack.is(Items.ECHO_SHARD) || !level.dimension().equals(SiftPortalBlock.SIFT_DIM)
                    || !level.getBlockState(hit.getBlockPos()).is(SoulCrystal.SOUL_CRYSTAL_BLOCK)) {
                return InteractionResult.PASS;
            }
            if (!(level instanceof ServerLevel server)) {
                return InteractionResult.SUCCESS;
            }
            SiftPortalBlock.Frame frame = SiftPortalBlock.findFrame(server, hit.getBlockPos(), 6, SoulCrystal.SOUL_CRYSTAL_BLOCK);
            if (frame == null) {
                player.sendOverlayMessage(Component.translatable("message.pysift.ritual.no_crystal_frame").withStyle(ChatFormatting.LIGHT_PURPLE));
                return InteractionResult.FAIL;
            }
            SiftPortalBlock.fillFrame(server, frame);
            stack.consume(1, player);
            Vec3 c = frame.centre();
            server.playSound(null, BlockPos.containing(c), SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 2.0f, 1.2f);
            server.playSound(null, BlockPos.containing(c), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 2.0f, 0.8f);
            server.sendParticles(ParticleTypes.END_ROD, c.x, c.y, c.z, 60, 1.0, 1.5, 1.0, 0.05);
            // 門一打開，主世界沒有靈魂的空氣就灌進來：周圍長出和野外裂隙一樣的腐爛帶（之後由 RotSpread 慢慢擴散）
            pryuan05.pysift.worldgen.WildRiftFeature.rotHalo(server, BlockPos.containing(c), server.getRandom());
            return InteractionResult.SUCCESS_SERVER;
        });
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            if (TASKS.isEmpty()) {
                return;
            }
            List<Task> due = new ArrayList<>();
            for (Iterator<Task> it = TASKS.iterator(); it.hasNext(); ) {
                Task t = it.next();
                if (t.level().getGameTime() >= t.at()) {
                    due.add(t);
                    it.remove();
                }
            }
            due.forEach(t -> t.run().run());
        });
    }

    private static void schedule(ServerLevel level, int delay, Runnable run) {
        TASKS.add(new Task(level, level.getGameTime() + delay, run));
    }

    private static boolean nearReinforcedDeepslate(ServerLevel level, BlockPos centre, int radius) {
        for (BlockPos p : BlockPos.betweenClosed(centre.offset(-radius, -radius, -radius), centre.offset(radius, radius, radius))) {
            if (level.getBlockState(p).is(Blocks.REINFORCED_DEEPSLATE)) {
                return true;
            }
        }
        return false;
    }

    // ------------------------------------------------------------------ step 1: the goat horn calls a ritual Singer
    private static void summonSinger(ServerLevel level, Player player) {
        BlockPos at = player.blockPosition();
        if (!nearReinforcedDeepslate(level, at, 16)
                || !level.getEntitiesOfClass(SingerEntity.class, new AABB(at).inflate(24)).isEmpty()) {
            return;
        }
        summonAt(level, at, player.position(), player.getYRot());
    }

    /** 在 at 附近決定儀式位置並召喚儀式歌者（面向 viewer）。 */
    private static SingerEntity summonAt(ServerLevel level, BlockPos at, Vec3 viewer, float viewerYaw) {
        Site site = computeSite(level, at, viewer, viewerYaw);   // 先找準中心與排列，再召喚
        BlockPos spot = standingSpot(level, site.onMiddle(site.rowDist() + SINGER_GAP, site.floorY()));
        double sx = site.axisX() ? site.middle() : spot.getX() + 0.5;
        double sz = site.axisX() ? spot.getZ() + 0.5 : site.middle();
        float yaw = (float) Math.toDegrees(Math.atan2(-(viewer.x - sx), viewer.z - sz));   // 面向玩家
        SingerEntity singer = ModEntities.SINGER.create(level, EntitySpawnReason.TRIGGERED);
        if (singer == null) {
            return null;
        }
        singer.snapTo(sx, spot.getY(), sz, yaw, 0);
        singer.setYHeadRot(yaw);
        singer.setYBodyRot(yaw);
        singer.setRitual(true);
        singer.setRitualSite(site);
        singer.startEmerging();   // 從地底爬出
        level.addFreshEntity(singer);
        level.sendParticles(ParticleTypes.SCULK_SOUL, singer.getX(), singer.getY() + 1, singer.getZ(), 24, 0.6, 0.8, 0.6, 0.04);
        singer.playSound(SoundEvents.SCULK_CATALYST_BLOOM, 2.0f, 1.0f);
        return singer;
    }

    /** 門的哪一側（框架平面的法線方向）朝向 pos。 */
    private static Direction sideOf(boolean axisX, BlockPos centre, Vec3 pos) {
        double d = axisX ? pos.z - (centre.getZ() + 0.5) : pos.x - (centre.getX() + 0.5);
        Direction normal = axisX ? Direction.SOUTH : Direction.EAST;
        return d >= 0 ? normal : normal.getOpposite();
    }

    /** spot 上下 3 格內最近的站立點（腳下實心、身體兩格是空的）。 */
    private static BlockPos standingSpot(ServerLevel level, BlockPos spot) {
        for (int dy : new int[]{0, 1, -1, 2, -2, 3, -3}) {
            BlockPos p = spot.above(dy);
            if (level.getBlockState(p).canBeReplaced() && level.getBlockState(p.above()).canBeReplaced()
                    && level.getBlockState(p.below()).isFaceSturdy(level, p.below(), Direction.UP)) {
                return p;
            }
        }
        return spot;
    }

    // ------------------------------------------------------------------ step 2: the Singer calls Echo Golems that set up the jukeboxes
    /** 迴音碎片右鍵儀式歌者。回傳是否有開始（或補完）擺放。 */
    public static boolean startRitual(SingerEntity singer, Player player) {
        if (!(singer.level() instanceof ServerLevel level)) {
            return false;
        }
        Plan plan = existingPlan(level, singer.blockPosition());
        List<BlockPos> todo;
        if (plan != null) {
            todo = plan.group().stream().filter(p -> !level.getBlockState(p).is(RitualBlocks.RESONANT_JUKEBOX)).toList();
            if (todo.isEmpty()) {
                tell(player, Component.translatable("message.pysift.ritual.already").withStyle(ChatFormatting.LIGHT_PURPLE));
                return false;
            }
        } else {
            plan = makePlan(level, singer, player);
            todo = plan.group();
        }
        if (!level.getEntitiesOfClass(EchoGolemEntity.class, new AABB(singer.blockPosition()).inflate(32), EchoGolemEntity::isRitualWorker).isEmpty()) {
            tell(player, Component.translatable("message.pysift.ritual.busy").withStyle(ChatFormatting.LIGHT_PURPLE));
            return false;
        }
        if (player != null) {
            singer.getLookControl().setLookAt(player, 60.0f, 60.0f);
        }
        // 先打掃：歌者揮手唱歌，音波由左到右把唱片盒一帶清乾淨；掃完再召喚傀儡
        singer.setAction(SingerEntity.ACTION_SWEEP);
        singer.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 2.0f, 1.2f);
        int sweepTicks = sweep(level, plan);
        Plan sweptPlan = plan;
        schedule(level, sweepTicks, () -> {
            if (singer.isAlive()) {
                singer.setAction(SingerEntity.ACTION_SUMMON);
                singer.playSound(SoundEvents.SCULK_SHRIEKER_SHRIEK, 1.5f, 1.4f);
                singer.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 2.0f, 0.8f);
                level.sendParticles(ParticleTypes.SCULK_SOUL, singer.getX(), singer.getY() + 0.2, singer.getZ(), 40, 2.0, 0.1, 2.0, 0.02);
            }
        });

        // 兩隻傀儡：前一半與後一半（唱片盒照「從左到右」的順序放，後面那隻會等前面的放好）
        List<BlockPos> ordered = plan.group().stream().filter(todo::contains).toList();
        int half = (ordered.size() + 1) / 2;
        List<List<BlockPos>> crews = List.of(new ArrayList<>(ordered.subList(0, half)), new ArrayList<>(ordered.subList(half, ordered.size())));
        Plan finalPlan = plan;
        int delay = sweepTicks + 20;   // 打掃完、等歌者的召喚動作舉起手
        for (List<BlockPos> jobs : crews) {
            if (jobs.isEmpty()) {
                continue;
            }
            BlockPos origin = jobs.getFirst().relative(towardsSinger(plan, singer), 2);
            schedule(level, delay, () -> spawnWorker(level, standingSpot(level, origin), jobs, finalPlan));
            delay += 10;
        }
        return true;
    }

    private static Direction towardsSinger(Plan plan, SingerEntity singer) {
        return sideOf(plan.axisX(), plan.portalCentre(), singer.position());
    }

    private static void spawnWorker(ServerLevel level, BlockPos at, List<BlockPos> jobs, Plan plan) {
        EchoGolemEntity golem = ModEntities.ECHO_GOLEM.create(level, EntitySpawnReason.TRIGGERED);
        if (golem == null) {
            return;
        }
        golem.snapTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, level.getRandom().nextFloat() * 360, 0);
        golem.startRitualWork(jobs, plan);
        level.addFreshEntity(golem);
    }

    /** 歌者附近已經有這次儀式的唱片盒（例如傀儡被卸載、或玩家打破了一個）：沿用原本的配置。 */
    private static Plan existingPlan(ServerLevel level, BlockPos near) {
        for (BlockPos p : BlockPos.betweenClosed(near.offset(-20, -8, -20), near.offset(20, 8, 20))) {
            if (level.getBlockEntity(p) instanceof ResonantJukeboxBlockEntity box && box.getPortalCentre() != null && !box.getGroup().isEmpty()) {
                return new Plan(box.getPortalCentre(), box.isAxisX(), box.isFrame(), box.getGroup());
            }
        }
        return null;
    }

    /**
     * 決定門的位置與 8 個唱片盒的位置：在歌者那一側、離門 4 格排成同一高度的一列，沿門的寬度方向每隔 2 格一個，
     * 順序是「站在歌者這一側看向門時，從左到右」。位置上有方塊擋住時，傀儡放置前會挖掉（見 {@link #placeJukebox}）。
     */
    private static Plan makePlan(ServerLevel level, SingerEntity singer, Player player) {
        Site site = singer.getRitualSite();
        if (site == null) {   // 舊存檔或指令召喚的歌者：現在才算
            site = computeSite(level, singer.blockPosition(), singer.position(), singer.getYRot() + 180);
            singer.setRitualSite(site);
        }
        Direction right = site.side().getOpposite().getClockWise();   // 面向門時的右手邊
        int rightSign = site.axisX() ? right.getStepX() : right.getStepZ();
        BlockPos middleSeat = site.onMiddle(site.rowDist(), site.floorY());
        List<BlockPos> seats = new ArrayList<>();
        for (int i = 0; i < SEATS; i++) {
            // 由左到右 8 個，以中心格左右對稱、間隔 2 格（中心格本身留給歌者那條線，不放唱片盒）
            int offset = (-7 + 2 * i) * rightSign;
            seats.add(site.axisX() ? middleSeat.offset(offset, 0, 0) : middleSeat.offset(0, 0, offset));
        }
        return new Plan(site.portalCentre(), site.axisX(), site.frame(), seats);
    }

    /** 傀儡放下唱片盒的那一刻。 */
    public static void placeJukebox(ServerLevel level, BlockPos pos, Plan plan) {
        clearSeat(level, pos);
        level.setBlock(pos, RitualBlocks.RESONANT_JUKEBOX.defaultBlockState(), net.minecraft.world.level.block.Block.UPDATE_ALL);
        if (level.getBlockEntity(pos) instanceof ResonantJukeboxBlockEntity box) {
            box.setup(plan.portalCentre(), plan.axisX(), plan.frame(), plan.group(), level.getGameTime());
        }
        level.playSound(null, pos, SoundEvents.WOOD_PLACE, SoundSource.BLOCKS, 1.2f, 0.8f);
        level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.5f, 1.2f);
        level.sendParticles(ParticleTypes.SCULK_SOUL, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 12, 0.4, 0.3, 0.4, 0.02);
        level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, pos.getX() + 0.5, pos.getY() + 0.1, pos.getZ() + 0.5, 16, 0.6, 0.05, 0.6, 0.02);
    }

    /**
     * 歌者打掃唱片盒那一帶：沿著那一排、左右各多 2 格、前後各 1 格（共 3 排）、地面以上 4 格內的方塊都清掉（照常掉落），
     * 地面有洞就補深板岩磚。一欄一欄由左到右進行，每欄有音波粒子與聲音。回傳打掃要花的 tick 數。
     */
    private static int sweep(ServerLevel level, Plan plan) {
        List<BlockPos> seats = plan.group();
        if (seats.size() < 2) {
            return 0;
        }
        BlockPos first = seats.getFirst(), last = seats.getLast();
        Direction right = Direction.getApproximateNearest(last.getX() - first.getX(), 0, last.getZ() - first.getZ());
        Direction depth = right.getClockWise();
        int width = (int) Math.round(Math.sqrt(first.distSqr(last)));
        int step = 0;
        for (int a = -2; a <= width + 2; a++, step++) {
            BlockPos column = first.relative(right, a);
            schedule(level, 2 + step * 2, () -> {
                for (int d = -1; d <= 1; d++) {
                    BlockPos base = column.relative(depth, d);
                    for (int dy = 0; dy <= 3; dy++) {
                        BlockPos p = base.above(dy);
                        BlockState s = level.getBlockState(p);
                        if (!s.isAir() && s.getDestroySpeed(level, p) >= 0 && !s.is(ModBlocks.SIFT_PORTAL) && !s.is(RitualBlocks.RESONANT_JUKEBOX)) {
                            quietBreak(level, p);
                        }
                    }
                    BlockPos below = base.below();
                    if (level.getBlockState(below).canBeReplaced()) {
                        level.setBlock(below, Blocks.DEEPSLATE_TILES.defaultBlockState(), net.minecraft.world.level.block.Block.UPDATE_ALL);
                    }
                }
                level.sendParticles(ParticleTypes.SONIC_BOOM, column.getX() + 0.5, column.getY() + 1.0, column.getZ() + 0.5, 1, 0, 0, 0, 0);
                level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, column.getX() + 0.5, column.getY() + 0.1, column.getZ() + 0.5, 6, 0.4, 0.05, 1.2, 0.02);
                level.playSound(null, column, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 0.8f, 0.8f + level.getRandom().nextFloat() * 0.6f);
            });
        }
        return 2 + step * 2 + 10;
    }

    /** 唱片盒的位置與上方 3 格有方塊就挖掉（照常掉落）；腳下是空的就補一塊深板岩磚。強化深板岩、傳送門與其他唱片盒不動。 */
    private static void clearSeat(ServerLevel level, BlockPos pos) {
        for (int dy = 0; dy <= 3; dy++) {
            BlockPos p = pos.above(dy);
            BlockState s = level.getBlockState(p);
            if (s.isAir() || s.getDestroySpeed(level, p) < 0 || s.is(ModBlocks.SIFT_PORTAL) || s.is(RitualBlocks.RESONANT_JUKEBOX)) {
                continue;
            }
            quietBreak(level, p);
        }
        BlockPos below = pos.below();
        if (!level.getBlockState(below).isFaceSturdy(level, below, Direction.UP)
                && level.getBlockState(below).getDestroySpeed(level, below) >= 0) {
            level.setBlock(below, Blocks.DEEPSLATE_BRICKS.defaultBlockState(), net.minecraft.world.level.block.Block.UPDATE_ALL);
        }
    }

    /** 打掉方塊並照常掉落，但不發出震動（幽匿感測器聽不到，不會引來伏守者）。 */
    private static void quietBreak(ServerLevel level, BlockPos p) {
        BlockState s = level.getBlockState(p);
        net.minecraft.world.level.block.Block.dropResources(s, level, p, level.getBlockEntity(p));
        level.levelEvent(2001, p, net.minecraft.world.level.block.Block.getId(s));   // 破壞粒子與聲音
        level.setBlock(p, Blocks.AIR.defaultBlockState(), net.minecraft.world.level.block.Block.UPDATE_ALL);
    }

    /** 這個位置之前（左邊）的唱片盒是不是都放好了；後面那隻傀儡要等。 */
    public static boolean previousSeatsReady(ServerLevel level, Plan plan, BlockPos seat) {
        for (BlockPos p : plan.group()) {
            if (p.equals(seat)) {
                return true;
            }
            if (!level.getBlockState(p).is(RitualBlocks.RESONANT_JUKEBOX)) {
                return false;
            }
        }
        return true;
    }

    // ------------------------------------------------------------------ step 3: discs
    private static List<ResonantJukeboxBlockEntity> boxes(ServerLevel level, ResonantJukeboxBlockEntity box) {
        List<ResonantJukeboxBlockEntity> out = new ArrayList<>();
        for (BlockPos p : box.getGroup()) {
            if (level.getBlockEntity(p) instanceof ResonantJukeboxBlockEntity other) {
                out.add(other);
            }
        }
        return out;
    }

    /** 同一組裡已經有人放了這張唱片。 */
    public static boolean discUsed(ServerLevel level, ResonantJukeboxBlockEntity box, RitualDiscs.Disc disc) {
        for (ResonantJukeboxBlockEntity other : boxes(level, box)) {
            if (other.getRitualDisc() == disc) {
                return true;
            }
        }
        return false;
    }

    public static void onDiscInserted(ServerLevel level, ResonantJukeboxBlockEntity box, Player player) {
        List<ResonantJukeboxBlockEntity> all = boxes(level, box);
        long filled = all.stream().filter(b -> b.getRitualDisc() != null).count();
        if (all.size() < box.getGroup().size() || filled < box.getGroup().size()) {
            tell(player, Component.translatable("message.pysift.ritual.progress", filled, box.getGroup().size())
                    .withStyle(ChatFormatting.LIGHT_PURPLE));
            return;
        }
        finale(level, box, all);
    }

    // ------------------------------------------------------------------ step 4: finale, the portal opens (or tears)
    private static void finale(ServerLevel level, ResonantJukeboxBlockEntity anyBox, List<ResonantJukeboxBlockEntity> all) {
        BlockPos centre = anyBox.getPortalCentre();
        if (centre == null) {
            return;
        }
        // 由左到右照座位奏出來：全部放對時剛好是 C 大調音階往上走
        List<ResonantJukeboxBlockEntity> melody = new ArrayList<>(all);
        melody.sort(Comparator.comparingInt(ResonantJukeboxBlockEntity::seatIndex));
        boolean discord = melody.stream().anyMatch(b -> b.getRitualDisc() != b.expectedDisc());
        List<SingerEntity> singers = level.getEntitiesOfClass(SingerEntity.class, new AABB(centre).inflate(32));
        for (SingerEntity singer : singers) {
            singer.getLookControl().setLookAt(Vec3.atCenterOf(centre));
            singer.setAction(SingerEntity.ACTION_FINALE);
            singer.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 2.0f, 1.0f);
        }
        for (int i = 0; i < melody.size(); i++) {
            ResonantJukeboxBlockEntity box = melody.get(i);
            schedule(level, 10 + i * FINALE_STEP, () -> {
                if (box.isRemoved() || box.getRitualDisc() == null) {
                    return;
                }
                RitualDiscs.Disc disc = box.getRitualDisc();
                boolean wrong = disc != box.expectedDisc();
                float pitch = wrong ? disc.pitch() * 0.94f : disc.pitch();   // 放錯的那一格走調（約低一個半音）
                BlockPos p = box.getBlockPos();
                box.flash(level.getGameTime());
                level.playSound(null, p, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.RECORDS, 3.0f, pitch);
                level.playSound(null, p, SoundEvents.NOTE_BLOCK_HARP.value(), SoundSource.RECORDS, 2.0f, pitch);
                level.sendParticles(new DustParticleOptions(disc.color() & 0xFFFFFF, 2.0f), p.getX() + 0.5, p.getY() + 3, p.getZ() + 0.5,
                        30, 0.2, 2.5, 0.2, 0.0);
                if (wrong) {
                    glitch(level, centre, p);
                }
                for (SingerEntity singer : singers) {   // 歌者跟著唱同一個音
                    if (singer.isAlive()) {
                        singer.humNote(pitch);
                    }
                }
            });
        }
        int after = 10 + melody.size() * FINALE_STEP + 14;
        if (discord) {
            schedule(level, after, () -> tearOpen(level, anyBox, melody, singers));
        } else {
            schedule(level, after, () -> openPortal(level, anyBox, melody));
        }
    }

    /** 走調的那一下：附近的玩家眼前一黑、晃一下，監守者在遠處躁動，尖嘯體的聲波從唱片盒冒出來。 */
    private static void glitch(ServerLevel level, BlockPos centre, BlockPos box) {
        level.playSound(null, box, SoundEvents.WARDEN_AGITATED, SoundSource.HOSTILE, 2.0f, 0.6f);
        level.playSound(null, box, SoundEvents.SCULK_SHRIEKER_SHRIEK, SoundSource.BLOCKS, 1.5f, 0.7f);
        level.sendParticles(new net.minecraft.core.particles.ShriekParticleOption(0), box.getX() + 0.5, box.getY() + 1.1, box.getZ() + 0.5,
                1, 0, 0, 0, 0);
        for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, new AABB(centre).inflate(32))) {
            player.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.DARKNESS, 50, 0, false, false));
            player.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.NAUSEA, 60, 0, false, false));
        }
    }

    /** 走調的八音：門被撕開、閃爍，深色幽匿爆開，歌者倒著唱把門闔上，唱片全部彈出來。 */
    private static final int TEAR_FLICKERS = 3;
    private static final int MOURN_STEP = 9;

    private static void tearOpen(ServerLevel level, ResonantJukeboxBlockEntity anyBox, List<ResonantJukeboxBlockEntity> melody,
                                 List<SingerEntity> singers) {
        BlockPos centre = anyBox.getPortalCentre();
        if (melody.stream().anyMatch(b -> b.isRemoved() || b.getRitualDisc() == null) || SiftPortalBlock.hasPortalNear(level, centre)) {
            return;
        }
        Direction.Axis axis = anyBox.isAxisX() ? Direction.Axis.X : Direction.Axis.Z;
        // 1. 撕裂：門閃開又熄滅幾次（每次只開 4 tick，進不去）
        level.playSound(null, centre, SoundEvents.WARDEN_ROAR, SoundSource.HOSTILE, 3.0f, 0.5f);
        level.playSound(null, centre, SoundEvents.PORTAL_TRIGGER, SoundSource.BLOCKS, 2.0f, 0.6f);
        for (int i = 0; i < TEAR_FLICKERS; i++) {
            schedule(level, i * 12, () -> {
                fillDoor(level, anyBox, centre, axis);
                level.sendParticles(ParticleTypes.SONIC_BOOM, centre.getX() + 0.5, centre.getY() + 0.5, centre.getZ() + 0.5, 1, 0, 0, 0, 0);
            });
            schedule(level, i * 12 + 4, () -> clearDoor(level, centre));
        }
        // 2. 深色幽匿從門前爆開
        schedule(level, TEAR_FLICKERS * 12, () -> sculkBurst(level, centre, melody));
        // 3. 歌者倒著唱（哀悼者的歌）：右到左、低八度的笛聲，底下墊著監守者的心跳
        int mournStart = TEAR_FLICKERS * 12 + 40;   // 等幽匿長得差不多（sculkBurst 約 50 tick）
        for (int i = 0; i < melody.size(); i++) {
            ResonantJukeboxBlockEntity box = melody.get(melody.size() - 1 - i);
            schedule(level, mournStart + i * MOURN_STEP, () -> {
                RitualDiscs.Disc disc = box.expectedDisc();
                if (disc == null || box.isRemoved()) {
                    return;
                }
                float pitch = Math.max(0.5f, disc.pitch() * 0.5f);
                BlockPos p = box.getBlockPos();
                level.playSound(null, p, SoundEvents.NOTE_BLOCK_FLUTE.value(), SoundSource.RECORDS, 2.5f, pitch);
                level.playSound(null, centre, SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 1.5f, 0.8f);
                level.sendParticles(ParticleTypes.SCULK_SOUL, p.getX() + 0.5, p.getY() + 1.5, p.getZ() + 0.5, 3, 0.2, 0.3, 0.2, 0.02);
                for (SingerEntity singer : singers) {
                    if (singer.isAlive()) {
                        singer.humNote(pitch);
                    }
                }
            });
        }
        // 4. 門闔上，唱片全部彈出來
        schedule(level, mournStart + melody.size() * MOURN_STEP + 10, () -> {
            level.playSound(null, centre, SoundEvents.BEACON_DEACTIVATE, SoundSource.BLOCKS, 3.0f, 0.6f);
            for (ResonantJukeboxBlockEntity box : melody) {
                if (!box.isRemoved()) {
                    box.ejectDisc();
                }
            }
            for (SingerEntity singer : singers) {
                if (singer.isAlive() && singer.isRitual()) {
                    singer.setAction(SingerEntity.ACTION_AWAIT);
                }
            }
            for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, new AABB(centre).inflate(32))) {
                player.sendSystemMessage(Component.translatable("message.pysift.ritual.discord").withStyle(ChatFormatting.DARK_AQUA));
            }
        });
    }

    /**
     * 清掉儀式開的門：門中心水平 13 格、上下 8 格內所有傳送門方塊（遠古城市的門框內寬將近 20 格）。裂隙門的形狀不規則，
     * 角落的幾格不一定和主體相連，只清相連的那一片（SiftPortalBlock.clearPortal）會留下殘塊，之後再開門時會被當成「門已經開著」。
     */
    private static int clearDoor(ServerLevel level, BlockPos centre) {
        int cleared = 0;
        for (BlockPos p : BlockPos.betweenClosed(centre.offset(-13, -8, -13), centre.offset(13, 8, 13))) {
            if (level.getBlockState(p).is(ModBlocks.SIFT_PORTAL)) {
                level.setBlock(p, Blocks.AIR.defaultBlockState(), net.minecraft.world.level.block.Block.UPDATE_ALL);
                cleared++;
            }
        }
        return cleared;
    }

    /** 填出（之後會被清掉的）門：有強化深板岩框架就填框架，沒有就開裂隙門。 */
    private static void fillDoor(ServerLevel level, ResonantJukeboxBlockEntity anyBox, BlockPos centre, Direction.Axis axis) {
        SiftPortalBlock.Frame frame = anyBox.isFrame() ? SiftPortalBlock.findFrame(level, centre, 12, Blocks.REINFORCED_DEEPSLATE) : null;
        if (frame != null) {
            SiftPortalBlock.fillFrame(level, frame);
        } else {
            SiftPortalBlock.buildRiftPortal(level, centre.below(), axis);
        }
    }

    /**
     * 門前地面爆出一片深色幽匿（遠古城市那次災難的重演），以唱片盒那一排的正中間為中心：
     * <ol>
     *   <li>中心先一聲音爆，靈魂從地面湧出；</li>
     *   <li>幽匿一圈一圈往外長（每圈隔 BURST_RING_TICKS），每一格被吞掉時噴出原本方塊的碎屑與幽匿電荷，
     *       每一圈地面上都有一道往外推的靈魂波紋；越外圈長得越稀；</li>
     *   <li>最後幾條幽匿觸手隨機往外再爬一段。</li>
     * </ol>
     * 只長在露天的地面上（整塊、半磚、階梯都會變成幽匿塊），不碰方塊實體、強化深板岩與無法破壞的方塊。
     */
    private static final int BURST_RADIUS = 8;
    private static final int BURST_RING_TICKS = 3;
    private static final int BURST_TENDRILS = 5;

    private static void sculkBurst(ServerLevel level, BlockPos portalCentre, List<ResonantJukeboxBlockEntity> row) {
        net.minecraft.util.RandomSource random = level.getRandom();
        BlockPos mid = row.get(row.size() / 2).getBlockPos();
        if (row.size() % 2 == 0) {   // 偶數個：取中間兩個的中點
            BlockPos other = row.get(row.size() / 2 - 1).getBlockPos();
            mid = new BlockPos((mid.getX() + other.getX()) / 2, mid.getY(), (mid.getZ() + other.getZ()) / 2);
        }
        BlockPos centre = mid;
        double cx = centre.getX() + 0.5, cz = centre.getZ() + 0.5;
        // 1. 音爆與湧出的靈魂
        level.playSound(null, portalCentre, SoundEvents.SCULK_CATALYST_BLOOM, SoundSource.BLOCKS, 3.0f, 0.6f);
        level.playSound(null, centre, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 1.5f, 0.6f);
        level.sendParticles(ParticleTypes.SONIC_BOOM, cx, centre.getY() + 0.5, cz, 1, 0, 0, 0, 0);
        level.sendParticles(ParticleTypes.SCULK_SOUL, cx, centre.getY() + 0.3, cz, 40, 1.2, 0.2, 1.2, 0.08);
        // 2. 一圈一圈往外長
        for (int ring = 0; ring <= BURST_RADIUS; ring++) {
            int r = ring;
            schedule(level, ring * BURST_RING_TICKS, () -> {
                level.playSound(null, centre, SoundEvents.SCULK_BLOCK_SPREAD, SoundSource.BLOCKS, 2.0f, 0.7f + r * 0.04f);
                for (int i = 0, n = 6 + r * 6; i < n; i++) {   // 地面上往外推的靈魂波紋
                    double a = Math.PI * 2 * i / n;
                    level.sendParticles(ParticleTypes.SCULK_SOUL, cx + Math.cos(a) * r, centre.getY() + 0.2, cz + Math.sin(a) * r,
                            1, 0.1, 0.05, 0.1, 0.01);
                }
                for (int dx = -r; dx <= r; dx++) {
                    for (int dz = -r; dz <= r; dz++) {
                        double d = Math.sqrt(dx * dx + dz * dz);
                        if ((int) Math.round(d) != r || random.nextDouble() < d / (BURST_RADIUS + 1.5)) {
                            continue;   // 只處理這一圈；越外圈越稀
                        }
                        consume(level, centre.offset(dx, 0, dz), random);
                    }
                }
            });
        }
        // 3. 幾條觸手往外再爬一段
        for (int t = 0; t < BURST_TENDRILS; t++) {
            double a = random.nextDouble() * Math.PI * 2;
            int length = 4 + random.nextInt(5);
            for (int step = 0; step < length; step++) {
                double reach = BURST_RADIUS - 1 + step;
                a += (random.nextDouble() - 0.5) * 0.5;   // 彎彎曲曲
                BlockPos column = BlockPos.containing(cx + Math.cos(a) * reach, centre.getY(), cz + Math.sin(a) * reach);
                schedule(level, (BURST_RADIUS + step) * BURST_RING_TICKS + 2, () -> consume(level, column, random));
            }
        }
    }

    /** 把 column 這一直排最上面的露天地面吞成幽匿，噴出碎屑與幽匿電荷。 */
    private static void consume(ServerLevel level, BlockPos column, net.minecraft.util.RandomSource random) {
        for (int dy = 4; dy >= -6; dy--) {
            BlockPos p = column.above(dy);
            BlockState state = level.getBlockState(p);
            if (state.getCollisionShape(level, p).isEmpty() || !level.getBlockState(p.above()).getCollisionShape(level, p.above()).isEmpty()) {
                continue;   // 找最上面那一格有碰撞、上面空著（或只有草、地毯）的地面
            }
            if (!state.hasBlockEntity() && state.getDestroySpeed(level, p) >= 0 && !state.is(Blocks.REINFORCED_DEEPSLATE)
                    && !state.is(ModBlocks.SIFT_PORTAL) && !state.is(Blocks.SCULK)) {
                level.levelEvent(2001, p, net.minecraft.world.level.block.Block.getId(state));   // 原本方塊的碎屑
                level.setBlock(p, Blocks.SCULK.defaultBlockState(), net.minecraft.world.level.block.Block.UPDATE_ALL);
                level.sendParticles(new net.minecraft.core.particles.SculkChargeParticleOptions(random.nextFloat() * 6.28f),
                        p.getX() + 0.5, p.getY() + 1.05, p.getZ() + 0.5, 3, 0.3, 0.02, 0.3, 0.0);
                level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, p.getX() + 0.5, p.getY() + 1.1, p.getZ() + 0.5, 2, 0.25, 0.1, 0.25, 0.02);
                if (random.nextInt(4) == 0) {
                    level.sendParticles(ParticleTypes.SCULK_SOUL, p.getX() + 0.5, p.getY() + 1.1, p.getZ() + 0.5, 1, 0.1, 0.1, 0.1, 0.03);
                }
            }
            return;
        }
    }

    private static void openPortal(ServerLevel level, ResonantJukeboxBlockEntity anyBox, List<ResonantJukeboxBlockEntity> scale) {
        BlockPos centre = anyBox.getPortalCentre();
        if (scale.stream().anyMatch(b -> b.isRemoved() || b.getRitualDisc() == null)) {
            return;   // 終曲途中有唱片盒被打破
        }
        if (SiftPortalBlock.hasPortalNear(level, centre)) {
            return;   // 已經開過了
        }
        Direction.Axis axis = anyBox.isAxisX() ? Direction.Axis.X : Direction.Axis.Z;
        SiftPortalBlock.Frame frame = anyBox.isFrame() ? SiftPortalBlock.findFrame(level, centre, 12, Blocks.REINFORCED_DEEPSLATE) : null;
        if (frame != null) {
            SiftPortalBlock.fillFrame(level, frame);
        } else {
            SiftPortalBlock.buildRiftPortal(level, centre.below(), axis);
        }
        Vec3 target = Vec3.atCenterOf(centre);
        for (ResonantJukeboxBlockEntity box : scale) {   // 8 道光匯聚到門中心
            Vec3 from = Vec3.atCenterOf(box.getBlockPos()).add(0, 4, 0);
            Vec3 step = target.subtract(from);
            int n = Math.max(6, (int) (step.length() * 2));
            DustParticleOptions dust = new DustParticleOptions(box.getRitualDisc().color() & 0xFFFFFF, 1.6f);
            for (int i = 0; i <= n; i++) {
                Vec3 p = from.add(step.scale(i / (double) n));
                level.sendParticles(dust, p.x, p.y, p.z, 2, 0.05, 0.05, 0.05, 0);
            }
        }
        level.sendParticles(ParticleTypes.END_ROD, target.x, target.y, target.z, 80, 1.5, 1.5, 1.5, 0.08);
        level.playSound(null, centre, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.BLOCKS, 2.0f, 1.2f);
        level.playSound(null, centre, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 3.0f, 1.0f);
        // 歌者的任務完成：先慶祝（跳起來轉圈、哼小號角），播完自己揮手道別、鑽回地底離開
        for (SingerEntity singer : level.getEntitiesOfClass(SingerEntity.class, new AABB(centre).inflate(32), SingerEntity::isRitual)) {
            singer.celebrate();
        }
        AdvancementHolder adv = level.getServer().getAdvancements().get(PySift.id("progression/eight_songs"));
        for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, new AABB(centre).inflate(32))) {
            player.sendSystemMessage(Component.translatable("message.pysift.ritual.opened").withStyle(ChatFormatting.LIGHT_PURPLE));
            if (adv != null) {
                player.getAdvancements().award(adv, "opened");
            }
        }
    }

    // ------------------------------------------------------------------ step 5: a jukebox is the key
    public static void onJukeboxRemoved(ServerLevel level, ResonantJukeboxBlockEntity box) {
        BlockPos centre = box.getPortalCentre();
        if (centre == null || !level.isLoaded(centre)) {
            return;
        }
        if (clearDoor(level, centre) > 0) {
            level.playSound(null, centre, SoundEvents.BEACON_DEACTIVATE, SoundSource.BLOCKS, 3.0f, 0.8f);
            for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, new AABB(centre).inflate(32))) {
                player.sendSystemMessage(Component.translatable("message.pysift.ritual.closed").withStyle(ChatFormatting.LIGHT_PURPLE));
            }
        }
    }

    /** 對玩家顯示快捷欄上方的訊息（測試指令沒有玩家時略過）。 */
    private static void tell(Player player, Component message) {
        if (player != null) {
            player.sendOverlayMessage(message);
        }
    }

    // ------------------------------------------------------------------ dev command: /pysift_ritual start | fill
    private static void registerCommand() {
        net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback.EVENT.register((dispatcher, registries, environment) ->
                dispatcher.register(net.minecraft.commands.Commands.literal("pysift_ritual")
                        .requires(net.minecraft.commands.Commands.hasPermission(net.minecraft.commands.Commands.LEVEL_GAMEMASTERS))
                        .then(net.minecraft.commands.Commands.literal("mouth").executes(ctx -> {
                            ServerLevel level = ctx.getSource().getLevel();
                            float yaw = ctx.getSource().getRotation().y;
                            Direction facing = Direction.fromYRot(yaw);
                            Direction.Axis axis = facing.getAxis() == Direction.Axis.Z ? Direction.Axis.X : Direction.Axis.Z;
                            BlockPos base = BlockPos.containing(ctx.getSource().getPosition()).relative(facing, 6);
                            if (!SiftPortalBlock.buildArrivalPortal(level, base, axis)) {
                                SiftPortalBlock.buildMouthFrame(level, base, axis);
                            }
                            return 1;
                        }))
                        .then(net.minecraft.commands.Commands.literal("landing").executes(ctx -> {
                            // 跟穿過傳送門一樣：在這裡找落點、蓋回程門，回報落點能不能站
                            ServerLevel level = ctx.getSource().getLevel();
                            BlockPos at = BlockPos.containing(ctx.getSource().getPosition());
                            BlockPos landing = SiftPortalBlock.prepareLanding(level, at.getX(), at.getZ());
                            boolean safe = SiftPortalBlock.isSafeLanding(level, landing);
                            ctx.getSource().sendSuccess(() -> Component.literal("landing " + landing.toShortString() + " safe=" + safe), false);
                            return safe ? 1 : 0;
                        }))
                        .then(net.minecraft.commands.Commands.literal("summon").executes(ctx -> {
                            ServerLevel level = ctx.getSource().getLevel();
                            Vec3 at = ctx.getSource().getPosition();
                            SingerEntity singer = summonAt(level, BlockPos.containing(at), at, ctx.getSource().getRotation().y);
                            if (singer == null) {
                                return 0;
                            }
                            Site site = singer.getRitualSite();
                            ctx.getSource().sendSuccess(() -> Component.literal("singer at " + singer.position() + " site " + site), false);
                            return 1;
                        }))
                        .then(net.minecraft.commands.Commands.literal("start").executes(ctx -> {
                            ServerLevel level = ctx.getSource().getLevel();
                            Vec3 at = ctx.getSource().getPosition();
                            List<SingerEntity> singers = level.getEntitiesOfClass(SingerEntity.class, new AABB(BlockPos.containing(at)).inflate(32),
                                    SingerEntity::isRitual);
                            if (singers.isEmpty()) {
                                ctx.getSource().sendFailure(Component.literal("No ritual Singer within 32 blocks"));
                                return 0;
                            }
                            boolean ok = startRitual(singers.getFirst(), null);
                            ctx.getSource().sendSuccess(() -> Component.literal("ritual start: " + ok), false);
                            return ok ? 1 : 0;
                        }))
                        .then(net.minecraft.commands.Commands.literal("fill")
                                .executes(ctx -> fill(ctx.getSource(), false))
                                .then(net.minecraft.commands.Commands.literal("wrong").executes(ctx -> fill(ctx.getSource(), true))))));
    }

    /** /pysift_ritual fill [wrong]：把附近的唱片盒放滿；wrong 會把第 3、4 張對調（測試走調的八音）。 */
    private static int fill(net.minecraft.commands.CommandSourceStack source, boolean wrong) {
        ServerLevel level = source.getLevel();
        Plan plan = existingPlan(level, BlockPos.containing(source.getPosition()));
        if (plan == null) {
            source.sendFailure(Component.literal("No Resonant Jukeboxes nearby"));
            return 0;
        }
        int i = 0;
        ResonantJukeboxBlockEntity last = null;
        for (BlockPos p : plan.group()) {
            if (level.getBlockEntity(p) instanceof ResonantJukeboxBlockEntity box && box.expectedDisc() != null) {
                int seat = box.seatIndex();
                int use = wrong && (seat == 2 || seat == 3) ? 5 - seat : seat;
                box.setDisc(new ItemStack(RitualDiscs.forSeat(use).item()));
                last = box;
                i++;
            }
        }
        if (last != null) {
            onDiscInserted(level, last, null);
        }
        int filled = i;
        source.sendSuccess(() -> Component.literal("filled " + filled + " jukeboxes" + (wrong ? " (two swapped)" : "")), false);
        return filled;
    }

    static boolean inSift(Level level) {
        return level.dimension().equals(SiftPortalBlock.SIFT_DIM);
    }
}
