<template>
  <div class="reservation-panel">
    <el-card class="panel-card">
      <div class="panel-header">
        <h3>预约管理</h3>
        <div class="panel-actions">
          <el-button type="primary" @click="executeAll" :loading="reserving" :disabled="configs.length === 0">
            一键预约全部
          </el-button>
          <el-button @click="loadHistory" :loading="loadingHistory">
            刷新历史
          </el-button>
          <el-button type="danger" plain @click="clearHistory" :disabled="!hasHistory">
            清空历史
          </el-button>
        </div>
      </div>

      <el-alert
        v-if="configs.length === 0"
        title="暂无预约配置"
        description="请先在「配置管理」中添加预约配置"
        type="info"
        show-icon
        :closable="false"
      />

      <el-table v-else :data="configs" border v-loading="reserving">
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column label="预约时间" width="160">
          <template #default="scope">
            {{ scope.row.time?.join(' ~ ') || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="roomid" label="房间ID" width="100" />
        <el-table-column label="座位号" width="120">
          <template #default="scope">
            {{ Array.isArray(scope.row.seatid) ? scope.row.seatid.join(', ') : scope.row.seatid }}
          </template>
        </el-table-column>
        <el-table-column label="预约日期" width="200">
          <template #default="scope">
            <el-tag v-for="day in scope.row.daysofweek" :key="day" size="small" type="info">
              {{ dayLabels[day] || day }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button
              size="small"
              type="success"
              @click="executeSingle(scope.$index)"
              :loading="reservingIndex === scope.$index"
            >
              立即预约
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 预约结果对话框 -->
      <el-dialog v-model="resultVisible" title="预约结果" width="500px">
        <el-alert
          v-for="(r, i) in reservationResults"
          :key="i"
          :title="`${r.username} — ${r.time?.join('~') || '-'}`"
          :description="r.message"
          :type="r.success ? 'success' : 'error'"
          show-icon
          :closable="false"
          class="result-item"
        />
        <template #footer>
          <el-button @click="resultVisible = false">关闭</el-button>
        </template>
      </el-dialog>
    </el-card>

    <!-- 预约历史记录 -->
    <el-card class="history-card">
      <div class="panel-header">
        <h3>预约历史</h3>
      </div>
      <div v-if="!hasHistory && !loadingHistory" class="empty-history">
        <el-empty description="暂无预约记录，执行预约后会自动记录" />
      </div>
      <div v-else v-for="(userData, username) in historyData" :key="username" class="user-history">
        <h4 class="user-name">{{ username }}</h4>
        <el-table :data="flattenHistory(userData)" border size="small">
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="timeSegment" label="时间段" width="160" />
          <el-table-column prop="reserveId" label="预约ID">
            <template #default="scope">
              <el-tag type="success">{{ scope.row.reserveId }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { configApi } from '../api/config'

const configs = ref([])
const reserving = ref(false)
const reservingIndex = ref(-1)
const resultVisible = ref(false)
const reservationResults = ref([])
const historyData = ref({})
const loadingHistory = ref(false)

const dayLabels = {
  Monday: '周一', Tuesday: '周二', Wednesday: '周三', Thursday: '周四',
  Friday: '周五', Saturday: '周六', Sunday: '周日'
}

const hasHistory = computed(() => Object.keys(historyData.value).length > 0)

const loadConfigs = async () => {
  try {
    const resp = await configApi.getReserveList()
    configs.value = resp.data.data || []
  } catch (e) {
    ElMessage.error('加载配置失败')
  }
}

const loadHistory = async () => {
  loadingHistory.value = true
  try {
    const resp = await configApi.getReservationHistory()
    historyData.value = resp.data.data || {}
  } catch (e) {
    ElMessage.error('加载预约历史失败')
  } finally {
    loadingHistory.value = false
  }
}

const flattenHistory = (userData) => {
  const rows = []
  for (const [date, segments] of Object.entries(userData)) {
    for (const [timeSegment, reserveId] of Object.entries(segments)) {
      rows.push({ date, timeSegment, reserveId })
    }
  }
  return rows.sort((a, b) => b.date.localeCompare(a.date) || b.timeSegment.localeCompare(a.timeSegment))
}

const executeSingle = async (index) => {
  reservingIndex.value = index
  try {
    const resp = await configApi.executeReservation(index)
    if (resp.data.success) {
      const taskId = resp.data.task_id
      ElMessage.info('预约任务已启动，正在执行...')

      // 轮询状态
      let attempts = 0
      const poll = setInterval(async () => {
        try {
          const statusResp = await configApi.getReservationStatus(taskId)
          const status = statusResp.data.data
          if (status.status === 'done') {
            clearInterval(poll)
            reservingIndex.value = -1
            reservationResults.value = status.results || []
            resultVisible.value = true
            loadHistory()

            const successCount = reservationResults.value.filter(r => r.success).length
            if (successCount > 0) {
              ElMessage.success(`预约完成: ${successCount} 成功, ${reservationResults.value.length - successCount} 失败`)
            } else {
              ElMessage.warning('预约失败，请查看详情')
            }
          }
        } catch (e) {
          clearInterval(poll)
          reservingIndex.value = -1
          ElMessage.error('获取预约状态失败')
        }
        attempts++
        if (attempts > 60) {
          clearInterval(poll)
          reservingIndex.value = -1
          ElMessage.warning('预约超时，请稍后查看结果')
        }
      }, 2000)
    } else {
      ElMessage.warning(resp.data.message || '预约启动失败')
      reservingIndex.value = -1
    }
  } catch (e) {
    ElMessage.error('预约请求失败: ' + (e.response?.data?.message || e.message))
    reservingIndex.value = -1
  }
}

const executeAll = async () => {
  try {
    await ElMessageBox.confirm('确定要执行所有配置的预约吗？', '确认', { type: 'warning' })
  } catch { return }

  reserving.value = true
  try {
    const resp = await configApi.executeReservation('all')
    if (resp.data.success) {
      const taskId = resp.data.task_id
      ElMessage.info(`预约任务已启动，共 ${resp.data.configs} 个配置`)

      let attempts = 0
      const poll = setInterval(async () => {
        try {
          const statusResp = await configApi.getReservationStatus(taskId)
          const status = statusResp.data.data
          if (status.status === 'done') {
            clearInterval(poll)
            reserving.value = false
            reservationResults.value = status.results || []
            resultVisible.value = true
            loadHistory()
            const successCount = reservationResults.value.filter(r => r.success).length
            ElMessage.success(`预约完成: ${successCount} 成功, ${reservationResults.value.length - successCount} 失败`)
          }
        } catch (e) {
          clearInterval(poll)
          reserving.value = false
        }
        attempts++
        if (attempts > 120) {
          clearInterval(poll)
          reserving.value = false
          ElMessage.warning('预约超时')
        }
      }, 2000)
    }
  } catch (e) {
    ElMessage.error('预约请求失败: ' + (e.response?.data?.message || e.message))
    reserving.value = false
  }
}

const clearHistory = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有预约历史记录吗？', '确认', { type: 'warning' })
    await configApi.clearReservationHistory()
    historyData.value = {}
    ElMessage.success('预约历史已清空')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('清空失败')
  }
}

onMounted(() => {
  loadConfigs()
  loadHistory()
})
</script>

<style scoped>
.panel-card { margin-bottom: 20px; }
.history-card { margin-bottom: 20px; }
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.panel-header h3 { margin: 0; font-size: 18px; font-weight: 600; }
.panel-actions { display: flex; gap: 8px; }
.result-item { margin-bottom: 8px; }
.empty-history { padding: 40px; }
.user-history { margin-bottom: 16px; }
.user-name { margin: 0 0 8px 0; font-size: 15px; color: #606266; }
</style>