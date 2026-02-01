<template>
  <div class="video-player-section">
    <!-- 视频播放器 -->
    <div ref="videoContainer" class="video-player"></div>

    <!-- 标签栏 -->
    <div class="editor-tabs">
      <div class="tabs-left">
        <div class="tab-btn" :class="{ active: activeTab === 'subtitle' }" @click="$emit('update:activeTab', 'subtitle')">
          <i class="icon">🎨</i> 样式
        </div>
        <div class="tab-btn" :class="{ active: activeTab === 'tool' }" @click="$emit('update:activeTab', 'tool')">
          <i class="icon">✂️</i> 工具
        </div>
        <div class="tab-btn" :class="{ active: activeTab === 'settings' }" @click="$emit('update:activeTab', 'settings')">
          <i class="icon">⚙️</i> 选项
        </div>
      </div>
      <div class="collapse-icon" @click="$emit('toggle-panel')">
        <i>{{ isPanelCollapsed ? '▼' : '▲' }}</i>
      </div>
    </div>

    <!-- 控制面板 -->
    <transition name="slide-fade">
      <div v-show="!isPanelCollapsed" class="control-panel">
        <!-- 样式面板 -->
        <div v-show="activeTab === 'subtitle'" class="panel-content">
          <!-- 第一行：颜色控制 -->
          <div class="control-row">
            <span class="row-label">颜色:</span>
            <div class="color-group">
              <span class="param-label">主颜色</span>
              <div class="color-picker-wrapper">
                <input v-model="mainColor" type="color" class="color-picker" />
              </div>
            </div>
            <div class="color-group">
              <span class="param-label">主描边</span>
              <div class="color-picker-wrapper">
                <input v-model="mainBorderColor" type="color" class="color-picker" />
              </div>
            </div>
            <div class="color-group">
              <span class="param-label">副颜色</span>
              <div class="color-picker-wrapper">
                <input v-model="subColor" type="color" class="color-picker" />
              </div>
            </div>
            <div class="color-group">
              <span class="param-label">副描边</span>
              <div class="color-picker-wrapper">
                <input v-model="subBorderColor" type="color" class="color-picker" />
              </div>
            </div>
          </div>

          <!-- 第二行：尺寸控制 -->
          <div class="control-row">
            <span class="row-label">尺寸:</span>
            <div class="slider-group">
              <span class="param-label">字号</span>
              <el-slider v-model="fontSize" :min="12" :max="72" class="slider-control" />
            </div>
            <div class="slider-group">
              <span class="param-label">字距</span>
              <el-slider v-model="letterSpacing" :min="0" :max="20" class="slider-control" />
            </div>
            <div class="slider-group">
              <span class="param-label">底距</span>
              <el-slider v-model="bottomDistance" :min="0" :max="100" class="slider-control" />
            </div>
          </div>

          <!-- 第三行：阴影控制 -->
          <div class="control-row">
            <span class="row-label">阴影:</span>
            <div class="shadow-toggle">
              <span class="param-label">背景</span>
              <el-switch v-model="hasShadow" size="small" />
            </div>
            <div class="slider-group">
              <span class="param-label">透明度</span>
              <el-slider v-model="shadowOpacity" :min="0" :max="100" class="slider-control" />
            </div>
            <div class="slider-group">
              <span class="param-label">描边</span>
              <el-slider v-model="strokeWidth" :min="0" :max="10" class="slider-control" />
            </div>
            <div class="slider-group">
              <span class="param-label">偏移</span>
              <el-slider v-model="shadowOffset" :min="0" :max="20" class="slider-control" />
            </div>
          </div>

          <!-- 第四行：字体控制 -->
          <div class="control-row">
            <span class="row-label">字体:</span>
            <el-select v-model="fontFamily" size="small" class="font-select">
              <el-option label="思源黑体(正常)" value="Source Han Sans" />
              <el-option label="微软雅黑" value="Microsoft YaHei" />
              <el-option label="黑体" value="SimHei" />
              <el-option label="宋体" value="SimSun" />
            </el-select>
            <div class="font-style-group">
              <span class="param-label">加粗</span>
              <el-switch v-model="isBold" size="small" />
            </div>
            <div class="font-style-group">
              <span class="param-label">斜体</span>
              <el-switch v-model="isItalic" size="small" />
            </div>
          </div>
        </div>

        <!-- 工具面板 -->
        <div v-show="activeTab === 'tool'" class="panel-content">
          <!-- 第一行：导入文件 -->
          <div class="control-row">
            <span class="row-label">导入文件:</span>
            <el-button size="small">📤 导入字幕</el-button>
            <el-button size="small">📥 导出 JSON</el-button>
          </div>

          <!-- 第二行：时间偏移 -->
          <div class="control-row">
            <span class="row-label">时间偏移:</span>
            <el-button size="small">- 0.1s</el-button>
            <el-button size="small">+ 0.1s</el-button>
            <el-button size="small">- 1.0s</el-button>
            <el-button size="small">+ 1.0s</el-button>
          </div>

          <!-- 第三行：文字替换 -->
          <div class="control-row">
            <span class="row-label">文字替换:</span>
            <el-input 
              size="small" 
              placeholder="请输入要替换的文字" 
              class="replace-input"
            />
            <span class="arrow-icon">→</span>
            <el-input 
              size="small" 
              placeholder="请输入替换后的文字" 
              class="replace-input"
            />
            <el-button size="small" type="primary">确定</el-button>
          </div>

          <!-- 第四行：批量处理 -->
          <div class="control-row">
            <span class="row-label">批量处理:</span>
            <el-button size="small" type="danger">清空字幕</el-button>
            <el-button size="small">移除空行</el-button>
            <el-button size="small">移除结尾标点</el-button>
            <el-button size="small">主副交换</el-button>
            <el-button size="small">换行转双字幕</el-button>
          </div>
        </div>

        <!-- 选项面板 -->
        <div v-show="activeTab === 'settings'" class="panel-content">
          <!-- 第一行：任务名字 -->
          <div class="control-row">
            <span class="row-label">任务名字:</span>
            <el-input 
              v-model="taskName" 
              size="small" 
              placeholder="请输入任务名称" 
              class="task-name-input"
            />
          </div>

          <!-- 第二行：音频波形 -->
          <div class="control-row">
            <span class="row-label">音频波形:</span>
            <div class="slider-group">
              <span class="param-label">时长</span>
              <el-slider v-model="waveformDuration" :min="1" :max="10" class="slider-control" />
            </div>
            <div class="slider-group">
              <span class="param-label">缩放</span>
              <el-slider v-model="waveformZoom" :min="1" :max="10" class="slider-control" />
            </div>
          </div>

          <!-- 第三行：导出选项 -->
          <div class="control-row">
            <span class="row-label">导出选项:</span>
            <div class="export-group">
              <span class="param-label">尺寸:</span>
              <el-select v-model="exportSize" size="small" class="export-select">
                <el-option label="原始" value="original" />
                <el-option label="1080P" value="1080p" />
                <el-option label="720P" value="720p" />
                <el-option label="480P" value="480p" />
              </el-select>
            </div>
            <div class="export-group">
              <span class="param-label">预设:</span>
              <el-select v-model="exportPreset" size="small" class="export-select">
                <el-option label="快速" value="fast" />
                <el-option label="标准" value="medium" />
                <el-option label="高质量" value="high" />
              </el-select>
            </div>
          </div>

          <!-- 第四行：其他选项 -->
          <div class="control-row">
            <span class="row-label">其他选项:</span>
            <div class="font-style-group">
              <span class="param-label">自动闪序</span>
              <el-switch v-model="autoFlash" size="small" />
            </div>
            <div class="font-style-group">
              <span class="param-label">提示信息</span>
              <el-switch v-model="showTips" size="small" />
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import Artplayer from 'artplayer'

