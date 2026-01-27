<template>
  <div class="recycle-bin-page">
    <div class="page-container">
      <PageHeader
        title="回收站"
        :breadcrumb="[{ label: '视频管理' }, { label: '回收站' }]"
      />

      <!-- 提示信息卡片 -->
      <el-card class="info-card" shadow="never">
        <div class="info-content">
          <el-icon class="info-icon"><InfoFilled /></el-icon>
          <div class="info-text">
            <p class="info-title">回收站说明</p>
            <p class="info-description">视频删除后将在回收站保留 30 天，您可以在此期间恢复视频，超过期限将自动永久删除</p>
          </div>
        </div>
      </el-card>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-skeleton
          :loading="loading"
          animated
          :count="3"
          :rows="3"
          class="video-skeleton"
        />
      </div>

      <!-- 空状态 -->
      <div v-else-if="videos.length === 0" class="empty-container">
        <el-empty
          description="回收站是空的"
          image="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNDEiIHZpZXdCb3g9IjAgMCA2NCA0MSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyB0cmFuc2Zvcm09InRyYW5zbGF0ZSg5LjUgMCkiIGZpbGw9Im5vbmUiIGZpbGwtcnVsZT0iZXZlbm9kZCI+PGNpcmNsZSBmaWxsPSIjRjlGQUZBIiBjeD0iMTgiIGN5PSIyMCIgcj0iMiIvPjxjaXJjbGUgZmlsbD0iI0Y5RkFGQSIgY3g9IjQ2IiBjeT0iMjAiIHI9IjIiLz48cGF0aCBkPSJtMTQgMjJMMCAyOWwxNCA3TDI4IDIybDEtNCA3eiIgZmlsbD0iI0Y5RkFGQSIvPjxwYXRoIGQ9Im0yOCA0NEwxNCA1MWw5LTUgMTQgM0w0OCA0NEgyOHoiIGZpbGw9IiNFRUVFRUUiLz48Y2lyY2xlIGZpbGw9IiNGRkE0QTQiIGN4PSIyMSIgY3k9IjIxIiByPSIyIi8+PGNpcmNsZSBmaWxsPSIjRjQ0QTQ2IiBjeD0iNDEiIGN5PSI0MCIgcj0iMiIvPjxjaXJjbGUgZmlsbD0iIzlCQ0U1NyIgY3g9IjMwIiBjeT0iMzciIHI9IjIiLz48L2c+PC9zdmc+"
        >
          <template #image>
            <el-icon size="64" class="empty-icon"><Delete /></el-icon>
          </template>
          <el-button type="primary" @click="$router.push('/user/videos/uploaded')">
            <el-icon><ArrowLeft /></el-icon>
            返回我的视频
          </el-button>
        </el-empty>
      </div>

      <!-- 视频列表 -->
      <div v-else class="video-grid">
        <div
          v-for="video in videos"
          :key="video.id"
          class="video-card"
          :class="{ 'urgent-delete': video.days_until_permanent_delete <= 3 }"
        >
          <div class="card-header">
            <div class="thumbnail-container">
              <img
                :src="video.thumbnail || defaultThumbnail"
                :alt="video.title"
                class="video-thumbnail"
                @error="handleImageError"
              />
              <div class="video-overlay">
                <div class="play-icon">
                  <el-icon size="24"><VideoPlay /></el-icon>
                </div>
                <div class="video-duration" v-if="video.duration">
                  {{ formatDuration(video.duration) }}
                </div>
              </div>
            </div>

            <!-- 删除倒计时标签 -->
            <div class="delete-badge" :class="getWarningClass(video.days_until_permanent_delete)">
              <el-icon size="14"><WarningFilled /></el-icon>
              <span v-if="video.days_until_permanent_delete > 0">
                {{ video.days_until_permanent_delete }}天后删除
              </span>
              <span v-else>即将删除</span>
            </div>
          </div>

          <div class="card-body">
            <h3 class="video-title" :title="video.title">{{ video.title }}</h3>

            <div class="video-meta">
              <div class="meta-item">
                <el-icon size="14"><View /></el-icon>
                <span>{{ video.views_count || 0 }} 次观看</span>
              </div>
              <div class="meta-item">
                <el-icon size="14"><Clock /></el-icon>
                <span>{{ formatDate(video.deleted_at) }} 删除</span>
              </div>
            </div>
          </div>

          <div class="card-footer">
            <el-button
              type="primary"
              size="small"
              @click="restoreVideo(video)"
              :loading="video.restoring"
            >
              <el-icon><RefreshRight /></el-icon>
              恢复
            </el-button>
            <el-button
              type="danger"
              size="small"
              plain
              @click="confirmPermanentDelete(video)"
              :loading="video.deleting"
            >
              <el-icon><Delete /></el-icon>
              永久删除
            </el-button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next, jumper"
          background
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  WarningFilled,
  RefreshRight,
  Delete,
  InfoFilled,
  VideoPlay,
  View,
  Clock,
  ArrowLeft
} from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import service from '@/api/user';

