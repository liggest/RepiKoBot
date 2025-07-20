#import "../base/md_base.typ": render-md, maybe-image-md
#import "../base/chat_base.typ": md-init, brighter-block-quote, system-init, reasoning-init, system-block, user-block, reasoning-block, assistant-block, tool-result-block, text-avatar, messages

#{
  set page(width: auto, height: auto, margin: 8pt)

  let content_data = sys.inputs.at("content", default: "[]")
  let content_type = sys.inputs.at("content_type", default: "str")

  if content_type == "file" {
    content_data = json(content_data)
  }

  if type(content_data) == str {
    content_data = json(bytes(content_data))
  }
  
  messages(content_data)

  // messages(
  //   json(bytes(```
  //   [
  //     {
  //       "role": "user",
  //       "content": "解码语者的效果是？\n123\n456"
  //     },
  //     {
  //       "role": "assistant",
  //       "content": "解码语者是《游戏王》中的连接怪兽，以下是其效果解析：\n\n【基础信息】\n电子界族/暗属性/LINK-3\n箭头方向：左上、上、右上\n连接素材：效果怪兽2只以上\n攻击力：2300\n\n【核心效果】\n①攻击强化：每存在1只连接区怪兽，攻击力提升500（如连接3只则提升至2300+1500=3800）\n\n②效果反制：\n- 触发条件：对方发动以我方场上卡为对象的效果（魔法/陷阱/怪兽）\n- 代价：解放1只连接区自身怪兽\n- 效果：无效并破坏对方发动的效果\n\n这张卡适合在电子界卡组中作为攻守兼备的终端，既能通过连接召唤灵活出场，又能有效干扰对手的指定型效果，是电子界卡组的重要干扰手段。"
  //     }
  //   ]```.text))
  // )
}
