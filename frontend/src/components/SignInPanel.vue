<template>
  <div class="signin-panel">
    <el-card class="panel-card">
      <div class="panel-header">
        <h3>签到管理</h3>
        <div class="panel-actions">
          <el-button type="primary" @click="handleBatchSignin" :loading="batchSigning" :disabled="!hasHistory">
            一键批量签到
          </el-button>
          <el-button @click="loadHistory" :loading="loadingHistory">
            刷新记录
          </el-button>
        </div>
      </div>

      <el-alert
        v-if="!hasHistory && !loadingHistory"
        title="暂无预约记录"
        description="请先在「预约管理」中执行预约，预约成功后系统会自动记录预约ID"
        type="info"
        show-icon
        :closable="false"
      />

      <div v-else>
        <!-- 签到配置提示 -->
        <el-alert
          v-if="signinConfig"
          title="签到配置"
          type="info"
          :closable="false"
          class="config-alert"
        >
          <template #default>
            <div>GPS位置: {{ signinConfig.location?.address || '未设置' }} ({{ signinConfig.location?.latitude }}, {{ signinConfig.location?.longitude }})</div>
            <div>状态: {{ signinConfig.enabled ? '已启用' : '已禁用' }}</div>
          </template>
        </el-alert>

        <div v-for="(userData, username) in historyData" :key="username" class="user-section">
          <h4 class="user-name">{{ username }}</h4>
          <el-table :data="flattenHistory(userData)" border size="small" v-loading="signingUsers[username]">
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column prop="timeSegment" label="时间段" width="160" />
            <el-table-column prop="reserveId" label="预约ID">
              <template #default="scope">
                <el-tag type="success">{{ scope.row.reserveId }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="scope">
                <el-button
                  size="small"
                  type="primary"
                  @click="handleSingleSignin(username, scope.row)"
                  :loading="currentSigning === `${username}_${scope.row.reserveId}`"
                >
                  签到
                </el-button>
                <el-button
                  size="small"
                  type="warning"
                  @click="handleCancelSignin(username, scope.row)"
                  :loading="currentCanceling === `${username}_${scope.row.reserveId}`"
                >
                  取消签到
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 签到结果对话框 -->
      <el-dialog v-model="resultVisible" title="签到结果" width="500px">
        <el-alert
          v-for="(r, i) in signinResults"
          :key="i"
          :title="`${r.username || ''} — ${r.time_segment || ''}`"
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { configApi } from '../api/config'

const historyData = ref({})
const loadingHistory = ref(false)
const signingUsers = ref({})
const currentSigning = ref('')
const currentCanceling = ref('')
const batchSigning = ref(false)
const resultVisible = ref(false)
const signinResults = ref([])
const signinConfig = ref(null)

const hasHistory = computed(() => Object.keys(historyData.value).length > 0)

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

const loadSigninConfig = async () => {
  try {
    const resp = await configApi.getSignin()
    signinConfig.value = resp.data.data
  } catch (e) {
    // 忽略
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

const findConfigForUser = async (username) => {
  try {
    const resp = await configApi.getReserveList()
    const configs = resp.data.data || []
    return configs.find(c => c.username === username)
  } catch {
    return null
  }
}

const handleSingleSignin = async (username, row) => {
  const key = `${username}_${row.reserveId}`
  currentSigning.value = key

  try {
    const cfg = await findConfigForUser(username)
    if (!cfg) {
      ElMessage.error(`未找到用户 ${username} 的配置信息`)
      currentSigning.value = ''
      return
    }

    const resp = await configApi.executeSignin({
      username,
      password: cfg.password,
      reserve_id: row.reserveId,
      roomid: cfg.roomid,
      date: row.date,
      time_segment: row.timeSegment
    })

    const data = resp.data
    if (data.success) {
      ElMessage.success(`${username} 签到成功`)
    } else {
      ElMessage.warning(data.message || '签到失败')
    }
    signinResults.value = [{ ...data, username, time_segment: row.timeSegment }]
    resultVisible.value = true
  } catch (e) {
    ElMessage.error('签到请求失败: ' + (e.response?.data?.message || e.message))
  } finally {
    currentSigning.value = ''
  }
}

const handleCancelSignin = async (username, row) => {
  try {
    await ElMessageBox.confirm(`确定取消 ${username} 的签到 (${row.reserveId})？`, '确认', { type: 'warning' })
  } catch { return }

  const key = `${username}_${row.reserveId}`
  currentCanceling.value = key

  try {
    const cfg = await findConfigForUser(username)
    if (!cfg) {
      ElMessage.error(`未找到用户 ${username} 的配置信息`)
      currentCanceling.value = ''
      return
    }

    const resp = await configApi.cancelSignin({
      username,
      password: cfg.password,
      reserve_id: row.reserveId
    })

    if (resp.data.success) {
      ElMessage.success('取消签到成功')
    } else {
      ElMessage.warning(resp.data.message || '取消签到失败')
    }
  } catch (e) {
    ElMessage.error('请求失败: ' + (e.response?.data?.message || e.message))
  } finally {
    currentCanceling.value = ''
  }
}

const handleBatchSignin = async () => {
  try {
    await ElMessageBox.confirm('确定要批量签到所有预约记录吗？', '确认', { type: 'warning' })
  } catch { return }

  batchSigning.value = true
  try {
    const resp = await configApi.batchSignin()
    const data = resp.data
    signinResults.value = data.data || []
    resultVisible.value = true

    const successCount = signinResults.value.filter(r => r.success).length
    if (successCount > 0) {
      ElMessage.success(`批量签到完成: ${successCount} 成功, ${signinResults.value.length - successCount} 失败`)
    } else {
      ElMessage.warning('批量签到失败')
    }
  } catch (e) {
    ElMessage.error('批量签到请求失败: ' + (e.response?.data?.message || e.message))
  } finally {
    batchSigning.value = false
  }
}

onMounted(() => {
  loadHistory()
  loadSigninConfig()
})
</script>

<style scoped>
.panel-card { margin-bottom: 20px; }
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.panel-header h3 { margin: 0; font-size: 18px; font-weight: 600; }
.panel-actions { display: flex; gap: 8px; }
.config-alert { margin-bottom: 16px; }
.user-section { margin-bottom: 20px; }
.user-name { margin: 0 0 8px 0; font-size: 15px; color: #606266; }
.result-item { margin-bottom: 8px; }
</style>