<template>
  <div class="timeline-panel">
    <!-- 时间刻度线 -->
    <div class="timeline-ruler">
      <div class="ruler-marks">
        <div 
          v-for="(mark, i) in timeMarks" 
          :key="i" 
          class="ruler-mark" 
          :class="{ major: mark.isMajor }"
          :style="{ left: mark.position + '%' }"
        >
          <span v-if="mark.isMajor" class="mark-time">{{ mark.label }}</span>
          <div class="mark-line"></div>
        </div>
      </div>
      <!-- 播放进度指示器 -->
      <div class="playhead" :style="{ left: playheadPosition + '%' }"></div>
    </div>
    
    <!-- 字幕轨道（包含波形图背景） -->
    <div class="subtitle-timeline" ref="timelineContainer" @click="handleTimelineClick">
      <!-- 波形图背景 -->
      <div ref="waveform" class="waveform-background"></div>
      
      <!-- 字幕块 -->
      <div
        v-for="(subtitle, index) in subtitles"
        :key="index"
        class="timeline-segment"
        :class="{ active: currentSubtitleIndex === index }"
        :style="getSubtitleStyle(subtitle)"
        @click.stop="selectSubtitle(index)"
        @mousedown="startDrag($event, index)"
      >
        <div class="segment-content">
          <span class="segment-label">{{ subtitle.text }}</span>
        </div>
        <!-- 调整手柄 -->
        <div class="resize-handle left" @mousedown.stop="startResize($event, index, 'left')"></div>
        <div class="resize-handle right" @mousedown.stop="startResize($event, index, 'right')"></div>
      </div>
      
      <!-- 播放进度线 -->
      <div class="playhead" :style="{ left: playheadPosition + '%' }"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  subtitles: {
    type: Array,
    default: () => []
  },
  currentSubtitleIndex: {
    type: Number,
    default: 0
  },
  duration: {
    type: Number,
    default: 127
  },
  currentTime: {
    type: Number,
    default: 0
  },
  videoUrl: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select-subtitle', 'update-subtitle', 'seek'])

const waveform = ref(null)
const timelineContainer = ref(null)
const waveformCanvas = ref(null)
const isDragging = ref(false)
const isResizing = ref(false)
const dragData = ref(null)

// 计算播放进度位置
const playheadPosition = computed(() => {
  if (props.duration === 0) return 0
  return (props.currentTime / props.duration) * 100
})

// 动态生成时间刻度 - 每秒一个刻度，每2秒显示时间
const timeMarks = computed(() => {
  const marks = []
  const duration = props.duration || 30
  const interval = 1 // 每1秒一个刻度
  
  const count = Math.ceil(duration / interval)
  for (let i = 0; i <= count; i++) {
    const time = i * interval
    if (time <= duration) {
      marks.push({
        position: (time / duration) * 100,
        label: formatTimeRuler(time),
        isMajor: time % 2 === 0 // 每2秒是主刻度，显示时间
      })
    }
  }
  return marks
})

onMounted(() => {
  drawMockWaveform()
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
})

// 绘制模拟波形图
const drawMockWaveform = () => {
  if (!waveform.value) return
  
  const canvas = document.createElement('canvas')
  const container = waveform.value
  const width = container.offsetWidth || 1000
  const height = container.offsetHeight || 80
  
  canvas.width = width
  canvas.height = height
  canvas.style.width = '100%'
  canvas.style.height = '100%'
  canvas.style.position = 'absolute'
  canvas.style.top = '0'
  canvas.style.left = '0'
  canvas.style.pointerEvents = 'none'
  
  const ctx = canvas.getContext('2d')
  
  // 清空画布
  ctx.clearRect(0, 0, width, height)
  
  // 绘制波形
  const barWidth = 2
  const barGap = 1
  const barCount = Math.floor(width / (barWidth + barGap))
  const centerY = height / 2
  
  // 绘制未播放部分（半透明灰色）
  for (let i = 0; i < barCount; i++) {
    const x = i * (barWidth + barGap)
    const progress = i / barCount
    
    // 生成随机波形高度，使用正弦波加随机数模拟真实波形
    const baseHeight = Math.sin(i * 0.08) * 18 + Math.random() * 22 + 10
    const barHeight = Math.min(baseHeight, height * 0.7)
    const y = centerY - barHeight / 2
    
    // 根据播放进度决定颜色
    const currentProgress = props.currentTime / props.duration
    if (progress <= currentProgress) {
      // 已播放部分 - 白色高亮
      ctx.fillStyle = 'rgba(255, 255, 255, 0.8)'
    } else {
      // 未播放部分 - 白色半透明
      ctx.fillStyle = 'rgba(255, 255, 255, 0.4)'
    }
    
    // 绘制圆角矩形
    ctx.beginPath()
    ctx.roundRect(x, y, barWidth, barHeight, 2)
    ctx.fill()
  }
  
  container.innerHTML = ''
  container.appendChild(canvas)
  waveformCanvas.value = canvas
}

