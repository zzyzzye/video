<template>
  <div class="system-monitor">
    <PageHeader 
      title="系统监控" 
      :breadcrumb="[
        { label: '超级管理员', path: '/superadmin/monitor' },
        { label: '系统监控' }
      ]"
    >
      <template #actions>
        <el-switch
          v-model="autoRefresh"
          active-text="自动刷新"
          @change="toggleAutoRefresh"
        />
        <el-select v-model="refreshInterval" placeholder="刷新间隔" style="width: 120px;" @change="onIntervalChange">
          <el-option label="5 秒" :value="5000" />
          <el-option label="10 秒" :value="10000" />
          <el-option label="30 秒" :value="30000" />
          <el-option label="60 秒" :value="60000" />
        </el-select>
        <el-button type="primary" @click="refreshAllData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </template>
    </PageHeader>

    <!-- 实时数据卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card cpu-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">CPU 使用率</div>
              <div class="stat-value">{{ currentCpuUsage }}%</div>
            </div>
          </div>
          <el-progress 
            :percentage="parseFloat(currentCpuUsage)" 
            :color="getProgressColor(parseFloat(currentCpuUsage))"
            :show-text="false"
          />
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card memory-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon><Coin /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">内存使用率</div>
              <div class="stat-value">{{ currentMemoryUsage }}%</div>
            </div>
          </div>
          <el-progress 
            :percentage="parseFloat(currentMemoryUsage)" 
            :color="getProgressColor(parseFloat(currentMemoryUsage))"
            :show-text="false"
          />
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card disk-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">磁盘使用率</div>
              <div class="stat-value">{{ currentDiskUsage }}%</div>
            </div>
          </div>
          <el-progress 
            :percentage="parseFloat(currentDiskUsage)" 
            :color="getProgressColor(parseFloat(currentDiskUsage))"
            :show-text="false"
          />
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card process-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">运行进程</div>
              <div class="stat-value">{{ currentProcessCount }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <el-icon><Cpu /></el-icon>
              <span>CPU 使用率趋势</span>
            </div>
          </template>
          <div ref="cpuChartRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <el-icon><Coin /></el-icon>
              <span>内存使用率趋势</span>
            </div>
          </template>
          <div ref="memoryChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <el-icon><FolderOpened /></el-icon>
              <span>磁盘 I/O</span>
            </div>
          </template>
          <div ref="diskIoChartRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <el-icon><Connection /></el-icon>
              <span>网络 I/O</span>
            </div>
          </template>
          <div ref="networkIoChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>


<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import { 
  Monitor, Cpu, Coin, FolderOpened, Connection, Refresh 
} from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import PageHeader from '@/components/common/PageHeader.vue';
import service from '@/api/user';

const loading = ref(false);
const autoRefresh = ref(true);
const refreshInterval = ref(10000); // 默认 10 �?

const cpuChartRef = ref(null);
const memoryChartRef = ref(null);
const diskIoChartRef = ref(null);
const networkIoChartRef = ref(null);

let cpuChart = null;
let memoryChart = null;
let diskIoChart = null;
let networkIoChart = null;
let refreshTimer = null;

const currentCpuUsage = ref(0);
const currentMemoryUsage = ref(0);
const currentDiskUsage = ref(0);
const currentProcessCount = ref(0);

const cpuData = ref([]);
const memoryData = ref([]);
const diskReadData = ref([]);
const diskWriteData = ref([]);
const netSentData = ref([]);
const netRecvData = ref([]);
const timeLabels = ref([]);

const initCharts = () => {
  nextTick(() => {
    if (cpuChartRef.value) {
      cpuChart = echarts.init(cpuChartRef.value);
      cpuChart.setOption(getCpuChartOption());
    }
    
    if (memoryChartRef.value) {
      memoryChart = echarts.init(memoryChartRef.value);
      memoryChart.setOption(getMemoryChartOption());
    }
    
    if (diskIoChartRef.value) {
      diskIoChart = echarts.init(diskIoChartRef.value);
      diskIoChart.setOption(getDiskIoChartOption());
    }
    
    if (networkIoChartRef.value) {
      networkIoChart = echarts.init(networkIoChartRef.value);
      networkIoChart.setOption(getNetworkIoChartOption());
    }

    window.addEventListener('resize', handleResize);
  });
};

const handleResize = () => {
  cpuChart?.resize();
  memoryChart?.resize();
  diskIoChart?.resize();
  networkIoChart?.resize();
};

const getCpuChartOption = () => ({
  tooltip: {
    trigger: 'axis',
    formatter: '{b}<br/>{a}: {c}%'
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '15%',
    top: '10%',
    containLabel: true
  },
  dataZoom: [
    {
      type: 'inside',
      start: 0,
      end: 100
    },
    {
      type: 'slider',
      start: 0,
      end: 100,
      height: 20,
      bottom: 10
    }
  ],
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: timeLabels.value,
    axisLabel: {
      fontSize: 10,
      rotate: 0
    }
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 100,
    axisLabel: {
      formatter: '{value}%',
      fontSize: 10
    }
  },
  series: [{
    name: 'CPU 使用率',
    type: 'line',
    smooth: true,
    data: cpuData.value,
    areaStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(33, 150, 243, 0.5)' },
        { offset: 1, color: 'rgba(33, 150, 243, 0.1)' }
      ])
    },
    lineStyle: {
      color: '#2196f3',
      width: 2
    },
    itemStyle: {
      color: '#2196f3'
    }
  }]
});

