<template>
  <el-dialog
    :title="isEdit ? '编辑预约配置' : '添加预约配置'"
    v-model="dialogVisible"
    width="600px"
    :before-close="handleClose"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="请输入学号或手机号" />
      </el-form-item>
      
      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" type="password" placeholder="请输入密码" />
      </el-form-item>
      
      <el-form-item label="预约时间" prop="time">
        <TimePicker v-model="form.time" />
      </el-form-item>
      
      <el-form-item label="房间ID" prop="roomid">
        <el-input v-model="form.roomid" placeholder="请输入房间ID" />
      </el-form-item>
      
      <el-form-item label="座位号" prop="seatid">
        <el-input v-model="form.seatid" placeholder="请输入座位号，多个用逗号分隔" />
      </el-form-item>
      
      <el-form-item label="预约日期">
        <DaySelector v-model="form.daysofweek" />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit">
        {{ isEdit ? '更新' : '添加' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import TimePicker from './TimePicker.vue'
import DaySelector from './DaySelector.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  editData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'submit'])

const isEdit = ref(false)
const formRef = ref(null)

// 同步 visible prop 到 dialogVisible，兼容 Vue 3 el-dialog 的 v-model
const dialogVisible = ref(false)
watch(() => props.visible, (val) => {
  dialogVisible.value = val
})
watch(dialogVisible, (val) => {
  if (!val) {
    emit('update:visible', false)
  }
})

const form = reactive({
  username: '',
  password: '',
  time: ['', ''],
  roomid: '',
  seatid: '',
  daysofweek: []
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ],
  time: [
    { 
      validator: (rule, value, callback) => {
        if (!value || !value[0] || !value[1]) {
          callback(new Error('请选择预约时间'))
        } else {
          callback()
        }
      }, 
      trigger: 'change' 
    }
  ],
  roomid: [
    { required: true, message: '请输入房间ID', trigger: 'blur' }
  ],
  seatid: [
    { required: true, message: '请输入座位号', trigger: 'blur' }
  ]
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    if (props.editData) {
      isEdit.value = true
      form.username = props.editData.username || ''
      form.password = props.editData.password || ''
      form.time = props.editData.time ? [...props.editData.time] : ['', '']
      form.roomid = props.editData.roomid || ''
      form.seatid = props.editData.seatid ? (Array.isArray(props.editData.seatid) ? props.editData.seatid.join(',') : props.editData.seatid) : ''
      form.daysofweek = props.editData.daysofweek ? [...props.editData.daysofweek] : []
    } else {
      isEdit.value = false
      resetForm()
    }
  }
})

const resetForm = () => {
  form.username = ''
  form.password = ''
  form.time = ['', '']
  form.roomid = ''
  form.seatid = ''
  form.daysofweek = []
}

const handleClose = () => {
  dialogVisible.value = false
  resetForm()
}

const handleSubmit = () => {
  formRef.value.validate((valid) => {
    if (!valid) return
    
    const seatid = form.seatid.split(',').map(s => s.trim()).filter(Boolean)
    
    const data = {
      username: form.username,
      password: form.password,
      time: form.time,
      roomid: form.roomid,
      seatid: seatid.length === 1 ? seatid[0] : seatid,
      daysofweek: form.daysofweek
    }
    
    emit('submit', {
      data,
      isEdit: isEdit.value
    })
    
    handleClose()
  })
}
</script>