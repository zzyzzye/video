<template>
  <div class="chart-card">
    <div class="chart-header">
      <h3>视频时长分布</h3>
      <span class="chart-subtitle">按时长区间统计</span>
    </div>
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
});

const chartRef = ref(null);
let chartInstance = null;

const initChart = () => {
  if (!chartRef.value) return;
  
  chartInstance = echarts.init(chartRef.value);
  
  const ranges = props.data.map(item => item.range);
  const counts = props.data.map(item => item.count);
  
  const option = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: '8%',
      top: '12%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ranges,
      axisLine: {
        show: true,
        lineStyle: {
          color: '#e5e7eb',
          width: 1
        }
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: '#6b7280',
        fontSize: 12,
        fontWeight: 500,
        margin: 12
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: '#9ca3af',
        fontSize: 12,
        fontWeight: 500
      },
      splitLine: {
        lineStyle: {
          color: '#f3f4f6',
          type: 'dashed'
        }
      }
    },
    series: [
      {
        name: '视频数量',
        type: 'bar',
        barWidth: '45%',
        data: counts,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#60a5fa' },
            { offset: 0.5, color: '#3b82f6' },
            { offset: 1, color: '#2563eb' }
          ]),
          borderRadius: [8, 8, 0, 0],
          shadowColor: 'rgba(59, 130, 246, 0.3)',
          shadowBlur: 10,
          shadowOffsetY: 4
        },
        label: {
          show: true,
          position: 'top',
          color: '#3b82f6',
          fontSize: 12,
          fontWeight: 600,
          distance: 8,
          formatter: '{c}'
        },
        animationDelay: (idx) => idx * 100,
        animationEasing: 'elasticOut',
        animationDuration: 1000
      }
    ],
    animationEasing: 'cubicOut',
    animationDuration: 800
  };
  
  chartInstance.setOption(option);
};

const updateChart = () => {
  if (!chartInstance) return;
  
  const ranges = props.data.map(item => item.range);
  const counts = props.data.map(item => item.count);
  
  chartInstance.setOption({
    xAxis: {
      data: ranges
    },
    series: [
      {
        data: counts
      }
    ]
  });
};

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize();
  }
};

onMounted(() => {
  initChart();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose();
  }
  window.removeEventListener('resize', handleResize);
});

watch(() => props.data, () => {
  updateChart();
}, { deep: true });
</script>

<style scoped>
.chart-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.chart-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.chart-subtitle {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
}

.chart-container {
  width: 100%;
  height: 380px;
}
</style>
