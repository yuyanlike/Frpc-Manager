<template>
  <div>
    <h2>编辑配置文件</h2>
    <el-select v-model="selectedConfig" placeholder="请选择配置文件">
      <el-option v-for="config in configs" :key="config" :label="config" :value="config"></el-option>
    </el-select>
    <el-input type="textarea" v-model="configContent" autosize></el-input>
    <el-button type="primary" @click="saveConfig">保存</el-button>
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
      configContent: ''
    };
  },
  methods: {
    getConfigs() {
      axios.get('/configs')
        .then(response => {
          this.configs = response.data;
        });
    },
    getConfig() {
      if (this.selectedConfig) {
        axios.get(`/configs/${this.selectedConfig}`)
          .then(response => {
            this.configContent = response.data.content;
          });
      }
    },
    saveConfig() {
      if (this.selectedConfig) {
        axios.put(`/configs/${this.selectedConfig}`, { content: this.configContent })
          .then(response => {
            if (response.data.status === 'success') {
              Swal.fire('保存成功', '', 'success');
            }
          });
      }
    }
  },
  watch: {
    selectedConfig() {
      this.getConfig();
    }
  },
  created() {
    this.getConfigs();
  }
}
</script>
