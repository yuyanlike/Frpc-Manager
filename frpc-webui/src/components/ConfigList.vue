<template>
  <div class="container">
    <h2>{{ VUE_APP_TITLE }}</h2>
    <el-row>
      <el-col :span="24">
        <h3>全部配置文件</h3>
        <el-table :data="configs" style="width: 100%">
          <el-table-column label="配置文件名" prop="name" width="300"></el-table-column>
          <el-table-column label="状态" prop="status" width="300"></el-table-column>
          <el-table-column label="操作" width="400">
            <template v-slot:default="scope">
              <el-button :disabled="scope.row.status === '运行中🟢'" type="primary"
                         @click="startProcess(scope.row.name)">启动
              </el-button>
              <el-button :disabled="scope.row.status !== '运行中🟢'" type="info"
                         @click="stopProcess(scope.row.name)">停止
              </el-button>
              <el-button :disabled="scope.row.status === '运行中🟢'" type="warning"
                         @click="showEditConfigDialog(scope.row.name)">编辑
              </el-button>
              <el-button :disabled="scope.row.status !== '运行中🟢'" type="success"
                         @click="showAccessLinks(scope.row.name)">访问
              </el-button>
              <el-button :disabled="scope.row.status === '运行中🟢'" type="danger"
                         @click="deleteConfig(scope.row.name)">删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-button class="button-spacing" type="primary" @click="showCreateConfigDialog">新建配置文件</el-button>
        <el-button class="button-spacing" type="primary" @click="getRemoteApiConfigDialog">获取远程配置</el-button>
      </el-col>
    </el-row>
    <el-row v-if="showEditor">
      <el-col :span="24">
        <h3>新建配置文件</h3>
        <el-input v-model="selectedConfig" :disabled="!isNewConfig" placeholder="文件名" type="text"
                  style="width: 1000px"
                  @change="validateFileName"></el-input>
        <el-input v-model="configContent" :autosize="{ minRows: 10, maxRows: Infinity }" class="button-spacing"
                  style="width: 1000px"
                  placeholder="配置内容" type="textarea"></el-input>
        <el-col :span="24">
        <el-button class="button-spacing" type="primary" @click="saveConfig">保存</el-button>
        </el-col>
      </el-col>
    </el-row>
    <el-row v-if="showapiconfig">
      <el-col :span="24">
        <h3>获取远程配置</h3>
        <el-text class="mx-1" type="danger">远程访问令牌都存储在本地Cookies中</el-text>
        <el-col :span="24">
        <el-radio-group v-model="selectedApi" class="ml-4">
          <el-radio label="muhanfrp" size="large">木韩FRP</el-radio>
          <el-radio label="sakurafrp" size="large">樱花FRP</el-radio>
        </el-radio-group>
        </el-col>
        <el-col :span="24">
          <el-input v-model="apiKeys[selectedApi]" placeholder="请输入API密钥" show-password style="width: 1000px"
                    type="password"></el-input>
        </el-col>
        <el-col :span="24">
        <el-button class="button-spacing" type="primary" @click="getRemoteApi">获取</el-button>
        </el-col>
        <el-table :data="remoteConfigs" style="width: 100%">
          <el-table-column label="ID" prop="id" width="300"></el-table-column>
          <el-table-column label="名称" prop="name" width="300"></el-table-column>
          <el-table-column label="操作" width="400">
            <template v-slot:default="scope">
              <el-button type="primary" @click="downloadConfig(scope.row)">下载</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import axios from 'axios';
