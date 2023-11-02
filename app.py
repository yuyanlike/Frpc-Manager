import logging
import os
import platform
import subprocess
import sys
import threading
import webbrowser

import psutil
import requests
from PIL import Image
from flask import Flask, jsonify, request, send_from_directory
from pystray import Icon as icon
from pystray import MenuItem as item
from werkzeug.serving import make_server

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask application
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
# 存储frpc进程的字典
frpc_processes = {}
# 全局工作目录配置
if getattr(sys, 'frozen', False):
	# 如果应用被打包，使用 '_MEIPASS' 目录
	base_dir = sys._MEIPASS
else:
	# 否则，使用当前目录
	base_dir = os.path.dirname(__file__)


# Tray application
class TrayApp:
	def __init__(self):
		self.webui_server = None
		self.status_item = item(lambda text: '当前WebUI正在运行 ✓' if self.is_flask_running() else '当前WebUI未运行 X',
		                        lambda text: text)
		
		# 创建托盘菜单
		self.menu = (self.status_item,
		             item('打开WebUI管理页面', self.open_webui),
		             item('启动WebUI', self.start_webui),
		             item('停止WebUI(这会关闭所有的FRPC客户端)', self.stop_webui),
		             item('退出应用(同上)', self.exit_app))
		
		icon_path = os.path.join(base_dir, 'webui', 'favicon.ico')
		# 创建托盘图标
		image = Image.open(icon_path)
		self.icon = icon("name", image, "FRPC客户端管理器", self.menu)
		# 在 TrayApp 初始化时启动 Flask 应用
		self.start_webui()
	
	@staticmethod
	def is_port_in_use(port):
		portsinuse = [conn.laddr[1] for conn in psutil.net_connections()]
		return port in portsinuse
	
	@staticmethod
	def is_flask_running():
		try:
			response = requests.get("http://localhost:19999", timeout=2)
			return response.status_code == 200
		except requests.exceptions.RequestException:
			return False
	
	def start_webui(self):
		if self.is_port_in_use(19999):
			logging.error('WebUI启动失败，端口19999已被占用')
		else:
			self.webui_server = make_server('0.0.0.0', 19999, app)
			server_thread = threading.Thread(target=self.webui_server.serve_forever)
			server_thread.start()
			self.icon.update_menu()
			logging.info('WebUI已启动')
	
	def stop_webui(self):
		stop_frpc()
		if self.webui_server is not None:
			self.webui_server.shutdown()
			self.webui_server = None
			logging.info('WebUI已停止')
		self.icon.update_menu()
	
	def open_webui(self):
		if self.is_flask_running():
			webbrowser.open_new_tab("http://localhost:19999")  # 你的Flask应用地址
		else:
			logging.info('WebUI未运行')
	
	def exit_app(self):
		stop_frpc()
		if self.webui_server is not None:
			self.webui_server.shutdown()
			self.webui_server = None
			logging.info('WebUI已停止')
		self.icon.stop()


# Flask routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
	if path != "" and os.path.exists(os.path.join(base_dir, "webui", path)):
		return send_from_directory(os.path.join(base_dir, 'webui'), path)
	else:
		return send_from_directory(os.path.join(base_dir, 'webui'), 'index.html')


@app.route('/api/configs', methods=['GET'])
def get_configs():
	"""
	获取./frpc目录中的配置文件列表并以JSON响应的方式返回。
	:return: 包含符合指定扩展名的配置文件名的JSON响应
	"""
	config_extensions = ['.toml', '.json', '.yaml', '.ini']
	configs = []
	
	for config_file in os.listdir('./frpc'):
		if os.path.splitext(config_file)[1] in config_extensions:
			configs.append(config_file)
	logging.info('获取配置文件成功，共有' + str(len(configs)) + '个配置文件')
	return jsonify(configs)


@app.route('/api/configs', methods=['POST'])
def create_config():
	"""
	创建一个新的配置文件并将其保存到./frpc目录中。
	:return: 包含成功状态的JSON响应
	"""
	config_name = request.json.get('name')
	
	for char in config_name:
		if not char.isalnum() and char not in "（）()_.":
			logging.error('创建配置文件失败: ' + config_name + '非法字符')
			return jsonify({'status': 'error', 'message': '配置文件名非法'})
	
	for ext in [".toml", ".ini", ".yaml", ".json"]:
		if config_name.endswith(ext):
			break
	else:
		config_name = config_name.rsplit('.', 1)[0] + ".toml"
	
	config_file_path = f'./frpc/{config_name}'
	
	if os.path.isfile(config_file_path):
		logging.error('创建配置文件失败: ' + config_name + '已存在')
		return jsonify({'status': 'error', 'message': '配置文件已存在'})
	
	config_content = request.json.get('content')
	
	try:
		with open(config_file_path, 'w') as f:
			f.write(config_content)
	except Exception as e:
		logging.error('创建配置文件失败: ' + config_name)
		return jsonify({'status': 'error', 'message': str(e)})
	logging.info('创建配置文件成功: ' + config_name)
	return jsonify({'status': 'success'})


