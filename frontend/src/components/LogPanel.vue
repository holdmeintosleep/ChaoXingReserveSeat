<template>
  <div class="log-panel">
    <div class="panel-header">
      <div class="header-left">
        <el-button type="primary" @click="handleRefresh">刷新日志</el-button>
        <el-button type="success" @click="handleExport">导出日志</el-button>
        <el-button type="warning" @click="handleClear">清除过期日志</el-button>
      </div>
      <div class="header-right">
        <el-tag type="info">共 {{ logs.length }} 条</el-tag>
      </div>
    </div>

    <div class="filter-bar">
      <el-select v-model="filterLevel" placeholder="日志级别" clearable style="width: 120px;">
        <el-option label="DEBUG" value="DEBUG" />
        <el-option label="INFO" value="INFO" />
        <el-option label="WARNING" value="WARNING" />
        <el-option label="ERROR" value="ERROR" />
        <el-option label="CRITICAL" value="CRITICAL" />
      </el-select>
      <el-select v-model="filterCategory" placeholder="日志分类" clearable style="width: 120px;">
        <el-option label="reserve" value="reserve" />
        <el-option label="signin" value="signin" />
        <el-option label="signout" value="signout" />
        <el-option label="scheduler" value="scheduler" />
        <el-option label="system" value="system" />
        <el-option label="api" value="api" />
      </el-select>
      <el-input v-model="filterKeyword" placeholder="搜索关键词" style="width: 200px;" @keyup.enter="handleSearch" />
      <el-button type="primary" size="small" @click="handleSearch">搜索</el-button>
    </div>

    <div class="log-content">
      <div v-for="(log, index) in displayLogs" :key="index" class="log-item" :class="getLogClass(log.level)">
        <span class="log-time">{{ log.time }}</span>
        <span class="log-level">{{ log.level }}</span>
        <span class="log-category">{{ log.category }}</span>
        <span class="log-message">{{ log.message }}</span>
      </div>
      <div v-if="displayLogs.length === 0" class="empty-state">
        <el-empty description="暂无日志数据" />
      </div>
    </div>

    <div class="pagination-bar">
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[20, 50, 100]"
        :page-size="pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
      />
    </div>

    <el-dialog title="日志统计" v-model="showStatsDialog" width="600px">
      <div v-if="stats" class="stats-content">
        <div class="stats-row">
          <span class="stats-label">总日志数:</span>
          <span class="stats-value">{{ stats.total }}</span>
        </div>
        <div class="stats-section">
          <h4>按级别统计</h4>
          <div class="stats-grid">
            <div v-for="(count, level) in stats.by_level" :key="level" class="stats-item">
              <el-tag :type="getLevelTag(level)">{{ level }}</el-tag>
              <span>{{ count }}</span>
            </div>
          </div>
        </div>
        <div class="stats-section">
          <h4>按分类统计</h4>
          <div class="stats-grid">
            <div v-for="(count, category) in stats.by_category" :key="category" class="stats-item">
              <el-tag type="info">{{ category }}</el-tag>
              <span>{{ count }}</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showStatsDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog title="导出日志" v-model="showExportDialog" width="400px">
      <el-form :model="exportForm" label-width="100px">
        <el-form-item label="导出格式">
          <el-select v-model="exportForm.format">
            <el-option label="JSON" value="json" />
            <el-option label="CSV" value="csv" />
            <el-option label="TXT" value="txt" />
          </el-select>
        </el-form-item>
        <el-form-item label="天数">
          <el-input-number v-model="exportForm.days" :min="1" :max="30" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmExport">确认导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { configApi } from '../api/config'

const logs = ref([])
const stats = ref(null)
const filterLevel = ref('')
const filterCategory = ref('')
const filterKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const showStatsDialog = ref(false)
const showExportDialog = ref(false)
const exportForm = ref({ format: 'json', days: 7 })

