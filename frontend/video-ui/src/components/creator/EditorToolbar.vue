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

    <div class="toolbar-center">
      <div class="custom-button-group">
        <button 
          class="custom-btn"
          @click="handleUpload"
          :disabled="isProcessing"
        >
          <el-icon><Upload /></el-icon>
          <span>上传视频</span>
        </button>
        
        <button 
          class="custom-btn"
          @click="handleExportSubtitle"
          :disabled="!hasSubtitles"
        >
          <el-icon><Download /></el-icon>
          <span>导出</span>
        </button>
        
        <button 
          class="custom-btn"
          @click="handleImportSubtitle"
        >
          <el-icon><Upload /></el-icon>
          <span>导入</span>
        </button>
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

    <!-- 上传视频对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传视频"
      width="600px"
      :close-on-click-modal="false"
      custom-class="dark-dialog"
      class="dark-dialog"
      modal-class="dark-overlay"
    >
      <el-upload
        ref="uploadRef"
        class="upload-area dark-upload-area"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept="video/*"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽视频文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 MP4、AVI、MOV 等格式，文件大小不超过 2GB
          </div>
        </template>
      </el-upload>

      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="confirmUpload"
          :loading="isUploading"
          :disabled="!selectedFile"
        >
          开始上传
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

    <!-- 导入字幕对话框 -->
    <input 
      ref="importFileInput" 
      type="file" 
      accept=".srt,.vtt,.ass" 
      style="display: none"
      @change="handleImportFile"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowLeft, 
  Upload, 
  Download, 
  Setting, 
  Check,
  UploadFilled 
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

const emit = defineEmits(['save', 'upload', 'export', 'import', 'settings-change'])

const router = useRouter()

// 状态
const showUploadDialog = ref(false)
const showSettings = ref(false)
const isProcessing = ref(false)
const isSaving = ref(false)
const isUploading = ref(false)
const selectedFile = ref(null)
const uploadRef = ref(null)
const importFileInput = ref(null)

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

// 上传视频
const handleUpload = () => {
  showUploadDialog.value = true
}

const handleFileChange = (file) => {
  selectedFile.value = file
}

const confirmUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择视频文件')
    return
  }

  isUploading.value = true
  
  try {
    emit('upload', selectedFile.value.raw)
    ElMessage.success('视频上传成功')
    showUploadDialog.value = false
    selectedFile.value = null
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  } finally {
    isUploading.value = false
  }
}

// 导出字幕
const handleExportSubtitle = () => {
  emit('export')
}

// 导入字幕
const handleImportSubtitle = () => {
  importFileInput.value?.click()
}

const handleImportFile = (event) => {
  const file = event.target.files[0]
  if (file) {
    emit('import', file)
    event.target.value = ''
  }
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
