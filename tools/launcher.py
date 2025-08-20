#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能会务机票助手 - 启动器

使用streamlit.web.bootstrap.run()直接启动应用，避免PyInstaller打包后的子进程问题。
这种方式可以确保在exe环境下正常运行Streamlit Web界面。
"""

import os
import sys
import time
import webbrowser
import socket
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
    try:
        print("[INFO] 正在启动智能会务机票助手...")
        print(f"[DEBUG] Python版本: {sys.version}")
        print(f"[DEBUG] 当前工作目录: {os.getcwd()}")
        print(f"[DEBUG] 是否为打包环境: {getattr(sys, 'frozen', False)}")
        
        if getattr(sys, 'frozen', False):
            print(f"[DEBUG] 临时目录: {sys._MEIPASS}")
            print(f"[DEBUG] 可执行文件路径: {sys.executable}")
        
        # 获取app.py路径
        app_path = get_app_path()
        print(f"[DEBUG] 尝试的app.py路径: {app_path}")
        
        if not os.path.exists(app_path):
            print(f"[ERROR] 错误：找不到应用文件 {app_path}")
            # 列出可用文件
            if getattr(sys, 'frozen', False):
                temp_dir = sys._MEIPASS
                print(f"[DEBUG] 临时目录内容: {os.listdir(temp_dir)}")
            input("按任意键退出...")
            return
        
        print(f"[INFO] 应用路径：{app_path}")
        
        # 查找可用端口
        port = find_free_port()
        print(f"[INFO] 使用端口：{port}")
        
        # 导入streamlit模块
        print("[DEBUG] 正在导入streamlit模块...")
        import streamlit.web.bootstrap
        print("[DEBUG] streamlit模块导入成功")
        
        print("[INFO] 正在启动Streamlit服务器...")
        
        # 延迟打开浏览器
        def open_browser():
            time.sleep(5)  # 等待服务器启动
            url = f"http://localhost:{port}"
            print(f"[INFO] 应用地址：{url}")
            print("[INFO] 正在打开浏览器...")
            try:
                webbrowser.open(url)
                print("[SUCCESS] 浏览器已打开！")
            except Exception as e:
                print(f"[WARNING] 无法自动打开浏览器：{e}")
                print(f"请手动访问：{url}")
        
        # 在后台线程中打开浏览器
        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        print("[INFO] 准备启动Streamlit...")
        print("\n按 Ctrl+C 或关闭窗口来停止服务...")
        
        # 直接使用streamlit.web.bootstrap.run启动
        print(f"[DEBUG] 启动streamlit，脚本路径: {app_path}")
        
        # 设置Streamlit配置参数
        import streamlit.config as config
        config.set_option('server.port', port)
        config.set_option('server.headless', True)
        config.set_option('browser.gatherUsageStats', False)
        config.set_option('server.enableCORS', False)
        config.set_option('server.enableXsrfProtection', False)
        
        streamlit.web.bootstrap.run(app_path, '', [], {})
        
    except KeyboardInterrupt:
        print("\n[INFO] 正在停止服务...")
        print("[SUCCESS] 服务已停止。")
    except ImportError as e:
        print(f"[ERROR] 无法导入Streamlit模块：{e}")
        print("请确保已正确安装Streamlit")
        input("按任意键退出...")
    except Exception as e:
        print(f"[ERROR] 启动过程中发生错误：{e}")
        import traceback
        traceback.print_exc()
        input("按任意键退出...")

if __name__ == "__main__":
    main()