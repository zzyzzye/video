<template>
  <div class="statistics-container">
    <PageHeader
      title="数据统计"
      :breadcrumb="[{ label: '管理后台' }, { label: '数据统计' }]"
    />

    <!-- 核心指标卡片 -->
    <div class="metrics-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
              <el-icon><User /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ stats.total_users }}</div>
              <div class="metric-label">总用户数</div>
              <div class="metric-trend positive">
                <el-icon><CaretTop /></el-icon>
                <span>{{ stats.new_users_today }} 今日新增</span>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
              <el-icon><VideoPlay /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ stats.total_videos }}</div>
              <div class="metric-label">总视频数</div>
              <div class="metric-trend positive">
                <el-icon><CaretTop /></el-icon>
                <span>{{ stats.new_videos_today }} 今日新增</span>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
              <el-icon><View /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ formatNumber(stats.total_views) }}</div>
              <div class="metric-label">总观看数</div>
              <div class="metric-trend positive">
                <el-icon><CaretTop /></el-icon>
                <span>{{ formatNumber(stats.views_today) }} 今日观看</span>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-icon" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
              <el-icon><Star /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ stats.vip_users }}</div>
              <div class="metric-label">VIP用户</div>
              <div class="metric-trend">
                <span>占比 {{ vipPercentage }}%</span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <div class="chart-card">
          <div class="chart-header">
            <h3>用户增长趋势</h3>
            <el-radio-group v-model="userChartPeriod" size="small" @change="loadUserTrend">
              <el-radio-button label="7">近7天</el-radio-button>
              <el-radio-button label="30">近30天</el-radio-button>
            </el-radio-group>
          </div>
          <div class="chart-content" ref="userChartRef" style="height: 300px;"></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="chart-card">
          <div class="chart-header">
            <h3>视频上传趋势</h3>
            <el-radio-group v-model="videoChartPeriod" size="small" @change="loadVideoTrend">
              <el-radio-button label="7">近7天</el-radio-button>
              <el-radio-button label="30">近30天</el-radio-button>
            </el-radio-group>
          </div>
          <div class="chart-content" ref="videoChartRef" style="height: 300px;"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <div class="chart-card">
          <div class="chart-header">
            <h3>用户角色分布</h3>
          </div>
          <div class="chart-content" ref="roleChartRef" style="height: 300px;"></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="chart-card">
          <div class="chart-header">
            <h3>视频状态分布</h3>
          </div>
          <div class="chart-content" ref="statusChartRef" style="height: 300px;"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 详细数据表格 -->
    <div class="table-section">
      <h3>热门视频排行</h3>
      <el-table :data="topVideos" style="width: 100%" v-loading="loading">
        <el-table-column type="index" label="排名" width="80" align="center" />
        <el-table-column prop="title" label="视频标题" min-width="200" />
        <el-table-column prop="user_username" label="作者" width="120" />
        <el-table-column prop="views" label="观看数" width="120" align="center">
          <template #default="scope">
            <span class="highlight-number">{{ formatNumber(scope.row.views) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="likes" label="点赞数" width="120" align="center">
          <template #default="scope">
            <span class="highlight-number">{{ formatNumber(scope.row.likes) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="160">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { User, VideoPlay, View, Star, CaretTop } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { 
  getStatisticsOverview, 
  getUserTrend, 
  getVideoTrend, 
  getRoleDistribution, 
  getStatusDistribution, 
  getTopVideos 
} from '@/api/admin'
import * as echarts from 'echarts'

const loading = ref(false)
const stats = ref({
  total_users: 0,
  vip_users: 0,
  active_users: 0,
  new_users_today: 0,
  total_videos: 0,
  new_videos_today: 0,
  total_views: 0,
  views_today: 0
})

const topVideos = ref([])
const userChartPeriod = ref('7')
const videoChartPeriod = ref('7')

const userChartRef = ref(null)
const videoChartRef = ref(null)
const roleChartRef = ref(null)
const statusChartRef = ref(null)

let userChart = null
let videoChart = null
let roleChart = null
let statusChart = null

const vipPercentage = computed(() => {
  if (stats.value.total_users === 0) return 0
  return ((stats.value.vip_users / stats.value.total_users) * 100).toFixed(1)
})

const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toString()
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const loadStats = async () => {
  try {
    const response = await getStatisticsOverview()
    stats.value = response
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  }
}

const loadUserTrend = async () => {
  try {
    const response = await getUserTrend(userChartPeriod.value)
    renderUserChart(response)
  } catch (error) {
    console.error('加载用户趋势失败:', error)
  }
}

const loadVideoTrend = async () => {
  try {
    const response = await getVideoTrend(videoChartPeriod.value)
    renderVideoChart(response)
  } catch (error) {
    console.error('加载视频趋势失败:', error)
  }
}

const loadRoleDistribution = async () => {
  try {
    const response = await getRoleDistribution()
    renderRoleChart(response)
  } catch (error) {
    console.error('加载角色分布失败:', error)
  }
}

const loadStatusDistribution = async () => {
  try {
    const response = await getStatusDistribution()
    renderStatusChart(response)
  } catch (error) {
    console.error('加载状态分布失败:', error)
  }
}

const loadTopVideos = async () => {
  loading.value = true
  try {
    const response = await getTopVideos(10)
    topVideos.value = response.results || []
  } catch (error) {
    console.error('加载热门视频失败:', error)
  } finally {
    loading.value = false
  }
}

const renderUserChart = (data) => {
  if (!userChart) {
    userChart = echarts.init(userChartRef.value)
  }

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.dates,
      boundaryGap: false
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '新增用户',
        type: 'line',
        smooth: true,
        data: data.counts,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(102, 126, 234, 0.5)' },
            { offset: 1, color: 'rgba(102, 126, 234, 0.1)' }
          ])
        },
        lineStyle: {
          color: '#667eea'
        },
        itemStyle: {
          color: '#667eea'
        }
      }
    ]
  }

  userChart.setOption(option)
}

