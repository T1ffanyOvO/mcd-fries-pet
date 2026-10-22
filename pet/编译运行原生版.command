#!/bin/bash
# 进阶版：用 Swift 编译原生「像素透明」悬浮挂件（需本机装有 Xcode 或 Command Line Tools）
# 双击运行；若提示“无法打开”，请右键 → 打开，或终端执行：chmod +x "编译运行原生版.command"
cd "$(dirname "$0")"
xcrun swiftc -framework Cocoa "麦麦.swift" -o "麦麦" && "./麦麦" &
