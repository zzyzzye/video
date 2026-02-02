<template>
  <div class="editor-toolbar">
    <div class="toolbar-left">
      <el-button 
        type="text" 
        :icon="ArrowLeft" 
        @click="handleBack"
        class="back-btn"
      >
        返回
      </el-button>
      
      <div class="video-info" v-if="videoTitle">
        <span class="video-title">{{ videoTitle }}</span>
        <el-tag v-if="videoStatus" :type="getStatusType(videoStatus)" size="small">
          {{ getStatusText(videoStatus) }}
        </el-tag>
      </div>
    </div>

    <div class="toolbar-right">
      <button 
        class="custom-btn icon-only"
        @click="showSettings = true"
      >
        <el-icon><Setting /></el-icon>
      </button>
      
      <button 
        class="custom-btn primary"
        @click="handleSave"
        :disabled="isSaving"
      >
        <el-icon v-if="!isSaving"><Check /></el-icon>
        <span>{{ saveButtonText }}</span>
      </button>
    </div>

    <!-- 设置对话框 -->
    <el-dialog
      v-model="showSettings"
      title="编辑器设置"
      width="500px"
      custom-class="dark-dialog"
      class="dark-dialog"
      modal-class="dark-overlay"
    >
      <el-form :model="settings" label-width="120px">
        <el-form-item label="自动保存">
          <el-switch v-model="settings.autoSave" />
          <span class="form-tip">每5分钟自动保存一次</span>
        </el-form-item>

        <el-form-item label="字幕显示">
          <el-radio-group v-model="settings.subtitleDisplay">
            <el-radio label="both">主副字幕</el-radio>
            <el-radio label="main">仅主字幕</el-radio>
            <el-radio label="translation">仅副字幕</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="时间轴缩放">
          <el-slider 
            v-model="settings.timelineZoom" 
            :min="50" 
            :max="200" 
            :step="10"
            show-stops
          />
        </el-form-item>

        <el-form-item label="快捷键提示">
          <el-switch v-model="settings.showShortcuts" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowLeft, 
  Setting, 
  Check
} from '@element-plus/icons-vue'

const props = defineProps({
  videoTitle: {
    type: String,
    default: ''
  },
  videoStatus: {
    type: String,
    default: ''
  },
  hasSubtitles: {
    type: Boolean,
    default: false
  },
  saveButtonText: {
    type: String,
    default: '保存'
  }
})

const emit = defineEmits(['save', 'settings-change'])

const router = useRouter()

// 状态
const showSettings = ref(false)
const isSaving = ref(false)

// 设置
const settings = ref({
  autoSave: true,
  subtitleDisplay: 'both',
  timelineZoom: 100,
  showShortcuts: true
})

// 返回
const handleBack = () => {
  ElMessageBox.confirm(
    '确定要离开吗？未保存的更改将会丢失。',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    router.back()
  }).catch(() => {})
}

// 保存
const handleSave = async () => {
  isSaving.value = true
  try {
    await emit('save')
  } finally {
    isSaving.value = false
  }
}

// 保存设置
const saveSettings = () => {
  emit('settings-change', settings.value)
  ElMessage.success('设置已保存')
  showSettings.value = false
}

// 状态相关
const getStatusType = (status) => {
  const statusMap = {
    'draft': 'info',
    'processing': 'warning',
    'published': 'success',
    'failed': 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    'draft': '草稿',
    'processing': '处理中',
    'published': '已发布',
    'failed': '失败'
  }
  return textMap[status] || status
}
</script>

