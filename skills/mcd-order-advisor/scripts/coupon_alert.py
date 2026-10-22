# -*- coding: utf-8 -*-
"""麦麦省优惠券提醒：有新券可领时，弹麦麦气泡 + macOS 通知。

设计要点：
- 直连麦当劳官方 MCP（https://mcp.mcd.cn），读 ~/.workbuddy/mcp.json 的 token，不经过对话也能自动跑。
- 「宠物不直连网络」的分层不变：本脚本只做取数 + 判定，呈现仍交给桌宠的 bubble.json 队列。
- 只提醒，不自动领券。涉及真券的操作（auto-bind-coupons）必须人工确认，脚本默认不做。

用法：
  coupon_alert.py              正常巡检：有「新可领」的券就弹提醒
  coupon_alert.py --status     只打印当前券列表和判定结果，不弹
  coupon_alert.py --test       造一张假券走完整推送链路，验证气泡（不联网）
  coupon_alert.py --force      忽略首次运行静默规则，当前可领的券立即弹一次
"""
import os
import re
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
MCP_URL = "https://mcp.mcd.cn"
STATE = os.path.expanduser("~/.mcd-pet/coupon_alert.json")
QUEUE = os.path.expanduser("~/.mcd-pet/bubble.json")
PET_MARKER = "麦麦-tk.py"
BUBBLE_WIN = os.path.join(HERE, "bubble_window.py")
PUSH_BUBBLE = os.path.join(HERE, "push_bubble.py")
PY = os.environ.get("MCD_PET_PY") or sys.executable

DISPLAY_MS = 45000        # 气泡停留时长
COOLDOWN_SEC = 6 * 3600   # 同一张券的提醒冷却，避免反复弹
QUIET_FROM, QUIET_TO = 23, 8   # 静默时段 23:00–08:00，期间只记录不打扰

# 已确认的「不可领」状态码；其余状态码按 label 文本兜底判断
CLAIMED_CODES = {"HAVING_RECEIVE", "RECEIVE_OTHER_CHANNEL"}
# label 里出现这些词 = 不用管
DEAD_WORDS = ("已领取", "已使用", "已过期", "已抢光", "已结束")


# ---------- 取数 ----------
def load_token():
    try:
        cfg = json.load(open(os.path.expanduser("~/.workbuddy/mcp.json"), encoding="utf-8"))
        srv = cfg.get("mcpServers", cfg)
        for _, v in srv.items():
            if isinstance(v, dict) and "mcd" in v.get("url", ""):
                t = v.get("headers", {}).get("authToken", "") or ""
                return t.replace("Bearer ", "").strip()
    except Exception as e:
        print("[coupon] 读取 token 失败:", e)
    return ""


def mcp_call(token, name, args=None):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": args or {}}}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("authToken", token)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_coupons():
    """返回 [{"name","status","label"}]；失败抛异常由调用方处理。"""
    token = load_token()
    if not token:
        raise RuntimeError("未取到 MCP token")
    res = mcp_call(token, "available-coupons")
    if res.get("error"):
        raise RuntimeError("MCP 返回错误: %s" % res["error"])
    sc = (res.get("result", {}).get("structuredContent") or {})
    if not sc.get("success") and sc.get("code") not in (None, 200):
        raise RuntimeError("业务失败: %s %s" % (sc.get("code"), sc.get("message")))
    out = []
    for it in (sc.get("data") or []):
        out.append({"name": (it.get("couponName") or "").strip(),
                    "status": (it.get("couponStatus") or "").strip(),
                    "label": (it.get("label") or "").strip()})
    if out:
        return out
    # 结构化数据缺失时，退化解析文本
    for c in res.get("result", {}).get("content", []):
        txt = c.get("text", "")
        for m in re.finditer(r"优惠券标题：(.+?)\s*\\?\s*\n\s*状态：(\S+)", txt):
            out.append({"name": m.group(1).strip(), "status": "", "label": m.group(2).strip()})
    return out


# ---------- 判定 ----------
def is_claimable(c):
    if c["status"] in CLAIMED_CODES:
        return False
    lab = c["label"]
    if any(w in lab for w in DEAD_WORDS):
        return False
    return any(w in lab for w in ("可领取", "待领取", "立即领取", "去领取", "领取"))


# ---------- 状态 ----------
def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_state(st):
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[coupon] 写状态失败:", e)


def quiet_now(now=None):
    h = (now or datetime.datetime.now()).hour
    return h >= QUIET_FROM or h < QUIET_TO


# ---------- 推送 ----------
def pet_running():
    try:
        out = subprocess.run(["pgrep", "-f", PET_MARKER], capture_output=True, text=True)
        return bool(out.stdout.strip())
    except Exception:
        return False


