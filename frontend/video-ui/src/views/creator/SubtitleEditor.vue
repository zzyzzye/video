<template>
  <div class="subtitle-editor">
    <!-- 顶部工具栏 -->
    <EditorToolbar
      :video-title="videoTitle"
      :video-status="videoStatus"
      :has-subtitles="subtitles.length > 0"
      :is-generating-subtitles="isGeneratingSubtitles"
      :show-upload-button="showUploadButton"
      @save="handleSave"
      @upload="handleUpload"
      @settings-change="handleSettingsChange"
      @generate-subtitles="startGenerateSubtitles"
    />

    <!-- 上半部分：视频+控制面板 和 字幕列表 -->
    <div class="top-section">
      <!-- 左侧：视频+控制面板 -->
      <div class="video-section">
        <VideoPlayerSection
          ref="videoPlayerRef"
          :video-url="videoUrl"
          :subtitles="subtitles"
          :active-tab="activeTab"
          :is-panel-collapsed="isPanelCollapsed"
          @update:active-tab="activeTab = $event"
          @toggle-panel="togglePanel"
          @time-update="handleTimeUpdate"
          @player-ready="handlePlayerReady"
          @export="handleExportSubtitle"
          @import="handleImportSubtitle"
          @upload="handleVideoUpload"
          @select-uploaded-video="handleSelectUploadedVideo"
        />
      </div>

      <!-- 右侧：字幕列表 -->
      <div class="subtitle-section">
        <SubtitleList
          :subtitles="subtitles"
          :current-subtitle-index="currentSubtitleIndex"
          :video-id="route.query.videoId"
          @select-subtitle="selectSubtitle"
          @add-subtitle="handleAddSubtitle"
          @merge-subtitle="handleMergeSubtitle"
          @delete-subtitle="handleDeleteSubtitle"
          @swap-subtitles="handleSwapSubtitles"
          @update-subtitles="handleUpdateSubtitles"
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import EditorToolbar from '@/components/creator/EditorToolbar.vue'
import VideoPlayerSection from '@/components/creator/VideoPlayerSection.vue'
import TimelinePanel from '@/components/creator/TimelinePanel.vue'
import SubtitleList from '@/components/creator/SubtitleList.vue'
import { triggerTranscode, uploadVideo, getVideoSubtitles, updateVideoSubtitles, getVideoDetail, generateSubtitles, getSubtitleTaskStatus } from '@/api/video'

// 路由相关
const route = useRoute()
const router = useRouter()


const isEditBeforeTranscode = computed(() => {
  return route.query.mode === 'edit_before_transcode'
})

// 是否显示上传按钮
const showUploadButton = computed(() => {
  // 调试日志
  console.log('=== 上传按钮显示条件检查 ===')
  console.log('isEditBeforeTranscode:', isEditBeforeTranscode.value)
  console.log('pendingVideoFile:', pendingVideoFile.value)
  console.log('videoStatus:', videoStatus.value)
  console.log('route.query:', route.query)
  
  // 转码前编辑模式下显示上传按钮
  if (!isEditBeforeTranscode.value) {
    console.log('不是转码前编辑模式，不显示按钮')
    return false
  }
  
  // 有待上传的本地视频文件
  if (pendingVideoFile.value) {
    console.log('有待上传的本地文件，显示按钮')
    return true
  }
  
  // 或者视频状态是 draft 或 pending_subtitle_edit（表示还没开始转码）
  if (videoStatus.value === 'draft' || videoStatus.value === 'pending_subtitle_edit') {
    console.log(`视频状态是 ${videoStatus.value}，显示按钮`)
    return true
  }
  
  console.log('不满足任何条件，不显示按钮')
  return false
})

// 状态
const videoUrl = ref('') // 模拟数据，暂时不需要真实视频
const videoTitle = ref('示例视频标题')
const videoStatus = ref('draft')
const activeTab = ref('subtitle')
const isPanelCollapsed = ref(false)

const localPreviewUrl = ref('')
const pendingVideoFile = ref(null) // 待上传的视频文件

const subtitles = ref([])

