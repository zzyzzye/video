<template>
  <div class="dashboard-content">
    <PageHeader 
      title="工作台" 
      :breadcrumb="[{ label: '创作者仪表盘' }, { label: '工作台' }]"
      class="animate-fade-in"
    />

    <!-- 数据统计卡片 -->
    <StatsCards :stats="stats" />

    <!-- 图表区域 -->
    <div class="charts-section">
      <!-- 趋势图 - 独占一行 -->
      <div class="chart-row full-width">
        <VideoTrendChart 
          :data="trendData" 
          @timeRangeChange="handleTimeRangeChange"
          class="trend-chart"
        />
      </div>
      
      <!-- 时长分布图 + 分类玫瑰图 - 同一行 -->
      <div class="chart-row two-columns">
        <VideoDurationChart 
          :data="durationData"
          class="duration-chart"
        />
        <VideoCategoryChart 
          :data="categoryData"
          class="category-chart"
        />
      </div>
    </div>

    <!-- 最近作品 -->
    <div class="table-data">
      <RecentVideos 
        :videos="recentVideos" 
        :loading="loading"
        @upload="goToCreate"
        @edit="editVideo"
        @delete="deleteVideoHandler"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import PageHeader from '@/components/common/PageHeader.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getDashboardStats, getDashboardChartData } from '@/api/user';
import { deleteVideo } from '@/api/video';

// 组件
import StatsCards from './components/StatsCards.vue';
import RecentVideos from './components/RecentVideos.vue';
import VideoTrendChart from './components/VideoTrendChart.vue';
import VideoCategoryChart from './components/VideoCategoryChart.vue';
import VideoDurationChart from './components/VideoDurationChart.vue';

const router = useRouter();
const loading = ref(true);

// 用户统计数据
const stats = reactive({
  videoCount: 0,
  likeCount: 0,
  followerCount: 0,
  viewCount: 0
});

// 最近视频数据
const recentVideos = ref([]);

// 图表数据
const trendData = reactive({
  dates: [],
  views: [],
  likes: [],
  comments: []
});

const categoryData = ref([]);
const durationData = ref([]);

onMounted(() => {
  fetchDashboardData();
  fetchChartData(7);
});

const fetchDashboardData = async () => {
  loading.value = true;
  try {
    const response = await getDashboardStats();
    Object.assign(stats, response.stats);
    recentVideos.value = response.recentVideos;
  } catch (error) {
    console.error('获取仪表盘数据失败:', error);
    ElMessage.error('获取仪表盘数据失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

const fetchChartData = async (days) => {
  try {
    const response = await getDashboardChartData(days);
    
    // 更新趋势数据
    Object.assign(trendData, response.trend);
    
    // 更新分类分布数据
    categoryData.value = response.categoryDistribution || [];
    
    // 更新时长分布数据
    durationData.value = response.durationDistribution || [];
  } catch (error) {
    console.error('获取图表数据失败:', error);
    ElMessage.error('获取图表数据失败');
  }
};

const handleTimeRangeChange = (days) => {
  fetchChartData(parseInt(days));
};

const goToCreate = () => {
  router.push('/user/dashboard/create');
};

const editVideo = (video) => {
  router.push(`/user/videos/edit/${video.id}`);
};

const deleteVideoHandler = async (video) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除视频 "${video.title}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    await deleteVideo(video.id);
    
    ElMessage.success('删除成功');
    
    const index = recentVideos.value.findIndex(v => v.id === video.id);
    if (index !== -1) {
      recentVideos.value.splice(index, 1);
    }
    
    fetchDashboardData();
    fetchChartData(7);
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除视频失败:', error);
      ElMessage.error('删除视频失败，请重试');
    }
  }
};
</script>

<style scoped>
.dashboard-content {
  padding: 32px;
  box-sizing: border-box;
  width: 100%;
  min-height: 100%;
  overflow-x: hidden;
  background: #f0f2f5;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.animate-fade-in {
  animation: fadeIn 0.6s ease-out;
}

.charts-section {
  margin: 24px 0;
}

.chart-row {
  display: grid;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-row.full-width {
  grid-template-columns: 1fr;
}

.chart-row.two-columns {
  grid-template-columns: 1fr 1fr;
}

.trend-chart,
.duration-chart,
.category-chart {
  animation: fadeIn 0.8s ease-out;
}

.table-data {
  display: flex;
  flex-wrap: wrap;
  grid-gap: 20px;
  margin-bottom: 32px;
  width: 100%;
}

.table-data > div {
  border-radius: 12px;
  background: #ffffff;
  padding: 32px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.table-data > div:hover {
  border-color: #d1d5db;
}

/* 响应式 */
@media screen and (max-width: 1200px) {
  .chart-row.two-columns {
    grid-template-columns: 1fr;
  }
}

@media screen and (max-width: 768px) {
  .dashboard-content {
    padding: 16px;
  }
}
</style>
