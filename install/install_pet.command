#!/bin/bash
# 安装 / 重启「麦麦」桌面挂件 + 看门狗（macOS 专用）。
# 双击运行即可：自动解析本机路径、生成本机 launchd 任务、注册并启动。
# 前置：麦麦挂件.app 需已位于 ~/Applications/麦麦挂件.app
# 注：不用 set -u —— macOS 默认 /bin/bash 3.2 在「双引号内同时含变量与全角括号」时会误报 unbound variable。

# 解析 WorkBuddy 托管 Python（任何 WorkBuddy 用户路径一致，仅 HOME 不同）
PY="$HOME/.workbuddy/binaries/python/envs/default/bin/python"
[ -x "$PY" ] || PY="$HOME/.workbuddy/binaries/python/versions/3.13.12/bin/python3"

APP="$HOME/Applications/麦麦挂件.app"
SKILL_DIR="$HOME/.workbuddy/skills/mcd-order-advisor/scripts"
AGENTS="$HOME/Library/LaunchAgents"

echo "🍟 安装 / 重启 麦麦 桌面挂件"
echo "----------------------------------------"
echo "Python  : $PY"
echo "App     : $APP"
echo "技能目录 : $SKILL_DIR"
echo "----------------------------------------"

if [ ! -d "$APP" ]; then
  echo "⚠️ 未找到 $APP"
  echo "   请先把「麦麦挂件.app」放到 ~/Applications，再运行本脚本。"
  exit 1
fi

mkdir -p "$AGENTS"

# 生成 麦麦挂件本体 plist（开机自启 + 崩溃保活）
cat > "$AGENTS/com.mcd.pet.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mcd.pet</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PY</string>
        <string>$APP/Contents/Resources/麦麦-tk.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ProcessType</key>
    <string>Interactive</string>
    <key>StandardOutPath</key>
    <string>/tmp/mcdpet.out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/mcdpet.err.log</string>
</dict>
</plist>
PLIST
echo "✅ 已生成 $AGENTS/com.mcd.pet.plist"

# 生成 看门狗 plist（探活麦麦，挂了自动拉起）
cat > "$AGENTS/com.mcd.pet.watchdog.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mcd.pet.watchdog</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PY</string>
        <string>$SKILL_DIR/watchdog.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/tmp/mcdpet-watchdog.err.log</string>
</dict>
</plist>
PLIST
echo "✅ 已生成 $AGENTS/com.mcd.pet.watchdog.plist"

# 注册并启动（bootout 先清旧的，再 bootstrap）
for L in com.mcd.pet com.mcd.pet.watchdog; do
  launchctl bootout "gui/$UID/$L" 2>/dev/null
  if launchctl bootstrap "gui/$UID" "$AGENTS/$L.plist" 2>/dev/null; then
    launchctl enable "gui/$UID/$L" 2>/dev/null
    echo "✅ $L 已注册并启动"
  else
    echo "⚠️ $L 注册失败：请直接在「终端」里双击本脚本（bootout/bootstrap 需要 GUI session）"
  fi
done

sleep 3
if pgrep -fl "麦麦-tk.py" >/dev/null; then
  echo "✅ 麦麦 已运行"
else
  echo "⚠️ 未检测到麦麦进程，请查看 /tmp/mcdpet.err.log"
fi
