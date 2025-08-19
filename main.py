#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能会务机票助手 - 主启动脚本

这个脚本用于启动Streamlit应用，确保在正确的Web环境下运行。
当打包为exe文件时，这个脚本会自动启动Streamlit服务器并打开浏览器。
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

# 设置环境变量确保UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

def get_app_path():
    """获取app.py的路径"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe文件
        app_dir = os.path.dirname(sys.executable)
        app_path = os.path.join(app_dir, 'app.py')
        if not os.path.exists(app_path):
            # 如果在exe目录找不到，尝试在临时目录查找
            app_path = os.path.join(sys._MEIPASS, 'app.py')
    else:
        # 如果是开发环境
        app_path = os.path.join(os.path.dirname(__file__), 'app.py')
    
    return app_path

def find_free_port(start_port=8501):
    """查找可用端口"""
    import socket
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return start_port  # 如果都不可用，返回默认端口

def main():
    """主函数"""
    print("[INFO] 正在启动智能会务机票助手...")
    
    # 获取app.py路径
    app_path = get_app_path()
    
    if not os.path.exists(app_path):
        print(f"[ERROR] 错误：找不到应用文件 {app_path}")
        input("按任意键退出...")
        return
    
    print(f"[INFO] 应用路径：{app_path}")
    
    # 查找可用端口
    port = find_free_port()
    print(f"[INFO] 使用端口：{port}")
    
    try:
        # 构建streamlit命令
        cmd = [
            sys.executable, 
            "-m", 
            "streamlit", 
            "run", 
            app_path,
            "--server.port", 
            str(port),
            "--server.headless", 
            "false",
            "--browser.gatherUsageStats", 
            "false"
        ]
        
        print("[INFO] 启动命令：", " ".join(cmd))
        print("[INFO] 正在启动Streamlit服务器...")
        
        # 启动streamlit进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        # 等待服务器启动
        time.sleep(3)
        
        # 检查进程是否还在运行
        if process.poll() is None:
            print("[SUCCESS] Streamlit服务器启动成功！")
            
            # 自动打开浏览器
            url = f"http://localhost:{port}"
            print(f"[INFO] 应用地址：{url}")
            print("[INFO] 正在打开浏览器...")
            
            try:
                webbrowser.open(url)
            except Exception as e:
                print(f"[WARNING] 无法自动打开浏览器：{e}")
                print(f"请手动访问：{url}")
            
            print("\n[INFO] 应用已启动，请在浏览器中使用。")
            print("[INFO] 关闭此窗口将停止应用服务。")
            print("\n按 Ctrl+C 或关闭窗口来停止服务...")
            
            # 等待进程结束
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n[INFO] 正在停止服务...")
                process.terminate()
                process.wait()
                print("[SUCCESS] 服务已停止。")
        else:
            # 进程启动失败
            stdout, stderr = process.communicate()
            print("[ERROR] Streamlit启动失败！")
            print("标准输出：", stdout)
            print("错误输出：", stderr)
            input("按任意键退出...")
            
    except Exception as e:
        print(f"[ERROR] 启动过程中发生错误：{e}")
        input("按任意键退出...")

if __name__ == "__main__":
    main()