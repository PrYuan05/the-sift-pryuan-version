package pryuan05.pysift.client.render;

import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;

/** SiftPortalBlockEntityRenderer 的渲染狀態：完整方塊六面鄰格判斷、世界座標、時間與種子。 */
public class SiftPortalRenderState extends BlockEntityRenderState {
    public int worldX;
    public int worldY;
    public int worldZ;
    public float time;
    public boolean faceUp, faceDown, faceNorth, faceSouth, faceWest, faceEast;
    public long seed;
    /** 0 = 白天，1 = 深夜（SiftDayPhase）。 */
    public float night;
}
