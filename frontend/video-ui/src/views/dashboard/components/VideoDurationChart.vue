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
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
        shadowStyle: {
          color: 'rgba(59, 130, 246, 0.1)'
        }
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      padding: [12, 16],
      textStyle: {
        color: '#374151',
        fontSize: 13
      },
      formatter: (params) => {
        const item = params[0];
        return `
          <div style="font-weight: 600; margin-bottom: 6px; color: #111827;">${item.name}</div>
          <div style="display: flex; align-items: center;">
            <span style="display: inline-block; width: 10px; height: 10px; background: linear-gradient(135deg, #3b82f6, #1e40af); border-radius: 50%; margin-right: 8px;"></span>
            <span style="color: #6b7280;">视频数量:</span>
            <span style="font-weight: 600; margin-left: 8px; color: #3b82f6;">${item.value}</span>
          </div>
        `;
      }
    },
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
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#93c5fd' },
              { offset: 0.5, color: '#60a5fa' },
              { offset: 1, color: '#3b82f6' }
            ]),
            shadowColor: 'rgba(59, 130, 246, 0.5)',
            shadowBlur: 15,
            shadowOffsetY: 6
          }
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
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  border-radius: 16px;
  padding: 28px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.chart-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
  opacity: 0;
  transition: opacity 0.3s;
}

.chart-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.chart-card:hover::before {
  opacity: 1;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f3f4f6;
}

.chart-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.chart-header h3::before {
  content: '📊';
  font-size: 20px;
}

.chart-subtitle {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  padding: 4px 12px;
  border-radius: 12px;
  border: 1px solid #bfdbfe;
}

.chart-container {
  width: 100%;
  height: 380px;
  position: relative;
}
</style>
