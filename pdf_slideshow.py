"""
PDF图片全屏幻灯片 - 显示器1
拖拽PDF文件到本程序图标，提取图片后在显示器1全屏轮播。
"""
import sys
import os
import ctypes
import ctypes.wintypes
import threading
import io
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

# ============ 配置 ============
DEFAULT_INTERVAL = 10  # 默认轮播间隔（秒）
THUMB_SIZE = (140, 180)  # 缩略图尺寸
BG_COLOR = "#1a1a2e"  # 全屏背景色


# ============ 显示器检测 ============
def get_monitors():
    """枚举所有显示器，返回 [(left, top, right, bottom, is_primary), ...]"""
    monitors = []

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.wintypes.DWORD),
            ("rcMonitor", ctypes.wintypes.RECT),
            ("rcWork", ctypes.wintypes.RECT),
            ("dwFlags", ctypes.wintypes.DWORD),
        ]

    MonitorEnumProc = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL,
        ctypes.wintypes.HMONITOR,
        ctypes.wintypes.HDC,
        ctypes.POINTER(ctypes.wintypes.RECT),
        ctypes.wintypes.LPARAM,
    )

    def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        ctypes.windll.user32.GetMonitorInfoW(hMonitor, ctypes.byref(info))
        r = info.rcMonitor
        is_primary = bool(info.dwFlags & 1)
        monitors.append((r.left, r.top, r.right, r.bottom, is_primary))
        return True

    ctypes.windll.user32.EnumDisplayMonitors(
        None, None, MonitorEnumProc(callback), 0
    )
    return monitors


def find_target_monitor(monitors):
    """
    找到目标显示器（显示器1）：
    优先选择竖屏（height > width），否则选第一个非主屏，最后fallback到第一个。
    """
    if not monitors:
        return (0, 0, 1080, 1920)

    # 优先找竖屏显示器
    for m in monitors:
        w = m[2] - m[0]
        h = m[3] - m[1]
        if h > w:
            return m[:4]

    # 没有竖屏就找非主屏
    for m in monitors:
        if not m[4]:
            return m[:4]

    return monitors[0][:4]


