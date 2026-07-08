<template>
  <el-card class="config-list-card">
    <div class="list-header">
      <h3 class="list-title">预约配置列表</h3>
      <el-button type="primary" @click="handleAdd">添加配置</el-button>
    </div>
    
    <el-table :data="configs" v-loading="loading" border>
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="time" label="预约时间" width="160">
        <template #default="scope">
          {{ scope.row.time?.join(' ~ ') || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="roomid" label="房间ID" width="100" />
      <el-table-column prop="seatid" label="座位号" width="120">
        <template #default="scope">
          {{ Array.isArray(scope.row.seatid) ? scope.row.seatid.join(', ') : scope.row.seatid }}
        </template>
      </el-table-column>
      <el-table-column prop="daysofweek" label="预约日期" width="200">
        <template #default="scope">
          <el-tag
            v-for="day in scope.row.daysofweek"
            :key="day"
            size="small"
            type="info"
          >
            {{ getDayLabel(day) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="scope">
          <el-button size="small" @click="handleEdit(scope.$index)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.$index)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div v-if="configs.length === 0 && !loading" class="empty-state">
      <el-empty description="暂无预约配置，点击上方按钮添加" />
    </div>
    
      <ConfigForm
      :visible="formVisible"
      @update:visible="formVisible = $event"
      :edit-data="editData"
      @submit="handleFormSubmit"
    />
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ConfigForm from './ConfigForm.vue'
import { configApi } from '../api/config'

const emit = defineEmits(['reload'])

const configs = ref([])
const loading = ref(false)
const formVisible = ref(false)
const editData = ref(null)
const editIndex = ref(-1)

const dayLabels = {
  Monday: '周一',
  Tuesday: '周二',
  Wednesday: '周三',
  Thursday: '周四',
  Friday: '周五',
  Saturday: '周六',
  Sunday: '周日'
}

const getDayLabel = (day) => {
  return dayLabels[day] || day
}

const loadConfigs = async () => {
  loading.value = true
  try {
    const response = await configApi.getReserveList()
    configs.value = response.data.data || []
  } catch (error) {
    ElMessage.error('加载配置失败: ' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  editData.value = null
  editIndex.value = -1
  formVisible.value = true
}

const handleEdit = (index) => {
  editData.value = { ...configs.value[index] }
  editIndex.value = index
  formVisible.value = true
}

const handleDelete = async (index) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个预约配置吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const response = await configApi.deleteReserve(index)
    if (response.data.success) {
      configs.value.splice(index, 1)
      ElMessage.success('删除成功')
      emit('reload')
    } else {
      ElMessage.error(response.data.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.response?.data?.message || error.message))
    }
  }
}

const handleFormSubmit = async ({ data, isEdit }) => {
  try {
    if (isEdit && editIndex.value >= 0) {
      const response = await configApi.updateReserve(editIndex.value, data)
      if (response.data.success) {
        configs.value[editIndex.value] = { ...data }
        ElMessage.success('更新成功')
      } else {
        ElMessage.error(response.data.message || '更新失败')
      }
    } else {
      const response = await configApi.addReserve(data)
      if (response.data.success) {
        configs.value.push({ ...data })
        ElMessage.success('添加成功')
      } else {
        ElMessage.error(response.data.message || '添加失败')
      }
    }
    emit('reload')
  } catch (error) {
    ElMessage.error('提交失败: ' + (error.response?.data?.message || error.message))
  }
}

loadConfigs()
</script>

<style scoped>
.config-list-card {
  margin-bottom: 20px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.list-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.empty-state {
  padding: 40px;
}
</style>