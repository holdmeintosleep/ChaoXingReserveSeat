<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-content">
        <h1 class="app-title">预约时间管理系统</h1>
        <div class="header-actions">
          <input
            type="file"
            id="import-input"
            class="import-input"
            accept=".json"
            @change="handleImport"
          />
          <label for="import-input" class="el-button">导入配置</label>
          <el-button type="success" @click="handleExport">导出配置</el-button>
        </div>
      </div>
    </header>

    <main class="app-main">
      <el-tabs v-model="activeTab" type="border-card" class="main-tabs">
        <el-tab-pane label="配置管理" name="config">
          <RuleDisplay />
          <ConfigList @reload="handleReload" />
        </el-tab-pane>
        <el-tab-pane label="预约管理" name="reservation">
          <ReservationPanel />
        </el-tab-pane>
        <el-tab-pane label="签到管理" name="signin">
          <SignInPanel />
        </el-tab-pane>
        <el-tab-pane label="任务调度" name="scheduler">
          <SchedulerPanel />
        </el-tab-pane>
        <el-tab-pane label="日志管理" name="logs">
          <LogPanel />
        </el-tab-pane>
      </el-tabs>
    </main>

    <footer class="app-footer">
      <p>预约时间可视化管理系统</p>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import RuleDisplay from './components/RuleDisplay.vue'
import ConfigList from './components/ConfigList.vue'
import ReservationPanel from './components/ReservationPanel.vue'
import SignInPanel from './components/SignInPanel.vue'
import SchedulerPanel from './components/SchedulerPanel.vue'
import LogPanel from './components/LogPanel.vue'
import { configApi } from './api/config'

const activeTab = ref('config')

const handleExport = async () => {
  try {
    const response = await configApi.exportConfig()
    const blob = new Blob([response.data], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'config.json'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('导出失败:', error)
  }
}

const handleImport = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      const content = e.target.result
      const config = JSON.parse(content)
      
      const reserveList = config.reserve || []
      for (const item of reserveList) {
        await configApi.addReserve(item)
      }
      
      handleReload()
      event.target.value = ''
    } catch (error) {
      console.error('导入失败:', error)
    }
  }
  reader.readAsText(file)
}

const handleReload = () => {
  console.log('配置已更新')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f5f7fa;
  min-height: 100vh;
}

#app {
  min-height: 100vh;
}
</style>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.import-input {
  display: none;
}

.app-main {
  flex: 1;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 24px;
}

.main-tabs {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.app-footer {
  text-align: center;
  padding: 16px;
  color: #909399;
  font-size: 14px;
  background-color: #fff;
  border-top: 1px solid #e4e7ed;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 12px;
  }
  
  .app-title {
    font-size: 20px;
  }
  
  .app-main {
    padding: 16px;
  }
}
</style>