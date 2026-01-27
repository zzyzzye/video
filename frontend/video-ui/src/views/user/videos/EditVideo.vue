<template>
  <div class="edit-video-container">
    <PageHeader 
      title="编辑视频" 
      :breadcrumb="[{ label: '视频管理' }, { label: '已上传视频', path: '/user/videos/uploaded' }, { label: '编辑视频' }]"
    />

    <div v-loading="loading" class="edit-content">
      <div class="edit-layout">
        <!-- 左侧：视频预览 -->
        <div class="left-section">
          <div class="preview-card">
            <h3 class="section-title">视频预览</h3>
            <div class="video-preview">
              <video 
                v-if="videoUrl" 
                ref="videoRef"
                controls 
                class="preview-video"
              />
              <div v-else class="no-video">
                <el-icon :size="48"><VideoPlay /></el-icon>
                <span>暂无视频</span>
              </div>
            </div>
            <div class="video-meta">
              <span><el-icon><Clock /></el-icon> {{ formatDuration(videoForm.duration) }}</span>
              <span><el-icon><View /></el-icon> {{ videoForm.views_count }} 播放</span>
              <span class="status-tag" :class="videoForm.status">{{ statusText(videoForm.status) }}</span>
            </div>
          </div>
        </div>

        <!-- 右侧：封面和信息编辑 -->
        <div class="right-section">
          <!-- 封面设置 -->
          <div class="cover-card">
            <h3 class="section-title">视频封面</h3>
            <div class="cover-content">
              <div class="cover-preview">
                <el-image 
                  v-if="videoForm.thumbnail" 
                  :src="videoForm.thumbnail" 
                  :preview-src-list="[videoForm.thumbnail]"
                  :initial-index="0"
                  fit="cover"
                  class="cover-image"
                  preview-teleported
                />
                <div v-else class="no-cover">
                  <el-icon :size="32"><Picture /></el-icon>
                  <span>暂无封面</span>
                </div>
                <div v-if="videoForm.thumbnail" class="cover-mask">
                  <el-icon :size="20"><ZoomIn /></el-icon>
                  <span>查看大图</span>
                </div>
              </div>
              <div class="cover-actions">
                <el-upload
                  :show-file-list="false"
                  :before-upload="handleCoverUpload"
                  accept="image/*"
                >
                  <el-button type="primary" size="small">
                    <el-icon><Upload /></el-icon> 更换封面
                  </el-button>
                </el-upload>
                <p class="cover-tip">建议 1920x1080，JPG/PNG，≤2MB</p>
              </div>
            </div>
          </div>

          <!-- 基本信息 -->
          <div class="form-card">
            <h3 class="section-title">基本信息</h3>
            
            <el-form 
              ref="formRef"
              :model="videoForm" 
              :rules="rules"
              label-position="top"
            >
              <el-form-item label="视频标题" prop="title">
                <el-input 
                  v-model="videoForm.title" 
                  placeholder="请输入视频标题" 
                  maxlength="100"
                  show-word-limit
                />
              </el-form-item>

              <el-form-item label="视频描述" prop="description">
                <el-input 
                  v-model="videoForm.description" 
                  type="textarea" 
                  :rows="4" 
                  placeholder="请输入视频描述"
                  maxlength="1000"
                  show-word-limit
                />
              </el-form-item>

              <el-form-item label="分区">
                <el-select 
                  v-model="videoForm.category_id" 
                  placeholder="请选择分区" 
                  clearable
                  style="width: 100%"
                >
                  <el-option
                    v-for="category in categories"
                    :key="category.id"
                    :label="category.name"
                    :value="category.id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="标签">
                <el-select
                  v-model="videoForm.tag_ids"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  placeholder="选择或输入标签"
                  style="width: 100%"
                >
                  <el-option
                    v-for="tag in tags"
                    :key="tag.id"
                    :label="tag.name"
                    :value="tag.id"
                  />
                </el-select>
              </el-form-item>

              <!-- 审核信息 -->
              <div v-if="videoForm.review_remark" class="review-info">
                <el-alert 
                  :title="videoForm.status === 'rejected' ? '审核未通过' : '审核备注'" 
                  :type="videoForm.status === 'rejected' ? 'error' : 'info'"
                  :description="videoForm.review_remark"
                  show-icon
                  :closable="false"
                />
              </div>

              <!-- 操作按钮 -->
              <div class="form-actions">
                <el-button type="primary" @click="handleSubmit" :loading="submitting">
                  <el-icon><Check /></el-icon> 保存修改
                </el-button>
                <el-button @click="handleCancel">
                  <el-icon><Close /></el-icon> 取消
                </el-button>
                <el-button 
                  v-if="videoForm.status === 'rejected'" 
                  type="warning" 
                  @click="handleResubmit"
                  :loading="submitting"
                >
                  <el-icon><Refresh /></el-icon> 重新提交
                </el-button>
              </div>
            </el-form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay, Clock, View, Upload, Check, Close, Refresh, Picture, ZoomIn } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { getVideoDetail, getCategories, getTags, updateVideoInfo, uploadThumbnail, publishVideo } from '@/api/video'
