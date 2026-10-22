---
name: mcd-order-advisor
description: "麦当劳中国点餐与营养顾问：调用麦当劳官方 MCP（mcd-mcp）拉取当前门店菜单与餐品营养数据，按热量目标/预算/忌口推荐套餐组合并给出卡路里参考，再把一句话推荐推给桌面宠物「麦麦」用气泡说出来。适用于「麦当劳吃什么」「帮我配一顿 600 大卡」「这个套餐多少卡」「麦当劳推荐+热量」等请求。触发词：麦当劳、麦麦、点餐、吃什么、卡路里、热量、营养、套餐推荐、麦乐送。"
agent_created: true
---

# 麦当劳点餐 + 卡路里顾问（带宠物播报）

接麦当劳中国官方 MCP，给出**能直接照着点**的套餐组合与热量账，再让桌上的
开心麦麦用气泡把推荐说出来。

## 何时使用

- 用户问「麦当劳吃什么 / 帮我配一顿 / 这个多少卡 / 有没有低卡的」
- 用户给了热量目标或预算，要按条件挑餐品
- 用户想看当前门店在售菜单、优惠、活动
- 用户明确说「让麦麦帮我推荐 / 让麦麦说」

## 前置条件（必须先确认）

MCP 连接器 `mcd-mcp` 需要用户自己的 **MCP Token**：

1. 打开 https://open.mcd.cn/mcp ，手机号登录
2. 控制台 → 激活 → 申请 MCP Token
3. 填进 `~/.workbuddy/mcp.json`。
   ⚠️ **必须同时写两个请求头，缺一个都过不了鉴权**（实测，与官方 README 不一致）：
   ```json
   "headers": {
     "Authorization": "Bearer <TOKEN>",
     "authToken": "<TOKEN>"
   }
   ```
   - 只给 `Authorization: Bearer` → 403 `校验鉴权authToken必填!`
   - 只给 `authToken` → 403 `系统错误`
   - **两个同时给 → 200 正常**
4. 在连接管理页把新连接器点「信任」启用，然后**完全退出 WorkBuddy 再重开**，
   新会话才会加载工具（只点信任、不重启，工具搜不到）

**如果 MCP 工具不可用**（未列出、调用报 401/403），直接告诉用户：Token 没配、过期
或配置写法不对，去 open.mcd.cn/mcp 重新申请并替换，**不要编造菜单和热量数据**。
限流 600 次/分钟。

**快速自检**（绕开客户端，直接验服务端通不通）：拿 `mcp.json` 里的 token 用 urllib
POST `https://mcp.mcd.cn` 打 `initialize`（带上述两个头），返回 200 且
`serverInfo.name=mcd-mcp` 就说明服务端没问题，剩下只是客户端没挂载。

## 工作流

### 1. 定需求（缺什么就问，别硬猜）

| 维度 | 默认值（用户没说时） |
|---|---|
| 热量目标 | 一顿 500–700 kcal |
| 预算 | 不限，但标注每套价格 |
| 忌口/偏好 | 无（主动问一句：不吃辣？不吃牛肉？要低钠？） |
| 就餐方式 | 堂食/外带；要送才走麦乐送 |

先用 `now-time-info` 判断时段——**早餐菜单和正餐完全不同**，别拿晚餐标准推荐早晨。

### 2. 拿数据

已实测（2026-10-21）的调用要点：

- `list-nutrition-foods` → **无需入参**，直接返回约 160 个餐品的营养表；字段为
  `productName, nutritionDescription, energyKj, energyKcal, protein, fat, carbohydrate, sodium, calcium`。
  这是算热量的主力工具，先调它。
- `now-time-info` → 无需入参，返回服务器时间（判早餐/正餐时段用）。
- `query-meals` → 需要 `beType`（1 到店取餐 / 2 麦乐送到家 / 5 得来速 / 6 企业团餐），
  外送/得来速/团餐还要 `beCode` 与 `storeCode`：先用 `query-nearby-stores`（到店）或
  `delivery-query-addresses` + `delivery-query-stores`（外送）拿门店。返回分类、餐品编码、标签。
