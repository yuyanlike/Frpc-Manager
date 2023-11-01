<template>
  <div>
    <h2>运行的进程</h2>
    <el-select v-model="selectedConfig" placeholder="请选择配置文件">
      <el-option v-for="config in configs" :key="config" :label="config" :value="config"></el-option>
    </el-select>
    <el-button type="primary" @click="startProcess">启动</el-button>
    <el-table :data="processes.map(process =>({ process }))" style="width: 100%">
      <el-table-column prop="process" label="进程名"></el-table-column>
      <el-table-column
        label="操作"
        width="180">
        <template v-slot:default="scope">
          <el-button type="danger" @click="stopProcess(scope.row.process)">停止</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script>
import axios from 'axios';
import Swal from 'sweetalert2';

export default {
  data() {
    return {
      configs: [],
      processes: [],
      selectedConfig: null
    };
  },
  methods: {
    getConfigs() {
      axios.get('/configs')
        .then(response => {
          this.configs = response.data;
        });
    },
    getProcesses() {
      axios.get('/processes')
        .then(response => {
          this.processes = response.data;
        });
    },
    startProcess() {
      if (this.selectedConfig) {
        axios.post('/processes', { name: this.selectedConfig })
          .then(response => {
            if (response.data.status === 'success') {
              this.getProcesses();
            }
          });
      }
    },
    stopProcess(configName) {
      Swal.fire({
        title: '确认',
        text: '你确定要停止这个进程吗？',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: '停止',
        cancelButtonText: '取消'
      }).then((result) => {
        if (result.isConfirmed) {
          axios.delete(`/processes/${configName}`)
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
    this.getConfigs();
    this.getProcesses();
  }
}
</script>