const renderVideoChart = (data) => {
  if (!videoChart) {
    videoChart = echarts.init(videoChartRef.value)
  }

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.dates,
      boundaryGap: false
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '新增视频',
        type: 'line',
        smooth: true,
        data: data.counts,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(240, 147, 251, 0.5)' },
            { offset: 1, color: 'rgba(240, 147, 251, 0.1)' }
          ])
        },
        lineStyle: {
          color: '#f093fb'
        },
        itemStyle: {
          color: '#f093fb'
        }
      }
    ]
  }

  videoChart.setOption(option)
}

const renderRoleChart = (data) => {
  if (!roleChart) {
    roleChart = echarts.init(roleChartRef.value)
  }

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      bottom: '5%',
      left: 'center'
    },
    series: [
      {
        name: '用户角色',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: data.map((item, index) => ({
          value: item.count,
          name: item.role_display,
          itemStyle: {
            color: ['#667eea', '#f093fb', '#4facfe', '#fa709a'][index]
          }
        }))
      }
    ]
  }

  roleChart.setOption(option)
}

const renderStatusChart = (data) => {
  if (!statusChart) {
    statusChart = echarts.init(statusChartRef.value)
  }

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      bottom: '5%',
      left: 'center'
    },
    series: [
      {
        name: '视频状态',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: data.map((item, index) => ({
          value: item.count,
          name: item.status_display,
          itemStyle: {
            color: ['#67c23a', '#e6a23c', '#f56c6c', '#909399'][index]
          }
        }))
      }
    ]
  }

  statusChart.setOption(option)
}

onMounted(async () => {
  await loadStats()
  await nextTick()
  
  loadUserTrend()
  loadVideoTrend()
  loadRoleDistribution()
  loadStatusDistribution()
  loadTopVideos()

  window.addEventListener('resize', () => {
    userChart?.resize()
    videoChart?.resize()
    roleChart?.resize()
    statusChart?.resize()
  })
})
</script>

<style scoped>
.statistics-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.metrics-section {
  margin-bottom: 20px;
}

.metric-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
}

.metric-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.metric-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  color: #fff;
  font-size: 28px;
  flex-shrink: 0;
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 32px;
  font-weight: 700;
  color: #333;
  line-height: 1;
  margin-bottom: 8px;
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.metric-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
}

.metric-trend.positive {
  color: #67c23a;
}

.metric-trend .el-icon {
  font-size: 14px;
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.table-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-top: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.table-section h3 {
  margin: 0 0 20px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.highlight-number {
  color: #409eff;
  font-weight: 600;
}
</style>
