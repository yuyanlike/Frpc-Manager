# -*- coding: utf-8 -*-
"""
暂留 备份文件
"""


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
from flask_cors import CORS
from pystray import Icon as icon
from pystray import MenuItem as item
from werkzeug.serving import make_server

# Flask application
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
# 跨域配置
CORS(app, supports_credentials=True)
# 存储frpc进程的字典
frpc_processes = {}
# 全局工作目录配置
if getattr(sys, 'frozen', False):
	# 如果应用被打包，使用 '_MEIPASS' 目录
	base_dir = sys._MEIPASS
	PORT = 19999
	APPNAME = 'FRPC客户端管理器-WebUI'
	logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
	                    encoding='utf-8')
else:
	# 否则，使用当前目录
	base_dir = os.path.dirname(__file__)
	PORT = 19998
	APPNAME = 'FRPC客户端管理器开发服务器'
	logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s',
	                    encoding='utf-8')  # 开发环境


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
		self.icon = icon("name", image, APPNAME, self.menu)
		# 在 TrayApp 初始化时启动 Flask 应用
		self.start_webui()
	
	@staticmethod
	def is_port_in_use(port):
		portsinuse = [conn.laddr[1] for conn in psutil.net_connections()]
		return port in portsinuse
	
	@staticmethod
	def is_flask_running():
		try:
			response = requests.get("http://localhost:" + str(PORT), timeout=2)
			return response.status_code == 200
		except requests.exceptions.RequestException:
			return False
	
	def start_webui(self):
		if self.is_port_in_use(PORT):
			logging.error('WebUI启动失败，端口' + str(PORT) + '已被占用')
		else:
			self.webui_server = make_server(host='0.0.0.0', port=PORT, app=app)
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
			webbrowser.open_new_tab("http://localhost:" + str(PORT) + "/")  # 你的Flask应用地址
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


def create_config_file(config_name, config_content):
	"""
	创建一个新的配置文件并将其保存到./frpc目录中。
	:param config_name: 配置文件名
	:param config_content: 配置内容
	:return: 包含成功状态的JSON响应
	"""
	for char in config_name:
		if not char.isalnum() and char not in "（）()_.":
			logging.error('创建配置文件失败: ' + config_name + '非法字符')
			return {'status': 'error', 'message': '配置文件名非法' + config_name}
	
	for ext in [".toml", ".ini", ".yaml", ".json"]:
		if config_name.endswith(ext):
			break
	else:
		config_name = config_name.rsplit('.', 1)[0] + ".toml"
	
	config_file_path = f'./frpc/{config_name}'
	
	if os.path.isfile(config_file_path):
		logging.error('创建配置文件失败: ' + config_name + '已存在')
		return {'status': 'error', 'message': '配置文件已存在 ： ' + config_name + '请先删除同名配置文件。'}
	
	try:
		with open(config_file_path, 'w') as f:
			f.write(config_content)
	except Exception as e:
		logging.error('创建配置文件失败: ' + config_name)
		return {'status': 'error', 'message': str(e)}
	logging.info('创建配置文件成功: ' + config_name)
	return {'status': 'success', 'message': '配置文件创建成功' + config_name}


@app.route('/api/configs', methods=['POST'])
def create_config():
	config_name = request.json.get('name')
	config_content = request.json.get('content')
	result = create_config_file(config_name, config_content)
	return jsonify(result)


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
		                                stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
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


@app.route('/api/get_configurations', methods=['GET'])
def get_configurations():
	"""
	获取./frpc目录中的配置文件列表并以JSON响应的方式返回。
	:return: 包含符合指定扩展名的配置文件名的JSON响应
	"""
	api_channels = {
		"muhanfrp": "https://muhanfrp.cn/api/tunnels",  # 木韩FRP
		"sakurafrp": "https://api.natfrp.com/v4/tunnels",  # 樱花FRP
	}
	
	api_channel = request.args.get("api_channel")  # 获取API渠道参数
	api_key = request.args.get("api_key")  # 获取API密钥参数
	
	if api_channel not in api_channels:
		return jsonify({"error": "Invalid API channel"})
	
	url = api_channels[api_channel]
	headers = {
		"Accept": "application/json",
		"Authorization": f"Bearer {api_key}"
	}
	
	try:
		response = requests.get(url, headers=headers)
		response.raise_for_status()
		data = response.json()
		configurations = []
		
		for item in data:
			configuration = {
				"id": item.get("id"),
				"name": item.get("name")
			}
			configurations.append(configuration)
		logging.info('获取远程配置文件列表成功' + '一共' + str(len(configurations)) + '个')
		return jsonify(configurations)
	except requests.exceptions.RequestException as e:
		logging.error('获取远程配置文件列表失败: ' + str(e))
		return jsonify({"error": str(e)})


@app.route('/api/downloadConfig', methods=['GET'])
def downloadConfig():
	"""
	下载指定的配置文件。
	:return:  包含成功状态的JSON响应
	"""
	config_id = request.args.get('config_id')
	config_name = request.args.get('config_name')
	api_key = request.args.get('api_key')
	api_channel = request.args.get('api_channel')
	
	headers = {
		'Authorization': f'Bearer {api_key}',
		'Accept': 'application/json'
	}
	
	if api_channel == 'muhanfrp':
		url = f'https://muhanfrp.cn/api/tunnels/{config_id}'
		response = requests.get(url, headers=headers)
		if response.status_code == 200:
			data = response.json()
			server_config = data['config']['server']
			client_config = data['config']['client']
			config_content = f'{server_config}\n\n{client_config}'
		else:
			return jsonify({'status': 'error', 'message': '上游API接口可能异常'})
	elif api_channel == 'sakurafrp':
		url = f'https://api.natfrp.com/v4/tunnel/config?token={api_key}'
		data = {"query": config_id}
		response = requests.post(url, headers=headers, json=data)
		if response.status_code == 200:
			config_content = response.text
		else:
			return jsonify({'status': 'error', 'message': '上游API接口异常'})
	else:
		return jsonify({'status': 'error', 'message': '未知的API渠道'})
	
	new_config_name = f'{api_channel}_{config_name}_{config_id}.ini'
	result = create_config_file(new_config_name, config_content)
	if result['status'] == 'success':
		logging.info('下远程配置文件成功: ' + new_config_name)
		return jsonify(result)
	else:
		logging.error('下远程配置文件失败: ' + new_config_name)
		return jsonify({'status': 'error', 'message': result['message']})


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
		webbrowser.open('http://localhost:' + str(PORT))


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
