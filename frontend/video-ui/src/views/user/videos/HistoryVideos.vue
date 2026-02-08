<template>
  <div class="history-container">
    <PageHeader 
      title="观看历史" 
      :breadcrumb="[{ label: '视频管理' }, { label: '观看历史' }]"
      class="animate-slide-up"
    >
      <template #actions>
        <div class="header-actions animate-slide-up" style="animation-delay: 0.1s">
          <el-input
            v-model="searchQuery"
            placeholder="搜索观看历史..."
            clearable
            @input="handleSearch"
            style="width: 240px;"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-button type="danger" plain @click="clearHistory">
            <el-icon><Delete /></el-icon> 清空历史
          </el-button>
        </div>
      </template>
    </PageHeader>
    
    <div class="filter-bar animate-slide-up" style="animation-delay: 0.1s">
      <el-radio-group v-model="currentFilter" @change="handleFilterChange">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="today">今天</el-radio-button>
        <el-radio-button label="week">本周</el-radio-button>
        <el-radio-button label="month">本月</el-radio-button>
      </el-radio-group>
    </div>
    
    <div class="content-wrapper animate-slide-up" style="animation-delay: 0.2s">
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else-if="filteredVideos.length === 0" class="empty-container">
        <el-empty description="暂无观看记录">
          <el-button type="primary" @click="goToHome">去首页浏览</el-button>
        </el-empty>
      </div>
      
      <div v-else class="video-list">
        <div v-for="video in filteredVideos" :key="video.id" class="video-card">
          <div class="video-thumb" @click="watchVideo(video.id)">
            <img :src="video.thumbnail" alt="视频缩略图" />
            <div class="duration-badge">{{ video.duration }}</div>
            <div class="progress-overlay">
              <div class="progress-bar" :style="{ width: video.progress + '%' }"></div>
            </div>
            <div class="play-overlay">
              <el-icon class="play-icon"><VideoPlay /></el-icon>
            </div>
          </div>
          <div class="video-info">
            <h3 class="video-title" @click="watchVideo(video.id)">{{ video.title }}</h3>
            <div class="video-meta">
              <span class="author">{{ video.author }}</span>
              <span class="separator">·</span>
              <span class="views">{{ video.views }}次观看</span>
              <span class="separator">·</span>
              <span class="time">{{ video.publishTime }}</span>
            </div>
            <div class="watch-info">
              <el-icon><Clock /></el-icon>
              <span>观看于 {{ video.watchTime }}</span>
              <span class="progress-text">· 已观看 {{ video.progress }}%</span>
            </div>
            <div class="video-actions">
              <el-button size="small" type="primary" @click="watchVideo(video.id)">
                <el-icon><VideoPlay /></el-icon> 继续观看
              </el-button>
              <el-button size="small" plain @click="removeFromHistory(video)">
                <el-icon><Delete /></el-icon> 删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
      
      <div class="pagination-wrapper" v-if="filteredVideos.length > 0">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="totalVideos"
          :page-size="pageSize"
          :current-page="currentPage"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { VideoPlay, Delete, Search, Clock } from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getWatchHistory, deleteWatchRecord, clearWatchHistory } from '@/api/video';

const router = useRouter();
const loading = ref(true);
const searchQuery = ref('');
const currentFilter = ref('all');
const currentPage = ref(1);
const pageSize = ref(10);
const totalVideos = ref(0);
const historyVideos = ref([]);

// 获取观看历史记录
const fetchWatchHistory = async () => {
  loading.value = true;
  try {
    // 构建查询参数
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    };
    
    // 如果有搜索关键词，添加到参数中
    if (searchQuery.value) {
      params.search = searchQuery.value;
    }
    
    // 如果有时间筛选，添加到参数中
    if (currentFilter.value !== 'all') {
      params.time_filter = currentFilter.value;
    }
    
    // 调用API获取观看历史
    const response = await getWatchHistory(params);
    
    // 更新视频列表和总数
    historyVideos.value = response.results.map(item => ({
      id: item.video.id,
      title: item.video.title,
      thumbnail: item.video.thumbnail,
      duration: formatDuration(item.video.duration),
      progress: calculateProgress(item.watched_duration, item.video.duration),
      author: item.video.user.username,
      views: formatNumber(item.video.views_count),
      publishTime: formatTimeAgo(item.video.created_at),
      watchTime: formatTimeAgo(item.view_date),
      recordId: item.id // 保存记录ID，用于删除
    }));
    
    totalVideos.value = response.count;
    
  } catch (error) {
    console.error('获取观看历史失败:', error);
    ElMessage.error('获取观看历史失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 计算观看进度百分比
const calculateProgress = (watched, total) => {
  if (!watched || !total) return 0;
  const progress = (watched / total) * 100;
  return Math.min(progress, 100); // 确保不超过100%
};

// 格式化数字（如观看次数）
const formatNumber = (num) => {
  if (!num && num !== 0) return '0';
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + '千';
  }
  return num.toString();
};

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds && seconds !== 0) return '00:00';
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
};