<style scoped lang="scss">
.editor-toolbar {
  height: 42px;
  background: #1a1a1a;
  border-bottom: 1px solid #2a2a2a;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;

  .back-btn {
    color: #fff;
    font-size: 13px;

    &:hover {
      color: #409eff;
    }
  }

  .video-info {
    display: flex;
    align-items: center;
    gap: 10px;

    .video-title {
      font-size: 13px;
      color: #fff;
      max-width: 300px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.toolbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.toolbar-right {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.custom-button-group {
  display: flex;
  gap: 12px;
}

.custom-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;

  &:hover:not(:disabled) {
    background: #3a3a3a;
    border-color: #4a4a4a;
  }

  &:active:not(:disabled) {
    transform: scale(0.98);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .el-icon {
    font-size: 16px;
  }

  &.icon-only {
    padding: 6px;
    width: 32px;
    height: 32px;
    justify-content: center;
  }

  &.primary {
    background: #409eff;
    border-color: #409eff;

    &:hover:not(:disabled) {
      background: #66b1ff;
      border-color: #66b1ff;
    }
  }
}

.upload-area {
  :deep(.el-upload) {
    width: 100%;
  }

  :deep(.el-upload-dragger) {
    width: 100%;
    padding: 40px;
  }
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

:deep(.el-dialog) {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;

  .el-dialog__header {
    border-bottom: 1px solid #2a2a2a;
  }

  .el-dialog__body {
    color: #fff;
  }
}

:deep(.el-form-item__label) {
  color: #fff;
}

:deep(.el-upload__tip) {
  color: #909399;
}
</style>

<style lang="scss">
.dark-overlay {
  background-color: rgba(0, 0, 0, 0.75) !important;
}

body .el-overlay {
  background-color: rgba(0, 0, 0, 0.75) !important;
}

body .el-dialog {
  background: #1a1a1a !important;
  border: 1px solid #2a2a2a !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6) !important;
}

.el-dialog__header {
  border-bottom: 1px solid #2a2a2a !important;
}

.el-dialog__title {
  color: #fff !important;
}

.el-dialog__headerbtn .el-dialog__close {
  color: #aaa !important;
}

.el-dialog__headerbtn:hover .el-dialog__close {
  color: #fff !important;
}

.el-dialog__body {
  color: #fff !important;
}

.el-dialog__footer {
  border-top: 1px solid #2a2a2a !important;
}

.el-overlay .el-dialog__title {
  color: #fff !important;
}

.el-overlay .el-dialog__headerbtn .el-dialog__close {
  color: #aaa !important;
}

.el-overlay .el-dialog__headerbtn:hover .el-dialog__close {
  color: #fff !important;
}

.el-overlay .el-dialog__body {
  color: #fff !important;
}

.el-overlay .el-dialog__footer {
  border-top: 1px solid #2a2a2a !important;
}

.el-overlay .el-dialog .el-upload-dragger {
  background-color: #2a2a2a !important;
  border: 1px dashed #3a3a3a !important;
}

.el-overlay .el-dialog .el-upload-dragger:hover {
  border-color: #4a4a4a !important;
}

.el-overlay .el-dialog .el-upload__text {
  color: #ccc !important;
}

.el-overlay .el-dialog .el-upload__text em {
  color: #66b1ff !important;
}

.el-overlay .el-dialog .el-upload-dragger .el-icon--upload {
  color: #aaa !important;
}

.dark-dialog,
.dark-dialog .el-dialog,
.el-overlay-dialog.dark-dialog .el-dialog,
.el-overlay-dialog .el-dialog.dark-dialog {
  background: #1a1a1a;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
}

.dark-dialog .el-dialog__header {
  border-bottom: 1px solid #2a2a2a;
}

.dark-dialog .el-dialog__title {
  color: #fff;
}

.dark-dialog .el-dialog__headerbtn .el-dialog__close {
  color: #aaa;
}

.dark-dialog .el-dialog__headerbtn:hover .el-dialog__close {
  color: #fff;
}

.dark-dialog .el-dialog__body {
  color: #fff;
}

.dark-dialog .el-dialog__footer {
  border-top: 1px solid #2a2a2a;
}

.dark-dialog .el-upload-dragger {
  background: #2a2a2a;
  border: 1px dashed #3a3a3a;
}

.dark-dialog .el-upload-dragger:hover {
  border-color: #4a4a4a;
}

.dark-dialog .el-upload__text {
  color: #ccc;
}

.dark-dialog .el-upload__text em {
  color: #66b1ff;
}

.dark-dialog .el-upload-dragger .el-icon--upload {
  color: #aaa;
}
</style>
