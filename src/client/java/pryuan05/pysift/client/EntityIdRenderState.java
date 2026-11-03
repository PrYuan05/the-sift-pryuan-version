package pryuan05.pysift.client;

/** 加在 EntityRenderState 上（EntityRenderStateMixin）：這個 render state 是哪個實體的（WeaponPoses 用來找衝刺、揮擊次數）。 */
public interface EntityIdRenderState {
    int pysift$entityId();

    void pysift$setEntityId(int id);
}
