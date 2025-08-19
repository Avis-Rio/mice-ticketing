@echo off
echo 正在打包智能会务机票助手...
echo.

pyinstaller --onefile main.py --collect-all streamlit --add-data "logo.png;." --add-data "app.py;." --add-data "auto_updater.py;." --add-data "version.json;." --icon="logo.png" --name="智能会务机票助手"

echo.
echo 打包完成！
echo 生成的exe文件位于 dist 目录中
echo.
pause