import Hls from 'hls.js'

const router = useRouter()
const route = useRoute()
const videoId = route.params.id

const loading = ref(true)
const submitting = ref(false)
const formRef = ref(null)
const coverImageRef = ref(null)
const videoRef = ref(null)
const videoUrl = ref('')
const categories = ref([])
const tags = ref([])
let hls = null

const videoForm = reactive({
  title: '',
  description: '',
  category_id: null,
  tag_ids: [],
  thumbnail: '',
  duration: 0,
  views_count: 0,
  status: '',
  review_remark: ''
})

const rules = {
  title: [
    { required: true, message: '请输入视频标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度在 2 到 100 个字符', trigger: 'blur' }
  ]
}

const fetchVideoDetail = async () => {
  try {
    loading.value = true
    const data = await getVideoDetail(videoId)
    
    videoForm.title = data.title
    videoForm.description = data.description || ''
    videoForm.category_id = data.category?.id || null
    videoForm.tag_ids = data.tags?.map(t => t.id) || []
    videoForm.thumbnail = data.thumbnail
    videoForm.duration = data.duration
    videoForm.views_count = data.views_count
    videoForm.status = data.status
    videoForm.review_remark = data.review_remark || ''
    
    if (data.hls_file) {
      videoUrl.value = `http://localhost:8000/media/${data.hls_file}`
      await nextTick()
      initHlsPlayer()
    }
  } catch (error) {
    console.error('获取视频详情失败:', error)
    ElMessage.error('获取视频详情失败')
    router.push('/user/videos/uploaded')
  } finally {
    loading.value = false
  }
}

const initHlsPlayer = () => {
  if (!videoRef.value || !videoUrl.value) return
  
  if (Hls.isSupported()) {
    if (hls) {
      hls.destroy()
    }
    hls = new Hls()
    hls.loadSource(videoUrl.value)
    hls.attachMedia(videoRef.value)
  } else if (videoRef.value.canPlayType('application/vnd.apple.mpegurl')) {
    videoRef.value.src = videoUrl.value
  }
}

const fetchCategoriesAndTags = async () => {
  try {
    const [categoriesRes, tagsRes] = await Promise.all([getCategories(), getTags()])
    categories.value = categoriesRes?.results || categoriesRes || []
    tags.value = tagsRes?.results || tagsRes || []
  } catch (error) {
    console.error('获取分类和标签失败:', error)
  }
}

