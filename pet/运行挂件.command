#!/bin/bash
# 双击启动「麦薯条」桌面挂件（tkinter 版）
# 若仍被 macOS 拦截，请右键本文件 → 打开（第一次需这样放行一次）
cd "$(dirname "$0")"

# 优先用系统自带的 /usr/bin/python3（自带 tkinter，最稳）
PY="/usr/bin/python3"
[ -x "$PY" ] || PY="python3"

# 先确认 tkinter 可用，没有就弹窗并停留，避免闪退看不到原因
if ! "$PY" -c "import tkinter" 2>/dev/null; then
  osascript -e 'display dialog "本机 python 缺少 tkinter，无法运行挂件。" buttons {"好"} default button 1' 2>/dev/null
  echo "错误：python3 缺少 tkinter 模块，无法启动。"
  sleep 6
  exit 1
fi

"$PY" "麦薯条-tk.py"
