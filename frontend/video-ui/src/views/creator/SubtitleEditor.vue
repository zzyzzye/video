<template>
  <div class="subtitle-editor">
    <!-- 顶部工具栏 -->
    <EditorToolbar
      :video-title="videoTitle"
      :video-status="videoStatus"
      :has-subtitles="subtitles.length > 0"
      :save-button-text="saveButtonText"
      @save="saveAndPublish"
      @upload="handleVideoUpload"
      @export="handleExportSubtitle"
      @import="handleImportSubtitle"
      @settings-change="handleSettingsChange"
    />

    <!-- 上半部分：视频+控制面板 和 字幕列表 -->
    <div class="top-section">
      <!-- 左侧：视频+控制面板 -->
      <div class="video-section">
        <VideoPlayerSection
          :video-url="videoUrl"
          :subtitles="subtitles"
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import EditorToolbar from '@/components/creator/EditorToolbar.vue'
import VideoPlayerSection from '@/components/creator/VideoPlayerSection.vue'
import TimelinePanel from '@/components/creator/TimelinePanel.vue'
import SubtitleList from '@/components/creator/SubtitleList.vue'
import { triggerTranscode, uploadVideo, getVideoSubtitles, updateVideoSubtitles, getVideoDetail } from '@/api/video'

// 路由相关
const route = useRoute()
const router = useRouter()


const isEditBeforeTranscode = computed(() => {
  return route.query.mode === 'edit_before_transcode'
})

// 任务 5.1.3: 根据模式调整保存按钮文案
const saveButtonText = computed(() => {
  return isEditBeforeTranscode.value ? '保存并继续处理' : '保存'
})

// 状态
const videoUrl = ref('') // 模拟数据，暂时不需要真实视频
const videoTitle = ref('示例视频标题')
const videoStatus = ref('draft')
const activeTab = ref('subtitle')
const isPanelCollapsed = ref(false)

const localPreviewUrl = ref('')

const subtitles = ref([])

const currentSubtitleIndex = ref(-1)
const currentTime = ref(0)
const duration = ref(0)

const playerInstance = ref(null)

const loadSubtitles = async () => {
  const videoId = route.query.videoId
  if (!videoId) return
  try {
    const res = await getVideoSubtitles(videoId)
    const list = res?.subtitles || []
    subtitles.value = Array.isArray(list) ? list : []
    currentSubtitleIndex.value = subtitles.value.length ? 0 : -1
  } catch (error) {
    console.error('加载字幕失败:', error)
  }
}

const loadVideoInfo = async () => {
  const videoId = route.query.videoId
  if (!videoId) return
  try {
    const detail = await getVideoDetail(videoId)
    if (detail?.title) {
      videoTitle.value = detail.title
    }
    // TODO: 如果后端返回可播放地址，可在这里设置 videoUrl
  } catch (error) {
    console.error('加载视频信息失败:', error)
  }
}

onMounted(async () => {
  await Promise.all([loadVideoInfo(), loadSubtitles()])
})

const togglePanel = () => {
  isPanelCollapsed.value = !isPanelCollapsed.value
}

const selectSubtitle = (index) => {
  if (index < 0 || index >= subtitles.value.length) return
  currentSubtitleIndex.value = index
  const subtitle = subtitles.value[index]
  if (!subtitle) return
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
  } else if (!subtitles.value.length) {
    currentSubtitleIndex.value = -1
  }
}

const handlePlayerReady = (player) => {
  playerInstance.value = player
  if (player.duration && player.duration > 0) {
    duration.value = player.duration
  }
}

const handleAddSubtitle = (index) => {
  if (index < 0 || index >= subtitles.value.length) return
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
  if (index < 0 || index >= subtitles.value.length) {
    ElMessage.warning('无有效字幕可合并')
    return
  }
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
  if (index < 0 || index >= subtitles.value.length) return
  if (subtitles.value.length <= 1) {
    ElMessage.warning('至少保留一条字幕')
    return
  }
  subtitles.value.splice(index, 1)
  if (subtitles.value.length === 0) {
    currentSubtitleIndex.value = -1
  } else if (currentSubtitleIndex.value >= subtitles.value.length) {
    currentSubtitleIndex.value = subtitles.value.length - 1
  }
  ElMessage.success('字幕已删除')
}