// 点击时间轴跳转
const handleTimelineClick = (event) => {
  if (!timelineContainer.value) return
  const rect = timelineContainer.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const progress = x / rect.width
  const time = progress * props.duration
  emit('seek', time)
}

// 监听当前时间变化，更新波形进度
watch(() => props.currentTime, () => {
  drawMockWaveform()
})

// 监听容器大小变化，重绘波形
watch(() => props.duration, () => {
  setTimeout(() => drawMockWaveform(), 100)
})

const formatTimeRuler = (seconds) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const getSubtitleStyle = (subtitle) => {
  const left = (subtitle.startTime / props.duration) * 100
  const width = ((subtitle.endTime - subtitle.startTime) / props.duration) * 100
  return {
    left: `${left}%`,
    width: `${width}%`
  }
}

const selectSubtitle = (index) => {
  emit('select-subtitle', index)
}

// 开始拖拽字幕
const startDrag = (event, index) => {
  if (isResizing.value) return
  
  isDragging.value = true
  const subtitle = props.subtitles[index]
  dragData.value = {
    index,
    startX: event.clientX,
    originalStartTime: subtitle.startTime,
    originalEndTime: subtitle.endTime
  }
}

// 开始调整字幕时长
const startResize = (event, index, side) => {
  isResizing.value = true
  const subtitle = props.subtitles[index]
  dragData.value = {
    index,
    side,
    startX: event.clientX,
    originalStartTime: subtitle.startTime,
    originalEndTime: subtitle.endTime
  }
}

// 处理鼠标移动
const handleMouseMove = (event) => {
  if (!isDragging.value && !isResizing.value) return
  if (!dragData.value || !timelineContainer.value) return

  const containerWidth = timelineContainer.value.offsetWidth
  const deltaX = event.clientX - dragData.value.startX
  const deltaTime = (deltaX / containerWidth) * props.duration

  const subtitle = props.subtitles[dragData.value.index]
  const duration = subtitle.endTime - subtitle.startTime

  if (isDragging.value) {
    // 拖拽整个字幕
    let newStartTime = dragData.value.originalStartTime + deltaTime
    let newEndTime = dragData.value.originalEndTime + deltaTime

    // 限制在视频范围内
    if (newStartTime < 0) {
      newStartTime = 0
      newEndTime = duration
    }
    if (newEndTime > props.duration) {
      newEndTime = props.duration
      newStartTime = props.duration - duration
    }

    emit('update-subtitle', {
      index: dragData.value.index,
      startTime: newStartTime,
      endTime: newEndTime
    })
  } else if (isResizing.value) {
    // 调整字幕时长
    if (dragData.value.side === 'left') {
      let newStartTime = dragData.value.originalStartTime + deltaTime
      // 限制最小时长0.5秒
      if (newStartTime < 0) newStartTime = 0
      if (newStartTime >= subtitle.endTime - 0.5) newStartTime = subtitle.endTime - 0.5

      emit('update-subtitle', {
        index: dragData.value.index,
        startTime: newStartTime,
        endTime: subtitle.endTime
      })
    } else {
      let newEndTime = dragData.value.originalEndTime + deltaTime
      // 限制最小时长0.5秒
      if (newEndTime > props.duration) newEndTime = props.duration
      if (newEndTime <= subtitle.startTime + 0.5) newEndTime = subtitle.startTime + 0.5

      emit('update-subtitle', {
        index: dragData.value.index,
        startTime: subtitle.startTime,
        endTime: newEndTime
      })
    }
  }
}

