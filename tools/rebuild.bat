@echo off
chcp 65001
echo 正在重新打包应用程序...
pyinstaller --onefile main.py --collect-all streamlit --add-data "logo.png;." --add-data "app.py;." --add-data "auto_updater.py;." --add-data "version.json;." --icon="logo.png" --name="MICE TICKETING APP"
echo 打包完成！
pause