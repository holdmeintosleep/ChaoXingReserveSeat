<template>
  <div class="day-selector-container">
    <div class="day-actions">
      <el-button size="small" @click="selectWeekdays">工作日</el-button>
      <el-button size="small" @click="selectWeekends">周末</el-button>
      <el-button size="small" @click="selectAll">全选</el-button>
      <el-button size="small" @click="clearAll">清空</el-button>
    </div>
    <div class="day-grid">
      <el-checkbox-group v-model="selectedDays">
        <el-checkbox
          v-for="day in weekDays"
          :key="day.value"
          :label="day.value"
          :disabled="disabled"
        >
          {{ day.label }}
        </el-checkbox>
      </el-checkbox-group>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const weekDays = [
  { label: '周一', value: 'Monday' },
  { label: '周二', value: 'Tuesday' },
  { label: '周三', value: 'Wednesday' },
  { label: '周四', value: 'Thursday' },
  { label: '周五', value: 'Friday' },
  { label: '周六', value: 'Saturday' },
  { label: '周日', value: 'Sunday' }
]

const weekdaysValues = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
const weekendsValues = ['Saturday', 'Sunday']

const selectedDays = ref([...props.modelValue])

const selectWeekdays = () => {
  selectedDays.value = [...weekdaysValues]
  emit('update:modelValue', selectedDays.value)
  emit('change', selectedDays.value)
}

const selectWeekends = () => {
  selectedDays.value = [...weekendsValues]
  emit('update:modelValue', selectedDays.value)
  emit('change', selectedDays.value)
}

const selectAll = () => {
  selectedDays.value = weekDays.map(d => d.value)
  emit('update:modelValue', selectedDays.value)
  emit('change', selectedDays.value)
}

const clearAll = () => {
  selectedDays.value = []
  emit('update:modelValue', selectedDays.value)
  emit('change', selectedDays.value)
}

watch(selectedDays, (newVal) => {
  emit('update:modelValue', newVal)
  emit('change', newVal)
}, { deep: true })

watch(() => props.modelValue, (newVal) => {
  if (newVal && newVal.length !== selectedDays.value.length) {
    selectedDays.value = [...newVal]
  }
}, { deep: true })
</script>

<style scoped>
.day-selector-container {
  width: 100%;
}

.day-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.day-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.el-checkbox {
  margin-right: 8px;
}
</style>