const getMemoryChartOption = () => ({
  tooltip: {
    trigger: 'axis',
    formatter: '{b}<br/>{a}: {c}%'
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '15%',
    top: '10%',
    containLabel: true
  },
  dataZoom: [
    {
      type: 'inside',
      start: 0,
      end: 100
    },
    {
      type: 'slider',
      start: 0,
      end: 100,
      height: 20,
      bottom: 10
    }
  ],
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: timeLabels.value,
    axisLabel: {
      fontSize: 10,
      rotate: 0
    }
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 100,
    axisLabel: {
      formatter: '{value}%',
      fontSize: 10
    }
  },
  series: [{
    name: '内存使用率',
    type: 'line',
    smooth: true,
    data: memoryData.value,
    areaStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(76, 175, 80, 0.5)' },
        { offset: 1, color: 'rgba(76, 175, 80, 0.1)' }
      ])
    },
    lineStyle: {
      color: '#4caf50',
      width: 2
    },
    itemStyle: {
      color: '#4caf50'
    }
  }]
});

const getDiskIoChartOption = () => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      let result = params[0].name + '<br/>';
      params.forEach(item => {
        result += `${item.seriesName}: ${item.value} MB<br/>`;
      });
      return result;
    }
  },
  legend: {
    data: ['读取', '写入'],
    top: 0
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '15%',
    top: '15%',
    containLabel: true
  },
  dataZoom: [
    {
      type: 'inside',
      start: 0,
      end: 100
    },
    {
      type: 'slider',
      start: 0,
      end: 100,
      height: 20,
      bottom: 10
    }
  ],
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: timeLabels.value,
    axisLabel: {
      fontSize: 10,
      rotate: 0
    }
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: '{value} MB',
      fontSize: 10
    }
  },
  series: [
    {
      name: '读取',
      type: 'line',
      smooth: true,
      data: diskReadData.value,
      lineStyle: {
        color: '#ff9800',
        width: 2
      },
      itemStyle: {
        color: '#ff9800'
      }
    },
    {
      name: '写入',
      type: 'line',
      smooth: true,
      data: diskWriteData.value,
      lineStyle: {
        color: '#f44336',
        width: 2
      },
      itemStyle: {
        color: '#f44336'
      }
    }
  ]
});

const getNetworkIoChartOption = () => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      let result = params[0].name + '<br/>';
      params.forEach(item => {
        result += `${item.seriesName}: ${item.value} MB<br/>`;
      });
      return result;
    }
  },
  legend: {
    data: ['发送', '接收'],
    top: 0
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '15%',
    top: '15%',
    containLabel: true
  },
  dataZoom: [
    {
      type: 'inside',
      start: 0,
      end: 100
    },
    {
      type: 'slider',
      start: 0,
      end: 100,
      height: 20,
      bottom: 10
    }
  ],
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: timeLabels.value,
    axisLabel: {
      fontSize: 10,
      rotate: 0
    }
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: '{value} MB',
      fontSize: 10
    }
  },
  series: [
    {
      name: '发送',
      type: 'line',
      smooth: true,
      data: netSentData.value,
      lineStyle: {
        color: '#9c27b0',
        width: 2
      },
      itemStyle: {
        color: '#9c27b0'
      }
    },
    {
      name: '接收',
      type: 'line',
      smooth: true,
      data: netRecvData.value,
      lineStyle: {
        color: '#3f51b5',
        width: 2
      },
      itemStyle: {
        color: '#3f51b5'
      }
    }
  ]
});

