# PDF幻灯片 (PDF Slideshow)

将PDF中的图片提取出来，在指定显示器上全屏轮播。适合竖屏副屏做电子相框。

## 功能

- 拖拽PDF到程序图标即可运行
- 自动提取PDF中所有图片（过滤小图标）
- 缩略图预览，自由选择要轮播的图片
- 全屏无边框显示在目标显示器（自动识别竖屏）
- 鼠标移到顶部显示窗口控制按钮（最小化/最大化/关闭）
- 支持手动切换、暂停、右键菜单

## 使用方法

1. 下载 [Releases](../../releases) 中的 `PDF幻灯片.exe`
2. 将任意PDF文件拖拽到exe图标上
3. 在弹出窗口中勾选想要的图片，设置轮播间隔
4. 点击「开始轮播」，图片将在竖屏显示器上全屏展示

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
pyinstaller --onefile --noconsole --name "PDF幻灯片" pdf_slideshow.py
```

或直接运行 `build.bat`。

## 环境要求

- Windows 10/11
- Python 3.10+（构建时需要）
- 多显示器环境（程序自动选择竖屏显示器）

## 依赖

- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - PDF图片提取
- [Pillow](https://github.com/python-pillow/Pillow) - 图片处理
- [PyInstaller](https://github.com/pyinstaller/pyinstaller) - 打包exe