const handleCoverUpload = async (file) => {
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请上传图片文件')
    return false
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('封面图片不能超过 2MB')
    return false
  }
  try {
    const res = await uploadThumbnail(videoId, file)
    videoForm.thumbnail = res.thumbnail_url
    ElMessage.success('封面更新成功')
  } catch (error) {
    ElMessage.error('封面上传失败')
  }
  return false
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    const existingTagIds = []
    const newTags = []
    for (const tagId of videoForm.tag_ids) {
      if (typeof tagId === 'number') {
        existingTagIds.push(tagId)
      } else {
        newTags.push(tagId)
      }
    }
    
    await updateVideoInfo(videoId, {
      title: videoForm.title,
      description: videoForm.description,
      category_id: videoForm.category_id,
      tag_ids: existingTagIds,
      new_tags: newTags
    })
    
    ElMessage.success('视频信息更新成功')
    router.push('/user/videos/uploaded')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('更新失败: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    submitting.value = false
  }
}

const handleResubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    await updateVideoInfo(videoId, {
      title: videoForm.title,
      description: videoForm.description,
      category_id: videoForm.category_id,
      tag_ids: videoForm.tag_ids.filter(id => typeof id === 'number'),
      new_tags: videoForm.tag_ids.filter(id => typeof id === 'string')
    })
    
    await publishVideo(videoId)
    ElMessage.success('已重新提交审核')
    router.push('/user/videos/uploaded')
  } catch (error) {
    ElMessage.error('提交失败')
  } finally {
    submitting.value = false
  }
}

const handleCancel = () => router.push('/user/videos/uploaded')

const previewCover = () => {
  // el-image 自带预览功能，点击会自动触发
}

const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s < 10 ? '0' : ''}${s}`
}

const statusText = (status) => {
  const map = { approved: '已通过', pending: '待审核', rejected: '已拒绝', processing: '处理中', ready: '待发布' }
  return map[status] || status
}

onMounted(() => {
  fetchVideoDetail()
  fetchCategoriesAndTags()
})

onBeforeUnmount(() => {
  if (hls) {
    hls.destroy()
    hls = null
  }
})
</script>

<style scoped>
.edit-video-container {
  padding: 20px;
  text-align: left;
}

.edit-content {
  margin-top: 20px;
}

.edit-layout {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 24px;
}

.left-section {
  display: flex;
  flex-direction: column;
}

.right-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.cover-card, .preview-card, .form-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e4e7ed;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

/* 封面样式 */
.cover-content {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.cover-preview {
  width: 160px;
  aspect-ratio: 16/9;
  border-radius: 6px;
  overflow: hidden;
  background: #f5f7fa;
  flex-shrink: 0;
  position: relative;
  cursor: pointer;
}

.cover-image {
  width: 100%;
  height: 100%;
}

.cover-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
}

.cover-preview:hover .cover-mask {
  opacity: 1;
}

.no-cover {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  gap: 4px;
  font-size: 12px;
}

.cover-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cover-tip {
  font-size: 11px;
  color: #909399;
  margin: 0;
  line-height: 1.4;
}

/* 视频预览样式 */
.video-preview {
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 12px;
}

.preview-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.no-video {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #606266;
  gap: 8px;
}

.video-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: #606266;
}

.video-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-tag {
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  color: #fff;
}

.status-tag.approved { background: #67c23a; }
.status-tag.pending { background: #e6a23c; }
.status-tag.rejected { background: #f56c6c; }
.status-tag.processing { background: #409eff; }

/* 表单样式 */
.form-card {
  flex: 1;
}

.review-info {
  margin-bottom: 16px;
}

.form-actions {
  display: flex;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  margin-top: 20px;
}

@media (max-width: 900px) {
  .edit-layout {
    grid-template-columns: 1fr;
  }
  
  .left-section {
    flex-direction: row;
    flex-wrap: wrap;
  }
  
  .cover-card, .preview-card {
    flex: 1;
    min-width: 280px;
  }
}

@media (max-width: 600px) {
  .left-section {
    flex-direction: column;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .form-actions .el-button {
    width: 100%;
  }
}
</style>