def notify(title, text):
    """主通道：写 bubble.json（常驻桌宠会读）；兜底：独立窗口 + macOS 通知。"""
    try:
        subprocess.run([PY, PUSH_BUBBLE, text, str(DISPLAY_MS)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except Exception as e:
        print("[coupon] push_bubble 失败，改直写队列:", e)
        try:
            os.makedirs(os.path.dirname(QUEUE), exist_ok=True)
            with open(QUEUE, "w", encoding="utf-8") as f:
                json.dump({"text": text, "ts": time.time(), "ms": DISPLAY_MS,
                           "fries": 0}, f, ensure_ascii=False)
        except Exception as e2:
            print("[coupon] 直写队列也失败:", e2)
    if not pet_running():
        try:
            subprocess.Popen([PY, BUBBLE_WIN, text, str(DISPLAY_MS)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
        except Exception:
            pass
    try:
        subprocess.run(["osascript", "-e",
                        'display notification "%s" with title "%s"' %
                        (text.replace('"', ''), title)], check=False, timeout=10)
    except Exception:
        pass


def build_text(names):
    head = "🍟 有 1 张券可以领啦！" if len(names) == 1 else "🍟 有 %d 张券可以领啦！" % len(names)
    lines = [head] + ["· " + n for n in names]
    lines.append("回对话说一声我就去领 🍔")
    return "\n".join(lines)


def emit(names, st, reason=""):
    text = build_text(names)
    print("[coupon] 推送提醒(%s)：" % (reason or "new"), names)
    notify("🍟 麦当劳优惠券提醒", text)
    now = time.time()
    st.setdefault("notified", {})
    for n in names:
        st["notified"][n] = now
        st["pending"] = [x for x in st.get("pending", []) if x != n]


# ---------- 主流程 ----------
def main():
    args = sys.argv[1:]
    mode_status = "--status" in args
    mode_test = "--test" in args
    force = "--force" in args

    st = load_state()
    first_run = st is None
    st = st or {"seen": {}, "notified": {}, "pending": []}
    st.setdefault("seen", {})
    st.setdefault("notified", {})
    st.setdefault("pending", [])

    if mode_test:
        fake = [{"name": "测试券·免费脆薯饼", "status": "", "label": "可领取"}]
        notify("🍟 麦当劳优惠券提醒", build_text([c["name"] for c in fake]))
        print("[coupon] 已发送测试提醒（气泡 / macOS 通知）")
        return

    try:
        coupons = fetch_coupons()
    except Exception as e:
        print("[coupon] 拉取失败:", e)
        save_state(st)
        return 2

    claimable = [c for c in coupons if is_claimable(c)]
    print("[coupon] 共 %d 张券，其中可领 %d 张" % (len(coupons), len(claimable)))
    for c in coupons:
        print("   - %-20s status=%-24s label=%s %s" %
              (c["name"], c["status"], c["label"],
               "<== 可领" if c in claimable else ""))

    if mode_status:
        save_state(st)
        return 0

    now = time.time()
    # 状态迁移判定：新出现 / 从不可领变为可领 / 静默时段积压
    due = []
    for c in claimable:
        n = c["name"]
        prev = st["seen"].get(n)
        seen_before = prev is not None
        was_claimable = bool(prev and is_claimable({"name": n, "status": prev.get("status", ""),
                                                    "label": prev.get("label", "")}))
        changed = (not seen_before) or (not was_claimable)
        cooled = now - st["notified"].get(n, 0) < COOLDOWN_SEC
        if changed or n in st["pending"]:
            if not cooled or force:
                due.append(n)
            elif changed:
                st["pending"] = st["pending"] + [n] if n not in st["pending"] else st["pending"]

    # 更新 seen
    for c in coupons:
        st["seen"][c["name"]] = {"status": c["status"], "label": c["label"]}

    if first_run and not force:
        print("[coupon] 首次运行：已记录基线，本次不打扰（想立刻看效果加 --force）")
        if due:
            st["pending"] = sorted(set(st["pending"] + due))
        save_state(st)
        return 0

    if not due:
        print("[coupon] 没有需要提醒的新券" + ("（或处于冷却/静默）" if claimable else ""))
        save_state(st)
        return 0

    if quiet_now():
        st["pending"] = sorted(set(st["pending"] + due))
        print("[coupon] 静默时段(23:00–08:00)，已积压 %d 张，明早再提醒" % len(due))
        save_state(st)
        return 0

    emit(due, st, "new" if not first_run else "force")
    save_state(st)
    return 0


if __name__ == "__main__":
    sys.exit(main())