const subtitleTaskId = ref('')
const isGeneratingSubtitles = ref(false)

const currentSubtitleIndex = ref(-1)
const currentTime = ref(0)
const duration = ref(0)

const playerInstance = ref(null)
const videoPlayerRef = ref(null) // 添加子组件引用

const resolvePlayableUrl = (video) => {
  if (!video) return ''
  const raw = video.video_file || video.hls_file
  if (!raw) return ''
  if (typeof raw === 'string' && (raw.startsWith('http://') || raw.startsWith('https://'))) {
    return raw
  }
  const path = typeof raw === 'string' && raw.startsWith('/') ? raw : `/${raw}`
  return `http://localhost:8000${path}`
}

const loadSubtitles = async () => {
  const videoId = route.query.videoId
  if (!videoId) {
    console.log('没有视频ID，跳过加载字幕')
    return
  }
  try {
    const res = await getVideoSubtitles(videoId)
    const list = res?.subtitles || []
    subtitles.value = Array.isArray(list) ? list : []
    currentSubtitleIndex.value = subtitles.value.length ? 0 : -1
    console.log(`加载了 ${subtitles.value.length} 条字幕`)
    
    // 加载字幕样式配置
    if (res?.style && videoPlayerRef.value?.setSubtitleStyle) {
      videoPlayerRef.value.setSubtitleStyle(res.style)
      console.log('已加载字幕样式配置')
    }
  } catch (error) {
    console.error('加载字幕失败:', error)
    // 如果是404错误，说明视频还没有字幕，这是正常的
    if (error.response?.status === 404) {
      subtitles.value = []
      currentSubtitleIndex.value = -1
    }
  }
}

const startGenerateSubtitles = async (language = 'auto') => {
  const videoId = route.query.videoId
  if (!videoId) return
  if (isGeneratingSubtitles.value) return
  if (subtitles.value.length > 0) return

  isGeneratingSubtitles.value = true
  subtitleTaskId.value = ''
  try {
    ElMessage.info(`正在提交字幕生成任务（语言: ${language === 'auto' ? '自动检测' : language}）...`)
    const res = await generateSubtitles(videoId, language)
    const taskId = res?.task_id
    if (!taskId) {
      ElMessage.error('字幕任务提交成功但未返回 task_id')
      return
    }
    subtitleTaskId.value = taskId
    ElMessage.success('字幕生成已开始，正在生成...')
  } catch (e) {
    console.error('提交字幕生成失败:', e)
    ElMessage.error('提交字幕生成失败: ' + (e.message || '未知错误'))
    isGeneratingSubtitles.value = false
  }
}

const pollSubtitleTaskStatus = async () => {
  const videoId = route.query.videoId
  const taskId = subtitleTaskId.value
  if (!videoId || !taskId) return
  if (!isGeneratingSubtitles.value) return

  try {
    const res = await getSubtitleTaskStatus(videoId, taskId)
    const state = res?.state
    if (state === 'SUCCESS') {
      await loadSubtitles()
      isGeneratingSubtitles.value = false
      if (subtitles.value.length > 0) {
        ElMessage.success(`字幕生成完成，共 ${subtitles.value.length} 条`)
      } else {
        ElMessage.warning('字幕生成完成，但未识别到有效字幕')
      }
      return
    }
    if (state === 'FAILURE') {
      isGeneratingSubtitles.value = false
      ElMessage.error('字幕生成失败')
      return
    }
  } catch (e) {
    console.error('查询字幕任务状态失败:', e)
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
    const playableUrl = resolvePlayableUrl(detail)
    if (playableUrl) {
      videoUrl.value = playableUrl
    }
  } catch (error) {
    console.error('加载视频信息失败:', error)
  }
}

onMounted(async () => {
  const videoId = route.query.videoId
  
  // 转码前编辑模式 + 没有 videoId：等待用户上传新视频
  if (isEditBeforeTranscode.value && !videoId) {
    videoTitle.value = '新视频'
    videoStatus.value = 'draft'
    console.log('转码前编辑模式：等待用户上传视频')
    return
  }
  
  // 其他情况：加载已有视频信息（包括转码前编辑模式但有 videoId 的情况）
  await Promise.all([loadVideoInfo(), loadSubtitles()])
})

