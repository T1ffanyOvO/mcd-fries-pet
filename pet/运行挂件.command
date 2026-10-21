#!/bin/bash
# 双击启动「麦薯条」桌面挂件（PySide6 版）
# 若仍被 macOS 拦截，请右键本文件 → 打开（第一次需这样放行一次）
cd "$(dirname "$0")"

# 桌宠代码依赖 PySide6；优先使用安装了 PySide6 的 Python。
PY="python3"
if ! "$PY" -c "import PySide6" 2>/dev/null && [ -x "/usr/bin/python3" ]; then
  PY="/usr/bin/python3"
fi

# 先确认 tkinter 可用，没有就弹窗并停留，避免闪退看不到原因
if ! "$PY" -c "import PySide6" 2>/dev/null; then
  osascript -e 'display dialog "桌宠需要 PySide6。请先运行：python3 -m pip install PySide6" buttons {"好"} default button 1' 2>/dev/null
  echo "错误：当前 Python 缺少 PySide6。请运行：python3 -m pip install PySide6"
  sleep 6
  exit 1
fi

"$PY" "麦薯条-tk.py"