import Swal from 'sweetalert2';
import Cookies from 'js-cookie'; // 引入 js-cookie
export default {
  data() {
    return {
      configs: [],
      selectedConfig: null,
      configContent: '',
      showEditor: false,
      processes: [],
      isNewConfig: false,
      remoteConfigs: [],
      showapiconfig: false,
      selectedApi: '',
      VUE_APP_TITLE: process.env.VUE_APP_TITLE,

      apiKeys: {
        muhanfrp: Cookies.get('muhanfrpApiKey') || '',
        sakurafrp: Cookies.get('sakurafrpApiKey') || ''
      }
    };
  },
  methods: {
    getConfigs() {
      axios.get('/api/configs')
        .then(response => {
          this.configs = response.data.map(name => {
            const status = this.processes.includes(name) ? '运行中🟢' : '已停止🔴';
            return { name, status };
          });
        });
    },
    getProcesses() {
      axios.get('/api/processes')
          .then(response => {
            this.processes = response.data;
            this.getConfigs();
          })
          .catch(error => {
            console.error('获取数据时发生错误：', error);
            Swal.fire('Webui接口请求错误', '', 'error');
          });
    },

    showCreateConfigDialog() {
      this.showEditor = true;
      this.selectedConfig = '';
      this.configContent = '';
      this.isNewConfig = true;
      this.showapiconfig = false;
    },
    getRemoteApiConfigDialog() {
      this.showapiconfig = true;
      this.showEditor = false;
    },
    showEditConfigDialog(name) {
      this.showEditor = true;
      this.showapiconfig = false;
      this.selectedConfig = name;
      this.isNewConfig = false;
      this.getConfig();
    },
    deleteConfig(name) {
      Swal.fire({
        title: '确认',
        text: '你确定要删除这个配置文件吗？',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }).then((result) => {
        if (result.isConfirmed) {
          axios.delete(`/api/configs/${name}`)
            .then(response => {
              if (response.data.status === 'success') {
                this.getConfigs();
                Swal.fire('删除成功', '', 'success');
              } else {
                Swal.fire('删除失败', response.data.message, 'error');
              }
            });
        }
      });
    },
    getConfig() {
      if (this.selectedConfig) {
        axios.get(`/api/configs/${this.selectedConfig}`)
          .then(response => {
            this.configContent = response.data.content;
          });
      } else {
        this.configContent = '';
        Swal.fire('请求错误', '', 'error');
      }
    },
    saveConfig() {
      if (this.selectedConfig) {
        const data = { name: this.selectedConfig, content: this.configContent }
        if (this.isNewConfig) {
          axios.post('/api/configs', data)
            .then(response => {
              if (response.data.status === 'success') {
                this.getConfigs();
                Swal.fire('保存成功', '', 'success');
              } else {
                Swal.fire('保存失败', response.data.message, 'error');
              }
            });
        } else {
          const url = `/api/configs/${this.selectedConfig}`;
          axios.put(url, data)
            .then(response => {
              if (response.data.status === 'success') {
                this.getConfigs();
                Swal.fire('修改成功', '', 'success');
              } else {
                Swal.fire('修改失败', response.data.message, 'error');
              }
            });
        }
      }
    },
    startProcess(name) {
      axios.post('/api/processes', { name })
        .then(response => {
          if (response.data.status === 'success') {
            this.getProcesses();
            Swal.fire('启动成功', '', 'success');
          } else {
            Swal.fire('启动失败', response.data.message, 'error');
          }
        });
    },
    stopProcess(name) {
      Swal.fire({
        title: '确认',
        text: '你确定要停止这个进程吗？',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: '停止',
        cancelButtonText: '取消'
      }).then((result) => {
        if (result.isConfirmed) {
          axios.delete(`/api/processes/${name}`)
            .then(response => {
              if (response.data.status === 'success') {
                this.getProcesses();
                Swal.fire('停止成功', '', 'success');
              } else {
                Swal.fire('停止失败', response.data.message, 'error');
              }
            });
        }
      });
    },
    validateFileName() {
      const regex = /^[\w\p{Script=Hani}.-]+(\.toml|\.ini|\.json|\.yaml)?$/u;
      if (!regex.test(this.selectedConfig)) {
        Swal.fire('错误', '文件名只能包含中文、字母、数字、下划线和点，如果有后缀，只能是toml、ini、json、yaml', 'error');
        this.selectedConfig = '';
      } else if (this.isNewConfig && this.configs.some(config => config.name.split('.')[0] === this.selectedConfig.split('.')[0])) {
        Swal.fire('错误', '文件名已存在', 'error');
        this.selectedConfig = '';
      }
    },
    getRemoteApi() {
      const apiChannel = this.selectedApi;
      console.log("当前选择的API: " + apiChannel);
      axios.get('api/get_configurations', {
        params: {
          api_channel: apiChannel,
          api_key: this.apiKeys[this.selectedApi]
        }
      })
          .then(response => {
            if (response.data.length > 0) {  // 如果返回的数据是有效的
              this.remoteConfigs = response.data;
              // 设置 Cookie 过期时间为未来的某个日期，比如 10 年后
              const expirationDate = new Date();
              expirationDate.setFullYear(expirationDate.getFullYear() + 10);
              Cookies.set(this.selectedApi + 'ApiKey', this.apiKeys[this.selectedApi], {expires: expirationDate});
            } else {
              Swal.fire('请求错误', '', 'error');
            }

          })
          .catch(() => {
            Swal.fire('请求错误', '', 'error');
          });
    },
    downloadConfig(config) {
      axios.get('/api/downloadConfig', {
        params: {
          config_id: config.id,
          config_name: config.name,
          api_key: this.apiKeys[this.selectedApi],
          api_channel: this.selectedApi
        }
      })
          .then(response => {
            if (response.data.status === 'success') {
              Swal.fire('下载成功', '', 'success');
              this.getConfigs();  // 更新配置文件列表
            } else {
              Swal.fire('下载失败', response.data.message, 'error');
            }
          })
          .catch(() => {
            Swal.fire('请求错误', '', 'error');
          });
    },
    extractAccessLinks(configText) {
      const accessLinks = [];
      const lines = configText.split('\n');
      let currentServerAddr = '';
      let currentRemotePort = '';
      let currentCustomDomains = '';

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        const parts = line.split('=');

        if (parts.length === 2) {
          const key = parts[0].trim();
          let value = parts[1].trim();
          value = value.replace(/['"]+/g, ''); // 去掉可能存在的引号

          if (key === "server_addr" || key === "serverAddr") {
            currentServerAddr = value;
          } else if (key === "remote_port" || key === "remotePort") {
            currentRemotePort = value;
            accessLinks.push(currentServerAddr + ":" + currentRemotePort);
          } else if (key === "custom_domains" || key === "customDomains") {
            currentCustomDomains = value;
            accessLinks.push(currentCustomDomains);
          }
        }
      }

      return accessLinks;
    },
    showAccessLinks(name) {
      axios.get(`/api/configs/${name}`)
          .then(response => {
            const configContent = response.data.content;
            const accessLinks = this.extractAccessLinks(configContent);

            // 如果只有一个链接，直接在新窗口打开
            if (accessLinks.length === 1) {
              window.open('http://' + accessLinks[0], '_blank');
            } else {
              // 使用 Swal 展示访问链接
              const linksHtml = accessLinks.map(link => `<a href="http://${link}" target="_blank">${link}</a>`).join('<br><br>');
              Swal.fire({
                title: '访问地址',
                html: linksHtml,
                icon: 'info'
              });
            }
          })
          .catch(() => {
            Swal.fire('请求错误', '', 'error');
          });
    },
  },
  watch: {
    selectedApi() {
      // 当 selectedApi 的值发生变化时，调用 getRemoteApi 方法
      if (this.apiKeys[this.selectedApi]) {
        this.getRemoteApi();
      }
    }
  },
  created() {
    this.getProcesses();  // 只需要调用 getProcesses() 函数
  }
}
</script>

<style scoped>
.container {
  margin: 20px;
}

.button-spacing {
  margin-top: 15px;
}
</style>