watch(
  () => route.query.videoId,
  async (newId, oldId) => {
    if (!newId || newId === oldId) return
    subtitleTaskId.value = ''
    isGeneratingSubtitles.value = false
    await Promise.all([loadVideoInfo(), loadSubtitles()])
  }
)

watch(
  () => subtitleTaskId.value,
  (newTaskId) => {
    if (!newTaskId) return
    const timer = setInterval(async () => {
      if (!isGeneratingSubtitles.value) {
        clearInterval(timer)
        return
      }
      await pollSubtitleTaskStatus()
    }, 2000)
  }
)

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
  // 查找当前时间对应的字幕索引
  const index = subtitles.value.findIndex(
    sub => time >= sub.startTime && time < sub.endTime
  )
  
  if (index !== -1) {
    currentSubtitleIndex.value = index
  } else {
    // 如果没有匹配的字幕，检查是否处于两条字幕之间的间隙
    // 只有当时间超过最后一条字幕时才设为 -1
    const lastSub = subtitles.value[subtitles.value.length - 1]
    if (lastSub && time >= lastSub.endTime) {
      currentSubtitleIndex.value = -1
    }
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

// 处理字幕更新（翻译后）
const handleUpdateSubtitles = (newSubtitles) => {
  subtitles.value = newSubtitles
  if (subtitles.value.length > 0 && currentSubtitleIndex.value === -1) {
    currentSubtitleIndex.value = 0
  }
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


// 保存字幕（不上传视频）
const handleSave = async () => {
  try {
    const videoId = route.query.videoId
    
    // 转码前编辑模式：保存到本地状态
    if (isEditBeforeTranscode.value) {
      // 只是本地保存，不与服务器交互
      ElMessage.success('字幕已保存到本地')
      return
    }
    
    // 普通编辑模式：保存到服务器
    if (!videoId) {
      ElMessage.error('视频ID不存在')
      return
    }

    // 获取字幕样式配置
    const style = videoPlayerRef.value?.getSubtitleStyle?.() || null

    await updateVideoSubtitles(videoId, subtitles.value, style)
    ElMessage.success('字幕已保存')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败: ' + (error.message || '未知错误'))
  }
}

// 上传视频并触发转码（仅转码前编辑模式）
const handleUpload = async () => {
  try {
    let videoId = route.query.videoId
    
    // 情况1：有待上传的本地视频文件
    if (pendingVideoFile.value) {
      // 确认上传
      await ElMessageBox.confirm(
        '确定要上传视频并开始处理吗？',
        '确认上传',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info'
        }
      )
      
      // 上传视频文件
      ElMessage.info('正在上传视频...')
      const uploadedVideo = await uploadVideo(pendingVideoFile.value)
      console.log('上传视频返回:', uploadedVideo)
      
      videoId = uploadedVideo?.id || uploadedVideo?.video_id
      if (!videoId) {
        ElMessage.error('视频上传成功但未返回视频ID')
        return
      }
      
      ElMessage.success('视频上传成功')
      pendingVideoFile.value = null
    }
    // 情况2：已有 videoId，直接触发转码
    else if (videoId) {
      // 确认开始处理
      await ElMessageBox.confirm(
        '确定要开始处理视频吗？处理过程中将无法再编辑字幕。',
        '确认处理',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info'
        }
      )
    } else {
      ElMessage.error('请先选择要上传的视频文件')
      return
    }
    
    // 统一保存字幕和样式（无论是否有字幕内容，都要保存样式配置）
    if (videoId) {
      try {
        const style = videoPlayerRef.value?.getSubtitleStyle?.() || null
        await updateVideoSubtitles(videoId, subtitles.value, style)
        ElMessage.success('字幕和样式已保存')
      } catch (e) {
        console.error('保存字幕失败:', e)
        ElMessage.error('保存字幕失败: ' + (e.message || '未知错误'))
        return
      }
      
      // 触发转码
      try {
        await triggerTranscode(videoId)
        ElMessage.success('视频已开始处理')
        router.push('/user/dashboard')
      } catch (e) {
        console.error('触发转码失败:', e)
        ElMessage.error('触发转码失败: ' + (e.message || '未知错误'))
      }
    }
  } catch (error) {
    if (error === 'cancel') {
      // 用户取消
      return
    }
    console.error('操作失败:', error)
    ElMessage.error('操作失败: ' + (error.message || '未知错误'))
  }
}