// 处理鼠标释放
const handleMouseUp = () => {
  isDragging.value = false
  isResizing.value = false
  dragData.value = null
}
</script>

<style scoped lang="scss">
.timeline-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #0a0a0a;
  overflow: hidden;
  user-select: none;
}

.timeline-ruler {
  height: 32px;
  background: #1a1a1a;
  border-bottom: 1px solid #2a2a2a;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;

  .ruler-marks {
    height: 100%;
    position: relative;
    width: 100%;
  }

  .ruler-mark {
    position: absolute;
    display: flex;
    flex-direction: column;
    align-items: center;
    transform: translateX(-50%);
    top: 0;

    .mark-line {
      position: absolute;
      left: 50%;
      top: 0;
      width: 1px;
      height: 8px;
      background: #4a4a4a;
      transform: translateX(-50%);
    }

    .mark-time {
      font-size: 11px;
      color: #fff;
      line-height: 1;
      margin-top: 20px;
      white-space: nowrap;
      font-weight: 400;
      font-family: 'Courier New', monospace;
      display: none; // 默认不显示
    }

    // 主刻度（每2秒）
    &.major {
      .mark-line {
        height: 18px;
        background: #6a6a6a;
        width: 1px;
      }

      .mark-time {
        display: block; // 主刻度显示时间
        color: #fff;
        font-size: 11px;
        font-weight: 400;
      }
    }

    // 第一个刻度
    &:first-child {
      .mark-line {
        background: #6b46c1;
        width: 2px;
        height: 20px;
      }
      
      .mark-time {
        color: #6b46c1;
        font-weight: 500;
        display: block;
      }
    }
  }
}

.subtitle-timeline {
  flex: 1;
  background: #0a0a0a;
  position: relative;
  padding: 2px 0;
  min-height: 80px;
  max-height: 120px;
  cursor: pointer;
}

.waveform-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.timeline-segment {
  position: absolute;
  height: calc(100% - 16px);
  // top: 8px;
  background: linear-gradient(135deg, rgba(107, 70, 193, 0.75), rgba(107, 70, 193, 0.6));
  border: 1px solid rgba(107, 70, 193, 0.8);
  border-radius: 4px;
  cursor: move;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  transition: all 0.2s;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
  z-index: 10;

  &:hover {
    background: linear-gradient(135deg, rgba(107, 70, 193, 0.85), rgba(107, 70, 193, 0.7));
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(107, 70, 193, 0.5);
    z-index: 20;

    .resize-handle {
      opacity: 1;
    }
  }

  &.active {
    background: linear-gradient(135deg, rgba(107, 70, 193, 0.95), rgba(107, 70, 193, 0.85));
    border: 2px solid #8b6fd9;
    box-shadow: 0 0 10px rgba(107, 70, 193, 0.8), 0 2px 6px rgba(0, 0, 0, 0.5);
    z-index: 30;

    .resize-handle {
      opacity: 1;
    }
  }

  .segment-content {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    pointer-events: none;
  }

  .segment-label {
    font-size: 11px;
    color: #fff;
    font-weight: 500;
    line-height: 1.3;
    word-break: break-all;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
    padding: 2px;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .resize-handle {
    position: absolute;
    top: 0;
    width: 8px;
    height: 100%;
    background: rgba(255, 255, 255, 0.2);
    opacity: 0;
    transition: opacity 0.2s;
    z-index: 20;

    &.left {
      left: 0;
      cursor: ew-resize;
      border-left: 2px solid rgba(255, 255, 255, 0.5);
    }

    &.right {
      right: 0;
      cursor: ew-resize;
      border-right: 2px solid rgba(255, 255, 255, 0.5);
    }

    &:hover {
      background: rgba(255, 255, 255, 0.4);
    }
  }
}

.playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #ff4757;
  pointer-events: none;
  z-index: 100;
  box-shadow: 0 0 4px rgba(255, 71, 87, 0.8);

  &::before {
    content: '';
    position: absolute;
    top: -4px;
    left: 50%;
    transform: translateX(-50%);
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #ff4757;
  }
}
</style>
