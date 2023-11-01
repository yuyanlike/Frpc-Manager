## FRPC 管理器

### 警告： WebUI面板无鉴权，请勿作死映射面板运行的端口到外网
### 这是我自己用的 代码烂的和狗屎一样。看不惯您随意。
说明
```
 ./frpc目录  frpc本体

 ./frpc-webui目录  frpc-webui工程文件
 
 ./webui目录 打包好的webui文件
 
 webui-main.py webui后端代码  flask实现

 app.py tkinter实现的windows应用。与webui-main.py无依赖关系

```


### 依赖 ./frpc 目录下的本体和配置文件 本质是将frpc的启动命令可视化


## 使用

> windows 可以直接下载打包好的  （AMD64，X86_64）

> linux 没有打包 发行版下载 解压 `pip install flask`  然后 `python webui-main.py`即可  （AMD64，X86_64）

> 其他系统自己下载frpc二进制文件放进./frpc 目录

> WebUI 建议直接下载 `webui-main.py` 和 `./webui` 目录 新建 frpc目录 `mkdir frpc`

> windows webui 打包 `pyinstaller FRPC管理器-WebUI.spec` （AMD64，X86_64） 