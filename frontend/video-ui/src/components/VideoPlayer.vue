<template>
  <div class="video-player-container">
    <video
      ref="videoElement"
      class="video-js vjs-default-skin vjs-big-play-centered"
      controls
      preload="auto"
      :poster="posterUrl"
    >
      <p class="vjs-no-js">
        请启用 JavaScript 来播放视频
      </p>
    </video>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import videojs from 'video.js'
import 'video.js/dist/video-js.css'

const props = defineProps({
  // HLS 视频源（master.m3u8 的 URL）
  src: {
    type: String,
    required: true
  },
  // 封面图
  poster: {
    type: String,
    default: ''
  },
  // 是否自动播放
  autoplay: {
    type: Boolean,
    default: false
  },
  // 视频 ID（用于上报播放进度）
  videoId: {
    type: [String, Number],
    default: null
  }
})

const emit = defineEmits(['timeupdate', 'ended', 'error'])

const videoElement = ref(null)
let player = null

// 封面图 URL
const posterUrl = computed(() => {
  if (props.poster) {
    return props.poster.startsWith('http') 
      ? props.poster 
      : `${import.meta.env.VITE_API_BASE_URL}${props.poster}`
  }
  return ''
})

// 初始化播放器
const initPlayer = () => {
  if (!videoElement.value) return

  player = videojs(videoElement.value, {
    controls: true,
    autoplay: props.autoplay,
    preload: 'auto',
    fluid: true, // 响应式布局
    aspectRatio: '16:9',
    playbackRates: [0.5, 0.75, 1, 1.25, 1.5, 2], // 播放速度
    controlBar: {
      children: [
        'playToggle',
        'volumePanel',
        'currentTimeDisplay',
        'timeDivider',
        'durationDisplay',
        'progressControl',
        'remainingTimeDisplay',
        'playbackRateMenuButton',
        'qualitySelector', // 清晰度切换
        'fullscreenToggle'
      ]
    },
    sources: [{
      src: props.src,
      type: 'application/x-mpegURL' // HLS 格式
    }]
  })

  // 监听播放进度
  player.on('timeupdate', () => {
    const currentTime = player.currentTime()
    const duration = player.duration()
    emit('timeupdate', { currentTime, duration, videoId: props.videoId })
  })

  // 监听播放结束
  player.on('ended', () => {
    emit('ended', { videoId: props.videoId })
  })

  // 监听错误
  player.on('error', (error) => {
    console.error('播放器错误:', error)
    emit('error', error)
  })
}

// 销毁播放器
const destroyPlayer = () => {
  if (player) {
    player.dispose()
    player = null
  }
}

// 监听 src 变化
watch(() => props.src, (newSrc) => {
  if (player && newSrc) {
    player.src({
      src: newSrc,
      type: 'application/x-mpegURL'
    })
  }
})

onMounted(() => {
  initPlayer()
})

onBeforeUnmount(() => {
  destroyPlayer()
})

// 暴露播放器实例方法
defineExpose({
  play: () => player?.play(),
  pause: () => player?.pause(),
  currentTime: (time) => {
    if (time !== undefined) {
      player?.currentTime(time)
    }
    return player?.currentTime()
  },
  duration: () => player?.duration(),
  volume: (vol) => {
    if (vol !== undefined) {
      player?.volume(vol)
    }
    return player?.volume()
  }
})
</script>

<style scoped>
.video-player-container {
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
}

.video-js {
  width: 100%;
  height: 100%;
}

/* 自定义播放器样式 */
.video-js .vjs-big-play-button {
  border-radius: 50%;
  width: 80px;
  height: 80px;
  line-height: 80px;
  border: none;
  background-color: rgba(0, 0, 0, 0.7);
  font-size: 3em;
}

.video-js .vjs-big-play-button:hover {
  background-color: rgba(0, 0, 0, 0.9);
}
</style>
