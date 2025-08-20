@echo off
chcp 65001 > nul
echo ========================================
echo 智能会务机票助手 - 打包脚本
echo ========================================
echo.

echo [1/5] 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误：未找到Python环境，请先安装Python
    pause
    exit /b 1
)

echo [2/5] 检查依赖包...
pip show pyinstaller > nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
)

echo [3/5] 清理旧的构建文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "__pycache__" rmdir /s /q "__pycache__"

echo [4/5] 开始打包应用程序...
echo 这可能需要几分钟时间，请耐心等待...
pyinstaller app.spec

if %errorlevel% equ 0 (
    echo [5/5] 打包完成！
    echo.
    echo 可执行文件位置：dist\智能会务机票助手.exe
    echo 文件大小：
    dir "dist\智能会务机票助手.exe" | find ".exe"
    echo.
    echo 打包成功！应用程序已生成。
) else (
    echo 打包失败！请检查错误信息。
    echo.
    echo 常见问题解决方案：
    echo 1. 确保所有依赖都已安装：pip install -r requirements.txt
    echo 2. 检查app.py文件是否存在语法错误
    echo 3. 确保logo.png文件存在
)

echo.
echo 按任意键退出...
pause > nul