const displayLogs = computed(() => {
  let result = [...logs.value]
  
  if (filterLevel.value) {
    result = result.filter(log => log.level === filterLevel.value)
  }
  if (filterCategory.value) {
    result = result.filter(log => log.category === filterCategory.value)
  }
  if (filterKeyword.value) {
    const keyword = filterKeyword.value.toLowerCase()
    result = result.filter(log => 
      log.message.toLowerCase().includes(keyword) ||
      log.category.toLowerCase().includes(keyword)
    )
  }
  
  total.value = result.length
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

const loadLogs = async () => {
  try {
    const params = {}
    if (filterLevel.value) params.level = filterLevel.value
    if (filterCategory.value) params.category = filterCategory.value
    params.limit = 1000
    const response = await configApi.getLogs(params)
    logs.value = response.data.data
  } catch (error) {
    console.error('加载日志失败:', error)
  }
}

const loadStats = async () => {
  try {
    const response = await configApi.getLogStats(7)
    stats.value = response.data.data
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const handleRefresh = () => {
  loadLogs()
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page) => {
  currentPage.value = page
}

const handleExport = () => {
  showExportDialog.value = true
}

const confirmExport = async () => {
  try {
    const response = await configApi.exportLogs({
      format: exportForm.value.format,
      days: exportForm.value.days
    })
    
    const blob = new Blob([response.data], { type: 'application/octet-stream' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `logs.${exportForm.value.format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    showExportDialog.value = false
  } catch (error) {
    console.error('导出日志失败:', error)
  }
}

const handleClear = async () => {
  try {
    await configApi.clearLogs(30)
    await loadLogs()
  } catch (error) {
    console.error('清除日志失败:', error)
  }
}

const getLogClass = (level) => {
  const map = {
    DEBUG: 'log-debug',
    INFO: 'log-info',
    WARNING: 'log-warning',
    ERROR: 'log-error',
    CRITICAL: 'log-critical'
  }
  return map[level] || 'log-info'
}

const getLevelTag = (level) => {
  const map = {
    DEBUG: 'info',
    INFO: 'success',
    WARNING: 'warning',
    ERROR: 'danger',
    CRITICAL: 'danger'
  }
  return map[level] || 'info'
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.log-panel {
  padding: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  gap: 12px;
}

.log-content {
  background: #0d1117;
  border-radius: 8px;
  padding: 16px;
  max-height: 500px;
  overflow-y: auto;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
}

.log-item {
  padding: 8px 0;
  border-bottom: 1px solid #30363d;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.log-time {
  color: #8b949e;
  min-width: 190px;
}

.log-level {
  color: #58a6ff;
  min-width: 70px;
  font-weight: bold;
}

.log-category {
  color: #a371f7;
  min-width: 80px;
}

.log-message {
  color: #c9d1d9;
  flex: 1;
}

.log-debug .log-level { color: #8b949e; }
.log-info .log-level { color: #58a6ff; }
.log-warning .log-level { color: #d29922; }
.log-error .log-level { color: #f85149; }
.log-critical .log-level { color: #f778ba; }

.empty-state {
  padding: 40px;
}

.pagination-bar {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.stats-content {
  padding: 16px 0;
}

.stats-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.stats-label {
  font-weight: bold;
}

.stats-value {
  font-size: 24px;
  color: #667eea;
}

.stats-section {
  margin-top: 16px;
}

.stats-section h4 {
  margin-bottom: 12px;
  font-size: 14px;
  color: #606266;
}

.stats-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.stats-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .header-left {
    flex-wrap: wrap;
  }
  
  .filter-bar {
    flex-wrap: wrap;
  }
  
  .log-content {
    max-height: 400px;
  }
  
  .log-item {
    flex-direction: column;
    gap: 4px;
  }
  
  .log-time {
    min-width: auto;
  }
  
  .log-level {
    min-width: auto;
  }
  
  .log-category {
    min-width: auto;
  }
}
</style>