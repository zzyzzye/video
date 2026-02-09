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
        class="custom-btn"
        @click="showLanguageDialog = true"
        :disabled="isGeneratingSubtitles || hasSubtitles"
      >
        <span>生成字幕</span>
      </button>
      
      <button 
        class="custom-btn"
        @click="handleSave"
        :disabled="isSaving"
      >
        <el-icon v-if="!isSaving"><Check /></el-icon>
        <span>保存</span>
      </button>

      <button 
        v-if="showUploadButton"
        class="custom-btn primary"
        @click="handleUpload"
        :disabled="isUploading"
      >
        <el-icon v-if="!isUploading"><Upload /></el-icon>
        <span>{{ isUploading ? '上传中...' : '上传并处理' }}</span>
      </button>
    </div>

    <!-- 语言选择对话框 -->
    <el-dialog
      v-model="showLanguageDialog"
      title="选择字幕语言"
      width="400px"
      custom-class="dark-dialog"
      class="dark-dialog"
      modal-class="dark-overlay"
    >
      <el-form label-width="80px">
        <el-form-item label="语言">
          <el-select 
            v-model="selectedLanguage" 
            placeholder="请选择语言"
            style="width: 100%"
          >
            <el-option label="自动检测（推荐）" value="auto" />
            <el-option label="中文" value="zh" />
            <el-option label="英语" value="en" />
            <el-option label="日语" value="ja" />
            <el-option label="韩语" value="ko" />
            <el-option label="西班牙语" value="es" />
            <el-option label="法语" value="fr" />
            <el-option label="德语" value="de" />
            <el-option label="俄语" value="ru" />
            <el-option label="阿拉伯语" value="ar" />
            <el-option label="葡萄牙语" value="pt" />
            <el-option label="意大利语" value="it" />
            <el-option label="荷兰语" value="nl" />
            <el-option label="波兰语" value="pl" />
            <el-option label="土耳其语" value="tr" />
            <el-option label="越南语" value="vi" />
            <el-option label="泰语" value="th" />
            <el-option label="印尼语" value="id" />
          </el-select>
        </el-form-item>
        
        <el-alert
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 12px"
        >
          <template #title>
            <div style="font-size: 12px; line-height: 1.5;">
              <div>• 自动检测：适合不确定语言的视频</div>
              <div>• 指定语言：提高识别准确率和速度</div>
              <div>• 生成时间：约为视频时长的 1/3</div>
            </div>
          </template>
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="showLanguageDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="confirmGenerateSubtitles"
          :loading="isGeneratingSubtitles"
        >
          开始生成
        </el-button>
      </template>
    </el-dialog>

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
  Check,
  Upload
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
  isGeneratingSubtitles: {
    type: Boolean,
    default: false
  },
  showUploadButton: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['save', 'upload', 'settings-change', 'generate-subtitles'])

const router = useRouter()

// 状态
const showSettings = ref(false)
const showLanguageDialog = ref(false)
const isSaving = ref(false)
const isUploading = ref(false)
const selectedLanguage = ref('auto')

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

// 上传
const handleUpload = async () => {
  isUploading.value = true
  try {
    await emit('upload')
  } finally {
    isUploading.value = false
  }
}

const confirmGenerateSubtitles = async () => {
  showLanguageDialog.value = false
  await emit('generate-subtitles', selectedLanguage.value)
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
