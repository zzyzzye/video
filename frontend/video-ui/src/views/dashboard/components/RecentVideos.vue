<template>
  <div class="todo">
    <div class="head">
      <h3>最近作品</h3>
      <span class="video-count-badge">最近 {{ videos.length }} 个</span>
    </div>
    
    <div v-if="loading" class="loading">
      <el-skeleton :rows="3" animated />
    </div>
    
    <div v-else-if="videos.length === 0" class="empty-state">
      <el-empty description="暂无视频作品" />
      <el-button type="primary" @click="$emit('upload')" class="upload-now-btn">
        <el-icon><VideoCamera /></el-icon>
        立即上传
      </el-button>
    </div>
    
    <div v-else class="video-list">
      <div v-for="video in videos" :key="video.id" class="video-item">
        <div class="thumbnail">
          <img 
            v-if="video.thumbnail" 
            :src="getThumbnailUrl(video.thumbnail)" 
            alt="视频缩略图" 
            @error="handleImageError"
          />
          <div v-else class="thumbnail-placeholder">
            <el-icon><VideoCamera /></el-icon>
            <span>{{ getStatusText(video.status) }}</span>
          </div>
          <div class="duration" v-if="video.duration">{{ video.duration }}</div>
          <div class="status-badge" :class="getStatusClass(video.status)">
            {{ getStatusText(video.status) }}
          </div>
        </div>
        <div class="details">
          <h4>{{ video.title }}</h4>
          <div class="video-meta">
            <span class="meta-item">
              <el-icon><View /></el-icon>
              {{ video.views }}次观看
            </span>
            <span v-if="video.is_published" class="meta-item">
              <el-icon><Clock /></el-icon>
              {{ video.publishTime }}
            </span>
            <span v-else class="meta-item unpublished">
              <el-icon><Warning /></el-icon>
              未发布
            </span>
          </div>
          <div class="actions">
            <el-button size="small" @click="$emit('edit', video)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="$emit('delete', video)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, computed } from 'vue';
import { VideoCamera, View, Clock, Warning, Edit, Delete } from '@element-plus/icons-vue';
import { useNotificationStore } from '@/store/notification';

const props = defineProps({
  videos: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['upload', 'edit', 'delete', 'statusUpdate']);

const notificationStore = useNotificationStore();
let unsubscribe = null;

// 获取完整的缩略图 URL
const getThumbnailUrl = (thumbnail) => {
  if (!thumbnail) return null;
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  return thumbnail.startsWith('http') 
    ? thumbnail 
    : `${baseUrl}${thumbnail}`;
};

onMounted(() => {
  // 监听视频状态更新
  unsubscribe = notificationStore.onVideoStatusUpdate((videoData) => {
    // 查找并更新对应视频的状态
    const videoIndex = props.videos.findIndex(v => v.id === videoData.id);
    if (videoIndex !== -1) {
      const video = props.videos[videoIndex];
      
      // 使用 Object.assign 确保响应式更新
      Object.assign(video, {
        status: videoData.status,
        ...(videoData.duration && { duration: videoData.duration }),
        ...(videoData.resolution && { resolution: videoData.resolution }),
        ...(videoData.thumbnail && { thumbnail: videoData.thumbnail })
      });
      
      console.log('视频状态已更新:', {
        id: videoData.id,
        status: videoData.status,
        duration: videoData.duration,
        resolution: videoData.resolution,
        thumbnail: videoData.thumbnail
      });
      
      // 通知父组件状态已更新
      emit('statusUpdate', videoData);
    }
  });
});

onUnmounted(() => {
  // 取消监听
  if (unsubscribe) {
    unsubscribe();
  }
});

const statusMap = {
  'uploading': '上传中',
  'pending': '待审核',
  'approved': '已通过',
  'rejected': '未通过',
  'processing': '处理中',
  'ready': '就绪',
  'failed': '失败'
};

const getStatusText = (status) => statusMap[status] || status;

const getStatusClass = (status) => {
  const classMap = {
    'uploading': 'status-uploading',
    'pending': 'status-pending',
    'approved': 'status-approved',
    'rejected': 'status-rejected',
    'processing': 'status-processing',
    'ready': 'status-ready',
    'failed': 'status-failed'
  };
  return classMap[status] || '';
};

const handleImageError = (event) => {
  event.target.style.display = 'none';
  const placeholder = event.target.parentElement.querySelector('.thumbnail-placeholder');
  if (placeholder) {
    placeholder.style.display = 'flex';
  }
};
</script>

<style scoped>
.todo {
  border-radius: 12px;
  background: #ffffff;
  padding: 32px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
  flex-grow: 1;
  flex-basis: 300px;
}

.todo:hover {
  border-color: #d1d5db;
}

.head {
  display: flex;
  align-items: center;
  grid-gap: 16px;
  margin-bottom: 28px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f3f4f6;
}

.head h3 {
  margin-right: auto;
  font-size: 20px;
  font-weight: 700;
  color: #111827;
}

.video-count-badge {
  padding: 4px 12px;
  background: #eff6ff;
  color: #3b82f6;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}

.video-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.video-item {
  display: flex;
  flex-direction: column;
  padding: 16px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  transition: all 0.3s;
}

.video-item:hover {
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-4px);
}

.video-item .thumbnail {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: #f3f4f6;
  margin-bottom: 12px;
}

.video-item .thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.video-item:hover .thumbnail img {
  transform: scale(1.05);
}

.thumbnail-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  gap: 8px;
}

.thumbnail-placeholder .el-icon {
  font-size: 32px;
}

.thumbnail-placeholder span {
  font-size: 12px;
  font-weight: 600;
}

.video-item .thumbnail .duration {
  position: absolute;
  bottom: 6px;
  right: 6px;
  background-color: rgba(0, 0, 0, 0.85);
  color: white;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.video-item .thumbnail .status-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  color: white;
  backdrop-filter: blur(4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.status-uploading {
  background: linear-gradient(135deg, rgba(107, 114, 128, 0.95) 0%, rgba(75, 85, 99, 0.95) 100%);
}

.status-pending {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.95) 0%, rgba(245, 158, 11, 0.95) 100%);
}

.status-approved {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.95) 0%, rgba(5, 150, 105, 0.95) 100%);
}

.status-rejected {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.95) 0%, rgba(220, 38, 38, 0.95) 100%);
}

.status-processing {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.95) 0%, rgba(37, 99, 235, 0.95) 100%);
  animation: pulse 2s ease-in-out infinite;
}

.status-ready {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.95) 0%, rgba(124, 58, 237, 0.95) 100%);
}

.status-failed {
  background: linear-gradient(135deg, rgba(185, 28, 28, 0.95) 0%, rgba(153, 27, 27, 0.95) 100%);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.video-item .details {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.video-item .details h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: #2d3748;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.video-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 8px 0;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #718096;
  font-weight: 500;
}

.meta-item .el-icon {
  font-size: 14px;
}

.meta-item.unpublished {
  color: #f59e0b;
  font-weight: 600;
}

.video-item .actions {
  display: flex;
  gap: 8px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 48px 0;
}

.upload-now-btn {
  min-width: 160px;
  padding: 16px 40px !important;
  font-size: 16px !important;
  margin-top: 16px;
}

.loading {
  padding: 20px;
}

/* 响应式 */
@media screen and (max-width: 1200px) {
  .video-list {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media screen and (max-width: 768px) {
  .video-list {
    grid-template-columns: 1fr;
  }
}
</style>
