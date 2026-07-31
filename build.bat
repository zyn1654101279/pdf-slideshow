@echo off
chcp 65001 >nul
echo Installing dependencies...
pip install -r requirements.txt -q
echo Building exe...
pyinstaller --onefile --noconsole --name "PDF幻灯片" --clean pdf_slideshow.py
echo Done! Check dist\ folder.
pause
