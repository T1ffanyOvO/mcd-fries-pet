# -*- coding: utf-8 -*-
"""固定时间用餐提醒 + 自动推荐（12:00 午餐 / 18:00 晚餐）。
由 launchd (com.mcd.pet.reminder.plist, StartCalendarInterval) 定时触发。
薯条在跑 → 推气泡（贴薯条头，点一下消失）；没跑 → 退化为 macOS 通知。
推荐来自 reminder_meals.json（数值取自麦当劳官方营养库，离线缓存，避免触发时再连 MCP）。
用法：reminder.py [lunch|dinner|now]   （now/无参按当前小时；lunch/dinner 用于手动演示）
"""
import os
import sys
import json
import time
import random
import subprocess
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
MEALS = os.path.join(HERE, "reminder_meals.json")
QUEUE = os.path.expanduser("~/.mcd-pet/bubble.json")
PET_MARKER = "麦薯条-tk.py"
PY = sys.executable  # 用运行本脚本的解释器，避免写死本机路径
BUBBLE_WIN = os.path.join(HERE, "bubble_window.py")
DISPLAY_MS = 60000  # 提醒停留 60s


def pet_running():
    try:
        out = subprocess.run(["pgrep", "-f", PET_MARKER],
                             capture_output=True, text=True)
        return bool(out.stdout.strip())
    except Exception:
        return False


def push(text, fries=0):
    # 把「共X大卡」换到独立一行（与气泡格式规则一致）
    text = text.replace(" 共", "\n共", 1)
    try:
        os.makedirs(os.path.dirname(QUEUE), exist_ok=True)
        with open(QUEUE, "w", encoding="utf-8") as f:
            json.dump({"text": text, "ts": time.time(),
                       "ms": DISPLAY_MS, "fries": fries}, f, ensure_ascii=False)
    except Exception:
        pass
    # 兜底：薯条没在跑，用独立窗口尽力弹（macOS 通知兜底在下方）
    if not pet_running():
        try:
            subprocess.Popen([PY, BUBBLE_WIN, text, str(DISPLAY_MS)],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             start_new_session=True)
        except Exception:
            pass
        try:
            subprocess.run(["osascript", "-e",
                            f'display notification "{text}" with title "🍟 麦当劳用餐提醒"'],
                           check=False)
        except Exception:
            pass


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg in ("lunch", "dinner"):
        slot = arg
    elif arg == "now":
        slot = "lunch" if datetime.datetime.now().hour < 15 else "dinner"
    else:
        h = datetime.datetime.now().hour
        slot = "lunch" if 11 <= h < 15 else "dinner"

    greet = "午餐时间到～" if slot == "lunch" else "晚餐时间到～"
    try:
        with open(MEALS, encoding="utf-8") as f:
            data = json.load(f)
        pool = data.get(slot, data.get("lunch", [{"line": "i'm lovin' it 🍟"}]))
        line = random.choice(pool)["line"]
    except Exception:
        line = "i'm lovin' it 🍟"

    fries = line.count("薯条")
    push(greet + "\n" + line, fries)


if __name__ == "__main__":
    main()
