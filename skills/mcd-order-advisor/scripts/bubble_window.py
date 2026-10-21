# -*- coding: utf-8 -*-
"""独立气泡浮窗：作为薯条挂件的兜底/主播报通道。
用法：bubble_window.py "<文字>" [显示毫秒]
不依赖主挂件是否运行，自己弹一个置顶气泡窗口，到时自毁。
"""
import sys
from ctypes import c_void_p
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QLabel

try:
    import objc
    from Cocoa import NSStatusWindowLevel
    _HAVE_OBJC = True
except Exception:
    _HAVE_OBJC = False


def main():
    text = sys.argv[1] if len(sys.argv) > 1 else "i'm lovin' it 🍟"
    ms = int(sys.argv[2]) if len(sys.argv) > 2 else 20000

    app = QApplication(sys.argv)
    w = QLabel()
    w.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    w.setAttribute(Qt.WA_TranslucentBackground, True)
    w.setText(text)
    w.setStyleSheet(
        "background: rgba(255,255,255,247); color:#C8102E;"
        "border:2px solid #FFD23F; border-radius:16px;"
        "padding:10px 18px; font: 15px 'PingFang SC';"
    )
    w.adjustSize()
    ww, wh = w.width(), w.height()
    scr = QApplication.primaryScreen().availableGeometry()
    # 屏幕水平居中、顶部下方一点：最显眼，不挡菜单栏也不挡中间对话框
    x = scr.x() + (scr.width() - ww) // 2
    y = scr.y() + 90
    w.move(x, y)
    w.show()
    # macOS 原生置顶 + 切到别的 App 也不隐藏
    if _HAVE_OBJC:
        try:
            view = objc.objc_object(c_void_p=int(w.winId()))
            nswin = view.window()
            if nswin:
                nswin.setHidesOnDeactivate_(False)
                nswin.setLevel_(NSStatusWindowLevel)
        except Exception:
            pass
    QTimer.singleShot(ms, app.quit)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