- 想省钱：`query-store-coupons` / `available-coupons`；想蹭活动：`campaign-calendar`。

工具总数 35 个，含下单/积分/抽奖/派对预约等，**本 skill 只用其中查菜单与营养的部分**。

### 3. 出方案

给 **2–3 套**，每套一张小表：

```
A. 清爽低卡（≈520 kcal）
麦香鱼堡    340 kcal | 蛋白 16g | 脂肪 14g
玉米杯       70 kcal
无糖可乐      0 kcal
合计 410 kcal · 蛋白 20g · 钠 xxx mg
```

配一句**为什么选它**（高蛋白/低钠/扛饿/便宜），不要只报数字。
热量单位统一用 kcal（接口给的 kJ 要 ÷4.184 换算）。

### 4. 推给麦麦（关键动作）

把结论压成**一句话**，文案格式固定 **「菜品在前、卡路里在后，且『共X大卡』另起一行」**：

```
菜品1+菜品2+饮品
共X大卡
```

例：
```
麦香鱼+玉米杯+红茶
共495大卡
```
（挂件 `_bubble` 会自动在「共」前插入换行，手动带 `\n` 也不重复处理。）气泡**贴在麦麦头顶**，
用户**点一下麦麦才关闭**（不自动消失）。菜品用 `+` 连、末尾 `共X大卡`、热量单位用 kcal，控制在 22 字内。

```bash
/Users/nina/.workbuddy/binaries/python/envs/default/bin/python \
  ~/.workbuddy/skills/mcd-order-advisor/scripts/push_bubble.py "<一句话>" [毫秒] [--fries N]
```

⚠️ **结构化触发分身（必做）**：配方案时**自己数套餐里有几份薯条**，用 `--fries N` 传给挂件，
**不要**依赖挂件数文字。例：`巨无霸+中薯条+大薯条` 含 2 份 → `--fries 2`；
`麦香鱼+玉米杯+红茶` 含 0 份 → 不传该参数。`fries >= 2` 才放分身合奏（固定 2 只）。

### 分身合奏动画（推荐含 ≥2 份薯条时自动播，点麦麦才消失）

挂件内置「分身合奏」彩蛋：推送时 **`fries >= 2`**（结构化字段，由 skill 计算后传入；
未传则回退到数文字「薯条」次数），麦麦本体左右各探出一只缩小版小麦麦、
跟着左右摇摆。**动画与气泡绑定**：持续摇摆直到用户**点一下麦麦**，气泡和分身一起消失
（分身有 0.35s 进场/退场缩放过渡）。
- 触发判断写在挂件 `poll_queue`：推送时 `text.count("薯条") >= 2` → `play_ensemble()`；
  若新推文案 <2 份薯条则 `hide_ensemble()`（自动收掉上一轮）。
- 单份薯条（如 `巨无霸+中薯条`）不触发；只有 ≥2 份才演。
- 动画期间遮罩临时扩到分身区域，退场完成（0.35s）后自动收回（不长期占用点击穿透区）。
- 点击收尾写在 `mouseReleaseEvent`：气泡可见时左键轻点 → `bubble.hide()` + `hide_ensemble()`。

⚠️ 推送链路关键坑（2026-10-21 实测，别踩）：
- 脚本**只写队列文件** `~/.mcd-pet/bubble.json`，由麦麦进程（每 0.5s 轮询）读取并绘制气泡。
  **不要**用 `start_new_session`/Bash 后台去起独立窗口——macOS 上那种进程要么被回收、要么画不出 GUI，
  用户啥也看不到（之前连跪 4 次的根因）。
- 麦麦挂件本体用 `open "/Users/nina/Applications/麦麦挂件.app"` 启动（归系统管、常驻、GUI 会话），
  **不要用 nohup/后台**，同样会被回收。

