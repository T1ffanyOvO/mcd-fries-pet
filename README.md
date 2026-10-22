# 🍟 麦麦 · 会聊麦当劳的桌面宠物（McDonald's MCP Desktop Pet）

一个基于**麦当劳官方 MCP（`mcd-mcp`）**的陪伴型桌面宠物。它不只是萌——当你在 WorkBuddy 里问「麦当劳吃什么」「帮我配一顿 600 大卡」，它会调用麦当劳**真实**菜单与营养数据，算出方案，再让桌面上那只开心麦麦用气泡把推荐播报出来。

> 麦当劳程序员节创意开发大赛参赛作品 · 由参赛者独立开发，非麦当劳官方产品。

## ✨ 特性

- 🤝 **真·麦当劳数据**：通过 `mcd-mcp` 拉取实时菜单、营养（约 160 个餐品）、门店、优惠与活动。
- 💬 **气泡播报**：推荐结论由桌宠「麦麦」用头顶气泡说出来；菜品与热量分行显示，点击桌宠可关闭气泡。
- 🍟 **分身合奏**：推荐中有 ≥2 份薯条时，桌宠左右各探出一只小麦麦并持续摇摆；点击桌宠会一并收起。
- 🛡️ **看门狗脚本**：提供故障探测与重启脚本（`scripts/watchdog.py`，每 5s 探活、挂了自动拉起），仓库已附 `launchd/` 下的 `com.mcd.pet.watchdog.plist` 与 `com.mcd.pet.coupon.plist`，可 `launchctl load` 实现登录启动与持续保活。
- 🥧 **多形态**：PySide6 浮空桌宠（Python）、macOS 原生悬浮挂件（Swift）、网页版虚拟宠物（HTML）。
- 🎟️ **新券可领提醒**：`coupon_alert.py` 直连 mcd-mcp 定时巡检麦麦省，一旦发现券状态跳变成「可领取」，就推气泡 + macOS 通知。**只提醒，不自动领券**（自动领券属于真实消费行为，必须人工确认）。

## 🧩 架构

```
你 / WorkBuddy 对话
   → mcd-mcp（真实数据）
   → mcd-order-advisor skill（算方案）
   → push_bubble.py（附带薯条份数）
   → ~/.mcd-pet/bubble.json
   → 麦麦桌宠（每 0.5s 轮询 → 气泡）
```

## 🚀 安装

### 1. 接入麦当劳 MCP
在 WorkBuddy 连接器配置中填入你的 MCP Token（字段见 `mcp-config.example.json`）：

1. 去 https://open.mcd.cn/mcp 用手机号登录，控制台 → 激活 → 申请 MCP Token。
2. 按 `mcp-config.example.json` 的字段填入，并在连接器页面点「信任」启用。
3. ⚠️ 实测需**同时**带 `Authorization` 与 `authToken` 两个请求头，缺一个会 403；配置后需完全退出 WorkBuddy 重开才会加载工具。

### 2. 安装并运行桌宠

桌宠与 Skill 分开运行：桌宠负责显示，Skill 负责取麦当劳数据、生成建议并向桌宠发送气泡。运行桌宠的 Mac 需要 Python 3 和 PySide6：

```bash
python3 -m pip install PySide6
python3 pet/麦麦-tk.py
```

保持桌宠进程运行。也可双击 `pet/运行挂件.command`；若启动失败，请用上面的终端命令。

其它展示版本：
- **网页版**：直接用浏览器打开 `pet/虚拟宠物-麦麦.html`
- **macOS 原生**：运行 `sh 编译运行原生版.command`（需 Xcode Command Line Tools）

### 3. 在 WorkBuddy 安装 Skill 并触发

1. 在 WorkBuddy 中把本仓库的 `skills/mcd-order-advisor/` 作为本地 Skill 导入/安装，并确认已启用；如果你的 WorkBuddy 版本使用不同的 Skill 导入入口，请选择该目录中的 `SKILL.md`。
2. 确认麦当劳 MCP 连接器已配置、启用，且 WorkBuddy 已加载 `mcd-mcp` 工具。首次配置需要 MCP Token；不要把 Token 写进仓库。
3. 在 WorkBuddy 对话中直接说：

   - “麦当劳帮我配一顿 600 大卡，推荐两套，并让桌面麦麦播报。”
   - “查一下我附近门店现在有什么优惠，给我推荐一份 50 元以内的晚餐，麦麦说出来。”
   - “我想吃麦当劳，低钠优先，帮我配餐并推送给桌面宠物。”