const loadPerformanceData = async () => {
  try {
    const response = await service({
      url: '/users/system/performance/',
      method: 'get'
    });

    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

    timeLabels.value.push(timeStr);
    cpuData.value.push(response.cpu_avg?.toFixed(2) || 0);
    memoryData.value.push(response.memory_percent?.toFixed(2) || 0);
    diskReadData.value.push(response.disk_read_mb?.toFixed(2) || 0);
    diskWriteData.value.push(response.disk_write_mb?.toFixed(2) || 0);
    netSentData.value.push(response.net_sent_mb?.toFixed(2) || 0);
    netRecvData.value.push(response.net_recv_mb?.toFixed(2) || 0);

    currentCpuUsage.value = response.cpu_avg?.toFixed(2) || 0;
    currentMemoryUsage.value = response.memory_percent?.toFixed(2) || 0;
    currentProcessCount.value = response.process_count || 0;

    const diskInfo = await service({
      url: '/users/system/info/',
      method: 'get'
    });
    currentDiskUsage.value = diskInfo.disk?.percent?.toFixed(2) || 0;

    updateCharts();
  } catch (error) {
    console.error('加载性能数据失败:', error);
  }
};

const loadHistoryData = async () => {
  try {
    const response = await service({
      url: '/users/system/history/',
      method: 'get',
      params: {
        minutes: 60
      }
    });

    timeLabels.value = response.time_labels || [];
    cpuData.value = response.cpu_data || [];
    memoryData.value = response.memory_data || [];
    diskReadData.value = response.disk_read_data || [];
    diskWriteData.value = response.disk_write_data || [];
    netSentData.value = response.net_sent_data || [];
    netRecvData.value = response.net_recv_data || [];

    if (cpuData.value.length > 0) {
      currentCpuUsage.value = cpuData.value[cpuData.value.length - 1];
      currentMemoryUsage.value = memoryData.value[memoryData.value.length - 1];
    }

    updateCharts();
  } catch (error) {
    console.error('加载历史数据失败:', error);
  }
};

const updateCharts = () => {
  cpuChart?.setOption({
    xAxis: { data: timeLabels.value },
    series: [{ data: cpuData.value }]
  });

  memoryChart?.setOption({
    xAxis: { data: timeLabels.value },
    series: [{ data: memoryData.value }]
  });

  diskIoChart?.setOption({
    xAxis: { data: timeLabels.value },
    series: [
      { data: diskReadData.value },
      { data: diskWriteData.value }
    ]
  });

  networkIoChart?.setOption({
    xAxis: { data: timeLabels.value },
    series: [
      { data: netSentData.value },
      { data: netRecvData.value }
    ]
  });
};

const refreshAllData = async () => {
  loading.value = true;
  try {
    await loadPerformanceData();
  } finally {
    loading.value = false;
  }
};

const toggleAutoRefresh = (value) => {
  if (value) {
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
};

const startAutoRefresh = () => {
  stopAutoRefresh();
  refreshTimer = setInterval(() => {
    loadPerformanceData();
  }, refreshInterval.value);
};

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
};

const onIntervalChange = () => {
  if (autoRefresh.value) {
    startAutoRefresh();
  }
};

const getProgressColor = (percent) => {
  if (percent < 60) return '#67c23a';
  if (percent < 80) return '#e6a23c';
  return '#f56c6c';
};

onMounted(async () => {
  initCharts();
  await loadHistoryData();
  if (autoRefresh.value) {
    startAutoRefresh();
  }
});

onBeforeUnmount(() => {
  stopAutoRefresh();
  window.removeEventListener('resize', handleResize);
  cpuChart?.dispose();
  memoryChart?.dispose();
  diskIoChart?.dispose();
  networkIoChart?.dispose();
});
</script>


<style scoped>
.system-monitor {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 70px);
}



.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
}

.stat-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.cpu-card .stat-icon {
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
  color: #fff;
}

.memory-card .stat-icon {
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
  color: #fff;
}

.disk-card .stat-icon {
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
  color: #fff;
}

.process-card .stat-icon {
  background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
  color: #fff;
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.chart-card {
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.card-header .el-icon {
  font-size: 20px;
  color: #2196f3;
}

.chart-container {
  width: 100%;
  height: 350px;
}
</style>
