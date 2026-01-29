<template>
  <div class="preview-wrapper">
    <!-- 上传/预览区域 -->
    <div class="upload-preview-area">
      <!-- 状态1: 未选择文件 -->
      <el-upload
        v-if="!file"
        class="video-uploader"
        drag
        action=""
        :auto-upload="false"
        :on-change="handleChange"
        :before-upload="beforeUpload"
        :show-file-list="false"
        accept="video/*"
      >
        <div class="upload-content">
          <el-icon class="upload-icon"><Upload /></el-icon>
          <div class="upload-text">点击或拖拽视频到此处上传</div>
          <div class="upload-tip">支持mp4, mov, avi等格式，最大500MB</div>
        </div>
      </el-upload>

      <!-- 状态2: 正在上传 -->
      <div v-else-if="uploading" class="uploading-state">
        <div class="video-preview">
          <video v-if="previewUrl" :src="previewUrl" class="video-element"></video>
        </div>
        <div class="upload-progress">
          <div class="progress-info">
            <span class="progress-status">{{ status }}</span>
            <span class="progress-percent">{{ Math.round(progress) }}%</span>
          </div>
          <el-progress :percentage="Math.round(progress)" :stroke-width="6" :show-text="false" color="#8b5cf6" />
        </div>
      </div>

      <!-- 状态3: 已选择文件 -->
      <div v-else class="preview-state">
        <video v-if="previewUrl" :src="previewUrl" controls class="video-player"></video>
      </div>
    </div>

    <!-- 底部信息栏 -->
    <div class="info-bar" v-if="file">
      <div class="file-header">
        <el-icon class="file-icon"><VideoPlay /></el-icon>
        <div class="file-name">{{ file.name }}</div>
        <!-- 字幕检测状态 -->
        <div class="subtitle-status" v-if="subtitleDetecting || subtitleInfo">
          <el-icon v-if="subtitleDetecting" class="is-loading"><Loading /></el-icon>
          <el-icon v-else-if="subtitleInfo?.has_subtitle" class="check-icon"><CircleCheck /></el-icon>
          <el-icon v-else class="none-icon"><CircleClose /></el-icon>
          <span class="status-text">
            {{ subtitleDetecting ? '检测字幕中...' : (subtitleInfo?.has_subtitle ? '已检测到字幕' : '未检测到字幕') }}
          </span>
        </div>
      </div>
      <div class="file-meta-grid">
        <div class="meta-card">
          <el-icon class="meta-icon"><Document /></el-icon>
          <div class="meta-content">
            <div class="meta-label">文件大小</div>
            <div class="meta-value">{{ formatFileSize(file.size) }}</div>
          </div>
        </div>
        <div class="meta-card">
          <el-icon class="meta-icon"><Files /></el-icon>
          <div class="meta-content">
            <div class="meta-label">文件格式</div>
            <div class="meta-value">{{ getFileExtension(file.name).toUpperCase() }}</div>
          </div>
        </div>
        <div class="meta-card" v-if="duration">
          <el-icon class="meta-icon"><Clock /></el-icon>
          <div class="meta-content">
            <div class="meta-label">视频时长</div>
            <div class="meta-value">{{ formatDuration(duration) }}</div>
          </div>
        </div>
        <div class="meta-card" v-if="aspectRatio">
          <el-icon class="meta-icon"><Crop /></el-icon>
          <div class="meta-content">
            <div class="meta-label">视频比例</div>
            <div class="meta-value">{{ aspectRatio }}</div>
          </div>
        </div>
        <!-- 字幕信息卡片 -->
        <div class="meta-card" v-if="subtitleInfo && !subtitleDetecting">
          <el-icon class="meta-icon" :class="subtitleInfo.has_subtitle ? 'success-icon' : 'info-icon'">
            <ChatDotRound />
          </el-icon>
          <div class="meta-content">
            <div class="meta-label">字幕信息</div>
            <div class="meta-value">
              {{ subtitleInfo.has_subtitle ? `${getSubtitleTypeText(subtitleInfo.subtitle_type)} (${subtitleInfo.subtitle_language || '未知语言'})` : '无字幕' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传提示信息 -->
    <div class="upload-tips" v-else>
      <div class="tips-header">
        <el-icon class="header-icon"><QuestionFilled /></el-icon>
        <span class="header-text">上传须知</span>
      </div>
      <div class="tips-list">
        <div class="tip-item">
          <el-icon class="tip-icon"><VideoCamera /></el-icon>
          <span>建议上传16:9比例的视频以获得最佳观看体验</span>
        </div>
        <div class="tip-item">
          <el-icon class="tip-icon"><Picture /></el-icon>
          <span>视频将自动生成4张封面，您也可以自定义上传</span>
        </div>
        <div class="tip-item">
          <el-icon class="tip-icon"><Check /></el-icon>
          <span>支持格式：MP4、MOV、AVI、FLV、MKV等主流格式</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Upload, QuestionFilled, VideoCamera, Picture, Check, VideoPlay, Document, Files, Clock, Crop, ChatDotRound, CircleCheck, CircleClose, Loading } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { formatFileSize, getFileExtension, formatDuration } from '@/utils/format';

const props = defineProps({
  file: { type: Object, default: null },
  previewUrl: { type: String, default: '' },
  uploading: { type: Boolean, default: false },
  progress: { type: Number, default: 0 },
  status: { type: String, default: '' },
  duration: { type: Number, default: 0 },
  aspectRatio: { type: String, default: '' },
  subtitleDetecting: { type: Boolean, default: false },
  subtitleInfo: { type: Object, default: null }
});

const emit = defineEmits(['change']);

const getSubtitleTypeText = (type) => {
  const typeMap = {
    'soft': '软字幕',
    'hard': '硬字幕',
    'none': '无字幕'
  };
  return typeMap[type] || type;
};

const beforeUpload = (file) => {
  const isVideo = file.type.startsWith('video/');
  const isLt500M = file.size / 1024 / 1024 < 500;
  
  if (!isVideo) {
    ElMessage.error('只能上传视频文件!');
    return false;
  }
  if (!isLt500M) {
    ElMessage.error('视频大小不能超过500MB!');
    return false;
  }
  return true;
};

const handleChange = (uploadFile) => {
  if (uploadFile.raw) {
    emit('change', uploadFile);
  }
};
</script>

<style scoped>
.preview-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 上传/预览区域 */
.upload-preview-area {
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* 上传器 */
.video-uploader {
  width: 100%;
  height: 100%;
}

.video-uploader :deep(.el-upload) {
  width: 100%;
  height: 100%;
  display: block;
}

.video-uploader :deep(.el-upload-dragger) {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #1a1a1a;
  border: 2px dashed #404040;
  border-radius: 8px;
  transition: all 0.3s;
  padding: 0;
  margin: 0;
}

.video-uploader :deep(.el-upload-dragger:hover) {
  background: #252525;
  border-color: #8b5cf6;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 40px;
  pointer-events: none;
}

.upload-icon {
  font-size: 64px;
  color: #8b5cf6;
  margin-bottom: 20px;
  transition: transform 0.3s;
}

.video-uploader :deep(.el-upload-dragger:hover) .upload-icon {
  transform: translateY(-5px) scale(1.1);
}

.upload-text {
  font-size: 16px;
  color: #e5e7eb;
  margin-bottom: 8px;
  font-weight: 500;
}

.upload-tip {
  font-size: 14px;
  color: #9ca3af;
}

/* 上传中状态 */
.uploading-state {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #000;
}

.video-preview {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.upload-progress {
  padding: 20px 24px;
  background: rgba(0, 0, 0, 0.9);
  border-top: 1px solid #404040;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-status {
  font-size: 14px;
  font-weight: 500;
  color: #e5e7eb;
}

.progress-percent {
  font-size: 18px;
  font-weight: 700;
  color: #8b5cf6;
}

/* 预览状态 */
.preview-state {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* 底部信息栏 */
.info-bar {
  background: linear-gradient(135deg, #fff 0%, #fafbfc 100%);
  border: 1px solid #e3e5e7;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.file-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f3f4f6;
}

.file-icon {
  font-size: 20px;
  color: #8b5cf6;
  flex-shrink: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 600;
  color: #18191c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.file-meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.meta-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #fff;
  border: 1px solid #e3e5e7;
  border-radius: 6px;
  transition: all 0.2s;
}

.meta-card:hover {
  border-color: #8b5cf6;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.1);
  transform: translateY(-2px);
}

.meta-icon {
  font-size: 18px;
  color: #8b5cf6;
  flex-shrink: 0;
}

.meta-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.meta-label {
  font-size: 11px;
  color: #9ca3af;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.meta-value {
  font-size: 14px;
  color: #18191c;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 上传提示 */
.upload-tips {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 10px;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  border: 1px solid #e3e5e7;
  border-radius: 8px;
}

.tips-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 5px;
  border-bottom: 2px solid #e3e5e7;
}

.header-icon {
  font-size: 20px;
  color: #8b5cf6;
}

.header-text {
  font-size: 15px;
  font-weight: 600;
  color: #18191c;
}

.tips-list {
  display: flex;
  flex-direction: column;
  /* gap: 12px; */
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  color: #61666d;
  line-height: 1.6;
  padding: 8px 12px;
  background: #fff;
  border-radius: 6px;
  transition: all 0.2s;
}

.tip-item:hover {
  background: #faf5ff;
  transform: translateX(4px);
}

.tip-icon {
  font-size: 16px;
  color: #8b5cf6;
  margin-top: 2px;
  flex-shrink: 0;
}

/* 字幕检测状态 */
.subtitle-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.subtitle-status .check-icon {
  color: #10b981;
}

.subtitle-status .none-icon {
  color: #9ca3af;
}

.subtitle-status .status-text {
  color: #6b7280;
}

.success-icon {
  color: #10b981;
}

.info-icon {
  color: #9ca3af;
}

/* 响应式 */
@media screen and (max-width: 768px) {
  .upload-preview-area {
    aspect-ratio: 16/9;
  }

  .upload-icon {
    font-size: 48px;
  }

  .upload-text {
    font-size: 14px;
  }

  .upload-tip {
    font-size: 12px;
  }
}
</style>
