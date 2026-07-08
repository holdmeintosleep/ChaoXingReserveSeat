<template>
  <div class="scheduler-panel">
    <div class="panel-header">
      <div class="header-left">
        <el-button type="primary" @click="handleStart">启动调度器</el-button>
        <el-button type="danger" @click="handleStop">停止调度器</el-button>
        <el-button type="success" @click="handleAutoSchedule">自动生成任务</el-button>
      </div>
      <div class="header-right">
        <el-tag :type="schedulerStatus.running ? 'success' : 'info'">
          {{ schedulerStatus.running ? '运行中' : '已停止' }}
        </el-tag>
        <span class="task-count">任务数: {{ schedulerStatus.taskCount }}</span>
      </div>
    </div>

    <div class="filter-bar">
      <el-select v-model="statusFilter" placeholder="筛选状态" clearable style="width: 150px;">
        <el-option label="待执行" value="pending" />
        <el-option label="运行中" value="running" />
        <el-option label="成功" value="success" />
        <el-option label="失败" value="failed" />
        <el-option label="已跳过" value="skipped" />
      </el-select>
      <el-button type="primary" size="small" @click="handleRefresh">刷新</el-button>
    </div>

    <el-table :data="tasks" border class="task-table">
      <el-table-column prop="task_id" label="任务ID" width="200" />
      <el-table-column label="类型" width="100">
        <template #default="scope">
          <el-tag :type="getTaskTypeTag(scope.row.task_type)">
            {{ getTaskTypeName(scope.row.task_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="config_index" label="配置索引" width="100" />
      <el-table-column prop="target_time" label="目标时间" width="180" />
      <el-table-column label="状态" width="100">
        <template #default="scope">
          <el-tag :type="getStatusTag(scope.row.status)">
            {{ getStatusName(scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="retry_count" label="重试次数" width="100" />
      <el-table-column prop="result" label="结果" min-width="200" />
      <el-table-column label="操作" width="120">
        <template #default="scope">
          <el-button size="small" type="danger" @click="handleCancel(scope.row.task_id)" 
            :disabled="scope.row.status !== 'pending'">取消</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog title="创建任务" v-model="showCreateDialog" width="500px">
      <el-form :model="newTask" label-width="100px">
        <el-form-item label="任务类型">
          <el-select v-model="newTask.task_type" placeholder="请选择任务类型">
            <el-option label="预约" value="reserve" />
            <el-option label="签到" value="signin" />
            <el-option label="签退" value="signout" />
          </el-select>
        </el-form-item>
        <el-form-item label="配置索引">
          <el-select v-model="newTask.config_index" placeholder="请选择配置">
            <el-option v-for="(cfg, idx) in configList" :key="idx" :label="cfg.username" :value="idx" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标时间" v-if="newTask.task_type === 'signin' || newTask.task_type === 'signout'">
          <el-date-picker v-model="newTask.target_time" type="datetime" placeholder="选择目标时间" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="提前阈值(分钟)" v-if="newTask.task_type === 'signin'">
          <el-input-number v-model="newTask.advance_threshold" :min="0" :max="60" />
        </el-form-item>
        <el-form-item label="延迟阈值(分钟)" v-if="newTask.task_type === 'signout'">
          <el-input-number v-model="newTask.delay_threshold" :min="0" :max="60" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { configApi } from '../api/config'

const tasks = ref([])
const schedulerStatus = ref({ running: false, taskCount: 0 })
const statusFilter = ref('')
const showCreateDialog = ref(false)
const configList = ref([])

const newTask = ref({
  task_type: '',
  config_index: null,
  target_time: '',
  advance_threshold: 0,
  delay_threshold: 0
})

const loadTasks = async () => {
  try {
    const response = await configApi.getTasks(statusFilter.value)
    tasks.value = response.data.data
  } catch (error) {
    console.error('加载任务失败:', error)
  }
}

const loadStatus = async () => {
  try {
    const response = await configApi.getSchedulerStatus()
    schedulerStatus.value = response.data.data
  } catch (error) {
    console.error('获取状态失败:', error)
  }
}

const loadConfigList = async () => {
  try {
    const response = await configApi.getReserveList()
    configList.value = response.data.data
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

const handleRefresh = () => {
  loadTasks()
  loadStatus()
}

const handleStart = async () => {
  try {
    await configApi.startScheduler()
    await loadStatus()
  } catch (error) {
    console.error('启动调度器失败:', error)
  }
}

const handleStop = async () => {
  try {
    await configApi.stopScheduler()
    await loadStatus()
  } catch (error) {
    console.error('停止调度器失败:', error)
  }
}

const handleAutoSchedule = async () => {
  try {
    await configApi.autoSchedule()
    await loadTasks()
  } catch (error) {
    console.error('自动生成任务失败:', error)
  }
}

const handleCancel = async (taskId) => {
  try {
    await configApi.cancelTask(taskId)
    await loadTasks()
  } catch (error) {
    console.error('取消任务失败:', error)
  }
}

const handleCreate = async () => {
  try {
    const data = { ...newTask.value }
    if (data.target_time) {
      data.target_time = new Date(data.target_time).toISOString().slice(0, 19).replace('T', ' ')
    }
    await configApi.createTask(data)
    showCreateDialog.value = false
    newTask.value = {
      task_type: '',
      config_index: null,
      target_time: '',
      advance_threshold: 0,
      delay_threshold: 0
    }
    await loadTasks()
  } catch (error) {
    console.error('创建任务失败:', error)
  }
}

const getTaskTypeName = (type) => {
  const map = { reserve: '预约', signin: '签到', signout: '签退' }
  return map[type] || type
}

const getTaskTypeTag = (type) => {
  const map = { reserve: 'info', signin: 'success', signout: 'warning' }
  return map[type] || 'info'
}

const getStatusName = (status) => {
  const map = { pending: '待执行', running: '运行中', success: '成功', failed: '失败', skipped: '已跳过' }
  return map[status] || status
}

const getStatusTag = (status) => {
  const map = { pending: 'info', running: 'warning', success: 'success', failed: 'danger', skipped: 'info' }
  return map[status] || 'info'
}

onMounted(() => {
  loadTasks()
  loadStatus()
  loadConfigList()
})
</script>

<style scoped>
.scheduler-panel {
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

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.task-count {
  font-size: 14px;
  color: #606266;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.task-table {
  width: 100%;
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
}
</style>