<template>
  <div class="collection-container animate-slide-up">
    <PageHeader 
      title="收藏视频" 
      :breadcrumb="[{ label: '视频管理' }, { label: '收藏视频' }]"
      class="animate-slide-up"
    >
      <template #actions>
        <div class="header-actions animate-slide-up">
          <el-input
            v-model="searchQuery"
            placeholder="搜索收藏视频..."
            clearable
            @input="handleSearch"
            style="width: 240px;"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-button type="danger" plain @click="clearCollection">
            <el-icon><Delete /></el-icon> 清空收藏
          </el-button>
        </div>
      </template>
    </PageHeader>
    
    <div class="filter-bar animate-slide-up" style="animation-delay: 0.1s">
      <el-radio-group v-model="currentFilter" @change="handleFilterChange">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="recent">最近收藏</el-radio-button>
        <el-radio-button label="popular">最多播放</el-radio-button>
      </el-radio-group>
    </div>
    
    <div class="content-wrapper animate-slide-up" style="animation-delay: 0.2s">
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else-if="filteredVideos.length === 0" class="empty-container">
        <el-empty description="暂无收藏视频">
          <el-button type="primary" @click="goToHome">去首页浏览</el-button>
        </el-empty>
      </div>
      
      <div v-else class="video-list">
        <div v-for="video in filteredVideos" :key="video.id" class="video-card">
          <div class="video-thumb" @click="watchVideo(video.id)">
            <img :src="video.thumbnail" alt="视频缩略图" />
            <div class="duration-badge">{{ video.duration }}</div>
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
            <div class="collection-info">
              <el-icon><Star /></el-icon>
              <span>收藏于 {{ video.collectedAt }}</span>
            </div>
            <div class="video-actions">
              <el-button size="small" type="primary" @click="watchVideo(video.id)">
                <el-icon><VideoPlay /></el-icon> 观看
              </el-button>
              <el-button size="small" plain @click="removeFromCollection(video)">
                <el-icon><Delete /></el-icon> 取消收藏
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
import { VideoPlay, Delete, Search, Star } from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getCollections, deleteCollection, clearCollections } from '@/api/video';

const router = useRouter();
const loading = ref(true);
const searchQuery = ref('');
const currentFilter = ref('all');
const currentPage = ref(1);
const pageSize = ref(10);
const totalVideos = ref(0);
const collectionVideos = ref([]);

// 获取收藏列表
const fetchCollections = async () => {
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
    
    // 添加排序参数
    if (currentFilter.value !== 'all') {
      params.ordering = currentFilter.value;
    }
    
    // 调用API获取收藏列表
    const response = await getCollections(params);
    
    // 更新视频列表和总数
    collectionVideos.value = response.results.map(item => ({
      id: item.video.id,
      title: item.video.title,
      thumbnail: item.video.thumbnail,
      duration: formatDuration(item.video.duration),
      author: item.video.user.username,
      views: formatNumber(item.video.views_count),
      publishTime: formatTimeAgo(item.video.created_at),
      collectedAt: formatDate(item.created_at),
      collectionId: item.id // 保存收藏记录ID，用于删除
    }));
    
    totalVideos.value = response.count;
    
  } catch (error) {
    console.error('获取收藏列表失败:', error);
    ElMessage.error('获取收藏列表失败，请稍后重试');
  } finally {
    loading.value = false;
  }
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

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
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
  return collectionVideos.value;
});

// 初始化
onMounted(() => {
  fetchCollections();
});

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1;
  fetchCollections();
};

// 处理筛选变化
const handleFilterChange = () => {
  currentPage.value = 1;
  fetchCollections();
};

// 处理页码变化
const handlePageChange = (page) => {
  currentPage.value = page;
  fetchCollections();
};

// 观看视频
const watchVideo = (id) => {
  router.push(`/video/${id}`);
};

// 取消收藏
const removeFromCollection = async (video) => {
  ElMessageBox.confirm(
    `确定要取消收藏"${video.title}"吗？`,
    '取消收藏',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      // 调用API删除收藏记录
      await deleteCollection(video.collectionId);
      
      ElMessage({
        type: 'success',
        message: '已取消收藏'
      });
      
      // 重新获取收藏列表
      fetchCollections();
    } catch (error) {
      console.error('取消收藏失败:', error);
      ElMessage.error('取消收藏失败，请稍后重试');
    }
  }).catch(() => {
    // 取消操作
  });
};

// 清空收藏
const clearCollection = () => {
  ElMessageBox.confirm(
    '确定要清空所有收藏吗？此操作无法撤销。',
    '清空收藏',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      // 调用API清空收藏
      await clearCollections();
      
      ElMessage({
        type: 'success',
        message: '已清空所有收藏'
      });
      
      // 清空本地数据
      collectionVideos.value = [];
      totalVideos.value = 0;
    } catch (error) {
      console.error('清空收藏失败:', error);
      ElMessage.error('清空收藏失败，请稍后重试');
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
.collection-container {
  padding: 20px;
  min-height: 100%;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-bar {
  background: #fff;
  padding: 16px 20px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.content-wrapper {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  min-height: 400px;
}

.loading-container {
  padding: 20px 0;
}

.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.video-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

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

.collection-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #fb7299;
  margin-top: auto;
}

.collection-info .el-icon {
  font-size: 14px;
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
  .collection-container {
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