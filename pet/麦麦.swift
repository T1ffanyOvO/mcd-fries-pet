import Cocoa

// 麦当劳麦麦桌面挂件 —— 透明悬浮窗口，可拖动，带轻微摇摆待机动画
// 仅含基础形态，交互功能后续按需添加

class FriesView: NSView {

    override func draw(_ dirtyRect: NSRect) {
        super.draw(dirtyRect)
        drawFries(in: bounds)
    }

    private func drawFries(in rect: NSRect) {
        let cx = rect.width / 2

        // ---- 薯条（先画，底部会被盒子盖住）----
        let fryColor = NSColor(red: 1.0, green: 0.78, blue: 0.17, alpha: 1.0)   // 麦当劳黄 #FFC72C
        let tipColor = NSColor(red: 0.83, green: 0.52, blue: 0.09, alpha: 1.0)  // 烤色顶端
        let positions: [CGFloat] = [-48, -28, -8, 12, 32, 52]
        let heights:  [CGFloat] = [78, 102, 86, 108, 80, 68]
        let boxTopY: CGFloat = 120
        for i in 0..<positions.count {
            let fw: CGFloat = 17
            let fh = heights[i]
            let fx = cx + positions[i] - fw / 2
            let fy = boxTopY - fh + 12
            let fry = NSBezierPath(roundedRect: NSRect(x: fx, y: fy, width: fw, height: fh), xRadius: 8, yRadius: 8)
            fryColor.setFill(); fry.fill()
            let tip = NSBezierPath(roundedRect: NSRect(x: fx, y: fy + fh - 24, width: fw, height: 24), xRadius: 8, yRadius: 8)
            tipColor.setFill(); tip.fill()
        }

        // ---- 红色包装盒 ----
        let boxTopW: CGFloat = 138
        let boxBotW: CGFloat = 100
        let boxTopY2: CGFloat = 120
        let boxBotY:  CGFloat = 272
        let box = NSBezierPath()
        box.move(to: NSPoint(x: cx - boxTopW / 2, y: boxTopY2))
        box.line(to: NSPoint(x: cx + boxTopW / 2, y: boxTopY2))
        box.line(to: NSPoint(x: cx + boxBotW / 2, y: boxBotY))
        box.line(to: NSPoint(x: cx - boxBotW / 2, y: boxBotY))
        box.close()
        NSColor(red: 0.855, green: 0.161, blue: 0.110, alpha: 1.0).setFill()  // 麦当劳红 #DA291C
        box.fill()

        // 盒子开口（暗红椭圆）
        let opening = NSBezierPath(ovalIn: NSRect(x: cx - boxTopW / 2, y: boxTopY2 - 9, width: boxTopW, height: 18))
        NSColor(red: 0.55, green: 0.07, blue: 0.05, alpha: 1.0).setFill()
        opening.fill()

        // 盒身白色弧线装饰
        let stripe = NSBezierPath()
        stripe.move(to: NSPoint(x: cx - 32, y: 205))
        stripe.appendArc(withCenter: NSPoint(x: cx, y: 205), radius: 32, startAngle: 180, endAngle: 0)
        NSColor(white: 1.0, alpha: 0.85).setStroke()
        stripe.lineWidth = 5
        stripe.stroke()
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!

    func applicationDidFinishLaunching(_ notification: Notification) {
        let size = NSSize(width: 220, height: 300)

        window = NSWindow(contentRect: NSRect(origin: .zero, size: size),
                          styleMask: [.borderless],
                          backing: .buffered,
                          defer: false)
        window.isOpaque = false
        window.backgroundColor = .clear
        window.level = .floating          // 置顶悬浮
        window.isMovableByWindowBackground = true  // 点击即可拖动
        window.collectionBehavior = [.canJoinAllSpaces, .stationary]
        window.hasShadow = false

        let view = FriesView(frame: NSRect(origin: .zero, size: size))
        view.wantsLayer = true
        window.contentView = view

        // 右键菜单：退出
        let menu = NSMenu()
        let quit = NSMenuItem(title: "退出麦麦", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        quit.target = NSApp
        menu.addItem(quit)
        view.menu = menu

        // 初始位置：屏幕底部居中（离底边 120pt）
        if let screen = NSScreen.main {
            let x = screen.visibleFrame.midX - size.width / 2
            let y = screen.visibleFrame.minY + 120
            window.setFrameOrigin(NSPoint(x: x, y: y))
        }
        window.makeKeyAndOrderFront(nil)

        // 轻微摇摆待机动画
        if let layer = view.layer {
            let anim = CABasicAnimation(keyPath: "transform.rotation.z")
            anim.fromValue = -0.05
            anim.toValue = 0.05
            anim.duration = 2.6
            anim.autoreverses = true
            anim.repeatCount = .infinity
            anim.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
            layer.add(anim, forKey: "sway")
        }
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.accessory)   // 不在 Dock 显示，更像挂件
app.run()
