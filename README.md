# 🍟 麦薯条 · 会聊麦当劳的桌面宠物（McDonald's MCP Desktop Pet）

一个基于**麦当劳官方 MCP（`mcd-mcp`）**的陪伴型桌面宠物。它不只是萌——当你在 WorkBuddy 里问「麦当劳吃什么」「帮我配一顿 600 大卡」，它会调用麦当劳**真实**菜单与营养数据，算出方案，再让桌面上那只开心薯条用气泡把推荐播报出来。

> 麦当劳程序员节创意开发大赛参赛作品 · 由参赛者独立开发，非麦当劳官方产品。

## ✨ 特性

- 🤝 **真·麦当劳数据**：通过 `mcd-mcp` 拉取实时菜单、营养（约 160 个餐品）、门店、优惠与活动。
- 💬 **气泡播报**：推荐结论由桌宠「麦薯条」用头顶气泡说出来（格式：`菜品+… 共X大卡`）。
- 🍟 **分身合奏**：套餐含 ≥2 份薯条时，薯条左右各探出小薯条摇摆庆祝。
- 🛡️ **看门狗保活**：挂了 5 秒内自动拉起，Mac 重启也常驻（launchd）。
- 🥧 **多形态**：PySide6 浮空桌宠（Python）、macOS 原生悬浮挂件（Swift）、网页版虚拟宠物（HTML）。

## 🧩 架构

```
你 / WorkBuddy 对话
   → mcd-mcp（真实数据）
   → mcd-order-advisor skill（算方案）
   → push_bubble.py
   → ~/.mcd-pet/bubble.json
   → 麦薯条桌宠（每 0.5s 轮询 → 气泡）
```

## 🚀 安装

### 1. 接入麦当劳 MCP
在 WorkBuddy 连接器配置中填入你的 MCP Token（字段见 `mcp-config.example.json`）：

1. 去 https://open.mcd.cn/mcp 用手机号登录，控制台 → 激活 → 申请 MCP Token。
2. 按 `mcp-config.example.json` 的字段填入，并在连接器页面点「信任」启用。
3. ⚠️ 实测需**同时**带 `Authorization` 与 `authToken` 两个请求头，缺一个会 403；配置后需完全退出 WorkBuddy 重开才会加载工具。

### 2. 运行桌宠（展示层，任选其一）
- **Python 浮空桌宠**：`python pet/麦薯条-tk.py`（需 `pip install PySide6`）
- **网页版**：直接用浏览器打开 `pet/虚拟宠物-麦麦.html`
- **macOS 原生**：运行 `sh 编译运行原生版.command`（需 Xcode Command Line Tools）

### 3. 试一试
在 WorkBuddy 里对助手说：「麦当劳帮我配一顿 600 大卡」，稍候桌面上的薯条就会冒出气泡推荐。

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
│           └── reminder_meals.json
├── pet/                         # 桌宠展示层源码
│   ├── 麦薯条-tk.py
│   ├── 麦薯条.swift
│   ├── 虚拟宠物-麦麦.html
│   ├── 运行挂件.command
│   ├── 编译运行原生版.command
│   ├── 诊断-窗口测试.py
│   └── fries_mascot.png
└── previews/
    ├── 薯条动画预览/index.html
    └── 薯条看门狗预览/index.html
```

## ⚠️ 声明

参赛声明见 `CONTEST_DECLARATION.md`。本项目非麦当劳官方产品，餐品 / 价格 / 供应状态以麦当劳官方渠道实时结果为准；项目输出仅供参考，不构成医疗或营养专业建议。
