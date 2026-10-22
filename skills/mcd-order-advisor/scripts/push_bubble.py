# -*- coding: utf-8 -*-
"""把一句话推到麦麦气泡。
主通道：写队列文件 ~/.mcd-pet/bubble.json，常驻的麦麦挂件（open 启动、GUI 会话）会读它
并在屏幕中上弹气泡。气泡由主挂件进程绘制，确保能显示且不被回收。
兜底：主挂件没在跑时，用 start_new_session 弹独立窗口（仍可能受会话限制，但尽力）。
用法：push_bubble.py "<文字>" [显示毫秒，默认20000] [--fries N]
  --fries N  结构化字段：套餐里薯条份数（≥2 时挂件放分身合奏）。
            不传则挂件回退到数文字"薯条"次数（兼容手动推送）。
"""
import sys
import os
import json
import time
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.expanduser("~/.mcd-pet/bubble.json")
PET_MARKER = "麦麦-tk.py"
PY = sys.executable  # 用运行本脚本的解释器，避免写死本机路径
BUBBLE_WIN = os.path.join(HERE, "bubble_window.py")


def pet_running():
    try:
        out = subprocess.run(["pgrep", "-f", PET_MARKER],
                             capture_output=True, text=True)
        return bool(out.stdout.strip())
    except Exception:
        return False


def main():
    args = sys.argv[1:]
    text = "i'm lovin' it 🍟"
    ms = "20000"
    fries = None
    # 解析可选 --fries N（其余位置参数按顺序作 text / ms）
    cleaned = []
    i = 0
    while i < len(args):
        if args[i] == "--fries" and i + 1 < len(args):
            try:
                fries = int(args[i + 1])
            except ValueError:
                fries = None
            i += 2
            continue
        cleaned.append(args[i])
        i += 1
    if cleaned:
        text = cleaned[0]
    if len(cleaned) > 1:
        try:
            int(cleaned[1])
            ms = cleaned[1]
        except ValueError:
            pass

    # 写队列（主挂件若运行会读它弹气泡）
    payload = {"text": text, "ts": time.time(), "ms": int(ms)}
    if fries is not None:
        payload["fries"] = fries  # 结构化字段：薯条份数，≥2 触发分身
    try:
        os.makedirs(os.path.dirname(QUEUE), exist_ok=True)
        with open(QUEUE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
    except Exception:
        pass

    # 兜底：主挂件没在跑，用独立窗口尽力弹
    if not pet_running():
        try:
            subprocess.Popen([PY, BUBBLE_WIN, text, str(ms)],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             start_new_session=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
