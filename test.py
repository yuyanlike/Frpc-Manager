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

"""
带有托盘应用和用户界面的WebUI管理器
"""
class App:
	def __init__(self, root):
		self.icon = None
		self.root = root
		self.root.geometry('350x200')  # 设置窗口大小
		self.root.protocol("WM_DELETE_WINDOW", self.hide)
		self.root.title("FRPC WebUI Manager")
		self.webui_process = None
		
		# 创建按钮
		self.start_button = tk.Button(root, text='启动WebUI', command=self.start_webui, bg='#00d26a')
		self.stop_button = tk.Button(root, text='停止WebUI', command=self.stop_webui, bg='#f56c6c')
		self.open_button = tk.Button(root, text='打开WebUI管理页面', command=self.open_webui, bg='#409eff')
		self.hide_button = tk.Button(root, text='隐藏窗口', command=self.hide, bg='#909399')
		self.exit_button = tk.Button(root, text='退出应用', command=self.exit_app)
		
		# 布局
		self.start_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
		self.stop_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
		self.open_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
		self.hide_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
		self.exit_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
	
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
			python_executable = ".\\venv\\Scripts\\python.exe"  # Windows
			
			# 启动子进程
			self.webui_process = subprocess.Popen([python_executable, "webuiapi.py"])
			# self.webui_process = subprocess.Popen(['python', "webuiapi.py"])
			tkinter.messagebox.showinfo('信息', 'WebUI已启动')
	
	def stop_webui(self):
		if self.webui_process is not None:
			self.webui_process.terminate()
			self.webui_process.wait()  # 等待进程结束
			self.webui_process = None
			tkinter.messagebox.showinfo('信息', 'WebUI已停止')
	
	def open_webui(self):
		if self.is_flask_running():
			webbrowser.open_new_tab("http://localhost:19999")  # 你的Flask应用地址
		else:
			tkinter.messagebox.showerror('错误', 'WebUI未运行')
	
	def hide(self):
		self.root.withdraw()
	
	def show(self):
		self.root.deiconify()
	
	def exit_app(self):
		if self.webui_process is not None:
			self.webui_process.terminate()
			self.webui_process = None
		self.icon.stop()
		self.root.quit()
	
	def run_icon(self):
		image = Image.open("./webui/favicon.ico")  # 你的图标地址
		menu = (item('打开WebUI管理页面', self.open_webui),
		        item('启动WebUI', self.start_webui),
		        item('停止WebUI', self.stop_webui),
		        item('显示窗口', self.show),
		        item('退出应用', self.exit_app))
		self.icon = icon("name", image, "FRPC WebUI Manager", menu)
		self.icon.run()


if __name__ == "__main__":
	root = tk.Tk()
	app = App(root)
	icon_thread = threading.Thread(target=app.run_icon)
	icon_thread.start()
	root.mainloop()
