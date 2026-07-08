<template>
  <div class="rules-container">
    <el-card class="rule-card" shadow="hover">
      <div class="rule-header" @click="toggleCollapse('reservation')">
        <el-icon :class="['mr-2', { 'rotate-180': collapsed.reservation }]">
          <ChevronDownIcon />
        </el-icon>
        <span class="rule-title">{{ rules.reservation?.title || '预约规则' }}</span>
      </div>
      <div v-show="!collapsed.reservation" class="rule-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item
            v-for="item in rules.reservation?.items"
            :key="item.name"
            :label="item.name"
          >
            {{ item.value }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <el-card class="rule-card" shadow="hover">
      <div class="rule-header" @click="toggleCollapse('violation')">
        <el-icon :class="['mr-2', { 'rotate-180': collapsed.violation }]">
          <ChevronDownIcon />
        </el-icon>
        <span class="rule-title">{{ rules.violation?.title || '违规规则' }}</span>
      </div>
      <div v-show="!collapsed.violation" class="rule-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item
            v-for="item in rules.violation?.items"
            :key="item.name"
            :label="item.name"
          >
            {{ item.value }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <el-card class="rule-card" shadow="hover">
      <div class="rule-header" @click="toggleCollapse('process')">
        <el-icon :class="['mr-2', { 'rotate-180': collapsed.process }]">
          <ChevronDownIcon />
        </el-icon>
        <span class="rule-title">{{ rules.process?.title || '使用流程' }}</span>
      </div>
      <div v-show="!collapsed.process" class="rule-content">
        <el-steps :space="20">
          <el-step
            v-for="step in rules.process?.steps"
            :key="step.step"
            :title="step.name"
            :description="step.description"
          />
        </el-steps>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ArrowDown as ChevronDownIcon } from '@element-plus/icons-vue'
import { configApi } from '../api/config'

const rules = ref({})
const collapsed = reactive({
  reservation: false,
  violation: false,
  process: true
})

const toggleCollapse = (key) => {
  collapsed[key] = !collapsed[key]
}

const loadRules = async () => {
  try {
    const response = await configApi.getRules()
    rules.value = response.data
  } catch (error) {
    console.error('加载规则失败:', error)
  }
}

loadRules()
</script>

<style scoped>
.rules-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.rule-card {
  cursor: pointer;
}

.rule-header {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.rule-title {
  flex: 1;
}

.rule-content {
  margin-top: 16px;
}

.rotate-180 {
  transform: rotate(180deg);
  transition: transform 0.3s;
}

.el-icon {
  transition: transform 0.3s;
}
</style>