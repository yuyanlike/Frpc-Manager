import os
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.messagebox
import webbrowser

import psutil
import requests
from PIL import Image
from pystray import Icon as icon
from pystray import MenuItem as item

"""
带有一个托盘应用的WebUI管理器
"""


class App:
	def __init__(self):
		if getattr(sys, 'frozen', False):
			# 如果应用被打包，使用 '_MEIPASS' 目录
			base_dir = sys._MEIPASS
		else:
			# 否则，使用当前目录
			base_dir = os.path.dirname(__file__)
		icon_path = os.path.join(base_dir, 'webui', 'favicon.ico')
		Image.open(icon_path)
		self.root = tk.Tk()
		self.root.withdraw()  # 隐藏无用的tk窗口
		self.webui_process = None
		self.status_item = item(lambda text: '当前WebUI正在运行 ✓' if self.is_flask_running() else '当前WebUI未运行 X',
		                        lambda text: text)
		
		# 创建托盘菜单
		print(icon_path)
		self.menu = (self.status_item,
		             item('打开WebUI管理页面', self.open_webui),
		             item('启动WebUI', self.start_webui(base_dir)),
		             item('停止WebUI', self.stop_webui),
		             item('退出应用', self.exit_app))
		
		# 创建托盘图标
		image = Image.open(icon_path)
		self.icon = icon("name", image, "FRPC客户端管理器", self.menu)
	
	@staticmethod
	def is_port_in_use(port):
		portsinuse = [conn.laddr[1] for conn in psutil.net_connections()]
		return port in portsinuse
	
	@staticmethod
	def is_flask_running():
		try:
			response = requests.get("http://127.0.0.1:19999", timeout=1)
			return response.status_code == 200
		except requests.exceptions.RequestException:
			return False
	
	def start_webui(self, base_dir):
		if self.is_port_in_use(19999):
			tkinter.messagebox.showerror('错误', '端口19999已被占用')
		else:
			# 指定 Python 解释器路径，确保使用正确的虚拟环境
			# python_executable = "./venv/bin/python"  # Unix/Linux
			# python_executable = ".\\venv\\Scripts\\python.exe"  # Windows
			
			# 启动子进程
			webuiapi_path = os.path.join(base_dir, 'webuiapi.py')
			self.webui_process = subprocess.Popen(['python', webuiapi_path])
			# self.webui_process = subprocess.Popen([python_executable, webuiapi_path])
			tkinter.messagebox.showinfo('信息', 'WebUI已启动')
	
	def stop_webui(self):
		if self.webui_process is not None:
			self.webui_process.terminate()
			self.webui_process.wait()  # 等待进程结束
			self.webui_process = None
			tkinter.messagebox.showinfo('信息', 'WebUI已停止')
		self.icon.update_menu()
	
	def open_webui(self):
		if self.is_flask_running():
			webbrowser.open_new_tab("http://127.0.0.1:19999")  # 你的Flask应用地址
		else:
			tkinter.messagebox.showerror('错误', 'WebUI未运行')
	
	def exit_app(self):
		if self.webui_process is not None:
			self.webui_process.terminate()
			self.webui_process = None
		self.icon.stop()
		self.root.quit()


if __name__ == "__main__":
	app = App()
	icon_thread = threading.Thread(target=app.icon.run)
	icon_thread.start()
	app.root.mainloop()
