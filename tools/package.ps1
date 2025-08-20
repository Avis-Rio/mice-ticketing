# 智能会务机票助手打包脚本
Write-Host "正在打包智能会务机票助手..." -ForegroundColor Green
Write-Host ""

# 激活虚拟环境
& ".\venv\Scripts\Activate.ps1"

# 检查PyInstaller是否已安装
Write-Host "检查PyInstaller..." -ForegroundColor Yellow
$pyinstallerCheck = python -m pip show pyinstaller 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller未安装，正在安装..." -ForegroundColor Yellow
    python -m pip install pyinstaller
}

# 执行打包命令
Write-Host "开始打包..." -ForegroundColor Yellow
python -m PyInstaller --onefile main.py --collect-all streamlit --add-data "logo.png;." --add-data "app.py;." --add-data "auto_updater.py;." --add-data "version.json;." --icon="logo.png" --name="智能会务机票助手"

if ($LASTEXITCODE -eq 0) {
    Write-Host "" 
    Write-Host "打包完成！" -ForegroundColor Green
    Write-Host "生成的exe文件位于 dist 目录中" -ForegroundColor Green
} else {
    Write-Host "" 
    Write-Host "打包失败！" -ForegroundColor Red
}

Write-Host ""
Write-Host "按任意键继续..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")