const router = useRouter();
const loading = ref(true);
const videos = ref([]);
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);
const defaultThumbnail = 'https://via.placeholder.com/320x180?text=No+Thumbnail';

// 获取回收站视频列表
const fetchRecycleBin = async () => {
  try {
    loading.value = true;
    const response = await service({
      url: '/videos/videos/recycle_bin/',
      method: 'get',
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      }
    });

    videos.value = response.results || response;
    total.value = response.count || 0;
  } catch (error) {
    console.error('获取回收站列表失败:', error);
    ElMessage.error('获取回收站列表失败');
  } finally {
    loading.value = false;
  }
};

// 处理图片加载错误
const handleImageError = (event) => {
  event.target.src = defaultThumbnail;
};

// 恢复视频
const restoreVideo = async (video) => {
  try {
    await service({
      url: `/videos/videos/${video.id}/restore/`,
      method: 'post'
    });

    ElMessage.success('视频已恢复');
    fetchRecycleBin();
  } catch (error) {
    console.error('恢复视频失败:', error);
    ElMessage.error('恢复视频失败');
  }
};

// 确认永久删除
const confirmPermanentDelete = (video) => {
  ElMessageBox.confirm(
    `确定要永久删除视频"${video.title}"吗？此操作不可恢复！`,
    '永久删除确认',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'error',
      confirmButtonClass: 'el-button--danger'
    }
  ).then(() => {
    permanentDeleteVideo(video);
  }).catch(() => {
    // 用户取消
  });
};

// 永久删除视频
const permanentDeleteVideo = async (video) => {
  try {
    await service({
      url: `/videos/videos/${video.id}/permanent-delete/`,
      method: 'post'
    });

    ElMessage.success('视频已永久删除');
    fetchRecycleBin();
  } catch (error) {
    console.error('永久删除视频失败:', error);
    ElMessage.error('永久删除视频失败');
  }
};

// 分页切换
const handlePageChange = (page) => {
  currentPage.value = page;
  fetchRecycleBin();
};

// 格式化时长
const formatDuration = (seconds) => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) return '今天';
  if (days === 1) return '昨天';
  if (days < 7) return `${days} 天前`;
  return date.toLocaleDateString('zh-CN');
};

// 获取警告样式
const getWarningClass = (daysLeft) => {
  if (daysLeft <= 3) return 'urgent';
  if (daysLeft <= 7) return 'warning';
  return '';
};

onMounted(() => {
  fetchRecycleBin();
});
</script>

<style scoped>
.recycle-bin-page {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 24px;
}

.page-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 信息卡片美化 */
.info-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.info-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.info-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
}

.info-icon {
  color: #667eea;
  font-size: 32px;
  flex-shrink: 0;
}

.info-text {
  flex: 1;
}

.info-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.info-description {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  margin: 0;
}

/* 加载状态美化 */
.loading-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.video-skeleton {
  margin: 0 auto;
  max-width: 800px;
}

/* 空状态美化 */
.empty-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 24px;
  padding: 80px 40px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  margin: 40px 0;
}

.empty-icon {
  color: #cbd5e0;
  margin-bottom: 24px;
}