const handleVideoUpload = async (file) => {
  try {
    console.log('选择视频文件:', file)

    // 转码前编辑模式：只做本地预览，不立即上传
    if (isEditBeforeTranscode.value) {
      if (localPreviewUrl.value) {
        URL.revokeObjectURL(localPreviewUrl.value)
        localPreviewUrl.value = ''
      }
      localPreviewUrl.value = URL.createObjectURL(file)
      videoUrl.value = localPreviewUrl.value

      // 保存待上传的文件，等保存时再上传
      pendingVideoFile.value = file

      ElMessage.success('视频已加载，可以开始编辑字幕')
      videoStatus.value = 'draft'
      return
    }
    
    // 普通模式：立即上传
    ElMessage.info('正在上传视频...')
    const uploadedVideo = await uploadVideo(file)
    console.log('上传视频返回:', uploadedVideo)
    
    const videoId = uploadedVideo?.id || uploadedVideo?.video_id
    if (!videoId) {
      ElMessage.error('视频上传成功但未返回视频ID')
      return
    }
    
    // 更新路由参数
    await router.replace({
      query: {
        ...route.query,
        videoId: videoId
      }
    })
    
    ElMessage.success('视频上传成功')
  } catch (error) {
    console.error('处理视频失败:', error)
    ElMessage.error('处理视频失败: ' + (error.message || '未知错误'))
  }
}

