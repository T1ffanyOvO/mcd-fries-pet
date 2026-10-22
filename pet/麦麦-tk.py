# -*- coding: utf-8 -*-
"""麦麦 · 桌面宠物（Qt 真透明浮空版）
运行：python 麦麦-tk.py（需 PySide6）
右键点它或按 Esc 退出。透明区不挡桌面点击。
"""
import sys, os, json, math, random, time
from ctypes import c_void_p
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPixmap, QPainter, QColor, QBitmap, QRegion
from PySide6.QtWidgets import QApplication, QWidget, QLabel

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fries_mascot.png")

PHRASES = [
    "i'm lovin' it 🍟", "你今天开心吗？", "一起加油呀～", "饿了吗？我看着呢",
    "欢迎回来！", "摸鱼时间到～", "今天也要元气满满", "麦麦给你比心❤",
]

HEART_CHARS = ["❤", "✦", "★"]
HEART_COLORS = ["#ff5b7f", "#ffd23f", "#7fd1ff"]


class Pet(QWidget):
    def __init__(self):
        super().__init__()
        # 无边框 + 整窗半透明合成 + 置顶 + 不进 Dock
        self.setWindowFlags(
            Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # 关键：真透明

        self.pix = QPixmap(IMG)
        # 整体形象缩小（0.8）：缩放 pixmap，iw/ih 同步更新
        SCALE = 0.8
        if self.pix.width():
            self.pix = self.pix.scaled(
                int(self.pix.width() * SCALE),
                int(self.pix.height() * SCALE),
                Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.iw, self.ih = self.pix.width(), self.pix.height()
        self.pad_x, self.pad_top, self.pad_bot = 110, 96, 16
        self.W = self.iw + self.pad_x * 2
        self.H = self.ih + self.pad_top + self.pad_bot
        self.resize(self.W, self.H)
        self.setMouseTracking(True)  # 无按键也收 mouseMove

        # 动画状态
        self.t = 0.0
        self.float_y = 0.0
        self.bounce_y = 0.0
        self.bounce_v = 0.0
        self.parallax = 0.0
        self.parallax_target = 0.0

        # 分身合奏状态：与气泡绑定，一直演到用户点击麦麦才消失
        self.ensemble_on = False        # 是否正在展示分身
        self.ensemble_hiding = False    # 是否处于退场动画
        self.ensemble_t0 = 0.0          # 最近一次状态切换时间（用于进出场缩放）

        # 交互状态
        self.dragging = False
        self.drag_offset = QPoint()
        self.press_global = None
        self.moved = False

        # 气泡（贴麦麦头的子标签，跟随宠物移动；点击宠物即可消除）
        self.bubble = QLabel(self)
        self.bubble.setWordWrap(True)
        self.bubble.setMaximumWidth(235)
        self.bubble.setStyleSheet(
            "background: rgba(255,255,255,247); color:#C8102E;"
            "border:2px solid #FFD23F; border-radius:16px;"
            "padding:8px 14px; font: 15px 'PingFang SC';"
        )
        self.bubble.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.bubble.hide()

        self.hearts = []  # (label, step)

        # 外部消息通道：其他程序/skill 写 ~/.mcd-pet/bubble.json，宠物就用气泡说出来
        self.queue_path = os.path.expanduser("~/.mcd-pet/bubble.json")
        self.last_ts = 0.0
        self.qtimer = QTimer(self)
        self.qtimer.timeout.connect(self.poll_queue)
        self.qtimer.start(500)

        # 默认放右侧居中，避开对话框中心，也不压 Dock
        scr = QApplication.primaryScreen().availableGeometry()
        self.move(scr.x() + scr.width() - self.W - 40,
                  scr.y() + (scr.height() - self.H) // 2)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(30)
        QTimer.singleShot(300, self._fix_window)
        QTimer.singleShot(500, self.show_hint)

    # ---------- 绘制 ----------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        bx = self.pad_x + self.parallax
        by = self.pad_top + self.float_y + self.bounce_y
        # 分身合奏：缩小版同款麦麦从主体身后探出、左右摇摆；与气泡绑定，点击才消失
        if self.ensemble_on or self.ensemble_hiding:
            now = time.time()
            if self.ensemble_hiding:
                k = 1.0 - min(1.0, (now - self.ensemble_t0) / 0.35)  # 退场缩小
            else:
                k = min(1.0, (now - self.ensemble_t0) / 0.35)        # 进场放大
            if k > 0.02:
                main_cx = bx + self.iw / 2
                base_cy = by + self.ih * 0.5
                for side, phase in ((-1, 0.0), (1, 1.7)):
                    s = 0.5 * k
                    sway = 9 * math.sin(self.t * 3.0 + phase)
                    cx = main_cx + side * (self.iw * 0.60) + side * sway
                    cy = base_cy + 4 * math.sin(self.t * 2.5 + phase)
                    ang = side * 8 * math.sin(self.t * 2.5 + phase)
                    p.save()
                    p.translate(cx, cy)
                    p.rotate(ang)
                    p.scale(s, s)
                    p.drawPixmap(-self.iw / 2, -self.ih / 2, self.pix)
                    p.restore()
        # 主体
        p.drawPixmap(int(bx), int(by), self.pix)

    # ---------- 主循环 ----------
    def tick(self):
        self.t += 0.08
        self.float_y = 6 * math.sin(self.t)
        self.bounce_v += 0.9
        self.bounce_y += self.bounce_v
        if self.bounce_y >= 0:
            self.bounce_y, self.bounce_v = 0.0, 0.0
        self.parallax += (self.parallax_target - self.parallax) * 0.12
        # 分身合奏退场完成 → 收回遮罩（去除分身可点区域，恢复透明区点击穿透）
        if self.ensemble_hiding and time.time() - self.ensemble_t0 > 0.35:
            self.ensemble_hiding = False
            self._build_mask(False)
        # 爱心上浮（重建列表，避免索引错位/访问已删除控件）
        alive = []
        for lab, step in self.hearts:
            step += 1
            if step >= 30:
                lab.hide()
                lab.deleteLater()
            else:
                lab.move(lab.x(), lab.y() - 2)
                alive.append((lab, step))
        self.hearts = alive
        if self.bubble.isVisible():
            self._place_bubble()
        self.update()

    # ---------- 气泡 ----------
    def show_hint(self):
        self._bubble("欢迎您来～", 3200)

    # ---------- 形状 & macOS 原生置顶 ----------
    def _fix_window(self):
        # 1) 仅不透明像素可点，透明区穿透（不被宠物挡点击）
        try:
            self._build_mask(False)
        except Exception:
            pass
        # 2) macOS：切到别的 App 也不隐藏、且置顶
        try:
            import objc
            from Cocoa import NSStatusWindowLevel
            view = objc.objc_object(c_void_p=int(self.winId()))
            nswin = view.window()
            if nswin:
                nswin.setHidesOnDeactivate_(False)
                nswin.setLevel_(NSStatusWindowLevel)
        except Exception:
            pass

    # ---------- 外部消息通道 ----------
    def poll_queue(self):
        """每 0.5s 检查一次外部消息队列，有新消息就用气泡说出来并弹一下。"""
        try:
            with open(self.queue_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            ts = float(data.get("ts", 0))
            text = (data.get("text") or "").strip()
            if not text or ts <= self.last_ts:
                return
            self.last_ts = ts
            self.bounce_v = -12
            self._bubble(text)
            # 推荐含 ≥2 份麦麦 → 触发分身合奏（与气泡绑定，点麦麦才消失）
            # 优先读结构化字段 fries；未提供时回退到数文字（兼容手动推送）
            fries = data.get("fries")
            if fries is None:
                fries = text.count("麦麦")
            if fries >= 2:
                self.play_ensemble()
            else:
                self.hide_ensemble()
        except Exception:
            pass  # 文件不存在/正在写入都忽略

    # ---------- 分身合奏动画 ----------
    def _build_mask(self, include_clones):
        """构建点击/显示遮罩；include_clones=True 时把分身区域也纳入（动画期间才需要）。"""
        try:
            bmp = self.pix.toImage().createAlphaMask()
            region = QRegion(bmp).translated(self.pad_x, self.pad_top)
            rb = region.boundingRect()
            region = region.united(QRegion(rb.adjusted(-18, -14, 18, 10)))
            bubble_zone = QRegion(self.pad_x - 32, 2,
                                  self.iw + 64, self.pad_top + self.ih)
            region = region.united(bubble_zone)
            if include_clones:
                cw = int(self.iw * 0.5) + 34
                chh = int(self.ih * 0.5) + 34
                main_cx = self.pad_x + self.iw / 2
                cy = int(self.pad_top + self.ih * 0.5)
                for side in (-1, 1):
                    zx = int(main_cx + side * self.iw * 0.62 - cw / 2)
                    region = region.united(QRegion(zx, cy - chh // 2, cw, chh))
            self.setMask(region)
        except Exception:
            pass

    def play_ensemble(self):
        # 与气泡绑定：进场放大后持续摇摆，直到 hide_ensemble（点击麦麦时调用）
        if not self.ensemble_on:
            self.ensemble_on = True
            self.ensemble_hiding = False
            self.ensemble_t0 = time.time()
            self._build_mask(True)
        self.bounce_v = -12

    def hide_ensemble(self):
        # 开始退场（缩小），0.35s 后由 tick 收回遮罩
        if self.ensemble_on and not self.ensemble_hiding:
            self.ensemble_on = False
            self.ensemble_hiding = True
            self.ensemble_t0 = time.time()

    def _place_bubble(self):
        self.bubble.adjustSize()
        w = self.bubble.width()
        h = self.bubble.height()
        bx = self.pad_x + self.iw / 2 - w / 2
        # 贴在麦麦头顶，跟随浮动；限制最低 y 避免被窗口顶边裁切
        by = self.pad_top + self.float_y - h - 6
        self.bubble.move(max(4, int(bx)), max(4, int(by)))

    def _bubble(self, text, ms=0):
        # 贴麦麦头的气泡：不自动消失，由点击宠物消除
        # 文案格式：菜品一行、『共X大卡』另起一行（推送未手动换行则自动补）
        if "\n" not in text and "共" in text:
            text = text.replace("共", "\n共", 1)
        # 用富文本让『共X大卡』那一行字号更小（11px vs 正文 15px）
        html = "<br>".join(
            f'<span style="font-size:11px;color:#C8102E">{ln}</span>'
            if "共" in ln else
            f'<span style="font-size:15px;color:#C8102E">{ln}</span>'
            for ln in text.split("\n")
        )
        self.bubble.setText(html)
        self._place_bubble()
        self.bubble.show()
        self.bubble.raise_()

    # ---------- 交互 ----------
    def react(self):
        self.bounce_v = -14
        self._bubble(random.choice(PHRASES))
        for _ in range(6):
            lab = QLabel(random.choice(HEART_CHARS), self)
            lab.setStyleSheet(
                "color:%s; font: 20px 'Arial'; background:transparent;"
                % random.choice(HEART_COLORS))
            lab.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            lab.adjustSize()
            hx = self.pad_x + self.iw / 2 + random.randint(-44, 44)
            hy = self.pad_top + self.ih * 0.3
            lab.move(int(hx), int(hy))
            lab.show()
            lab.raise_()
            self.hearts.append((lab, 0))

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self.close()
            return
        if e.button() == Qt.LeftButton:
            self.dragging = True
            self.moved = False
            self.press_global = e.globalPosition().toPoint()
            self.drag_offset = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self.dragging:
            gp = e.globalPosition().toPoint()
            if self.press_global and (
                abs(gp.x() - self.press_global.x()) > 4
                or abs(gp.y() - self.press_global.y()) > 4
            ):
                self.moved = True
            self.move(gp - self.drag_offset)
        else:
            cx = e.position().x() - (self.pad_x + self.iw / 2)
            self.parallax_target = max(-16, min(16, cx * 0.07))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.dragging = False
            if not self.moved:
                if self.bubble.isVisible():
                    # 点击麦麦 → 关闭当前气泡，同时收掉分身合奏动画
                    self.bubble.hide()
                    self.hide_ensemble()
                    self.bounce_v = -8
                else:
                    self.react()

    def leaveEvent(self, e):
        self.parallax_target = 0.0

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    pet = Pet()
    pet.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
