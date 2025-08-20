#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包执行脚本
"""

import subprocess
import sys
import os

def main():
    print("🚀 开始打包智能会务机票助手...")
    
    # 构建PyInstaller命令
    cmd = [
        sys.executable, 
        "-m", 
        "PyInstaller",
        "--onefile",
        "main.py",
        "--collect-all",
        "streamlit",
        "--add-data",
        "logo.png;.",
        "--add-data",
        "app.py;.",
        "--add-data",
        "auto_updater.py;.",
        "--add-data",
        "version.json;.",
        "--icon",
        "logo.png",
        "--name",
        "MICE TICKETING APP"
    ]
    
    print("📦 执行命令：", " ".join(cmd))
    print("⏳ 正在打包，请稍候...")
    
    try:
        # 执行打包命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 打包成功！")
            print("📁 生成的exe文件位于 dist 目录中")
            
            # 检查生成的文件
            dist_dir = "dist"
            if os.path.exists(dist_dir):
                files = os.listdir(dist_dir)
                print(f"📋 生成的文件: {files}")
        else:
            print("❌ 打包失败！")
            print("错误输出：", result.stderr)
            
    except Exception as e:
        print(f"❌ 执行过程中发生错误：{e}")

if __name__ == "__main__":
    main()