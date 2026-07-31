# PDF幻灯片 / 图片幻灯片

将PDF中的图片或直接拖入的图片/文件夹，在竖屏显示器上全屏轮播。适合副屏做电子相框。

## 两个版本

| 程序 | 输入 | 大小 | 说明 |
|------|------|------|------|
| `PDF幻灯片.exe` | PDF文件 | 73MB | 提取PDF内嵌图片 |
| `图片幻灯片.exe` | 图片/文件夹 | 32MB | 直接拖图片，更轻量 |

## 功能

- 拖拽PDF/图片/文件夹到程序图标即可运行
- 自动提取/扫描所有图片（过滤小图标）
- 缩略图预览，自由选择要轮播的图片
- 全屏无边框显示在目标显示器（自动识别竖屏）
- 鼠标移到顶部显示窗口控制按钮（最小化/最大化/关闭）
- 支持手动切换、暂停、右键菜单

## 使用方法

1. 下载 [Releases](../../releases) 中的exe
2. 将PDF文件或图片/文件夹拖拽到exe图标上
3. 在弹出窗口中勾选想要的图片，设置轮播间隔
4. 点击「开始轮播」，图片将在竖屏显示器上全屏展示

**图片版支持格式：** JPG、PNG、BMP、GIF、WebP、TIFF

## 轮播操作

| 操作 | 说明 |
|------|------|
| 鼠标移到顶部 | 显示窗口控制栏 |
| ← → | 上一张 / 下一张 |
| 空格 | 暂停 / 继续 |
| 右键 | 菜单 |
| Esc | 退出 |

## 从源码构建

```bash
pip install -r requirements.txt

# PDF版
pyinstaller --onefile --noconsole --name "PDF幻灯片" pdf_slideshow.py

# 图片版（不需要PyMuPDF）
pyinstaller --onefile --noconsole --name "图片幻灯片" image_slideshow.py
```

## 环境要求

- Windows 10/11
- Python 3.10+（构建时需要）
- 多显示器环境（程序自动选择竖屏显示器）

## 依赖

- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - PDF图片提取（仅PDF版）
- [Pillow](https://github.com/python-pillow/Pillow) - 图片处理
- [PyInstaller](https://github.com/pyinstaller/pyinstaller) - 打包exe