// 处理选择已上传的视频
const handleSelectUploadedVideo = async (video) => {
  try {
    console.log('选择已上传视频:', video)
    console.log('视频文件字段:', {
      video_file: video.video_file,
      hls_file: video.hls_file
    })
    
    // 清理本地预览
    if (localPreviewUrl.value) {
      URL.revokeObjectURL(localPreviewUrl.value)
      localPreviewUrl.value = ''
    }
    pendingVideoFile.value = null
    
    // 设置视频信息
    videoTitle.value = video.title || '未命名视频'
    videoStatus.value = video.status || 'draft'
    
    // 优先使用原始 MP4 文件（用于编辑和波形图）
    let targetUrl = ''
    if (video.video_file) {
      // 检查是否已经是完整URL
      if (video.video_file.startsWith('http://') || video.video_file.startsWith('https://')) {
        targetUrl = video.video_file
        console.log('使用原始视频文件(完整URL):', targetUrl)
      } else {
        // 如果是相对路径，需要拼接完整 URL
        const videoPath = video.video_file.startsWith('/') ? video.video_file : `/${video.video_file}`
        targetUrl = `http://localhost:8000${videoPath}`
        console.log('使用原始视频文件(相对路径):', targetUrl)
      }
    } else if (video.hls_file) {
      // 如果没有原始文件，使用 HLS（但波形图可能无法工作）
      if (video.hls_file.startsWith('http://') || video.hls_file.startsWith('https://')) {
        targetUrl = video.hls_file
      } else {
        const hlsPath = video.hls_file.startsWith('/') ? video.hls_file : `/${video.hls_file}`
        targetUrl = `http://localhost:8000${hlsPath}`
      }
      console.log('使用 HLS 文件:', targetUrl)
      ElMessage.warning('使用 HLS 文件播放，波形图功能可能不可用')
    } else {
      ElMessage.warning('该视频暂无可播放文件')
      console.warn('视频没有可用的文件')
      return
    }
    
    // 先更新路由参数
    if (video.id && video.id !== route.query.videoId) {
      await router.replace({
        query: {
          ...route.query,
          videoId: video.id
        }
      })
    }
    
    // 加载该视频的字幕
    if (video.id) {
      try {
        const res = await getVideoSubtitles(video.id)
        const list = res?.subtitles || []
        subtitles.value = Array.isArray(list) ? list : []
        currentSubtitleIndex.value = subtitles.value.length ? 0 : -1
        console.log(`加载了 ${subtitles.value.length} 条字幕`)
      } catch (error) {
        console.error('加载字幕失败:', error)
        // 如果是404错误，说明视频还没有字幕，这是正常的
        if (error.response?.status === 404) {
          subtitles.value = []
          currentSubtitleIndex.value = -1
          console.log('该视频暂无字幕，可以开始添加')
        }
      }
    }
    
    // 最后设置视频URL，触发播放器更新
    console.log('设置视频URL:', targetUrl)
    console.log('设置前 videoUrl.value:', videoUrl.value)
    videoUrl.value = targetUrl
    console.log('设置后 videoUrl.value:', videoUrl.value)
    
    ElMessage.success('视频已加载')
  } catch (error) {
    console.error('加载已上传视频失败:', error)
    ElMessage.error('加载视频失败: ' + (error.message || '未知错误'))
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
          const style = videoPlayerRef.value?.getSubtitleStyle?.() || null
          await updateVideoSubtitles(videoId, subtitles.value, style)
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
  overflow: hidden;
  flex-shrink: 0;
}

.video-section {
  width: 50%;
  display: flex;
  flex-direction: column;
  background: #000;
  border-right: 1px solid #2a2a2a;
  overflow: hidden;
}

.subtitle-section {
  width: 50%;
  display: flex;
  flex-direction: column;
  background: #1a1a1a;
  overflow: hidden;
}

.bottom-section {
  border-top: 1px solid rgb(102, 0, 219);
  height: 15%;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #0a0a0a;
  overflow: hidden;
}

// Element Plus 对话框深色主题样式（全局）
:deep(.el-dialog) {
  background: #1a1a1a;
  border: 1px solid #3a3a3a;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);

  .el-dialog__header {
    border-bottom: 1px solid #2a2a2a;
    padding: 20px;

    .el-dialog__title {
      color: #fff;
      font-size: 18px;
      font-weight: 600;
    }

    .el-dialog__headerbtn {
      .el-dialog__close {
        color: #999;
        
        &:hover {
          color: #fff;
        }
      }
    }
  }

  .el-dialog__body {
    padding: 20px;
    color: #ccc;
  }

  .el-dialog__footer {
    border-top: 1px solid #2a2a2a;
    padding: 16px 20px;
  }
}

:deep(.el-input__wrapper) {
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

:deep(.el-input__inner) {
  color: #fff;
}

:deep(.el-button) {
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  color: #ccc;

  &:hover {
    background: #3a3a3a;
    border-color: #4a4a4a;
    color: #fff;
  }

  &.el-button--primary {
    background: #6b46c1;
    border-color: #6b46c1;
    color: #fff;

    &:hover {
      background: #7c5dd1;
      border-color: #7c5dd1;
    }

    &.is-disabled {
      background: #4a4a4a;
      border-color: #4a4a4a;
      color: #999;
    }
  }
}

:deep(.el-scrollbar) {
  .el-scrollbar__bar {
    opacity: 0.6;
    
    &.is-horizontal .el-scrollbar__thumb {
      background: #555;
    }
    
    &.is-vertical .el-scrollbar__thumb {
      background: #555;
    }
  }
  
  .el-scrollbar__thumb:hover {
    background: #666;
  }
}
</style>

<style lang="scss">
// 全局样式 - Element Plus 下拉框深色主题（因为下拉框通过 teleport 挂载到 body）
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
      border: 2px solid #6b46c1 !important;
      font-weight: 500;
    }
    
    &.is-hovering {
      background: #3a3a3a !important;
    }
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

// 滚动条样式
.el-scrollbar__bar {
  opacity: 0.6;
  
  &.is-horizontal .el-scrollbar__thumb {
    background: #555 !important;
  }
  
  &.is-vertical .el-scrollbar__thumb {
    background: #555 !important;
  }
}

.el-scrollbar__thumb:hover {
  background: #666 !important;
}
</style>
