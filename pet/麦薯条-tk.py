# -*- coding: utf-8 -*-
"""麦薯条 · 桌面宠物（Qt 真透明浮空版）
运行：python 麦薯条-tk.py（需 PySide6）
右键点它或按 Esc 退出。透明区不挡桌面点击。
"""
import sys, os, json, math, random
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtWidgets import QApplication, QWidget, QLabel

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fries_mascot.png")

PHRASES = [
    "i'm lovin' it 🍟", "你今天开心吗？", "一起加油呀～", "饿了吗？我看着呢",
    "欢迎回来！", "摸鱼时间到～", "今天也要元气满满", "薯条给你比心❤",
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
        self.iw, self.ih = self.pix.width(), self.pix.height()
        self.pad_x, self.pad_top, self.pad_bot = 46, 64, 16
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

        # 交互状态
        self.dragging = False
        self.drag_offset = QPoint()
        self.press_global = None
        self.moved = False

        # 气泡
        self.bubble = QLabel(self)
        self.bubble.setStyleSheet(
            "background: rgba(255,255,255,242); color:#C8102E;"
            "border:2px solid #FFD23F; border-radius:14px;"
            "padding:5px 12px; font: 14px 'PingFang SC';"
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

        # 居中
        scr = QApplication.primaryScreen().availableGeometry()
        self.move(scr.x() + (scr.width() - self.W) // 2,
                  scr.y() + (scr.height() - self.H) // 2)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(30)
        QTimer.singleShot(500, self.show_hint)

    # ---------- 绘制 ----------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawPixmap(int(self.pad_x + self.parallax),
                     int(self.pad_top + self.float_y + self.bounce_y),
                     self.pix)

    # ---------- 主循环 ----------
    def tick(self):
        self.t += 0.08
        self.float_y = 6 * math.sin(self.t)
        self.bounce_v += 0.9
        self.bounce_y += self.bounce_v
        if self.bounce_y >= 0:
            self.bounce_y, self.bounce_v = 0.0, 0.0
        self.parallax += (self.parallax_target - self.parallax) * 0.12
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
        self.update()

    # ---------- 气泡 ----------
    def show_hint(self):
        self._bubble("欢迎您来", 3200)

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
            self._bubble(text, int(data.get("ms", 7000)))
        except Exception:
            pass  # 文件不存在/正在写入都忽略

    def _bubble(self, text, ms=2600):
        self.bubble.setText(text)
        self.bubble.adjustSize()
        bx = self.pad_x + self.parallax + self.iw / 2 - self.bubble.width() / 2
        by = self.pad_top + self.float_y - self.bubble.height() - 6
        self.bubble.move(max(2, int(bx)), max(2, int(by)))
        self.bubble.show()
        self.bubble.raise_()
        QTimer.singleShot(ms, self.bubble.hide)

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