const handleSwapSubtitles = () => {
  if (!subtitles.value.length) {
    ElMessage.warning('暂无字幕可交换')
    return
  }
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


const saveAndPublish = async () => {
  try {
    // 获取视频ID
    const videoId = route.query.videoId
    
    if (!videoId) {
      ElMessage.error('视频ID不存在')
      return
    }

    try {
      await updateVideoSubtitles(videoId, subtitles.value)
    } catch (e) {
      console.error('保存字幕到后端失败:', e)
      ElMessage.error('保存字幕失败: ' + (e.message || '未知错误'))
      return
    }
    

    console.log('保存字幕数据:', subtitles.value)
    

    if (isEditBeforeTranscode.value) {
      // 转码前编辑模式：保存后触发转码
      await triggerTranscode(videoId)
      
      ElMessage.success('字幕已保存，视频已开始处理')
      
      router.push('/user/dashboard')
    } else {
      ElMessage.success('字幕已保存')
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败: ' + (error.message || '未知错误'))
  }
}

const handleVideoUpload = async (file) => {
  try {
    console.log('上传视频文件:', file)

    // 先本地预览，保证视频区域立即可见
    if (localPreviewUrl.value) {
      URL.revokeObjectURL(localPreviewUrl.value)
      localPreviewUrl.value = ''
    }
    localPreviewUrl.value = URL.createObjectURL(file)
    videoUrl.value = localPreviewUrl.value

    // 再进行真实上传（分片上传）
    const uploadedVideo = await uploadVideo(file)
    console.log('上传视频返回:', uploadedVideo)

    // 如果后端返回了可播放地址，覆盖本地预览地址
    const remoteUrl = uploadedVideo?.video_url || uploadedVideo?.url || uploadedVideo?.file_url
    if (remoteUrl) {
      videoUrl.value = remoteUrl
      if (localPreviewUrl.value) {
        URL.revokeObjectURL(localPreviewUrl.value)
        localPreviewUrl.value = ''
      }
    }

    ElMessage.success('视频上传成功，开始处理')
    videoStatus.value = 'processing'
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('上传失败: ' + (error.message || '未知错误'))
  }
}

// 导出字幕
const handleExportSubtitle = () => {
  try {
    // 生成 SRT 格式字幕
    let srtContent = ''
    subtitles.value.forEach((subtitle, index) => {
      const startTime = formatSRTTime(subtitle.startTime)
      const endTime = formatSRTTime(subtitle.endTime)
      
      srtContent += `${index + 1}\n`
      srtContent += `${startTime} --> ${endTime}\n`
      srtContent += `${subtitle.text}\n`
      if (subtitle.translation) {
        srtContent += `${subtitle.translation}\n`
      }
      srtContent += `\n`
    })
    
    // 创建下载链接
    const blob = new Blob([srtContent], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${videoTitle.value || 'subtitle'}.srt`
    link.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('字幕导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 导入字幕
const handleImportSubtitle = async (file) => {
  try {
    const text = await file.text()
    const imported = parseSRTFile(text)
    
    if (imported.length > 0) {
      subtitles.value = imported
      currentSubtitleIndex.value = 0
      if (playerInstance.value?.duration && playerInstance.value.duration > 0) {
        duration.value = playerInstance.value.duration
      }
      ElMessage.success(`成功导入 ${imported.length} 条字幕`)

      const videoId = route.query.videoId
      if (videoId) {
        try {
          await updateVideoSubtitles(videoId, subtitles.value)
        } catch (e) {
          console.error('导入后保存字幕失败:', e)
        }
      }
    } else {
      ElMessage.warning('未能解析字幕文件')
    }
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入失败: ' + (error.message || '未知错误'))
  }
}

// 处理设置变更
const handleSettingsChange = (newSettings) => {
  console.log('设置已更新:', newSettings)
  // TODO: 应用设置到编辑器
}

// 辅助函数：格式化时间为 SRT 格式
const formatSRTTime = (seconds) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 1000)
  
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')},${String(ms).padStart(3, '0')}`
}

// 辅助函数：解析 SRT 文件
const parseSRTFile = (text) => {
  const result = []
  const blocks = text.trim().split(/\n\s*\n/)
  
  blocks.forEach(block => {
    const lines = block.trim().split('\n')
    if (lines.length >= 3) {
      const timeLine = lines[1]
      const timeMatch = timeLine.match(/(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})/)
      
      if (timeMatch) {
        const startTime = parseInt(timeMatch[1]) * 3600 + parseInt(timeMatch[2]) * 60 + parseInt(timeMatch[3]) + parseInt(timeMatch[4]) / 1000
        const endTime = parseInt(timeMatch[5]) * 3600 + parseInt(timeMatch[6]) * 60 + parseInt(timeMatch[7]) + parseInt(timeMatch[8]) / 1000
        
        const text = lines[2]
        const translation = lines[3] || ''
        
        result.push({
          startTime,
          endTime,
          text,
          translation
        })
      }
    }
  })
  
  return result
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
  height: calc(85% - 42px); // 减去工具栏高度
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
  border-top: 1px solid rgb(102, 0, 219);
  height: 15%;
  display: flex;
  flex-direction: column;
  background: #0a0a0a;
  min-height: 150px;
}
</style>
