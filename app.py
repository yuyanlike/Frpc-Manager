import subprocess
import threading
import tkinter as tk
import tkinter.messagebox
import webbrowser

import psutil
import requests
from PIL import Image
from pystray import Icon as icon
from pystray import MenuItem as item


class App:
	def __init__(self):
		self.root = tk.Tk()
		self.root.withdraw()  # 隐藏窗口
		self.webui_process = None
		self.status_item = item(lambda text: '当前WebUI正在运行 ✓' if self.is_flask_running() else '当前WebUI未运行 X',
		                        lambda text: text)
		
		# 创建托盘菜单
		self.menu = (self.status_item,
		             item('打开WebUI管理页面', self.open_webui),
		             item('启动WebUI', self.start_webui),
		             item('停止WebUI', self.stop_webui),
		             item('退出应用', self.exit_app))
		
		# 创建托盘图标
		image = Image.open("./webui/favicon.ico")  # 你的图标地址
		self.icon = icon("name", image, "FRPC WebUI Manager", self.menu)
	
	@staticmethod
	def is_port_in_use(port):
		portsinuse = [conn.laddr[1] for conn in psutil.net_connections()]
		return port in portsinuse
	
	@staticmethod
	def is_flask_running():
		try:
			response = requests.get("http://localhost:19999", timeout=1)
			return response.status_code == 200
		except requests.exceptions.RequestException:
			return False
	
	def start_webui(self):
		if self.is_port_in_use(19999):
			tkinter.messagebox.showerror('错误', '端口19999已被占用')
		else:
			# 指定 Python 解释器路径，确保使用正确的虚拟环境
			# python_executable = "./venv/bin/python"  # Unix/Linux
			# python_executable = ".\\venv\\Scripts\\python.exe"  # Windows
			#
			# # 启动子进程
			# self.webui_process = subprocess.Popen([python_executable, "webuiapi.py"])
			self.webui_process = subprocess.Popen(['python', "webuiapi.py"])
			tkinter.messagebox.showinfo('信息', 'WebUI已启动')
	
	def stop_webui(self):
		if self.webui_process is not None:
			self.webui_process.terminate()
			self.webui_process.wait()  # 等待进程结束
			self.webui_process = None
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