// 格式化时间为"多久之前"
const formatTimeAgo = (dateString) => {
  if (!dateString) return '';
  
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  const diffMonth = Math.floor(diffDay / 30);
  const diffYear = Math.floor(diffMonth / 12);
  
  if (diffYear > 0) {
    return `${diffYear}年前`;
  } else if (diffMonth > 0) {
    return `${diffMonth}个月前`;
  } else if (diffDay > 0) {
    if (diffDay === 1) return '昨天';
    if (diffDay < 7) return `${diffDay}天前`;
    return `${Math.floor(diffDay / 7)}周前`;
  } else if (diffHour > 0) {
    return `${diffHour}小时前`;
  } else if (diffMin > 0) {
    return `${diffMin}分钟前`;
  } else {
    return '刚刚';
  }
};

// 根据筛选条件和搜索查询过滤视频
const filteredVideos = computed(() => {
  return historyVideos.value;
});

// 初始化
onMounted(() => {
  fetchWatchHistory();
});

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1;
  fetchWatchHistory();
};

// 处理筛选变化
const handleFilterChange = () => {
  currentPage.value = 1;
  fetchWatchHistory();
};

// 处理页码变化
const handlePageChange = (page) => {
  currentPage.value = page;
  fetchWatchHistory();
};

// 观看视频
const watchVideo = (id) => {
  router.push(`/video/${id}`);
};

// 从历史记录中删除
const removeFromHistory = async (video) => {
  ElMessageBox.confirm(
    `确定要删除"${video.title}"的观看记录吗？`,
    '删除记录',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      // 调用API删除观看记录
      await deleteWatchRecord(video.recordId);
      
      ElMessage({
        type: 'success',
        message: '已删除观看记录'
      });
      
      // 重新获取观看历史
      fetchWatchHistory();
    } catch (error) {
      console.error('删除观看记录失败:', error);
      ElMessage.error('删除观看记录失败，请稍后重试');
    }
  }).catch(() => {
    // 取消操作
  });
};

// 清空历史记录
const clearHistory = () => {
  ElMessageBox.confirm(
    '确定要清空所有观看历史记录吗？此操作无法撤销。',
    '清空历史记录',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      // 调用API清空观看历史
      await clearWatchHistory();
      
      ElMessage({
        type: 'success',
        message: '已清空所有观看历史'
      });
      
      // 清空本地数据
      historyVideos.value = [];
      totalVideos.value = 0;
    } catch (error) {
      console.error('清空观看历史失败:', error);
      ElMessage.error('清空观看历史失败，请稍后重试');
    }
  }).catch(() => {
    // 取消操作
  });
};

// 跳转到首页
const goToHome = () => {
  router.push('/');
};
</script>

<style scoped>
.history-container {
  padding: 20px;
  min-height: 100%;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 筛选栏 */
.filter-bar {
  background: #fff;
  padding: 16px 20px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* 内容包装器 */
.content-wrapper {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  min-height: 400px;
}

/* 加载状态 */
.loading-container {
  padding: 20px 0;
}

/* 空状态 */
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

/* 视频列表 - 网格布局 */
.video-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

/* 视频卡片 - 垂直布局 */
.video-card {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
  border: 1px solid #e8e8e8;
  cursor: pointer;
}

.video-card:hover {
  border-color: #00a1d6;
  box-shadow: 0 4px 12px rgba(0, 161, 214, 0.15);
  transform: translateY(-2px);
}

/* 视频缩略图 - 全宽 */
.video-thumb {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 宽高比 */
  background: #000;
  overflow: hidden;
}

.video-thumb img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.video-card:hover .video-thumb img {
  transform: scale(1.05);
}

.duration-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  z-index: 2;
}

.progress-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  z-index: 1;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #00a1d6 0%, #00b5e5 100%);
  transition: width 0.3s;
}

.play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  opacity: 0;
  transition: opacity 0.3s;
  z-index: 1;
}

.video-card:hover .play-overlay {
  opacity: 1;
}

.play-icon {
  font-size: 48px;
  color: #fff;
}

/* 视频信息 */
.video-info {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.video-title {
  font-size: 14px;
  font-weight: 500;
  color: #18191c;
  margin: 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: color 0.2s;
  min-height: 40px;
}

.video-card:hover .video-title {
  color: #00a1d6;
}

.video-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #9499a0;
  flex-wrap: wrap;
}

.video-meta .author {
  color: #61666d;
  font-weight: 500;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-meta .separator {
  color: #c9ccd0;
}

.watch-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #00a1d6;
  margin-top: auto;
}

.watch-info .el-icon {
  font-size: 14px;
}

.progress-text {
  color: #9499a0;
}

.video-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.video-actions .el-button {
  flex: 1;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e8e8e8;
}

/* 动画定义 */
@keyframes subtleSlideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-slide-up {
  animation: subtleSlideUp 0.4s ease-out both;
}

/* 响应式 */
@media screen and (max-width: 1200px) {
  .video-list {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media screen and (max-width: 768px) {
  .header-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .header-actions .el-input {
    width: 100% !important;
  }
  
  .video-list {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  }
}

@media screen and (max-width: 576px) {
  .history-container {
    padding: 12px;
  }
  
  .filter-bar {
    padding: 12px;
  }
  
  .content-wrapper {
    padding: 12px;
  }
  
  .video-list {
    grid-template-columns: 1fr;
  }
}
</style> 