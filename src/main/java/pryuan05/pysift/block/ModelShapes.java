package pryuan05.pysift.block;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.phys.shapes.BooleanOp;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import pryuan05.pysift.PySift;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * VoxelShapes that follow the block models: assets/pysift/block_shapes.json (written by
 * tools/models/build_block_shapes.py from the blockstates and models) lists, per block and blockstate variant, the
 * boxes of the model in pixels. {@link pryuan05.pysift.mixin.ModelShapeMixin} returns them from BlockState.getShape:
 * the outline, the collision of blocks that have collision, and the occlusion all follow what is drawn.
 * <p>
 * Shapes are built per block on its first query and cached. Vanilla asks for shapes while it bootstraps, before any
 * pysift block exists, so a block is only cached once it is registered (an unregistered block reports the air key).
 * A variant key ("facing=north,powered=false", or "" for every state) matches a state when every property it names has
 * that value, like vanilla blockstate files.
 */
public final class ModelShapes {
    private static final JsonObject RAW = read();
    private static final Map<Block, Map<BlockState, VoxelShape>> CACHE = new ConcurrentHashMap<>();
    private static final Map<BlockState, VoxelShape> NONE = Map.of();

    private ModelShapes() {
    }

    private static JsonObject read() {
        try (InputStream in = ModelShapes.class.getResourceAsStream("/assets/pysift/block_shapes.json")) {
            if (in != null) {
                return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            }
        } catch (Exception e) {
            PySift.LOGGER.error("cannot read pysift block_shapes.json", e);
        }
        return new JsonObject();
    }

    /** The model shape of this state, or null when the block keeps its own shape. */
    public static VoxelShape get(BlockState state) {
        Block block = state.getBlock();
        Map<BlockState, VoxelShape> map = CACHE.get(block);
        if (map == null) {
            map = forBlock(block);
            if (map == null) {
                return null;                 // not registered yet: ask again later
            }
            CACHE.put(block, map);
        }
        return map.get(state);
    }

    private static Map<BlockState, VoxelShape> forBlock(Block block) {
        Identifier id = BuiltInRegistries.BLOCK.getKey(block);
        if (block != Blocks.AIR && id.equals(BuiltInRegistries.BLOCK.getKey(Blocks.AIR))) {
            return null;
        }
        if (!PySift.MOD_ID.equals(id.getNamespace()) || !RAW.has(id.getPath())) {
            return NONE;
        }
        JsonObject data = RAW.getAsJsonObject(id.getPath());
        Map<String, VoxelShape> variants = new HashMap<>();
        for (String key : data.keySet()) {
            variants.put(key, shape(data.getAsJsonArray(key)));
        }
        Map<BlockState, VoxelShape> out = new IdentityHashMap<>();
        for (BlockState state : block.getStateDefinition().getPossibleStates()) {
            for (Map.Entry<String, VoxelShape> v : variants.entrySet()) {
                if (matches(state, v.getKey())) {
                    out.put(state, v.getValue());
                    break;
                }
            }
        }
        return out;
    }

    private static VoxelShape shape(JsonArray boxes) {
        VoxelShape s = Shapes.empty();
        for (JsonElement el : boxes) {
            JsonArray b = el.getAsJsonArray();
            s = Shapes.joinUnoptimized(s, Block.box(b.get(0).getAsDouble(), b.get(1).getAsDouble(), b.get(2).getAsDouble(),
                    b.get(3).getAsDouble(), b.get(4).getAsDouble(), b.get(5).getAsDouble()), BooleanOp.OR);
        }
        return s.optimize();
    }

    private static boolean matches(BlockState state, String key) {
        if (key.isEmpty()) {
            return true;
        }
        for (String part : key.split(",")) {
            String[] kv = part.split("=", 2);
            Property<?> prop = state.getBlock().getStateDefinition().getProperty(kv[0]);
            if (prop == null || !value(state, prop).equals(kv[1])) {
                return false;
            }
        }
        return true;
    }

    private static <T extends Comparable<T>> String value(BlockState state, Property<T> prop) {
        return prop.getName(state.getValue(prop));
    }
}
