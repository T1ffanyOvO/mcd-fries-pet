#!/usr/bin/env python3
# 诊断脚本：极简红色不透明窗口
# 用途：判断这台 Mac 能否从终端正常显示 Tk 窗口。
#   - 如果看到红窗口、白字 → Tk 显示没问题，问题在挂件脚本本身
#   - 如果啥都没有 → Tk 框架在这台机器从终端启动有故障，需换方案
import tkinter as tk

root = tk.Tk()
root.title("诊断窗口")
root.geometry("340x200+200+200")
root.configure(bg='red')
label = tk.Label(root, text="如果看到这个红窗口，\n说明 Tk 能正常显示 ✅",
                 bg='red', fg='white', font=('PingFang SC', 18))
label.pack(expand=True, fill='both')
root.mainloop()
