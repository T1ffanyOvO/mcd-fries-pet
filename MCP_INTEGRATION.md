# MCP 集成说明（MCP_INTEGRATION.md）

本项目使用麦当劳中国官方 MCP（`mcd-mcp`）提供菜单、营养、门店和优惠券数据。项目有两条 MCP 数据路径：WorkBuddy 对话中的点餐推荐，以及由 launchd 定时运行的优惠券提醒。桌宠「麦麦」只负责显示消息，不直接连接 MCP。

## 一、Server 与鉴权

- **Server**：`mcd-mcp`，远程托管，使用 Streamable HTTP。
- **端点**：`https://mcp.mcd.cn`。
- **WorkBuddy 对话路径**：在 WorkBuddy 的 MCP 连接器中配置 Token，由 WorkBuddy 加载并调用 MCP Tools。脱敏配置见 `mcp-config.example.json`。
- **优惠券提醒路径**：`skills/mcd-order-advisor/scripts/coupon_alert.py` 直接向 MCP 端点发送 `tools/call` 请求，不依赖 WorkBuddy 对话进程；脚本从本机 `~/.workbuddy/mcp.json` 读取 Token。该文件只在用户本机，不应提交到仓库。
- 作者环境的配置同时带 `Authorization: Bearer <TOKEN>` 和 `authToken: <TOKEN>` 请求头。鉴权行为可能变化；遇到 401/403 时，应检查 Token、配置和官方指南。

## 二、使用的 MCP Tools

| Tool | 入参 | 使用场景 |
|---|---|---|
| `now-time-info` | 无 | 对话推荐时判断早餐或正餐时段 |
| `list-nutrition-foods` | 无 | 获取餐品营养数据，用于热量和营养参考 |
| `query-meals` | `beType`；部分用餐方式还需门店编码 | 查询对应场景的在售菜单 |
| `query-nearby-stores` | 按 Tool schema 提供位置条件 | 查询附近门店 |
| `query-meal-detail` | 餐品编码 | 查询套餐组成和选项 |
| `query-store-coupons` | 按 Tool schema 提供门店信息 | 查询当前门店适用的优惠券 |
| `available-coupons` | 无 | 查询当前麦麦省优惠券及其领取状态；对话推荐和定时提醒均会使用 |
| `campaign-calendar` | 按 Tool schema 提供日期条件 | 查询活动日历 |

`coupon_alert.py` 只调用 `available-coupons` 查询状态，不调用 `auto-bind-coupons`。后者会把当前可领券加入用户账户；只有用户明确要求并确认后，才可执行。下单、抽奖、积分兑换等会改变订单或账户状态的操作也必须先取得用户确认。

## 三、WorkBuddy 对话推荐流程

1. 用户在 WorkBuddy 中提出点餐、热量、预算或优惠需求。
2. `mcd-order-advisor` 按需求调用 `now-time-info`、`list-nutrition-foods`、`query-meals`、`query-store-coupons` 等 Tools 获取当轮数据。
3. Skill 根据 MCP 返回结果组织建议；没有实时价格、门店或营养数据时，应说明未知，不编造结果。
4. 用户要求桌宠播报时，Skill 调用 `skills/mcd-order-advisor/scripts/push_bubble.py`，把消息和结构化 `--fries N` 份数写入 `~/.mcd-pet/bubble.json`。
5. `pet/麦麦-tk.py` 每 0.5 秒读取队列并显示气泡。`fries >= 2` 时播放分身动画；气泡和动画由用户点击桌宠关闭。旧消息没有 `fries` 字段时，源码会从文案中的“薯条”次数兼容判断。

## 四、定时优惠券提醒流程

1. 用户运行 `install/install_coupon_reminder.command`。脚本把 `coupon_alert.py` 安装到 WorkBuddy Skill 脚本目录，并按本机路径生成 `~/Library/LaunchAgents/com.mcd.pet.coupon.plist`。
2. launchd 每小时运行一次 `coupon_alert.py`；`RunAtLoad` 也会在注册时触发一次。
3. 脚本从本机 `~/.workbuddy/mcp.json` 读取 Token，直接调用 MCP `available-coupons`，根据返回的 `couponName`、`couponStatus` 和 `label` 判断可领状态。
4. 首次运行只保存状态基线，不弹提醒。之后在新券出现或已有券状态转为可领取时提醒；同券有 6 小时冷却，23:00–08:00 静默，期间待提醒项目会延后处理。
5. 提醒通过 `push_bubble.py` 写入桌宠队列，并发送 macOS 通知；桌宠未运行时还会尝试独立气泡兜底。脚本只提醒，不自动领取。

状态保存在 `~/.mcd-pet/coupon_alert.json`，日志写入 `/tmp/mcdpet-coupon.log` 和 `/tmp/mcdpet-coupon.err.log`。可用 `coupon_alert.py --status` 查看状态，`--test` 测试本地提醒链路，`--force` 忽略首次静默和冷却并立即提醒当前可领券。

## 五、业务价值与数据边界

WorkBuddy 把麦当劳 MCP 的当轮数据转成个性化建议；优惠券巡检脚本可以在对话之外发现新可领券；桌宠则提供轻量、可见的提醒方式。桌宠进程不访问网络，但 `coupon_alert.py` 会直接访问 MCP。

- 菜单、营养、价格和券状态可能随时间、门店及就餐方式变化；推荐时以本轮 MCP 返回为准。
- `reminder_meals.json` 是离线提醒缓存，不代表实时在售或当前营养数据。
- 单品营养数据不能自动代表套餐或替换选项；套餐热量应优先查询 `query-meal-detail`。
- 营养信息只作一般参考，不构成医疗或个体化营养建议。

## 六、代码位置

- MCP 对话调用规则：`skills/mcd-order-advisor/SKILL.md`
- 优惠券定时巡检：`skills/mcd-order-advisor/scripts/coupon_alert.py`
- 安装脚本：`install/install_coupon_reminder.command`
- 桌宠消息推送：`skills/mcd-order-advisor/scripts/push_bubble.py`
- 桌宠展示：`pet/麦麦-tk.py`
