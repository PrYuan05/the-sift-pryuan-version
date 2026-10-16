package pryuan05.pysift.client.render;

import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.core.Direction;

/** SiftPortalBlockEntityRenderer 的渲染狀態：軸向、世界座標、時間，以及四個方向是否緊鄰邊框。 */
public class SiftPortalRenderState extends BlockEntityRenderState {
    public Direction.Axis axis = Direction.Axis.X;
    public int horiz;        // 沿門面水平方向的世界座標（X 軸門用 x，Z 軸門用 z）
    public int worldY;
    public float time;       // (gameTime + partialTick) * 0.003
    public boolean edgeUp, edgeDown, edgeMinus, edgePlus;   // 該方向的鄰格不是傳送門（緊鄰邊框）
    public long seed;
}
