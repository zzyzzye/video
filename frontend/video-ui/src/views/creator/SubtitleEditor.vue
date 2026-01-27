<template>
  <div class="subtitle-editor">
    <!-- 上半部分：视频+控制面板 和 字幕列表 -->
    <div class="top-section">
      <!-- 左侧：视频+控制面板 -->
      <div class="video-section">
        <VideoPlayerSection
          :video-url="videoUrl"
          :active-tab="activeTab"
          :is-panel-collapsed="isPanelCollapsed"
          @update:active-tab="activeTab = $event"
          @toggle-panel="togglePanel"
          @time-update="handleTimeUpdate"
          @player-ready="handlePlayerReady"
        />
      </div>

      <!-- 右侧：字幕列表 -->
      <div class="subtitle-section">
        <SubtitleList
          :subtitles="subtitles"
          :current-subtitle-index="currentSubtitleIndex"
          @select-subtitle="selectSubtitle"
          @add-subtitle="handleAddSubtitle"
          @merge-subtitle="handleMergeSubtitle"
          @delete-subtitle="handleDeleteSubtitle"
          @swap-subtitles="handleSwapSubtitles"
        />
      </div>
    </div>

    <!-- 下半部分：时间轴 -->
    <div class="bottom-section">
      <TimelinePanel
        :subtitles="subtitles"
        :current-subtitle-index="currentSubtitleIndex"
        :duration="duration"
        :current-time="currentTime"
        :video-url="videoUrl"
        @select-subtitle="selectSubtitle"
        @update-subtitle="handleUpdateSubtitle"
        @seek="handleSeek"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import VideoPlayerSection from '@/components/creator/VideoPlayerSection.vue'
import TimelinePanel from '@/components/creator/TimelinePanel.vue'
import SubtitleList from '@/components/creator/SubtitleList.vue'

// 状态
const videoUrl = ref('') // 模拟数据，暂时不需要真实视频
const activeTab = ref('subtitle')
const isPanelCollapsed = ref(false)

// 字幕数据 - 模拟数据，连续无空白
const subtitles = ref([
  { startTime: 0, endTime: 3.5, text: '君の名は', translation: '你的名字' },
  { startTime: 3.5, endTime: 5.2, text: 'はあ', translation: '啊' },
  { startTime: 5.2, endTime: 7.8, text: 'はっ', translation: '哈！' },
  { startTime: 7.8, endTime: 11.5, text: 'これでもしかして', translation: '这难道是' },
  { startTime: 11.5, endTime: 15.2, text: '俺たちは夢の中で', translation: '我们在梦境中' },
  { startTime: 15.2, endTime: 19.0, text: '入れ替わってる', translation: '交换了身体' },
  { startTime: 19.0, endTime: 23.5, text: '男子の視線スカート注意', translation: '男生的视线请注意裙子' },
  { startTime: 23.5, endTime: 27.8, text: 'えぇミツハ', translation: '诶，三叶' },
  { startTime: 27.8, endTime: 30, text: 'どういうこと', translation: '这是怎么回事' }
])

const currentSubtitleIndex = ref(2)
const currentTime = ref(6.5) // 模拟当前播放时间在6.5秒
const duration = ref(30) // 模拟视频总时长30秒

const playerInstance = ref(null)

const togglePanel = () => {
  isPanelCollapsed.value = !isPanelCollapsed.value
}

const selectSubtitle = (index) => {
  currentSubtitleIndex.value = index
  const subtitle = subtitles.value[index]
  
  if (playerInstance.value) {
    playerInstance.value.currentTime = subtitle.startTime
  }
}

const handleTimeUpdate = (time) => {
  currentTime.value = time
  const index = subtitles.value.findIndex(
    sub => time >= sub.startTime && time <= sub.endTime
  )
  if (index !== -1) {
    currentSubtitleIndex.value = index
  }
}

const handlePlayerReady = (player) => {
  playerInstance.value = player
  if (player.duration && player.duration > 0) {
    duration.value = player.duration
  }
}

const handleAddSubtitle = (index) => {
  const newSubtitle = {
    startTime: subtitles.value[index].endTime,
    endTime: subtitles.value[index].endTime + 2,
    text: '',
    translation: ''
  }
  
  subtitles.value.splice(index + 1, 0, newSubtitle)
  ElMessage.success('字幕已插入')
}

const handleMergeSubtitle = (index) => {
  if (index >= subtitles.value.length - 1) {
    ElMessage.warning('已经是最后一条字幕，无法向下合并')
    return
  }
  
  const current = subtitles.value[index]
  const next = subtitles.value[index + 1]
  
  current.text = current.text + (current.text && next.text ? ' ' : '') + next.text
  current.translation = current.translation + (current.translation && next.translation ? ' ' : '') + next.translation
  current.endTime = next.endTime
  
  subtitles.value.splice(index + 1, 1)
  
  ElMessage.success('字幕已合并')
}

const handleDeleteSubtitle = (index) => {
  if (subtitles.value.length <= 1) {
    ElMessage.warning('至少保留一条字幕')
    return
  }
  subtitles.value.splice(index, 1)
  if (currentSubtitleIndex.value >= subtitles.value.length) {
    currentSubtitleIndex.value = subtitles.value.length - 1
  }
  ElMessage.success('字幕已删除')
}

const handleSwapSubtitles = () => {
  subtitles.value.forEach(subtitle => {
    const temp = subtitle.text
    subtitle.text = subtitle.translation
    subtitle.translation = temp
  })
  ElMessage.success('主副字幕已交换')
}

// 处理字幕时间更新（拖拽或调整时长）
const handleUpdateSubtitle = ({ index, startTime, endTime }) => {
  if (index >= 0 && index < subtitles.value.length) {
    subtitles.value[index].startTime = Math.max(0, startTime)
    subtitles.value[index].endTime = Math.min(duration.value, endTime)
  }
}

// 处理时间轴跳转
const handleSeek = (time) => {
  if (playerInstance.value) {
    playerInstance.value.currentTime = time
  }
}
</script>

<style scoped lang="scss">
.subtitle-editor {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #0a0a0a;
  color: #fff;
  overflow: hidden;
}

.top-section {
  height: 85%;
  display: flex;
  border-bottom: 1px solid #2a2a2a;
}

.video-section {
  width: 50%;
  display: flex;
  flex-direction: column;
  background: #000;
  border-right: 1px solid #2a2a2a;
}

.subtitle-section {
  width: 50%;
  display: flex;
  flex-direction: column;
  background: #1a1a1a;
}

.bottom-section {
  height: 15%;
  display: flex;
  flex-direction: column;
  background: #0a0a0a;
  min-height: 150px;
}
</style>
