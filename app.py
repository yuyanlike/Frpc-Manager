import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog, ttk
import os
import subprocess
from glob import glob


class EditDialog(simpledialog.Dialog):
	def __init__(self, parent, title=None, text=None):
		self.text = text
		super().__init__(parent, title)
	
	def body(self, master):
		self.text_editor = scrolledtext.ScrolledText(master, width=50, height=20)
		self.text_editor.insert(tk.INSERT, self.text)
		self.text_editor.pack()
		# 在 ScrolledText 中捕获并处理回车键事件
		self.text_editor.bind('<KeyPress-Return>', self.newline)
	
	def newline(self, event=None):
		self.text_editor.insert(tk.INSERT, '\n')
		return 'break'
	
	def apply(self):
		self.text = self.text_editor.get('1.0', tk.END)
	
	def buttonbox(self):
		# remove default buttonbox
		box = tk.Frame(self)
		
		w = tk.Button(box, text="OK", width=10, command=self.ok, default="active")
		w.pack(side="left", padx=5, pady=5)
		
		w = tk.Button(box, text="Cancel", width=10, command=self.cancel)
		w.pack(side="left", padx=5, pady=5)
		
		self.bind("<Return>", self.ok)
		self.bind("<Escape>", self.cancel)
		
		box.pack()


