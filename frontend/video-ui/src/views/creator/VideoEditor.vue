<template>
  <div class="video-editor">
    <div class="editor-header">
      <h2>视频编辑器</h2>
      <div class="header-actions">
        <el-button @click="handleBack">返回</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
        <el-button type="success" @click="handleExport">导出</el-button>
      </div>
    </div>

    <div class="editor-content">
      <div class="preview-section">
        <div ref="videoContainer" class="video-preview"></div>
        <div class="preview-controls">
          <el-button-group>
            <el-button @click="handlePlay" :icon="isPlaying ? 'VideoPause' : 'VideoPlay'">
              {{ isPlaying ? '暂停' : '播放' }}
            </el-button>
            <el-button @click="handleStop" icon="Close">停止</el-button>
          </el-button-group>
          <span class="time-display">{{ currentTime }} / {{ duration }}</span>
        </div>
      </div>

      <div class="tools-section">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="剪辑" name="trim">
            <div class="tool-panel">
              <h3>视频剪辑</h3>
              <el-form label-width="80px">
                <el-form-item label="开始时间">
                  <el-input-number v-model="trimStart" :min="0" :max="videoDuration" />
                </el-form-item>
                <el-form-item label="结束时间">
                  <el-input-number v-model="trimEnd" :min="0" :max="videoDuration" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="handleTrim">应用剪辑</el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-tab-pane>

          <el-tab-pane label="滤镜" name="filter">
            <div class="tool-panel">
              <h3>视频滤镜</h3>
              <div class="filter-options">
                <el-button @click="applyFilter('none')">无滤镜</el-button>
                <el-button @click="applyFilter('grayscale')">黑白</el-button>
                <el-button @click="applyFilter('sepia')">复古</el-button>
                <el-button @click="applyFilter('blur')">模糊</el-button>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="字幕" name="subtitle">
            <div class="tool-panel">
              <h3>字幕编辑</h3>
              <el-button type="primary" @click="goToSubtitleEditor">
                打开字幕编辑器
              </el-button>
            </div>
          </el-tab-pane>

          <el-tab-pane label="音频" name="audio">
            <div class="tool-panel">
              <h3>音频调整</h3>
              <el-form label-width="80px">
                <el-form-item label="音量">
                  <el-slider v-model="volume" :min="0" :max="100" />
                </el-form-item>
                <el-form-item label="淡入">
                  <el-slider v-model="fadeIn" :min="0" :max="5" :step="0.1" />
                </el-form-item>
                <el-form-item label="淡出">
                  <el-slider v-model="fadeOut" :min="0" :max="5" :step="0.1" />
                </el-form-item>
              </el-form>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <div class="timeline-section">
      <div class="timeline-header">
        <span>时间轴</span>
        <el-button-group size="small">
          <el-button @click="zoomIn" icon="ZoomIn">放大</el-button>
          <el-button @click="zoomOut" icon="ZoomOut">缩小</el-button>
        </el-button-group>
      </div>
      <div ref="timeline" class="timeline-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import Artplayer from 'artplayer'
import { ElMessage } from 'element-plus'

const router = useRouter()

// 状态
const videoContainer = ref(null)
const timeline = ref(null)
const artplayer = ref(null)
const activeTab = ref('trim')
const isPlaying = ref(false)
const currentTime = ref('00:00:00')
const duration = ref('00:00:00')
const videoDuration = ref(0)

// 编辑参数
const trimStart = ref(0)
const trimEnd = ref(0)
const volume = ref(100)
const fadeIn = ref(0)
const fadeOut = ref(0)

onMounted(() => {
  initPlayer()
})

onBeforeUnmount(() => {
  if (artplayer.value) {
    artplayer.value.destroy()
  }
})

const initPlayer = () => {
  artplayer.value = new Artplayer({
    container: videoContainer.value,
    url: '', // 从路由参数或状态获取视频URL
    poster: '',
    volume: 0.5,
    autoplay: false,
    pip: true,
    setting: true,
    fullscreen: true,
    fullscreenWeb: true
  })

  artplayer.value.on('ready', () => {
    videoDuration.value = artplayer.value.duration
    trimEnd.value = videoDuration.value
    duration.value = formatTime(videoDuration.value)
  })

  artplayer.value.on('video:timeupdate', () => {
    currentTime.value = formatTime(artplayer.value.currentTime)
  })

  artplayer.value.on('play', () => {
    isPlaying.value = true
  })

  artplayer.value.on('pause', () => {
    isPlaying.value = false
  })
}

const formatTime = (seconds) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const handlePlay = () => {
  if (artplayer.value) {
    if (isPlaying.value) {
      artplayer.value.pause()
    } else {
      artplayer.value.play()
    }
  }
}

const handleStop = () => {
  if (artplayer.value) {
    artplayer.value.pause()
    artplayer.value.currentTime = 0
  }
}

const handleTrim = () => {
  ElMessage.success('剪辑已应用')
}

const applyFilter = (filter) => {
  ElMessage.success(`已应用${filter}滤镜`)
}

const handleBack = () => {
  router.back()
}

const handleSave = () => {
  ElMessage.success('视频已保存')
}

const handleExport = () => {
  ElMessage.success('视频导出中...')
}

const goToSubtitleEditor = () => {
  router.push('/creator/subtitle')
}

const zoomIn = () => {
  ElMessage.info('时间轴放大')
}

const zoomOut = () => {
  ElMessage.info('时间轴缩小')
}
</script>

<style scoped lang="scss">
.video-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  h2 {
    margin: 0;
    font-size: 20px;
    color: #333;
  }

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.editor-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.preview-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: #000;
}

.video-preview {
  flex: 1;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.preview-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #1a1a1a;
  border-radius: 8px;
  margin-top: 16px;

  .time-display {
    color: #fff;
    font-family: monospace;
    font-size: 14px;
  }
}

.tools-section {
  width: 350px;
  background: #fff;
  border-left: 1px solid #e0e0e0;
  overflow-y: auto;

  // 修复 Element Plus 滑块样式
  :deep(.el-slider) {
    .el-slider__runway {
      margin: 16px 0;
    }

    .el-slider__button-wrapper {
      top: -8px;
    }

    .el-slider__button {
      width: 16px;
      height: 16px;
    }
  }
}

.tool-panel {
  padding: 20px;

  h3 {
    margin: 0 0 20px 0;
    font-size: 16px;
    color: #333;
  }

  .filter-options {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}

.timeline-section {
  height: 200px;
  background: #fff;
  border-top: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #e0e0e0;

  span {
    font-weight: 500;
    color: #333;
  }
}

.timeline-container {
  flex: 1;
  background: #f9f9f9;
  position: relative;
}
</style>