const props = defineProps({
  videoUrl: {
    type: String,
    default: ''
  },
  subtitles: {
    type: Array,
    default: () => []
  },
  activeTab: {
    type: String,
    default: 'subtitle'
  },
  isPanelCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:activeTab', 'toggle-panel', 'time-update', 'player-ready'])

const videoContainer = ref(null)
const artplayer = ref(null)
const subtitleBlobUrl = ref('')

// 编辑控制参数
const mainColor = ref('#FFFFFF')
const mainBorderColor = ref('#000000')
const subColor = ref('#00D1FF')
const subBorderColor = ref('#000000')
const fontSize = ref(24)
const letterSpacing = ref(0)
const bottomDistance = ref(20)
const hasShadow = ref(false)
const shadowOpacity = ref(50)
const strokeWidth = ref(2)
const shadowOffset = ref(5)
const fontFamily = ref('Source Han Sans')
const isBold = ref(false)
const isItalic = ref(false)

// 选项面板参数
const taskName = ref('Demo Task')
const waveformDuration = ref(5)
const waveformZoom = ref(5)
const exportSize = ref('original')
const exportPreset = ref('fast')
const autoFlash = ref(true)
const showTips = ref(true)

onMounted(() => {
  initArtplayer()
})

onBeforeUnmount(() => {
  if (artplayer.value) {
    artplayer.value.destroy()
  }
  if (subtitleBlobUrl.value) {
    URL.revokeObjectURL(subtitleBlobUrl.value)
    subtitleBlobUrl.value = ''
  }
})

watch(() => props.videoUrl, (newUrl) => {
  if (artplayer.value && newUrl) {
    artplayer.value.switchUrl(newUrl)
  }
})

const buildVttContent = (subs) => {
  const lines = ['WEBVTT', '']
  const toVttTime = (seconds) => {
    const s = Number(seconds) || 0
    const hours = Math.floor(s / 3600)
    const minutes = Math.floor((s % 3600) / 60)
    const secs = Math.floor(s % 60)
    const ms = Math.floor((s % 1) * 1000)
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(ms).padStart(3, '0')}`
  }

  ;(subs || []).forEach((sub, idx) => {
    if (!sub) return
    const start = toVttTime(sub.startTime)
    const end = toVttTime(sub.endTime)
    const text = (sub.text || '').trim()
    const translation = (sub.translation || '').trim()
    if (!text && !translation) return
    lines.push(String(idx + 1))
    lines.push(`${start} --> ${end}`)
    if (text) lines.push(text)
    if (translation) lines.push(translation)
    lines.push('')
  })

  return lines.join('\n')
}

const applySubtitlesToPlayer = (subs) => {
  if (!artplayer.value) return

  if (subtitleBlobUrl.value) {
    URL.revokeObjectURL(subtitleBlobUrl.value)
    subtitleBlobUrl.value = ''
  }

  if (!subs || subs.length === 0) {
    try {
      artplayer.value.subtitle.url = ''
    } catch (e) {}
    return
  }

  const vtt = buildVttContent(subs)
  const blob = new Blob([vtt], { type: 'text/vtt;charset=utf-8' })
  subtitleBlobUrl.value = URL.createObjectURL(blob)

  // Artplayer 的 subtitle 支持动态更新
  try {
    artplayer.value.subtitle.url = subtitleBlobUrl.value
    artplayer.value.subtitle.type = 'vtt'
  } catch (e) {
    // 兜底：重新初始化时会带上 subtitle
  }
}

watch(
  () => props.subtitles,
  (subs) => {
    applySubtitlesToPlayer(subs)
  },
  { deep: true }
)

const initArtplayer = () => {
  artplayer.value = new Artplayer({
    container: videoContainer.value,
    url: props.videoUrl || '',
    poster: '',
    volume: 0.5,
    autoplay: false,
    pip: true,
    setting: true,
    playbackRate: true,
    aspectRatio: true,
    fullscreen: true,
    fullscreenWeb: true,
    subtitleOffset: true,
    miniProgressBar: true,
    mutex: true,
    backdrop: true,
    playsInline: true,
    autoPlayback: true,
    airplay: true,
    theme: '#6b46c1',
    lang: 'zh-cn',
    subtitle: {
      url: '',
      type: 'vtt'
    },
    moreVideoAttr: {
      crossOrigin: 'anonymous'
    }
  })

  artplayer.value.on('ready', () => {
    console.log('Artplayer ready')
    emit('player-ready', artplayer.value)
    applySubtitlesToPlayer(props.subtitles)
  })

  artplayer.value.on('video:timeupdate', () => {
    emit('time-update', artplayer.value.currentTime)
  })

  artplayer.value.on('error', (error) => {
    console.error('Artplayer error:', error)
  })
}

// 暴露方法给父组件
defineExpose({
  player: artplayer
})
</script>

<style scoped lang="scss">
.video-player-section {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #000;
}

.video-player {
  flex: 1;
  width: 100%;
  min-height: 400px;
  background: #000;
  position: relative;
}

.editor-tabs {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #1a1a1a;
  padding: 3px 16px;
  border-top: 1px solid #2a2a2a;

  .tabs-left {
    display: flex;
    gap: 4px;
  }

  .tab-btn {
    padding: 6px 12px;
    background: transparent;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    color: #fff;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
    user-select: none;

    .icon {
      font-size: 16px;
    }

    &:hover {
      background: #2a2a2a;
      color: #fff;
    }

    &.active {
      background: #6b46c1;
      color: #fff;
    }
  }

  .collapse-icon {
    cursor: pointer;
    padding: 4px 8px;
    color: #999;
    font-size: 12px;
    user-select: none;
    
    &:hover {
      color: #fff;
    }
  }
}

.control-panel {
  background: #1a1a1a;
  padding: 12px 16px;
  border-top: 1px solid #2a2a2a;
  flex-shrink: 0;
  min-height: 150px; 
  

  .control-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
    height: 32px; // 固定每行高度

    &:last-child {
      margin-bottom: 0;
    }

    .row-label {
      color: white;
      font-size: 13px;
      min-width: 60px;
      font-weight: 500;
    }

    .param-label {
      margin-right: 1em;
      color: white;
      font-size: 14px;
      min-width: 45px;
      text-align: right;
    }

    .color-group {
      display: flex;
      align-items: center;
      gap: 6px;

      .color-picker-wrapper {
        width: 50px;
        height: 24px;
        border: 1px solid #3d3d3d;
        border-radius: 3px;
        overflow: hidden;
        position: relative;
        background: transparent;
      }

      .color-picker {
        position: absolute;
        top: -2px;
        left: -2px;
        width: calc(100% + 4px);
        height: calc(100% + 4px);
        border: none;
        cursor: pointer;
        background: transparent;

        &::-webkit-color-swatch-wrapper {
          padding: 0;
          border: none;
        }

        &::-webkit-color-swatch {
          border: none;
        }

        &::-moz-color-swatch {
          border: none;
        }
      }
    }

    .slider-group {
      display: flex;
      align-items: center;
      // justify-content: space-around;
      gap: 8px;
      flex: 1;
      min-width: 0;

      .slider-control {
        flex: 1;
        min-width: 80px;
        max-width: 150px;
      }
    }

    .shadow-toggle,
    .font-style-group {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .font-select {
      width: 160px;
    }
  }
}

// 下拉框聚焦样式
:deep(.el-select.is-focus) {
  .el-input__wrapper {
    border-color: #409eff !important;
    box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2) !important;
  }
}


// Element Plus 组件深色样式定制
:deep(.el-button) {
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  color: #ccc;
  border-radius: 6px;

  &:hover {
    background: #3a3a3a;
    border-color: #4a4a4a;
    color: #fff;
  }

  &.is-disabled {
    background: #1a1a1a;
    border-color: #2a2a2a;
    color: #666;
  }
}

:deep(.el-button--primary) {
  background: #6b46c1;
  border-color: #6b46c1;
  color: #fff;

  &:hover {
    background: #7c5dd1;
    border-color: #7c5dd1;
  }
}

:deep(.el-button--danger) {
  background: #f56c6c;
  border-color: #f56c6c;
  color: #fff;

  &:hover {
    background: #f78989;
    border-color: #f78989;
  }
}

:deep(.el-input__wrapper) {
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  box-shadow: none;
  border-radius: 6px;

  &:hover {
    border-color: #4a4a4a;
  }

  &.is-focus {
    border-color: #6b46c1;
    box-shadow: 0 0 0 1px rgba(107, 70, 193, 0.2);
  }
}

:deep(.el-input__inner) {
  color: #fff;
}

:deep(.el-select) {
  .el-input__wrapper {
    background: #2a2a2a !important;
    border: 1px solid #3a3a3a !important;
    box-shadow: none !important;
    border-radius: 6px !important;
    
    &:hover {
      border-color: #4a4a4a !important;
    }
  }
  
  .el-input__inner {
    color: #fff !important;
  }
  
  .el-select__caret {
    color: #999 !important;
  }
  
  &.is-focus {
    .el-input__wrapper {
      border-color: #409eff !important;
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2) !important;
    }
  }
}

:deep(.font-select) {
  --el-fill-color-blank: #2a2a2a;
  --el-text-color-regular: #fff;
  --el-border-color: #3a3a3a;
  --el-border-color-hover: #4a4a4a;
  --el-fill-color-light: #2a2a2a;

  .el-input__wrapper {
    background-color: #2a2a2a !important;
  }

  .el-input__inner {
    color: #fff !important;
  }
}

:deep(.el-select-dropdown) {
  background: #2a2a2a !important;
  border: 1px solid #3a3a3a !important;
  border-radius: 8px !important;
  padding: 8px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
}

:deep(.el-select-dropdown__item) {
  color: #ccc !important;
  border-radius: 6px !important;
  padding: 8px 12px !important;
  margin: 4px 0 !important;
  transition: all 0.2s !important;

  &:hover {
    background: #3a3a3a !important;
    color: #fff !important;
  }

  &.selected {
    color: #fff !important;
    background: #2a2a2a !important;
    border: 2px solid #409eff !important;
    font-weight: 500;
  }
  
  &.is-hovering {
    background: #3a3a3a !important;
  }
}

// Element Plus 滑块定制
:deep(.el-slider__runway) {
  background: #3d3d3d;
}

:deep(.el-slider__bar) {
  background: #ff6600;
}

:deep(.el-slider__button) {
  border-color: #ff6600;
}

// 隐藏滑块的提示框
:deep(.el-slider__marks-text),
:deep(.el-slider__stop) {
  display: none;
}

:deep(.el-switch) {
  --el-switch-on-color: #6b46c1;
  --el-switch-off-color: #3d3d3d;
}

:deep(.el-switch__core) {
  background: #3d3d3d;
  border-color: #3d3d3d;
  height: 20px;
  min-width: 40px;

  .el-switch__action {
    width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: bold;
    color: #333;
    
    &::before {
      content: 'N';
    }
  }
}

:deep(.el-switch.is-checked .el-switch__core) {
  background: #6b46c1;
  border-color: #6b46c1;
  
  .el-switch__action::before {
    content: 'Y';
  }
}

// 任务名称输入框样式
:deep(.task-name-input) {
  flex: 1;
  max-width: 400px;

  .el-input__wrapper {
    background: #2a2a2a;
    border: 1px solid #3a3a3a;
    box-shadow: none;

    &:hover {
      border-color: #4a4a4a;
    }

    &.is-focus {
      border-color: #6b46c1;
      box-shadow: 0 0 0 1px rgba(107, 70, 193, 0.2);
    }
  }
}

// 导出选项样式
.export-group {
  display: flex;
  align-items: center;
  gap: 8px;

  .param-label {
    color: #fff;
    font-size: 14px;
  }
}

.export-select {
  width: 120px;
}

// 导出选项下拉框深色样式
:deep(.export-select) {
  --el-fill-color-blank: #2a2a2a;
  --el-text-color-regular: #fff;
  --el-border-color: #3a3a3a;
  --el-border-color-hover: #4a4a4a;
  --el-fill-color-light: #2a2a2a;

  .el-input__wrapper {
    background: #2a2a2a !important;
    border: 1px solid #3a3a3a !important;
    box-shadow: none !important;
    border-radius: 6px !important;
    
    &:hover {
      border-color: #4a4a4a !important;
    }
    
    &.is-focus {
      border-color: #409eff !important;
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2) !important;
    }
  }
  
  .el-input__inner {
    color: #fff !important;
  }
  
  .el-select__caret {
    color: #999 !important;
  }
}

// 替换输入框样式
:deep(.replace-input) {
  flex: 1;
  max-width: 180px;

  .el-input__wrapper {
    background: #2a2a2a;
    border: 1px solid #3a3a3a;
    box-shadow: none;

    &:hover {
      border-color: #4a4a4a;
    }

    &.is-focus {
      border-color: #6b46c1;
      box-shadow: 0 0 0 1px rgba(107, 70, 193, 0.2);
    }
  }
}

.arrow-icon {
  color: #888;
  font-size: 16px;
  margin: 0 6px;
}

// 面板切换动画
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s ease-in;
  position: absolute;
}

.slide-fade-enter-from {
  transform: translateX(-20px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateX(20px);
  opacity: 0;
}

.panel-content {
  animation: fadeIn 0.3s ease-in-out;
  min-height: 156px; // 4行 × 32px + 3个间距 × 10px = 128px + 30px = 158px (留点余量)
  display: flex;
  flex-direction: column;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>

<style lang="scss">
// 全局样式 - 用于下拉菜单（因为下拉菜单通过 teleport 挂载到 body）
.el-select-dropdown {
  background: #2a2a2a !important;
  border: 1px solid #3a3a3a !important;
  border-radius: 8px !important;
  padding: 8px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
  
  .el-select-dropdown__wrap {
    background: #2a2a2a !important;
  }
  
  .el-scrollbar__view {
    background: #2a2a2a !important;
  }
}

.el-select-dropdown__item {
  color: #ccc !important;
  background: transparent !important;
  border-radius: 6px !important;
  padding: 8px 12px !important;
  margin: 4px 0 !important;
  transition: all 0.2s !important;
  border: 2px solid transparent !important;
  box-sizing: border-box !important;
  height: auto !important;
  min-height: 32px !important;
  line-height: 20px !important;
  display: flex !important;
  align-items: center !important;

  &:hover,
  &.hover {
    background: #3a3a3a !important;
    color: #fff !important;
  }

  &.selected {
    color: #fff !important;
    background: #2a2a2a !important;
    border: 2px solid #409eff !important;
    font-weight: 500;
  }
  
  &.is-hovering {
    background: #3a3a3a !important;
  }
}

.el-select__popper.el-popper,
.el-popper.is-light {
  background: #2a2a2a !important;
  border: 1px solid #3a3a3a !important;
}

.el-popper {
  background: #2a2a2a !important;
  border: 1px solid #3a3a3a !important;
  
  &.is-dark {
    background: #2a2a2a !important;
    border: 1px solid #3a3a3a !important;
  }
  
  .el-popper__arrow::before {
    background: #2a2a2a !important;
    border: 1px solid #3a3a3a !important;
  }
}
</style>
