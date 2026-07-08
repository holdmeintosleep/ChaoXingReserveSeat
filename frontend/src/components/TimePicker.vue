<template>
  <div class="time-picker-container">
    <div class="time-row">
      <div class="time-item">
        <label class="time-label">开始时间</label>
        <el-select
          v-model="startTime"
          placeholder="选择开始时间"
          :disabled="disabled"
          @change="handleTimeChange"
        >
          <el-option
            v-for="time in timeOptions"
            :key="time"
            :label="time"
            :value="time"
          />
        </el-select>
      </div>
      <span class="time-separator">~</span>
      <div class="time-item">
        <label class="time-label">结束时间</label>
        <el-select
          v-model="endTime"
          placeholder="选择结束时间"
          :disabled="disabled"
          @change="handleTimeChange"
        >
          <el-option
            v-for="time in timeOptions"
            :key="time"
            :label="time"
            :value="time"
          />
        </el-select>
      </div>
    </div>
    <div v-if="durationError" class="duration-warning">
      <el-alert type="warning" :title="durationError" show-icon />
    </div>
    <div v-if="showDuration && startTime && endTime" class="duration-info">
      <el-tag type="info">预约时长：{{ calculateDuration }}小时</el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => ['', '']
  },
  disabled: {
    type: Boolean,
    default: false
  },
  showDuration: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const startTime = ref(props.modelValue[0] || '')
const endTime = ref(props.modelValue[1] || '')
const durationError = ref('')

const timeOptions = []
for (let hour = 0; hour < 24; hour++) {
  for (let minute = 0; minute < 60; minute += 15) {
    const h = hour.toString().padStart(2, '0')
    const m = minute.toString().padStart(2, '0')
    timeOptions.push(`${h}:${m}`)
  }
}

const calculateDuration = computed(() => {
  if (!startTime.value || !endTime.value) return '0.0'
  const [sh, sm] = startTime.value.split(':').map(Number)
  const [eh, em] = endTime.value.split(':').map(Number)
  const startMinutes = sh * 60 + sm
  const endMinutes = eh * 60 + em
  const diffMinutes = endMinutes - startMinutes
  return (diffMinutes / 60).toFixed(1)
})

const handleTimeChange = () => {
  durationError.value = ''
  
  if (startTime.value && endTime.value) {
    const [sh, sm] = startTime.value.split(':').map(Number)
    const [eh, em] = endTime.value.split(':').map(Number)
    const startMinutes = sh * 60 + sm
    const endMinutes = eh * 60 + em
    
    if (endMinutes <= startMinutes) {
      durationError.value = '结束时间必须晚于开始时间'
    } else if ((endMinutes - startMinutes) > 240) {
      durationError.value = '预约时长不能超过4小时'
    }
  }
  
  emit('update:modelValue', [startTime.value, endTime.value])
  emit('change', { startTime: startTime.value, endTime: endTime.value })
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    startTime.value = newVal[0] || ''
    endTime.value = newVal[1] || ''
  }
}, { deep: true })
</script>

<style scoped>
.time-picker-container {
  width: 100%;
}

.time-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-item {
  flex: 1;
}

.time-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.time-separator {
  font-size: 20px;
  font-weight: bold;
  color: #909399;
  margin-top: 28px;
}

.duration-warning {
  margin-top: 12px;
}

.duration-info {
  margin-top: 12px;
}

.el-select {
  width: 100%;
}
</style>