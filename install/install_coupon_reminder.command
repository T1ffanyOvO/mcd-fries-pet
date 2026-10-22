#!/bin/bash
# 安装「麦麦省优惠券提醒」：每小时巡检，有新券可领时弹麦麦气泡 + macOS 通知。
# 双击运行（需在终端环境注册 launchd，AI 会话内无法注册）。
# 脚本位于 <仓库>/install/，自动推导仓库根，无需硬编码路径，任何人 clone 可用。
# 注：不用 set -u —— macOS 默认 /bin/bash 3.2 在「双引号内同时含变量与全角括号」时会误报 unbound variable。

# 仓库根：本脚本在 <repo>/install/，上一级即仓库根
REPO="$(cd "$(dirname "$0")/.." && pwd)"

# 解析 WorkBuddy 托管 Python（任何 WorkBuddy 用户路径一致，仅 HOME 不同）
PY="$HOME/.workbuddy/binaries/python/envs/default/bin/python"
[ -x "$PY" ] || PY="$HOME/.workbuddy/binaries/python/versions/3.13.12/bin/python3"

SKILL_DIR="$HOME/.workbuddy/skills/mcd-order-advisor/scripts"
AGENTS="$HOME/Library/LaunchAgents"
LABEL="com.mcd.pet.coupon"

echo "🍟 安装 优惠券提醒"
echo "----------------------------------------"
echo "仓库   : $REPO"
echo "Python : $PY"
echo "----------------------------------------"

mkdir -p "$SKILL_DIR"
cp "$REPO/skills/mcd-order-advisor/scripts/coupon_alert.py" "$SKILL_DIR/coupon_alert.py"
echo "✅ 已同步脚本 → $SKILL_DIR/coupon_alert.py"

# 生成本机 plist（每小时巡检一次）
cat > "$AGENTS/$LABEL.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PY</string>
        <string>$SKILL_DIR/coupon_alert.py</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>LowPriorityIO</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/mcdpet-coupon.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/mcdpet-coupon.err.log</string>
</dict>
</plist>
PLIST
echo "✅ 已生成 $AGENTS/$LABEL.plist"

launchctl bootout "gui/$UID/$LABEL" 2>/dev/null
if launchctl bootstrap "gui/$UID" "$AGENTS/$LABEL.plist" 2>/dev/null; then
  launchctl enable "gui/$UID/$LABEL" 2>/dev/null
  echo "✅ 已注册定时任务：$LABEL（每 1 小时巡检）"
else
  echo "⚠️ 注册失败，请手动执行：launchctl bootstrap gui/$UID $AGENTS/$LABEL.plist"
fi

echo "----------------------------------------"
echo "立即跑一次（首次只记录基线，不打扰）："
"$PY" "$SKILL_DIR/coupon_alert.py"
echo
echo "想立刻看气泡长什么样："
echo "  $PY $SKILL_DIR/coupon_alert.py --test"
echo "想手动查券不打扰："
echo "  $PY $SKILL_DIR/coupon_alert.py --status"
echo "卸载：launchctl bootout gui/$UID $LABEL && rm $AGENTS/$LABEL.plist"
echo "日志：/tmp/mcdpet-coupon.log"
echo "----------------------------------------"
