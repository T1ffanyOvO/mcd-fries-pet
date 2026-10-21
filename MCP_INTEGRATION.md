# MCP 集成说明（MCP_INTEGRATION.md）

本项目**真实使用**麦当劳官方 MCP（`mcd-mcp`）能力，把实时菜单 / 营养 / 门店 / 优惠数据，通过桌面宠物「麦薯条」用气泡播报出来。

## 一、使用的麦当劳 MCP

- **Server**：`mcd-mcp`（远程托管，Streamable HTTP）
- **端点**：`https://mcp.mcd.cn`
- **接入方式**：在 WorkBuddy 连接器配置中填入 Token（见 `mcp-config.example.json`），由 WorkBuddy 加载 MCP 工具后调用。
- **鉴权要点（作者环境实测）**：当前配置示例包含 `Authorization` 与 `authToken` 两个请求头。鉴权行为可能变化，请以官方 MCP 指南和实际响应为准；发生 401/403 时检查 Token 和连接器配置。

## 二、实际调用的 Tool 与用途

| Tool | 入参 | 用途 |
|---|---|---|
| `now-time-info` | 无 | 判断早餐 / 正餐时段，避免用晚餐菜单推荐早晨 |
| `list-nutrition-foods` | 无 | 拉取约 160 个餐品的营养表（能量/蛋白/脂肪/碳水/钠），是算热量的主力工具 |
| `query-meals` | `beType`（1 到店 / 2 外送 / 5 得来速 / 6 团餐），外送/得来速/团餐需门店编码 | 获取在售菜单、分类、餐品编码、标签 |
| `query-nearby-stores` | 到店场景 | 获取附近可自取门店 |
| `query-store-coupons` / `available-coupons` | — | 查询门店 / 可用优惠，做省钱推荐 |
| `campaign-calendar` | — | 查询当前活动，做活动推荐 |
| `query-meal-detail` | 餐品编码 | 查套餐明细（套餐热量非单品简单相加，需查明细） |

> 涉及真钱 / 真积分的工具（`create-order`、`draw-lottery`、`auto-bind-coupons`、`mall-create-order`）本项目**仅在有明确用户确认时**才调用，且调用前复述门店 / 餐品 / 总价 / 优惠。

## 三、调用流程（端到端）

1. 用户在 WorkBuddy 对话中发起需求（如「麦当劳吃什么」「帮我配一顿 600 大卡」「这个套餐多少卡」）。
2. `mcd-order-advisor` skill 先调 `now-time-info` 判断时段，再调 `list-nutrition-foods` 与 `query-meals` 等拉取**实时**菜单与营养数据。
3. skill 按热量目标 / 预算 / 忌口生成 2–3 套方案，并给出卡路里与营养账。
4. 结论被压成一句话（格式：`菜品1+菜品2+饮品\n共X大卡`，≤22 字），调用 `skills/mcd-order-advisor/scripts/push_bubble.py` 写入本地队列文件 `~/.mcd-pet/bubble.json`。
5. 已启动的「麦薯条」桌面宠物（`pet/麦薯条-tk.py`，每 0.5s 轮询该文件）读取后，用气泡把本轮推荐播报出来；套餐含 ≥2 份薯条时触发分身合奏动画。当前仓库未提供 launchd plist，因此开机启动与自动保活需要用户自行配置。

## 四、业务价值

把冰冷的菜单 / 营养 API 变成一个有温度的「陪伴型桌宠」：用户在桌面就能看到基于**实时官方数据**的个性化麦当劳推荐，而不是自己翻 App。MCP 提供真实数据底座，桌宠提供轻量、有趣的呈现层，二者通过本地队列文件解耦（宠物不直连网络，WorkBuddy / MCP 负责取数），既安全又好玩。

## 数据边界

- 实时对话推荐使用当轮查询的 MCP 结果；套餐详情优先查 `query-meal-detail`。单品营养数据不能自动代表套餐或个性化替换后的营养值。
- 如需从 kJ 换算 kcal，使用 `kJ ÷ 4.184` 并标记为估算；数据缺失时说明未知，不补造数字。
- 价格、优惠、菜单和供应状态必须对应本轮查询的门店与就餐方式。缺少实时价格时不得保证满足预算。
- 定时提醒读取 `reminder_meals.json` 离线缓存，可能过期，不属于实时 MCP 推荐，不能据此声称在售或保证热量。
- 营养值只作一般参考，不构成医疗或个体化营养建议。

## 五、代码位置

- MCP 调用逻辑与提示词：`skills/mcd-order-advisor/SKILL.md`
- 推送脚本：`skills/mcd-order-advisor/scripts/push_bubble.py`、`bubble_window.py`、`reminder.py`、`watchdog.py`
- 展示层（桌宠）：`pet/麦薯条-tk.py`（PySide6 浮空桌宠，轮询 `~/.mcd-pet/bubble.json`）
