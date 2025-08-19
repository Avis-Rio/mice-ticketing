import requests
import os
import sys
import subprocess
from pathlib import Path
import tempfile
import hashlib
import json
from datetime import datetime

class AutoUpdater:
    def __init__(self, repo_owner, repo_name):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    
    def check_for_updates(self, current_version):
        """检查是否有新版本"""
        try:
            response = requests.get(f"{self.api_base}/releases/latest", timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name'].lstrip('v')
                
                if self.is_newer_version(latest_version, current_version):
                    return {
                        'has_update': True,
                        'version': latest_version,
                        'download_url': self.get_download_url(release_data),
                        'release_notes': release_data.get('body', '')
                    }
            return {'has_update': False}
        except Exception as e:
            print(f"检查更新失败: {e}")
            return {'has_update': False}
    
    def is_newer_version(self, latest, current):
        """比较版本号"""
        try:
            # 简单的版本号比较，假设格式为 x.y.z
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # 补齐版本号长度
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except:
            return False
    
    def get_download_url(self, release_data):
        """获取下载链接"""
        assets = release_data.get('assets', [])
        for asset in assets:
            if asset['name'].endswith('.exe'):
                return asset['browser_download_url']
        return None
    
    def download_and_install(self, download_url):
        """下载并安装更新"""
        try:
            # 下载新版本
            response = requests.get(download_url, stream=True)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exe')
            
            with temp_file as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 验证文件完整性（可选）
            if self.verify_file_integrity(temp_file.name):
                # 启动更新脚本
                self.start_update_process(temp_file.name)
                return True
            
        except Exception as e:
            print(f"更新失败: {e}")
        return False
    
    def verify_file_integrity(self, file_path):
        """验证文件完整性"""
        try:
            # 简单的文件大小检查
            file_size = os.path.getsize(file_path)
            return file_size > 1024 * 1024  # 至少1MB
        except:
            return False
    
    def start_update_process(self, new_exe_path):
        """启动更新进程"""
        try:
            current_exe = sys.executable
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe
                current_exe = sys.executable
            else:
                # 开发环境，不执行实际更新
                print(f"开发环境：模拟更新 {new_exe_path} -> {current_exe}")
                return
            
            update_script = f"""
@echo off
echo 正在更新应用程序...
timeout /t 3 /nobreak > nul
move "{new_exe_path}" "{current_exe}"
if %errorlevel% equ 0 (
    echo 更新完成，正在重启应用...
    start "" "{current_exe}"
) else (
    echo 更新失败，请手动更新
    pause
)
            """
            
            script_path = tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False, encoding='gbk')
            script_path.write(update_script)
            script_path.close()
            
            # 启动更新脚本并退出当前程序
            subprocess.Popen([script_path.name], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
            sys.exit(0)
            
        except Exception as e:
            print(f"启动更新进程失败: {e}")
            return False
    
    def get_current_exe_path(self):
        """获取当前exe文件路径"""
        if getattr(sys, 'frozen', False):
            return sys.executable
        else:
            return os.path.abspath(__file__)

class VersionManager:
    def __init__(self):
        self.version_file = Path("version.json")
        self.current_version = self.load_current_version()
    
    def load_current_version(self):
        """加载当前版本信息"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('version', '1.0.0')
            except:
                pass
        return '1.0.0'
    
    def save_version(self, version):
        """保存版本信息"""
        data = {
            'version': version,
            'updated_at': datetime.now().isoformat()
        }
        try:
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存版本信息失败: {e}")
    
    def get_version_info(self):
        """获取版本信息"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            'version': self.current_version,
            'updated_at': datetime.now().isoformat()
        }

# 测试函数
if __name__ == "__main__":
    # 测试版本管理
    vm = VersionManager()
    print(f"当前版本: {vm.current_version}")
    
    # 测试自动更新（需要实际的GitHub仓库）
    # updater = AutoUpdater("your-username", "mice-ticketing")
    # update_info = updater.check_for_updates(vm.current_version)
    # print(f"更新检查结果: {update_info}")