/* 视频网格布局 */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 20px;
}

/* 视频卡片美化 */
.video-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
}

.video-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.video-card.urgent-delete {
  border: 2px solid #ff4757;
  box-shadow: 0 8px 32px rgba(255, 71, 87, 0.3);
}

.video-card.urgent-delete::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #ff4757, #ff3838);
  z-index: 1;
}

/* 卡片头部 */
.card-header {
  position: relative;
}

.thumbnail-container {
  position: relative;
  width: 100%;
  height: 180px;
  overflow: hidden;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.video-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.video-card:hover .video-thumbnail {
  transform: scale(1.1);
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.video-card:hover .video-overlay {
  opacity: 1;
}

.play-icon {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  transform: scale(0.8);
  transition: transform 0.3s ease;
}

.video-card:hover .play-icon {
  transform: scale(1);
}

.video-duration {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  backdrop-filter: blur(4px);
}

/* 删除标签 */
.delete-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 2;
}

.delete-badge.urgent {
  background: linear-gradient(135deg, #ff4757, #ff3838);
  color: white;
  animation: urgentPulse 2s infinite;
}

.delete-badge.warning {
  background: linear-gradient(135deg, #ffa726, #fb8c00);
  color: white;
}

@keyframes urgentPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* 卡片主体 */
.card-body {
  padding: 20px;
}

.video-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 12px 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  transition: color 0.3s ease;
}

.video-card:hover .video-title {
  color: #667eea;
}

.video-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
  transition: color 0.3s ease;
}

.video-card:hover .meta-item {
  color: #764ba2;
}

/* 卡片底部 */
.card-footer {
  padding: 0 20px 20px 20px;
  display: flex;
  gap: 12px;
}

.card-footer .el-button {
  flex: 1;
  border-radius: 12px;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.card-footer .el-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.card-footer .el-button:hover::before {
  left: 100%;
}

.card-footer .el-button--primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.card-footer .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.card-footer .el-button--danger {
  background: linear-gradient(135deg, #ff4757, #ff3838);
  border: none;
  box-shadow: 0 4px 15px rgba(255, 71, 87, 0.4);
}

.card-footer .el-button--danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 71, 87, 0.6);
}

/* 分页美化 */
.pagination-wrapper {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  justify-content: center;
}

.pagination-wrapper :deep(.el-pagination) {
  background: transparent;
}

.pagination-wrapper :deep(.el-pagination .el-pager li) {
  background: transparent;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.pagination-wrapper :deep(.el-pagination .el-pager li:hover) {
  color: #667eea;
  border-color: #667eea;
}

.pagination-wrapper :deep(.el-pagination .el-pager li.is-active) {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-color: transparent;
  color: white;
}

.pagination-wrapper :deep(.el-pagination .btn-prev, .el-pagination .btn-next) {
  background: transparent;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.pagination-wrapper :deep(.el-pagination .btn-prev:hover, .el-pagination .btn-next:hover) {
  color: #667eea;
  border-color: #667eea;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .recycle-bin-page {
    padding: 16px;
  }

  .page-container {
    gap: 16px;
  }

  .info-content {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }

  .video-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .video-card {
    border-radius: 16px;
  }

  .thumbnail-container {
    height: 200px;
  }

  .card-body {
    padding: 16px;
  }

  .card-footer {
    padding: 0 16px 16px 16px;
    flex-direction: column;
  }

  .card-footer .el-button {
    width: 100%;
  }

  .empty-container {
    padding: 60px 20px;
    margin: 20px 0;
  }

  .pagination-wrapper {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .recycle-bin-page {
    padding: 12px;
  }

  .thumbnail-container {
    height: 160px;
  }

  .info-card, .empty-container, .pagination-wrapper {
    border-radius: 12px;
  }

  .video-card {
    border-radius: 12px;
  }
}

/* 滚动条美化 */
:deep(.el-pagination)::-webkit-scrollbar {
  height: 6px;
}

:deep(.el-pagination)::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

:deep(.el-pagination)::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 3px;
}

:deep(.el-pagination)::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #5a67d8, #6b46c1);
}
</style>
