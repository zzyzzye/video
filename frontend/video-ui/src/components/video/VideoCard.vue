<template>
  <div class="video-card" @click="handleClick">
    <!-- 封面图 -->
    <div class="video-thumbnail">
      <img :src="thumbnailUrl" :alt="video.title" />
      <div class="video-duration">{{ formatDuration(video.duration) }}</div>
      <div class="video-overlay">
        <div class="play-icon">▶</div>
      </div>
    </div>

    <!-- 视频信息 -->
    <div class="video-info">
      <!-- 用户头像 -->
      <div class="user-avatar" v-if="showAvatar">
        <img :src="video.user?.avatar || defaultAvatar" :alt="video.user?.username" />
      </div>

      <!-- 视频详情 -->
      <div class="video-details">
        <h3 class="video-title" :title="video.title">{{ video.title }}</h3>
        <div class="video-meta">
          <span class="author">{{ video.user?.username || '未知用户' }}</span>
          <div class="stats">
            <span>{{ formatViews(video.views_count) }} 次观看</span>
            <span class="dot">·</span>
            <span>{{ formatDate(video.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  video: {
    type: Object,
    required: true
  },
  showAvatar: {
    type: Boolean,
    default: true
  }
})

const router = useRouter()
const defaultAvatar = 'https://via.placeholder.com/40'

// 缩略图 URL
const thumbnailUrl = computed(() => {
  if (!props.video.thumbnail) {
    return 'https://via.placeholder.com/320x180?text=No+Image'
  }
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  return props.video.thumbnail.startsWith('http') 
    ? props.video.thumbnail 
    : `${baseUrl}/media/${props.video.thumbnail}`
})

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`
}

// 格式化观看次数
const formatViews = (count) => {
  if (!count) return '0'
  if (count >= 100000000) return `${(count / 100000000).toFixed(1)}亿`
  if (count >= 10000) return `${(count / 10000).toFixed(1)}万`
  return count.toString()
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  if (days < 30) return `${Math.floor(days / 7)}周前`
  if (days < 365) return `${Math.floor(days / 30)}个月前`
  return `${Math.floor(days / 365)}年前`
}

// 点击跳转到播放页
const handleClick = () => {
  router.push(`/video/${props.video.id}`)
}
</script>

<style scoped>
.video-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.video-card:hover {
  transform: translateY(-4px);
}

.video-thumbnail {
  position: relative;
  width: 100%;
  padding-bottom: 56.25%; /* 16:9 比例 */
  background: #f0f0f0;
  border-radius: 12px;
  overflow: hidden;
}

.video-thumbnail img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.video-card:hover .video-overlay {
  opacity: 1;
}

.play-icon {
  width: 60px;
  height: 60px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #333;
  padding-left: 4px;
}

.video-info {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.user-avatar {
  flex-shrink: 0;
}

.user-avatar img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.video-details {
  flex: 1;
  min-width: 0;
}

.video-title {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
  margin: 0 0 4px 0;
  color: #333;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.video-card:hover .video-title {
  color: #00a1d6;
}

.video-meta {
  font-size: 12px;
  color: #666;
}

.author {
  display: block;
  margin-bottom: 2px;
}

.stats {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dot {
  color: #999;
}

/* 响应式 */
@media (max-width: 768px) {
  .video-thumbnail {
    border-radius: 8px;
  }

  .user-avatar img {
    width: 36px;
    height: 36px;
  }

  .video-title {
    font-size: 13px;
  }

  .video-meta {
    font-size: 11px;
  }
}
</style>
