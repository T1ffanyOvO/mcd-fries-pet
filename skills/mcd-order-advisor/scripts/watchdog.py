# -*- coding: utf-8 -*-
"""麦麦挂件看门狗：每 5s 探活，挂了自动 open 拉起；状态写入 ~/.mcd-pet/watchdog.json。
由 launchd (com.mcd.pet.watchdog.plist, KeepAlive) 保活，Mac 重启后自动起。
"""
import os
import time
import json
import subprocess

# 麦麦挂件 .app 路径解析：优先环境变量 MCD_PET_APP，否则依次尝试标准安装位置。
# 这样仓库 clone 到别的 Mac 也能自动找到 app，不必写死本机绝对路径。
def resolve_app():
    env = os.environ.get("MCD_PET_APP")
    if env and os.path.exists(env):
        return env
    candidates = [
        os.path.expanduser("~/Applications/麦麦挂件.app"),
        "/Applications/麦麦挂件.app",
        "麦麦挂件.app",  # 兜底：仅当 cwd 恰好在 app 所在目录时生效
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return os.path.abspath(c)
    return os.path.expanduser("~/Applications/麦麦挂件.app")  # 都没有则回退默认


APP = resolve_app()
MARKER = "麦麦-tk.py"
STATUS = os.path.expanduser("~/.mcd-pet/watchdog.json")
INTERVAL = 5


def pet_running():
    try:
        out = subprocess.run(["pgrep", "-f", MARKER],
                             capture_output=True, text=True)
        return bool(out.stdout.strip())
    except Exception:
        return False


def start_pet():
    try:
        subprocess.run(["open", APP], check=False)
    except Exception:
        pass


def notify(msg):
    try:
        subprocess.run(["osascript", "-e",
                        f'display notification "{msg}" with title "麦当劳麦麦挂件"'],
                       check=False)
    except Exception:
        pass


def write_status(alive, restarts, last_restart):
    try:
        os.makedirs(os.path.dirname(STATUS), exist_ok=True)
        with open(STATUS, "w", encoding="utf-8") as f:
            json.dump({"alive": alive, "restarts": restarts,
                       "last_restart": last_restart, "updated": time.time()},
                      f, ensure_ascii=False)
    except Exception:
        pass


def main():
    restarts = 0
    last_restart = 0
    while True:
        if not pet_running():
            restarts += 1
            last_restart = time.time()
            start_pet()
            notify("🍟 麦麦已自动重启")
            write_status(False, restarts, last_restart)
        else:
            write_status(True, restarts, last_restart)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