# ============ PDF图片提取 ============
def extract_images_from_pdf(pdf_path):
    """从PDF中提取所有图片，返回 [(page_num, img_index, PIL.Image), ...]"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        messagebox.showerror("缺少依赖", "需要安装 PyMuPDF:\npip install PyMuPDF")
        sys.exit(1)

    images = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        img_list = page.get_images(full=True)

        for img_idx, img_info in enumerate(img_list):
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                if base_image:
                    img_bytes = base_image["image"]
                    img = Image.open(io.BytesIO(img_bytes))
                    # 过滤太小的图片（可能是图标/装饰）
                    if img.width >= 200 and img.height >= 200:
                        images.append((page_num + 1, img_idx + 1, img))
            except Exception:
                continue

    doc.close()
    return images


# ============ 图片选择窗口 ============
class ImageSelector:
    def __init__(self, images, pdf_name):
        self.images = images  # [(page, idx, PIL.Image), ...]
        self.selected = []  # 选中的PIL.Image列表
        self.result = None

        self.root = tk.Tk()
        self.root.title(f"选择要轮播的图片 - {pdf_name}")
        self.root.configure(bg="#f0f0f0")

        # 窗口居中
        win_w, win_h = 800, 600
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")

        # 顶部提示
        header = tk.Frame(self.root, bg="#f0f0f0")
        header.pack(fill="x", padx=10, pady=(10, 5))
        tk.Label(
            header,
            text=f"共提取到 {len(images)} 张图片，勾选后点击「开始轮播」",
            font=("Microsoft YaHei UI", 11),
            bg="#f0f0f0",
        ).pack(side="left")

        # 间隔设置
        interval_frame = tk.Frame(header, bg="#f0f0f0")
        interval_frame.pack(side="right")
        tk.Label(
            interval_frame, text="间隔(秒):", font=("Microsoft YaHei UI", 10), bg="#f0f0f0"
        ).pack(side="left")
        self.interval_var = tk.StringVar(value=str(DEFAULT_INTERVAL))
        tk.Spinbox(
            interval_frame,
            from_=3,
            to=60,
            width=4,
            textvariable=self.interval_var,
            font=("Microsoft YaHei UI", 10),
        ).pack(side="left", padx=(4, 0))

        # 缩略图区域（带滚动条）
        container = tk.Frame(self.root)
        container.pack(fill="both", expand=True, padx=10, pady=5)

        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg="white")

        self.scroll_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # 生成缩略图
        self.check_vars = []
        self.thumb_images = []  # 防止GC回收

        cols = 4
        for i, (page, idx, img) in enumerate(images):
            row = i // cols
            col = i % cols

            frame = tk.Frame(self.scroll_frame, bg="white", padx=5, pady=5)
            frame.grid(row=row, column=col, sticky="nsew")

            # 缩略图
            thumb = img.copy()
            thumb.thumbnail(THUMB_SIZE, Image.LANCZOS)
            # 转为RGB（处理RGBA/P模式）
            if thumb.mode not in ("RGB", "L"):
                thumb = thumb.convert("RGB")
            tk_img = ImageTk.PhotoImage(thumb)
            self.thumb_images.append(tk_img)

            var = tk.BooleanVar(value=True)  # 默认全选
            self.check_vars.append(var)

            cb = tk.Checkbutton(frame, variable=var, bg="white", activebackground="white")
            cb.pack()

            lbl = tk.Label(frame, image=tk_img, bg="white", bd=1, relief="solid")
            lbl.pack()

            info_lbl = tk.Label(
                frame,
                text=f"P{page}-{idx}\n{img.width}×{img.height}",
                font=("Microsoft YaHei UI", 8),
                bg="white",
                fg="#666",
            )
            info_lbl.pack()

        # 底部按钮
        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(
            btn_frame,
            text="全选",
            command=self.select_all,
            font=("Microsoft YaHei UI", 10),
            padx=15,
        ).pack(side="left")
        tk.Button(
            btn_frame,
            text="取消全选",
            command=self.deselect_all,
            font=("Microsoft YaHei UI", 10),
            padx=15,
        ).pack(side="left", padx=(8, 0))

        tk.Button(
            btn_frame,
            text="开始轮播",
            command=self.start_slideshow,
            font=("Microsoft YaHei UI", 11, "bold"),
            bg="#4a90d9",
            fg="white",
            padx=25,
            pady=4,
        ).pack(side="right")

        tk.Button(
            btn_frame,
            text="退出",
            command=self.root.destroy,
            font=("Microsoft YaHei UI", 10),
            padx=15,
        ).pack(side="right", padx=(0, 8))

    def select_all(self):
        for v in self.check_vars:
            v.set(True)

    def deselect_all(self):
        for v in self.check_vars:
            v.set(False)

    def start_slideshow(self):
        self.selected = [
            self.images[i][2] for i, v in enumerate(self.check_vars) if v.get()
        ]
        if not self.selected:
            messagebox.showwarning("提示", "请至少选择一张图片")
            return
        try:
            self.interval = int(self.interval_var.get())
        except ValueError:
            self.interval = DEFAULT_INTERVAL
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self.selected, getattr(self, "interval", DEFAULT_INTERVAL)


# ============ 全屏幻灯片 ============
HOVER_ZONE_H = 6  # 顶部感应区高度(px)
CTRL_BAR_H = 36  # 控制栏高度
CTRL_HIDE_DELAY = 1200  # 鼠标离开后隐藏延迟(ms)


class FullscreenSlideshow:
    def __init__(self, images, monitor_rect, interval):
        self.images = images
        self.interval = interval
        self.monitor = monitor_rect  # (left, top, right, bottom)
        self.current = 0
        self.paused = False
        self.tk_images = []
        self.is_fullscreen = True
        self.ctrl_visible = False
        self._hide_job = None

        self.mon_w = self.monitor[2] - self.monitor[0]
        self.mon_h = self.monitor[3] - self.monitor[1]

        self.root = tk.Tk()
        self.root.title("PDF幻灯片")

        # 全屏无边框，定位到目标显示器
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry(
            f"{self.mon_w}x{self.mon_h}+{self.monitor[0]}+{self.monitor[1]}"
        )
        self.root.configure(bg=BG_COLOR)

        # 图片标签
        self.label = tk.Label(self.root, bg=BG_COLOR)
        self.label.pack(fill="both", expand=True)

        # 预缩放所有图片
        for img in self.images:
            scaled = self.scale_to_fill(img, self.mon_w, self.mon_h)
            if scaled.mode not in ("RGB", "L"):
                scaled = scaled.convert("RGB")
            self.tk_images.append(ImageTk.PhotoImage(scaled))

        # ---- 顶部控制栏 ----
        self.ctrl_bar = tk.Frame(
            self.root, bg="#222222", height=CTRL_BAR_H
        )
        # 初始不显示（place管理）
        self._build_ctrl_buttons()

        # ---- 顶部感应区（透明触发条）----
        self.hover_zone = tk.Frame(self.root, bg="", cursor="arrow")
        self.hover_zone.place(x=0, y=0, relwidth=1, height=HOVER_ZONE_H)
        self.hover_zone.bind("<Enter>", self._show_ctrl)
        self.hover_zone.configure(bg=BG_COLOR)
        # 让感应区视觉透明：用和背景一样的颜色

        # 控制栏的离开隐藏
        self.ctrl_bar.bind("<Leave>", self._schedule_hide)
        self.ctrl_bar.bind("<Enter>", self._cancel_hide)

        # 绑定按键
        self.root.bind("<Escape>", lambda e: self.quit())
        self.root.bind("<Right>", lambda e: self.next_image())
        self.root.bind("<Left>", lambda e: self.prev_image())
        self.root.bind("<space>", lambda e: self.toggle_pause())
        self.root.bind("<Button-3>", self.show_context_menu)
        self.root.bind("<Motion>", self._on_motion)

        # 右键菜单
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="上一张 (←)", command=self.prev_image)
        self.menu.add_command(label="下一张 (→)", command=self.next_image)
        self.menu.add_command(label="暂停/继续 (空格)", command=self.toggle_pause)
        self.menu.add_separator()
        self.menu.add_command(label="退出 (Esc)", command=self.quit)

        # 最小化后的恢复按钮（小浮动窗口）
        self.restore_btn = None

        # 显示第一张
        self.show_current()

        # 自动轮播
        self.auto_advance()

    # ---- 控制栏构建 ----
    def _build_ctrl_buttons(self):
        """在控制栏右侧放置 最小化/最大化/关闭 三个按钮"""
        btn_data = [
            ("─", self.do_minimize, "#cccccc", "#3a3a3a"),   # 最小化
            ("□", self.do_max_restore, "#cccccc", "#3a3a3a"),  # 最大化/还原
            ("✕", self.quit, "#ffffff", "#e81123"),           # 关闭（红底）
        ]
        # 从右往左排列
        for i, (text, cmd, fg, hover_bg) in enumerate(reversed(btn_data)):
            btn = tk.Label(
                self.ctrl_bar,
                text=text,
                font=("Segoe UI", 11),
                fg=fg,
                bg="#222222",
                width=4,
                height=1,
                cursor="hand2",
            )
            btn.pack(side="right", fill="y")
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            # 悬停效果
            btn.bind("<Enter>", lambda e, b=btn, bg=hover_bg: b.configure(bg=bg))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#222222"))

        # 左侧标题
        tk.Label(
            self.ctrl_bar,
            text="PDF幻灯片",
            font=("Microsoft YaHei UI", 9),
            fg="#aaaaaa",
            bg="#222222",
        ).pack(side="left", padx=(10, 0))

    # ---- 控制栏显示/隐藏 ----
    def _show_ctrl(self, event=None):
        self._cancel_hide()
        if not self.ctrl_visible:
            self.ctrl_bar.place(x=0, y=0, relwidth=1, height=CTRL_BAR_H)
            self.ctrl_bar.lift()
            self.ctrl_visible = True

    def _schedule_hide(self, event=None):
        self._cancel_hide()
        self._hide_job = self.root.after(CTRL_HIDE_DELAY, self._hide_ctrl)

    def _cancel_hide(self, event=None):
        if self._hide_job:
            self.root.after_cancel(self._hide_job)
            self._hide_job = None

    def _hide_ctrl(self):
        self.ctrl_bar.place_forget()
        self.ctrl_visible = False

    def _on_motion(self, event):
        """鼠标离开顶部区域时自动隐藏控制栏"""
        if self.ctrl_visible and event.y > CTRL_BAR_H + HOVER_ZONE_H:
            self._schedule_hide()

    # ---- 窗口控制 ----
    def do_minimize(self):
        """最小化：隐藏主窗口，在显示器上显示一个小恢复按钮"""
        self._hide_ctrl()
        self.root.withdraw()

        # 创建小恢复按钮窗口
        self.restore_btn = tk.Toplevel()
        self.restore_btn.overrideredirect(True)
        self.restore_btn.attributes("-topmost", True)
        # 放在目标显示器右上角
        btn_w, btn_h = 48, 48
        rx = self.monitor[2] - btn_w - 10
        ry = self.monitor[1] + 10
        self.restore_btn.geometry(f"{btn_w}x{btn_h}+{rx}+{ry}")
        self.restore_btn.configure(bg="#333333")

        lbl = tk.Label(
            self.restore_btn,
            text="▶",
            font=("Segoe UI", 16),
            fg="white",
            bg="#333333",
            cursor="hand2",
        )
        lbl.pack(fill="both", expand=True)
        lbl.bind("<Button-1>", lambda e: self.do_restore_from_minimize())
        lbl.bind("<Enter>", lambda e: lbl.configure(bg="#555555"))
        lbl.bind("<Leave>", lambda e: lbl.configure(bg="#333333"))

    def do_restore_from_minimize(self):
        """从最小化恢复"""
        if self.restore_btn:
            self.restore_btn.destroy()
            self.restore_btn = None
        self.root.deiconify()
        self.root.attributes("-topmost", True)

    def do_max_restore(self):
        """切换全屏 / 窗口模式"""
        self._hide_ctrl()
        if self.is_fullscreen:
            # 切到窗口模式：80%大小居中
            win_w = int(self.mon_w * 0.8)
            win_h = int(self.mon_h * 0.8)
            x = self.monitor[0] + (self.mon_w - win_w) // 2
            y = self.monitor[1] + (self.mon_h - win_h) // 2
            self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
            self.is_fullscreen = False
        else:
            # 恢复全屏
            self.root.geometry(
                f"{self.mon_w}x{self.mon_h}+{self.monitor[0]}+{self.monitor[1]}"
            )
            self.is_fullscreen = True

    # ---- 图片显示 ----
    def scale_to_fill(self, img, target_w, target_h):
        """等比缩放填满屏幕（cover模式，裁切多余部分）"""
        img_w, img_h = img.size
        scale = max(target_w / img_w, target_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        img_resized = img.resize((new_w, new_h), Image.LANCZOS)

        # 居中裁切
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return img_resized.crop((left, top, left + target_w, top + target_h))

    def show_current(self):
        self.label.configure(image=self.tk_images[self.current])

    def next_image(self):
        self.current = (self.current + 1) % len(self.images)
        self.show_current()

    def prev_image(self):
        self.current = (self.current - 1) % len(self.images)
        self.show_current()

    def toggle_pause(self):
        self.paused = not self.paused

    def auto_advance(self):
        if not self.paused:
            self.next_image()
        self.root.after(self.interval * 1000, self.auto_advance)

    def show_context_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def quit(self):
        if self.restore_btn:
            self.restore_btn.destroy()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ============ 主入口 ============
def main():
    # 高DPI支持
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    # 检查是否通过拖拽传入了PDF
    if len(sys.argv) < 2:
        # 没有拖拽文件，弹出提示
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "PDF图片幻灯片",
            "使用方法：\n\n将PDF文件拖拽到本程序图标上即可运行。\n\n"
            "程序会提取PDF中的图片，\n让你在显示器1上全屏轮播。",
        )
        root.destroy()
        sys.exit(0)

    pdf_path = sys.argv[1]

    if not os.path.isfile(pdf_path):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("错误", f"文件不存在：\n{pdf_path}")
        root.destroy()
        sys.exit(1)

    if not pdf_path.lower().endswith(".pdf"):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("错误", "请拖入PDF文件。")
        root.destroy()
        sys.exit(1)

    pdf_name = os.path.basename(pdf_path)

    # 提取图片
    images = extract_images_from_pdf(pdf_path)

    if not images:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("未找到图片", f"PDF中未提取到有效图片：\n{pdf_name}")
        root.destroy()
        sys.exit(0)

    # 选择图片
    selector = ImageSelector(images, pdf_name)
    selected, interval = selector.run()

    if not selected:
        sys.exit(0)

    # 检测显示器
    monitors = get_monitors()
    target = find_target_monitor(monitors)

    # 全屏轮播
    slideshow = FullscreenSlideshow(selected, target, interval)
    slideshow.run()


if __name__ == "__main__":
    main()