@app.route('/api/configs/<config_name>', methods=['GET'])
def get_config(config_name):
	"""
	读取指定的配置文件内容。

	:param config_name: 配置文件名
	:return: 包含配置文件内容的JSON响应
	"""
	try:
		with open(f'./frpc/{config_name}', 'r') as f:
			config_content = f.read()
	except Exception as e:
		logging.error('读取配置文件失败: ' + config_name)
		return jsonify({'status': 'error', 'message': str(e)})
	logging.info('读取配置文件成功: ' + config_name)
	return jsonify({'content': config_content})


@app.route('/api/configs/<config_name>', methods=['PUT'])
def edit_config(config_name):
	"""
	编辑指定的配置文件内容。

	:param config_name: 配置文件名
	:return: 包含成功状态的JSON响应
	"""
	config_content = request.json.get('content')
	try:
		with open(f'./frpc/{config_name}', 'w') as f:
			f.write(config_content)
	except Exception as e:
		logging.error('配置文件写入失败: ' + config_name)
		return jsonify({'status': 'error', 'message': str(e)})
	logging.info('编辑配置文件成功: ' + config_name)
	return jsonify({'status': 'success'})


@app.route('/api/configs/<config_name>', methods=['DELETE'])
def delete_config(config_name):
	"""
	删除指定的配置文件。

	:param config_name: 配置文件名
	:return: 包含成功状态的JSON响应
	"""
	if config_name in frpc_processes:
		return jsonify({'status': 'error', 'message': '请先停止客户端'})
	try:
		os.remove(f'./frpc/{config_name}')
	except Exception as e:
		logging.error('配置文件删除失败: ' + config_name)
		return jsonify({'status': 'error', 'message': str(e)})
	logging.info('配置文件删除成功: ' + config_name)
	return jsonify({'status': 'success'})


@app.route('/api/processes', methods=['GET'])
def get_processes():
	"""
	获取所有正在运行的frpc进程的配置文件名。

	:return: 包含所有正在运行的frpc进程的配置文件名的JSON响应
	"""
	# 检查每个运行的进程是否还在运行
	for config_file, frpc_process in list(frpc_processes.items()):
		if frpc_process.poll() is not None:  # 如果进程已经结束
			del frpc_processes[config_file]  # 从字典中删除
	logging.info('正在运行的客户端: ' + ' '.join(frpc_processes.keys()))
	return jsonify(list(frpc_processes.keys()))


@app.route('/api/processes', methods=['POST'])
def start_process():
	"""
	根据指定的配置文件启动一个frpc进程。

	:return: 包含成功状态的JSON响应
	"""
	config_name = request.json.get('name')
	if config_name in frpc_processes:
		return jsonify({'status': 'error', 'message': '客户端已启动'})
	try:
		frpc_process = subprocess.Popen(["./frpc/frpc", "-c", f"./frpc/{config_name}"], stdout=subprocess.PIPE,
		                                stderr=subprocess.PIPE)
		frpc_processes[config_name] = frpc_process
	except Exception as e:
		logging.error('启动客户端失败: ' + config_name)
		return jsonify({'status': 'error', 'message': str(e)})
	logging.info('启动客户端成功: ' + config_name)
	return jsonify({'status': 'success'})


@app.route('/api/processes/<config_name>', methods=['DELETE'])
def stop_process(config_name):
	"""
	停止指定的frpc进程。

	:param config_name: 配置文件名
	:return: 包含成功状态的JSON响应
	"""
	
	frpc_process = frpc_processes.get(config_name)
	if frpc_process:
		frpc_process.terminate()
		del frpc_processes[config_name]
	else:
		return jsonify({'status': 'error', 'message': '客户端未启动'})
	logging.info('停止客户端成功: ' + config_name)
	return jsonify({'status': 'success'})


@app.route('/api/stop_all', methods=['GET'])
def stop_all_processes():
	"""
	停止所有正在运行的frpc进程。

	:return: 包含成功状态的JSON响应
	"""
	if stop_frpc() is None:
		return jsonify({'status': 'error', 'message': '客户端未启动'})
	logging.info('停止所有客户端成功')
	return jsonify({'status': 'success'})


def stop_frpc():
	"""
	停止所有正在运行的frpc进程。
	:return:
	"""
	for frpc_process in frpc_processes.values():
		frpc_process.terminate()
	frpc_processes.clear()
	logging.info('停止所有客户端成功')


def windows_check():
	"""
	如果当前是在Windows或者MacOS中运行，启动应用的时候自动从浏览器打开127.0.0.1:19999
	:return:
	"""
	if platform.system() in ('Windows', 'Darwin'):
		logging.info('Windows或者MacOS中运行，WebUI界面')
		webbrowser.open('http://localhost:19999')


# 检查文件夹是否存在不存在则创建
def mkdir_if_not_exist():
	path = './frpc'
	if not os.path.exists(path):
		os.makedirs(path)


def main():
	tray_app = None
	try:
		tray_app = TrayApp()
		icon_thread = threading.Thread(target=tray_app.icon.run)
		icon_thread.start()
		windows_check()
		mkdir_if_not_exist()
	except KeyboardInterrupt:
		if tray_app is not None:
			tray_app.exit_app()
		logging.info('停止所有客户端成功')


if __name__ == "__main__":
	main()