class Application(tk.Frame):
	def __init__(self, master=None):
		super().__init__(master)
		self.master = master
		self.grid(sticky="nsew")
		self.create_widgets()
		self.processes = {}
		messagebox.showinfo("使用教程", "1. 新建配置文件\n"
		                                "2. 修改配置文件，输入你的配置文件内容保存。\n"
		                                "3. 选中配置文件，点击“启动”按钮启动客户端。启动后，在“正在运行的客户端”中可以看到你的客户端。\n"
		                                "4. 在“正在运行的客户端”中,选中已经启动的客户端点击停止按钮停止客户端。\n"
		                                "5. 修改和删除配置文件同上。")
		self.update_ui()
	
	def update_ui(self):
		# 保存当前选中的配置文件和客户端
		selected_config = self.config_list.curselection()
		selected_process = self.process_list.curselection()
		
		self.load_configs()
		self.load_processes()
		
		# 检查每个运行的进程是否还在运行
		for config_file, process in list(self.processes.items()):
			if process.poll() is not None:  # 如果进程已经结束
				del self.processes[config_file]  # 从字典中删除
				# 从正在运行的客户端列表中删除
				for i, item in enumerate(self.process_list.get(0, tk.END)):
					if item == config_file:
						self.process_list.delete(i)
						break
		
		# 恢复之前选中的配置文件和客户端
		if selected_config:
			self.config_list.selection_set(selected_config)
		if selected_process:
			self.process_list.selection_set(selected_process)
		
		# 每隔一秒更新一次界面
		self.master.after(1000, self.update_ui)
	
	def create_widgets(self):
		# Configure grid
		self.master.columnconfigure(0, weight=1)
		self.master.rowconfigure(0, weight=1)
		self.grid(sticky="nsew")
		
		for i in range(3):
			self.columnconfigure(i, weight=1)
		for i in range(4):
			self.rowconfigure(i, weight=1)
		
		# Configuration file list
		self.config_label = tk.Label(self, text="配置文件:")
		self.config_label.grid(row=0, column=0, sticky="w")
		
		self.config_list = tk.Listbox(self)
		self.config_list.grid(row=1, column=0, rowspan=3, sticky="nsew")
		self.config_list.bind('<<ListboxSelect>>', self.load_config)
		
		# Running process list
		self.process_label = tk.Label(self, text="正在运行的客户端:")
		self.process_label.grid(row=0, column=1, sticky="w")
		
		self.process_list = tk.Listbox(self)
		self.process_list.grid(row=1, column=1, rowspan=2, columnspan=2, sticky="nsew")
		
		# Buttons
		self.new_button = ttk.Button(self, text="新建", command=self.new_config)
		self.new_button.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
		
		self.edit_button = ttk.Button(self, text="编辑", command=self.edit_config)
		self.edit_button.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
		
		self.delete_button = ttk.Button(self, text="删除", command=self.delete_config)
		self.delete_button.grid(row=4, column=2, sticky="ew", padx=5, pady=5)
		
		self.start_button = ttk.Button(self, text="启动", command=self.start_client)
		self.start_button.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
		
		self.stop_button = ttk.Button(self, text="停止", command=self.stop_client)
		self.stop_button.grid(row=3, column=2, sticky="ew", padx=5, pady=5)
	
	def load_configs(self):
		configs = glob("./frpc/*")
		self.config_list.delete(0, tk.END)
		for config in configs:
			# 检查文件扩展名是否在列表中
			if os.path.splitext(config)[1] in ['.toml', '.json', '.yaml', '.ini']:
				self.config_list.insert(tk.END, os.path.basename(config))
	
	def load_processes(self):
		self.process_list.delete(0, tk.END)
		for config_file in self.processes:
			self.process_list.insert(tk.END, config_file)
	
	def load_config(self, event):
		# 检查是否有选中的配置文件
		if not self.config_list.curselection():
			return
		
		config_file = self.config_list.get(self.config_list.curselection())
		if not os.path.isfile("./frpc/" + config_file):
			messagebox.showerror("错误", "配置文件不存在")
			return
		
		with open("./frpc/" + config_file, 'r') as file:
			self.config_text = file.read()
	
	def new_config(self):
		config_file = simpledialog.askstring("新建配置文件", "请输入配置文件名(不带后缀):")
		if not config_file:
			return
		# 检查文件名是否非法字符串
		for char in config_file:
			if not char.isalnum() and char not in "（）()_.":
				messagebox.showerror("错误", "配置文件名非法")
				return
		# 检查输入是否带有后缀 .toml .ini .yaml  .json
		if config_file.endswith(".toml") or config_file.endswith(".ini") or config_file.endswith(
				".yaml") or config_file.endswith(".json"):
			config_file = config_file[:-4]
		
		config_file = config_file.rstrip('.') + ".toml"
		
		if os.path.isfile("./frpc/" + config_file):
			messagebox.showerror("错误", "配置文件已存在")
			return
		
		with open("./frpc/" + config_file, 'w') as file:
			file.write("")
		self.config_list.insert(tk.END, config_file)
	
	def edit_config(self):
		# 检查是否有选中的配置文件
		if not self.config_list.curselection():
			messagebox.showerror("错误", "没有选择配置文件")
			return
		
		config_file = self.config_list.get(self.config_list.curselection())
		
		dialog = EditDialog(self, text=self.config_text)
		if dialog.text != self.config_text:
			self.config_text = dialog.text
			with open("./frpc/" + config_file, 'w') as file:
				file.write(self.config_text)
			messagebox.showinfo("信息", "配置已保存")
	
	def delete_config(self):
		# 检查是否有选中的配置文件
		if not self.config_list.curselection():
			messagebox.showerror("错误", "没有选择配置文件")
			return
		
		config_file = self.config_list.get(self.config_list.curselection())
		
		if config_file in self.processes:
			messagebox.showerror("错误", "请先停止客户端")
			return
		
		os.remove("./frpc/" + config_file)
		self.config_list.delete(self.config_list.curselection())
		messagebox.showinfo("信息", "配置已删除")
	
	def start_client(self):
		# 检查是否有选中的配置文件
		if not self.config_list.curselection():
			messagebox.showerror("错误", "没有选择配置文件")
			return
		
		config_file = self.config_list.get(self.config_list.curselection())
		
		if config_file in self.processes:
			messagebox.showerror("错误", "客户端已启动")
			return
		
		try:
			# 将所有输出重定向到一个文件
			with open('app.log', 'a') as outfile:
				process = subprocess.Popen(["./frpc/frpc", "-c", "./frpc/" + config_file],
				                           stdout=outfile, stderr=outfile,
				                           creationflags=subprocess.CREATE_NO_WINDOW)
			self.processes[config_file] = process
			self.process_list.insert(tk.END, config_file)
			messagebox.showinfo("信息", "客户端已启动")
		except Exception as e:
			messagebox.showerror("错误", str(e))
	
	def stop_client(self):
		if not self.process_list.curselection():
			messagebox.showerror("错误", "没有选择客户端")
			return
		
		config_file = self.process_list.get(self.process_list.curselection())
		
		try:
			self.processes[config_file].terminate()
			del self.processes[config_file]
			self.process_list.delete(self.process_list.curselection())
			messagebox.showinfo("信息", "客户端已停止")
		except Exception as e:
			messagebox.showerror("错误", str(e))
	
	def quit(self):
		for process in self.processes.values():
			process.terminate()
		self.master.destroy()


root = tk.Tk()
root.title("frpc管理器")
app = Application(master=root)
root.protocol("WM_DELETE_WINDOW", app.quit)
root.mainloop()
