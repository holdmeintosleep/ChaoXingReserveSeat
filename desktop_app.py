import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys
import json
import webbrowser
import requests
import shutil
import zipfile
import logging
import datetime
import subprocess

APP_DATA_DIR = os.path.join(os.path.expanduser('~'), 'ChaoxingReserveSeat')
if not os.path.exists(APP_DATA_DIR):
    os.makedirs(APP_DATA_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(APP_DATA_DIR, 'app.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

APP_NAME = "超星座位预约"
APP_VERSION = "1.0.0"
BACKEND_PORT = 5000
GITHUB_REPO = "https://api.github.com/repos/your-username/ChaoXingReserveSeat/releases/latest"

window = None
backend_thread = None
is_closing = False
flask_app = None
backend_process = None

def get_app_data_dir():
    return APP_DATA_DIR

def get_config_path():
    return os.path.join(APP_DATA_DIR, 'config.json')

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def init_config():
    config_path = get_config_path()
    template_path = resource_path('config.template.json')
    
    if not os.path.exists(config_path) and os.path.exists(template_path):
        shutil.copy(template_path, config_path)
        logging.info(f"配置文件已初始化: {config_path}")
    
    return config_path

def start_backend():
    global backend_process
    
    try:
        resource_dir = resource_path('.')
        
        env = os.environ.copy()
        env['PYTHONPATH'] = resource_dir + os.pathsep + env.get('PYTHONPATH', '')
        
        backend_process = subprocess.Popen(
            [sys.executable, '-c', f'''
import sys
sys.path.insert(0, "{resource_dir}")
from backend.app import create_app
app = create_app()
app.config["RESOURCE_PATH"] = "{resource_dir}"
app.config["CONFIG_PATH"] = "{get_config_path()}"
app.config["STATIC_FOLDER"] = "{os.path.join(resource_dir, "frontend", "dist")}"
app.run(host="127.0.0.1", port={BACKEND_PORT}, debug=False, use_reloader=False)
'''],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        logging.info("后端服务已启动")
        return True
    except Exception as e:
        logging.error(f"启动后端服务失败: {e}")
        return False

def stop_backend():
    global is_closing, backend_process
    is_closing = True
    if backend_process:
        try:
            backend_process.terminate()
            backend_process.wait(timeout=3)
        except:
            backend_process.kill()
        logging.info("后端服务已停止")

def check_for_updates():
    try:
        response = requests.get(GITHUB_REPO, timeout=10)
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get('tag_name', 'v1.0.0').lstrip('v')
            download_url = data.get('assets', [{}])[0].get('browser_download_url', '')
            
            if latest_version > APP_VERSION and download_url:
                return {
                    'available': True,
                    'version': latest_version,
                    'url': download_url
                }
    except Exception as e:
        logging.debug(f"检查更新失败: {e}")
    
    return {'available': False}

def download_update(url, version):
    try:
        download_path = os.path.join(get_app_data_dir(), f'update_{version}.zip')
        
        response = requests.get(url, stream=True, timeout=30)
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
        
        return download_path
    except Exception as e:
        logging.error(f"下载更新失败: {e}")
        raise

def extract_update(zip_path):
    try:
        extract_dir = os.path.join(get_app_data_dir(), 'update_temp')
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        return extract_dir
    except Exception as e:
        logging.error(f"解压更新失败: {e}")
        raise

def apply_update(extract_dir):
    try:
        app_dir = os.path.dirname(sys.executable)
        
        for item in os.listdir(extract_dir):
            s = os.path.join(extract_dir, item)
            d = os.path.join(app_dir, item)
            
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.move(s, d)
            else:
                if os.path.exists(d):
                    os.remove(d)
                shutil.move(s, d)
        
        shutil.rmtree(extract_dir)
        for f in os.listdir(get_app_data_dir()):
            if f.startswith('update_') and f.endswith('.zip'):
                os.remove(os.path.join(get_app_data_dir(), f))
        
        logging.info("更新应用成功")
        return True
    except Exception as e:
        logging.error(f"应用更新失败: {e}")
        return False

def on_check_update():
    try:
        update_info = check_for_updates()
        if update_info['available']:
            result = messagebox.askyesno(
                "更新提示",
                f"发现新版本 {update_info['version']}，是否立即更新？"
            )
            if result:
                try:
                    zip_path = download_update(update_info['url'], update_info['version'])
                    extract_dir = extract_update(zip_path)
                    
                    if apply_update(extract_dir):
                        messagebox.showinfo("更新完成", "更新成功！应用将重启。")
                        os.startfile(sys.executable)
                        os._exit(0)
                    else:
                        messagebox.showerror("更新失败", "更新失败，请手动下载最新版本。")
                except Exception as e:
                    logging.error(f"更新过程出错: {e}")
                    messagebox.showerror("更新失败", f"更新失败: {str(e)}")
        else:
            messagebox.showinfo("检查更新", "当前已是最新版本。")
    except Exception as e:
        logging.error(f"检查更新失败: {e}")
        messagebox.showerror("检查更新", f"检查更新失败: {str(e)}")

def on_about():
    about_window = tk.Toplevel(window)
    about_window.title(f"关于 {APP_NAME}")
    about_window.geometry("300x200")
    about_window.resizable(False, False)
    
    ttk.Label(about_window, text=APP_NAME, font=('Arial', 16, 'bold')).pack(pady=10)
    ttk.Label(about_window, text=f"版本: {APP_VERSION}").pack(pady=5)
    ttk.Label(about_window, text="超星学习通座位预约与签到管理工具").pack(pady=5)
    ttk.Label(about_window, text="支持自动预约、定时签到等功能").pack(pady=5)
    
    ttk.Button(about_window, text="确定", command=about_window.destroy).pack(pady=10)

def on_exit():
    if messagebox.askyesno("退出确认", "确定要退出应用吗？"):
        stop_backend()
        window.destroy()

def open_browser():
    api_url = f'http://localhost:{BACKEND_PORT}'
    webbrowser.open(api_url)

def main():
    global window
    
    logging.info(f"启动 {APP_NAME} v{APP_VERSION}")
    
    init_config()
    
    success = start_backend()
    if not success:
        messagebox.showerror("启动失败", "无法启动后端服务，请检查日志。")
        return
    
    time.sleep(2)
    
    window = tk.Tk()
    window.title(f'{APP_NAME} v{APP_VERSION}')
    window.geometry('300x150')
    window.resizable(False, False)
    
    try:
        window.iconbitmap(resource_path('app.ico'))
    except:
        pass
    
    ttk.Button(window, text="打开预约管理界面", command=open_browser, width=25).pack(pady=15)
    
    menu_bar = tk.Menu(window)
    
    help_menu = tk.Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="检查更新", command=on_check_update)
    help_menu.add_command(label="关于", command=on_about)
    menu_bar.add_cascade(label="帮助", menu=help_menu)
    
    window.config(menu=menu_bar)
    
    window.protocol("WM_DELETE_WINDOW", on_exit)
    
    window.mainloop()

if __name__ == '__main__':
    main()