### 5. 下单（谨慎）

`create-order`、`draw-lottery`、`auto-bind-coupons`、`mall-create-order`
**涉及真钱/真积分，必须拿到用户明确确认后再调**，且调用前复述一遍：门店、餐品、
总价、优惠。用户没点头绝不执行。

### 6. 常点快捷方案（favorites.json）

- 用户确认过的方案存进 `favorites.json` 的 `presets` 数组（字段 id/name/tags/items/total/note）。
- 用户说「我的常点 / 常点B」时，读取对应 preset，把 `items` 用 `+` 连成菜品串，
  用 `push_bubble` 弹 `菜品串 共X大卡`（如 `麦香鱼+玉米杯+红茶 共495大卡`），并在聊天给明细；
  新增不覆盖已有 preset。
- 只动 favorites.json，无需改本文件。

### 7. 有新券可领时主动提醒（coupon_alert.py）

用户抱怨「总错过领券」时的方案：**脚本直连 MCP，绕开对话，定时巡检**。

```bash
~/.workbuddy/binaries/python/envs/default/bin/python \
  ~/.workbuddy/skills/mcd-order-advisor/scripts/coupon_alert.py [参数]
# --status  只打印当前券列表与判定，不弹（排查状态码用）
# --test    发一张假券走完整推送链路，验证气泡
# --force   忽略「首次运行静默」和冷却，立刻弹当前可领的券
```

实现要点（2026-10-22 实测）：

- **绕过客户端**：脚本自己 POST `https://mcp.mcd.cn`，JSON-RPC `tools/call`
  `available-coupons`，token 从 `~/.workbuddy/mcp.json` 读（两个头都要带）。
  返回体优先取 `result.structuredContent.data[]`，字段
  `couponName / couponStatus / label`。
- **状态码**：已知 `HAVING_RECEIVE`（本渠道已领）、`RECEIVE_OTHER_CHANNEL`（其他渠道已领），
  两者 label 都是「已领取」；可领的 label 为「可领取」。官方 schema **不枚举状态码**，
  所以判定走「状态码黑名单 + label 文本兜底」，遇到新状态码先用 `--status` 看一眼再改脚本。
- **不骚扰**：状态存 `~/.mcd-pet/coupon_alert.json`。首次运行**只记基线不打扰**；
  同一张券 6 小时冷却；只在「从未见过 → 可领」或「不可领 → 可领」的**状态跳变**时提醒；
  23:00–08:00 静默，积压到次日再弹。
- **只提醒不自动领**：脚本不碰 `auto-bind-coupons`。真要领，必须用户点头。
- 推送仍复用 `push_bubble.py` → `~/.mcd-pet/bubble.json` → 桌宠绘制；
  桌宠没在跑时才退化成独立窗口 + macOS 通知。
- 定时注册：**AI 会话里 `launchctl` 一定失败（EIO，拿不到 GUI session）**，
  必须让用户在终端里跑 `启用优惠券提醒.command`（项目根目录，双击即可）。


```
🍟 今日推荐（午餐 · 目标 600 kcal）

A. 高蛋白扛饿款 —— 约 580 kcal
   [表格]
B. 轻负担款 —— 约 430 kcal
   [表格]

📊 热量参考：成人一顿 500–700 kcal；你今天还有 xxx kcal 空间
💬 已让麦麦帮你播报推荐
```

## 雷区

- Token 没配时**绝不能凭记忆编造**餐品名、价格、热量——麦当劳菜单会变、地区有差异。
- 套餐的热量不等于各单品简单相加（酱料、替换项会变），能查 `query-meal-detail` 就查。
- 别把「钠」漏掉：麦当劳餐品钠普遍偏高，主动提一句更专业。
- 气泡文案固定格式「菜品+… 共X大卡」，菜品在前、热量在后，控制在 22 字内，别塞 emoji 堆砌。