Skill 会根据请求查麦当劳 MCP，并调用 `push_bubble.py` 写入 `~/.mcd-pet/bubble.json`；桌宠每 0.5 秒轮询队列，按结构化 `fries` 份数决定是否播放分身动画。气泡会留在桌宠头顶，点击桌宠关闭；只打开网页预览不会接收 Skill 消息。若 MCP 不可用，Skill 应明确告知，不应编造实时菜单、价格或营养数据。

### 4. 推荐计算与数据边界

- 菜品名称、在售状态、门店、优惠等以对应 MCP 查询结果为准；个别推荐路径会使用 `list-nutrition-foods` 的单品营养数据。
- 能量优先采用 MCP 返回的 `energyKcal`；只有该字段缺失而有 `energyKj` 时，按 `kcal = kJ ÷ 4.184` 换算并取整，标注为估算值。
- 组合热量只有在份量、规格及选项一致且各单品数据齐全时才可逐项相加；套餐或定制项优先调用 `query-meal-detail` 核对。无法核对的项目要标注估算/未知，不要给出虚假的精确总数。
- 预算推荐只在拿到对应门店当前价格/优惠时声称符合预算；缺少价格数据时先询问门店或说明无法核价。
- 定时提醒使用 `scripts/reminder_meals.json` 中的离线缓存，不是实时 MCP 查询结果。其菜品、热量及可售状态可能过期；提醒内容应视为缓存灵感，不能据此下单。日常推荐应以本轮 MCP 查询为准。
- MCP 营养信息仅供一般参考，不构成医疗或个体化营养建议；特殊饮食需求应优先遵从专业意见。

### 3.5 开启「新券可领」提醒（可选）

双击仓库外的 `启用优惠券提醒.command`：把 `coupon_alert.py` 同步到技能目录、注册
`com.mcd.pet.coupon` 定时任务（每 1 小时巡检），并立刻试跑一次。

```
mcd-mcp（available-coupons，脚本直连，不依赖对话）
   → coupon_alert.py（跳变判定 + 去重/冷却/静默时段）
   → push_bubble.py → ~/.mcd-pet/bubble.json → 麦麦气泡
   → 桌宠没在跑时兜底：独立气泡窗口 + macOS 通知
```

- 判定规则：**首次运行只记基线不打扰**；之后仅在「没见过 → 可领」或「不可领 → 可领」时提醒；同一张券 6 小时冷却；23:00–08:00 静默，积压到次日。
- 状态文件 `~/.mcd-pet/coupon_alert.json`，日志 `/tmp/mcdpet-coupon.log`。
- 手动调试：`coupon_alert.py --status`（只看不弹）/ `--test`（造假券验证链路）/ `--force`（强制弹一次）。
- ⚠️ 定时任务必须在**终端**里注册：AI 会话内的 `launchctl` 拿不到 GUI session，一律返回 `Load failed: 5: Input/output error`。

## 🎯 目标用户

- 常吃麦当劳、又想控制热量 / 预算的人
- 喜欢桌面宠物 / 萌系交互的开发者与用户
- 想用麦当劳 MCP 做出好玩东西的参赛者（可作参考）

## 📁 目录结构

```
mcd-fries-pet/
├── README.md
├── CONTEST_DECLARATION.md        # 参赛声明（内容不可改）
├── MCP_INTEGRATION.md            # 麦当劳 MCP 真实调用说明
├── mcp-config.example.json       # 脱敏配置示例（仅占位符）
├── skills/
│   └── mcd-order-advisor/        # 真正调用 mcd-mcp 的 skill
│       ├── SKILL.md
│       └── scripts/
│           ├── push_bubble.py    # 写气泡队列文件
│           ├── bubble_window.py  # 兜底独立气泡
│           ├── watchdog.py       # 看门狗保活
│           ├── reminder.py       # 定时用餐提醒
│           ├── reminder_meals.json
│           └── coupon_alert.py   # 新券可领提醒（直连 MCP 巡检）
├── launchd/
│   └── com.mcd.pet.coupon.plist  # 优惠券巡检定时任务（1h）
├── pet/                         # 桌宠展示层源码
│   ├── 麦麦-tk.py
│   ├── 麦麦.swift
│   ├── 虚拟宠物-麦麦.html
│   ├── 运行挂件.command
│   ├── 编译运行原生版.command
│   ├── 诊断-窗口测试.py
│   └── fries_mascot.png
└── previews/
    ├── 麦麦动画预览/index.html
    └── 麦麦看门狗预览/index.html
```

## ⚠️ 声明

参赛声明见 `CONTEST_DECLARATION.md`。本项目非麦当劳官方产品，餐品 / 价格 / 供应状态以麦当劳官方渠道实时结果为准；项目输出仅供参考，不构成医疗或营养专业建议。
