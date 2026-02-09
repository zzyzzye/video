<template>
  <div class="timeline-panel" ref="timelinePanel">
    <div class="timeline-scroll" ref="scrollContainer">
      <div 
        class="timeline-content" 
        ref="timelineContent" 
        :style="{ 
          width: timelineWidth + 'px',
          transform: `translateX(${-scrollOffset}px)`,
          willChange: 'transform'
        }"
      >
        <!-- 时间刻度线 -->
        <div class="timeline-ruler">
          <div class="ruler-marks">
            <div 
              v-for="(mark, i) in timeMarks" 
              :key="i" 
              class="ruler-mark" 
              :class="{ major: mark.isMajor }"
              :style="{ left: mark.position + 'px' }"
            >
              <span v-if="mark.isMajor" class="mark-time">{{ mark.label }}</span>
              <div class="mark-line"></div>
            </div>
          </div>
        </div>
        
        <!-- 字幕轨道 -->
        <div class="subtitle-timeline" ref="timelineContainer" @click="handleTimelineClick">
          <!-- 波形图背景占位 -->
          <div class="waveform-background" ref="waveformContainer"></div>
          
          <!-- 字幕块 -->
          <div
            v-for="(subtitle, index) in subtitles"
            :key="index"
            class="timeline-segment"
            :class="{ active: currentSubtitleIndex === index }"
            :style="getSubtitleStyle(subtitle)"
            @click.stop="selectSubtitle(index)"
          >
            <div class="segment-content">
              <span class="segment-label">{{ subtitle.text }}</span>
              <span v-if="subtitle.translation" class="segment-label translation">{{ subtitle.translation }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 播放进度线（固定在容器中间） -->
    <div class="playhead-fixed" :style="playheadStyle"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import WaveSurfer from 'wavesurfer.js'

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

const timelineContainer = ref(null)
const scrollContainer = ref(null)
const timelineContent = ref(null)
const timelinePanel = ref(null)
const waveformContainer = ref(null)
const scrollOffset = ref(0)
const wavesurfer = ref(null)
const animationFrameId = ref(null)
const SCROLL_SMOOTHING = 0.18

// 使用 requestAnimationFrame 实现平滑滚动
const updateScrollPosition = () => {
  if (!scrollContainer.value || !props.duration) {
    animationFrameId.value = null
    return
  }
  
  const containerWidth = scrollContainer.value.clientWidth
  const leftPadding = containerWidth / 2
  const timePosition = leftPadding + (props.currentTime / props.duration) * (props.duration * PIXELS_PER_SECOND)
  const targetOffset = Math.max(0, timePosition - containerWidth / 2)
  
  // 平滑过渡到目标位置（插值，减少抖动）
  if (!Number.isFinite(scrollOffset.value)) {
    scrollOffset.value = targetOffset
  } else {
    scrollOffset.value = scrollOffset.value + (targetOffset - scrollOffset.value) * SCROLL_SMOOTHING
  }
  
  // 继续下一帧
  animationFrameId.value = requestAnimationFrame(updateScrollPosition)
}

// 监听播放状态，启动或停止动画
watch(() => props.currentTime, () => {
  // 每次时间更新时，确保动画在运行
  if (!animationFrameId.value) {
    animationFrameId.value = requestAnimationFrame(updateScrollPosition)
  }
}, { immediate: true })

watch(() => props.duration, () => {
  if (!animationFrameId.value) {
    animationFrameId.value = requestAnimationFrame(updateScrollPosition)
  }
}, { immediate: true })

const PIXELS_PER_SECOND = 80

const timelineWidth = computed(() => {
  const duration = Math.max(0, Number(props.duration) || 0)
  const base = duration * PIXELS_PER_SECOND
  // 添加左右两侧空白区域，让时间轴可以完整滚动
  const containerWidth = scrollContainer.value?.clientWidth || 0
  const sidePadding = containerWidth / 2
  return base + sidePadding * 2 // 左右各加一半容器宽度
})

// 播放进度线样式（固定在容器中间）
const playheadStyle = computed(() => {
  if (!timelinePanel.value) return {}
  return {
    left: '50%',
    height: 'calc(100% - 0px)'
  }
})

// 动态生成时间刻度 - 每秒一个刻度，每2秒显示时间
const timeMarks = computed(() => {
  const marks = []
  const duration = props.duration || 30
  const interval = 1 // 每1秒一个刻度
  const containerWidth = scrollContainer.value?.clientWidth || 0
  const leftPadding = containerWidth / 2
  
  const count = Math.ceil(duration / interval)
  for (let i = 0; i <= count; i++) {
    const time = i * interval
    if (time <= duration) {
      marks.push({
        position: leftPadding + (time / duration) * (duration * PIXELS_PER_SECOND),
        label: formatTimeRuler(time),
        isMajor: time % 2 === 0 // 每2秒是主刻度，显示时间
      })
    }
  }
  return marks
})

// 初始化波形图
const initWaveform = async () => {
  if (!waveformContainer.value || !props.videoUrl) return
  
  try {
    // 销毁旧实例
    if (wavesurfer.value) {
      wavesurfer.value.destroy()
    }
    
    await nextTick()

    const height = waveformContainer.value?.clientHeight || 80
    
    // 创建 WaveSurfer 实例
    wavesurfer.value = WaveSurfer.create({
      container: waveformContainer.value,
      waveColor: 'rgba(203, 213, 225, 0.85)',
      progressColor: 'rgba(167, 139, 250, 0.95)',
      cursorWidth: 0,
      barWidth: 2,
      barGap: 0,
      barRadius: 2,
      height,
      normalize: true,
      interact: false, // 禁用交互，因为我们用外层的点击事件
      hideScrollbar: true,
      minPxPerSec: PIXELS_PER_SECOND, // 与时间轴同步：每秒80像素
      fillParent: false,
      autoCenter: false,
      backend: 'WebAudio'
    })
    
    // 加载音频
    await wavesurfer.value.load(props.videoUrl)
    
    // 加载完成后，调整波形图容器的宽度和位置
    updateWaveformPosition()
    
    console.log('波形图加载成功')
  } catch (error) {
    console.error('波形图加载失败:', error)
  }
}

// 更新波形图位置，使其与字幕块对齐
const updateWaveformPosition = () => {
  if (!wavesurfer.value || !waveformContainer.value || !scrollContainer.value) return
  
  const containerWidth = scrollContainer.value.clientWidth
  const leftPadding = containerWidth / 2
  
  // 设置波形图容器的左偏移，与字幕块对齐
  waveformContainer.value.style.paddingLeft = `${leftPadding}px`
  waveformContainer.value.style.paddingRight = `${leftPadding}px`
}

// 监听视频 URL 变化
watch(() => props.videoUrl, (newUrl) => {
  if (newUrl) {
    initWaveform()
  }
}, { immediate: true })

// 监听时间轴宽度变化，更新波形图
watch(timelineWidth, () => {
  if (wavesurfer.value) {
    nextTick(() => {
      wavesurfer.value.zoom(PIXELS_PER_SECOND)
      updateWaveformPosition()
    })
  }
})

onMounted(() => {
  // 启动平滑滚动动画
  animationFrameId.value = requestAnimationFrame(updateScrollPosition)
})

onBeforeUnmount(() => {
  // 清理波形图实例
  if (wavesurfer.value) {
    wavesurfer.value.destroy()
  }
  
  // 取消动画帧
  if (animationFrameId.value) {
    cancelAnimationFrame(animationFrameId.value)
  }
})

// 点击时间轴跳转
const handleTimelineClick = (event) => {
  if (!timelineContainer.value || !scrollContainer.value) return
  const rect = timelineContainer.value.getBoundingClientRect()
  const containerWidth = scrollContainer.value.clientWidth
  const leftPadding = containerWidth / 2
  
  // 计算点击位置相对于时间轴内容的位置
  const x = event.clientX - rect.left + scrollOffset.value - leftPadding
  const progress = x / (props.duration * PIXELS_PER_SECOND)
  const time = Math.max(0, Math.min(progress * props.duration, props.duration))
  emit('seek', time)
}

const formatTimeRuler = (seconds) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const getSubtitleStyle = (subtitle) => {
  // 添加左侧空白区域偏移
  const containerWidth = scrollContainer.value?.clientWidth || 0
  const leftPadding = containerWidth / 2
  const left = leftPadding + (subtitle.startTime / props.duration) * (props.duration * PIXELS_PER_SECOND)
  const width = ((subtitle.endTime - subtitle.startTime) / props.duration) * (props.duration * PIXELS_PER_SECOND)
  return {
    left: `${left}px`,
    width: `${width}px`
  }
}

const selectSubtitle = (index) => {
  emit('select-subtitle', index)
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
  position: relative; // 添加相对定位，让播放线相对于这个容器定位
}

.timeline-scroll {
  flex: 1;
  overflow: hidden; // 改为 hidden，不使用原生滚动
  position: relative;
}

// 播放进度线（固定在容器中间）
.playhead-fixed {
  position: absolute;
  left: 50%;
  width: 1px;
  background: #ff4757;
  pointer-events: none;
  z-index: 100;
  box-shadow: 0 0 4px rgba(255, 71, 87, 0.8);
  transform: translateX(-50%);

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

.timeline-content {
  height: 100%;
  position: relative;
  will-change: transform;
  display: flex;
  flex-direction: column;
}

.timeline-ruler {
  height: 32px;
  background: linear-gradient(180deg, rgba(22, 18, 38, 0.95) 0%, rgba(12, 10, 20, 0.95) 100%);
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
      background: rgba(148, 163, 184, 0.35);
      transform: translateX(-50%);
    }

    .mark-time {
      font-size: 11px;
      color: rgba(203, 213, 225, 0.7);
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
        background: rgba(203, 213, 225, 0.55);
        width: 1px;
      }

      .mark-time {
        display: block; // 主刻度显示时间
        color: rgba(226, 232, 240, 0.9);
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
        color: rgba(167, 139, 250, 0.95);
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
  cursor: pointer;
  display: flex;
  align-items: center;
}

.waveform-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  opacity: 0.95;
  box-sizing: border-box;
  
  :deep(wave) {
    overflow: visible !important;
    height: 100% !important;
  }
  
  :deep(canvas) {
    width: 100% !important;
  }
}

.timeline-segment {
  position: absolute;
  height: 100%;
  top: 0;
  background: rgba(148, 163, 184, 0.22);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  transition: background 0.2s;
  overflow: hidden;
  z-index: 10;
  opacity: 1;

  .segment-label {
    color: rgba(241, 245, 249, 0.9);
    text-shadow:
      0 2px 8px rgba(0, 0, 0, 0.85),
      0 1px 2px rgba(0, 0, 0, 0.95);
  }

  &:hover {
    background: rgba(148, 163, 184, 0.32);
    z-index: 20;
  }


  &.active {
    background: rgba(109, 40, 217, 0.55);
    z-index: 30;

    .segment-label {
      color: rgba(255, 255, 255, 0.98);
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
    font-size: 13px; // 调大字号
    font-weight: 600;
    line-height: 1.2;
    word-break: break-all;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
    padding: 0 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    line-clamp: 1;
    -webkit-box-orient: vertical;
    transition: color 0.2s;
    color: #ffffff; // 固定主字幕颜色为白色

    &.translation {
      font-size: 11px; // 副字幕也相应调大
      opacity: 0.9;
      color: #FFD700; // 固定副字幕颜色为金色
      margin-top: 2px;
    }
  }
}


</style>
