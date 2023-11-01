<template>
  <div class="container">
    <h2>frpc 管理器</h2>
    <el-row>
      <el-col :span="24">
        <h3>全部配置文件</h3>
        <el-table :data="configs" style="width: 100%">
          <el-table-column prop="name" label="配置文件名"></el-table-column>
          <el-table-column
            label="操作"
            width="300">
            <template v-slot:default="scope">
              <el-button type="primary" @click="startProcess(scope.row.name)" :disabled="scope.row.status === '运行中🟢'">启动</el-button>
              <el-button type="danger" @click="stopProcess(scope.row.name)" :disabled="scope.row.status !== '运行中🟢'">停止</el-button>
              <el-button type="warning" @click="showEditConfigDialog(scope.row.name)">编辑</el-button>
              <el-button type="info" @click="deleteConfig(scope.row.name)">删除</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态"></el-table-column>
        </el-table>
        <h3></h3>
        <el-button type="primary" @click="showCreateConfigDialog">新建配置文件</el-button>
      </el-col>
    </el-row>
    <el-row v-if="showEditor">
      <el-col :span="24">
        <h3>编辑器</h3>
        <el-input type="text" v-model="selectedConfig" placeholder="文件名"></el-input>
        <el-input type="textarea" v-model="configContent" :autosize="{ minRows: 10, maxRows: Infinity }"></el-input>
        <el-button type="primary" @click="saveConfig">保存</el-button>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import axios from 'axios';
import Swal from 'sweetalert2';

export default {
  data() {
    return {
      configs: [],
      selectedConfig: null,
      configContent: '',
      showEditor: false,
      processes: []
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
          this.getConfigs();  // 在这里调用 getConfigs() 函数
        });
    },
    showCreateConfigDialog() {
      this.showEditor = true;
      this.selectedConfig = '';
      this.configContent = '';
    },
    showEditConfigDialog(name) {
      this.showEditor = true;
      this.selectedConfig = name;
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
      }
    },
    saveConfig() {
      if (this.selectedConfig) {
        axios.put(`/api/configs/${this.selectedConfig}`, { content: this.configContent })
          .then(response => {
            if (response.data.status === 'success') {
              this.getConfigs();
              Swal.fire('保存成功', '', 'success');
            }
          });
      }
    },
    startProcess(name) {
      axios.post('/api/processes', { name })
        .then(response => {
          if (response.data.status === 'success') {
            this.getProcesses();
            Swal.fire('启动成功', '', 'success');
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
              }
            });
        }
      });
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
</style>
