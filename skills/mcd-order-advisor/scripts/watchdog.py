# -*- coding: utf-8 -*-
"""薯条挂件看门狗：每 5s 探活，挂了自动 open 拉起；状态写入 ~/.mcd-pet/watchdog.json。
由 launchd (com.mcd.pet.watchdog.plist, KeepAlive) 保活，Mac 重启后自动起。
"""
import os
import time
import json
import subprocess

# 薯条挂件 .app 路径：可用环境变量 MCD_PET_APP 覆盖，默认按文件名查找
APP = os.environ.get("MCD_PET_APP", "麦薯条挂件.app")
MARKER = "麦薯条-tk.py"
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
                        f'display notification "{msg}" with title "麦当劳薯条挂件"'],
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
            notify("🍟 薯条已自动重启")
            write_status(False, restarts, last_restart)
        else:
            write_status(True, restarts, last_restart)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
