#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
import sys

def main():
    print("正在重新打包应用程序...")
    
    # 设置编码
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # 构建PyInstaller命令
    cmd = [
        'pyinstaller',
        '--onefile',
        'main.py',
        '--collect-all', 'streamlit',
        '--add-data', 'logo.png;.',
        '--add-data', 'app.py;.',
        '--add-data', 'auto_updater.py;.',
        '--add-data', 'version.json;.',
        '--icon=logo.png',
        '--name=MICE TICKETING APP'
    ]
    
    try:
        print("执行命令:", ' '.join(cmd))
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        print("打包成功！")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {e}")
        print(f"错误输出: {e.stderr}")
    except Exception as e:
        print(f"执行错误: {e}")

if __name__ == '__main__':
    main()