<template>
  <div class="search-page">
    <!-- 顶部导航 -->
    <TopNav />

    <!-- 搜索结果区域 -->
    <div class="search-container">
      <!-- 搜索信息 -->
      <div class="search-header">
        <h2 class="search-title">
          搜索结果：<span class="search-keyword">{{ searchQuery }}</span>
        </h2>
        <div v-if="!loading && videos.length > 0" class="search-count">
          找到 {{ totalCount }} 个相关视频
        </div>
      </div>

      <!-- 筛选和排序 -->
      <div class="search-filters">
        <el-radio-group v-model="sortOption" size="default" @change="handleSortChange">
          <el-radio-button value="-created_at">最新发布</el-radio-button>
          <el-radio-button value="-views_count">最多播放</el-radio-button>
          <el-radio-button value="-likes_count">最多点赞</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading && videos.length === 0" class="loading-state">
        <div class="loading-spinner"></div>
        <p>搜索中...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="videos.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Search /></el-icon>
        <p class="empty-text">未找到与 "{{ searchQuery }}" 相关的视频</p>
        <p class="empty-hint">试试其他关键词吧</p>
      </div>

      <!-- 视频列表 -->
      <div v-else class="video-grid">
        <div
          v-for="(video, index) in videos"
          :key="video.id"
          class="video-item"
          :style="{ animationDelay: `${index * 0.05}s` }"
          @click="goToVideo(video.id)"
        >
          <div class="video-cover-wrapper">
            <el-image 
              :src="video.thumbnail" 
              fit="cover"
              class="video-cover"
              lazy
            >
              <template #error>
                <div class="cover-error">
                  <el-icon><VideoCamera /></el-icon>
                </div>
              </template>
            </el-image>
            
            <!-- 播放时长 -->
            <div class="video-duration">
              <el-icon class="play-icon"><VideoPlay /></el-icon>
              <span>{{ formatDuration(video.duration) }}</span>
            </div>
            
            <!-- 分辨率标识 -->
            <div v-if="video.resolution_label" class="resolution-badge" :class="video.resolution_label.toLowerCase()">
              {{ video.resolution_label }}
            </div>
          </div>
          
          <div class="video-info">
            <h3 class="video-title">{{ video.title }}</h3>
            <div class="video-meta">
              <div class="author-info" @click.stop="goToUser(video.user.id)">
                <el-avatar :size="20" :src="video.user.avatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <span class="author-name">{{ video.user.username }}</span>
              </div>
              <div class="video-stats">
                <span>{{ formatNumber(video.views_count) }} 播放</span>
                <span class="dot">·</span>
                <span>{{ formatNumber(video.likes_count) }} 点赞</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载更多 -->
      <div v-if="hasMore && !loading" class="load-more-wrapper">
        <el-button 
          @click="loadMore" 
          :loading="loadingMore"
          type="primary"
        >
          {{ loadingMore ? '加载中...' : '加载更多' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TopNav from '@/components/common/TopNav.vue'
import { Search, VideoCamera, VideoPlay, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import service from '@/api/user'

const route = useRoute()
const router = useRouter()

const searchQuery = ref('')
const loading = ref(false)
const loadingMore = ref(false)
const videos = ref([])
const totalCount = ref(0)
const hasMore = ref(true)
const currentPage = ref(1)
const sortOption = ref('-created_at')

// 执行搜索
const performSearch = async (query, page = 1) => {
  if (!query || !query.trim()) {
    return
  }

  try {
    if (page === 1) {
      loading.value = true
      videos.value = []
    } else {
      loadingMore.value = true
    }

    const params = {
      search: query.trim(),  // 使用 search 参数
      page,
      page_size: 20,
      ordering: sortOption.value
    }

    console.log('搜索参数:', params)
    // 使用数据库搜索接口
    const response = await service.get('/videos/videos/', { params })
    const response = await service.get('/videos/search/', { params })
    
    if (page === 1) {
      videos.value = response.results || []
    } else {
      videos.value = [...videos.value, ...(response.results || [])]
    }
    
    totalCount.value = response.count || 0
    hasMore.value = !!response.next
    currentPage.value = page
    
    console.log(`搜索到 ${videos.value.length} 个视频，总共 ${totalCount.value} 个`)
  } catch (error) {
    console.error('搜索失败:', error)
    // 如果 Elasticsearch 失败，回退到普通搜索
    console.log('尝试使用普通搜索...')
    try {
      const params = {
        search: query.trim(),
        page,
        page_size: 20,
        ordering: sortOption.value
      }
      const response = await service.get('/videos/videos/', { params })
      
      if (page === 1) {
        videos.value = response.results || []
      } else {
        videos.value = [...videos.value, ...(response.results || [])]
      }
      
      totalCount.value = response.count || 0
      hasMore.value = !!response.next
      currentPage.value = page
    } catch (fallbackError) {
      console.error('普通搜索也失败:', fallbackError)
      ElMessage.error('搜索失败，请稍后重试')
    }
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 处理排序变化
const handleSortChange = () => {
  currentPage.value = 1
  hasMore.value = true
  performSearch(searchQuery.value, 1)
}

// 加载更多
const loadMore = () => {
  if (!loadingMore.value && hasMore.value) {
    performSearch(searchQuery.value, currentPage.value + 1)
  }
}

// 跳转到视频详情
const goToVideo = (videoId) => {
  router.push(`/video/${videoId}`)
}

// 跳转到用户主页
const goToUser = (userId) => {
  router.push(`/user/${userId}`)
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds && seconds !== 0) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}

// 格式化数字
const formatNumber = (num) => {
  if (!num && num !== 0) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

// 监听路由参数变化
watch(() => route.query.q, (newQuery) => {
  if (newQuery) {
    searchQuery.value = newQuery
    currentPage.value = 1
    hasMore.value = true
    performSearch(newQuery, 1)
  }
})

onMounted(() => {
  if (route.query.q) {
    searchQuery.value = route.query.q
    performSearch(route.query.q, 1)
  }
})
</script>

<style scoped>
.search-page {
  min-height: 100vh;
  background: #ffffff;
}

.search-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 20px;
}

.search-header {
  margin-bottom: 24px;
}

.search-title {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.search-keyword {
  color: #3b82f6;
}

.search-count {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.search-filters {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.search-filters :deep(.el-radio-button__inner) {
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  padding: 8px 20px;
  font-weight: 500;
}

.search-filters :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 8px;
}

.search-filters :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 8px;
}

.search-filters :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 0;
  color: #6b7280;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 0;
  animation: fadeIn 0.6s ease-out;
}

.empty-icon {
  font-size: 80px;
  color: #d1d5db;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 18px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px 0;
}

.empty-hint {
  font-size: 14px;
  color: #9ca3af;
  margin: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 40px;
}

.video-item {
  background: #ffffff;
  cursor: pointer;
  overflow: hidden;
  animation: cardFadeIn 0.5s ease-out both;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.video-item:hover {
  transform: translateY(-4px);
}

@keyframes cardFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.video-cover-wrapper {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 */
  background: #000;
  overflow: hidden;
  border-radius: 10px;
}

.video-cover {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.video-cover :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-error {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: rgba(255, 255, 255, 0.8);
  font-size: 40px;
}

.video-duration {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  border-radius: 4px;
  color: #fff;
  font-size: 12px;
  font-weight: 500;
}

.play-icon {
  font-size: 12px;
}

.resolution-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}

.resolution-badge.4k {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  box-shadow: 0 2px 8px rgba(238, 90, 36, 0.4);
}

.resolution-badge.2k {
  background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
  box-shadow: 0 2px 8px rgba(108, 92, 231, 0.4);
}

.video-info {
  padding-top: 12px;
}

.video-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
  margin: 0 0 8px 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-word;
  transition: color 0.3s;
}

.video-item:hover .video-title {
  color: #3b82f6;
}

.video-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 6px;
  transition: color 0.3s;
}

.author-info:hover {
  color: #3b82f6;
}

.author-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #9ca3af;
}

.dot {
  color: #d1d5db;
}

.load-more-wrapper {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.load-more-wrapper .el-button {
  padding: 12px 32px;
  font-size: 15px;
  font-weight: 500;
  border-radius: 8px;
  background: #3b82f6;
  border: none;
  color: #fff;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.load-more-wrapper .el-button:hover {
  background: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
}

@media (max-width: 1200px) {
  .video-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .search-container {
    padding: 16px 12px;
  }

  .search-title {
    font-size: 20px;
  }

  .video-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .video-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
}
</style> 