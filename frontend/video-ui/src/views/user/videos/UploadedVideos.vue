<template>
  <div class="uploaded-videos-container">
    <PageHeader 
      title="已上传视频" 
      :breadcrumb="[{ label: '视频管理' }, { label: '已上传视频' }]"
      class="animate-slide-up"
    />

    <div class="toolbar animate-slide-up" style="animation-delay: 0.1s">
      <div class="toolbar-left">
        <el-checkbox 
          v-model="selectAll" 
          :indeterminate="isIndeterminate"
          @change="handleSelectAll"
        >
          全选
        </el-checkbox>
        <el-button 
          v-if="selectedVideos.length > 0" 
          type="danger" 
          size="small"
          @click="batchDelete"
        >
          <el-icon><Delete /></el-icon> 批量删除 ({{ selectedVideos.length }})
        </el-button>
        <el-dropdown 
          v-if="selectedVideos.length > 0"
          @command="handleBatchCommand"
        >
          <el-button size="small">
            批量操作 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="export">导出数据</el-dropdown-item>
              <el-dropdown-item command="download">下载视频</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-input 
          v-model="searchQuery" 
          placeholder="搜索视频" 
          clearable 
          prefix-icon="Search"
          class="search-input"
          @input="handleSearch" 
        />
        <el-button type="primary" @click="goToUpload">
          <el-icon><Plus /></el-icon> 上传视频
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-radio-group v-model="sortOption" size="small" @change="handleSearch">
          <el-radio-button value="-created_at">最新</el-radio-button>
          <el-radio-button value="-views_count">最热</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <el-tabs v-model="statusFilter" @tab-change="handleSearch">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane name="uploading">
        <template #label><el-icon><Upload /></el-icon> 上传中</template>
      </el-tab-pane>
      <el-tab-pane name="processing">
        <template #label><el-icon><Loading /></el-icon> 处理中</template>
      </el-tab-pane>
      <el-tab-pane name="pending">
        <template #label><el-icon><Clock /></el-icon> 待审核</template>
      </el-tab-pane>
      <el-tab-pane name="approved">
        <template #label><el-icon><CircleCheck /></el-icon> 已通过</template>
      </el-tab-pane>
      <el-tab-pane name="rejected">
        <template #label><el-icon><CircleClose /></el-icon> 已拒绝</template>
      </el-tab-pane>
      <el-tab-pane name="taken_down">
        <template #label><el-icon><WarningFilled /></el-icon> 已下架</template>
      </el-tab-pane>
      <el-tab-pane name="failed">
        <template #label><el-icon><WarningFilled /></el-icon> 失败</template>
      </el-tab-pane>
    </el-tabs>
    
    <div v-loading="loading" class="video-list animate-slide-up" style="animation-delay: 0.2s">
      <el-empty v-if="!loading && videos.length === 0" description="暂无上传视频" />
      
      <ul class="card-grid">
        <li v-for="video in videos" :key="video.id" class="card-item" :class="{ 'selected': isSelected(video.id) }">
          <div class="select-checkbox">
            <el-checkbox 
              :model-value="isSelected(video.id)"
              @change="toggleSelect(video.id)"
            />
          </div>
          <div class="thumb" @click="viewVideo(video)">
            <el-image :src="video.thumbnail" fit="cover" />
            <span class="time">{{ formatDuration(video.duration) }}</span>
            <span class="status" :class="getStatusClass(video.status)">
              {{ getStatusText(video.status) }}
            </span>
          </div>
          <div class="info">
            <h3 class="title" @click="viewVideo(video)">{{ video.title }}</h3>
            <div class="meta">
              <div class="stats">
                <span><el-icon><View /></el-icon>{{ video.views_count }}</span>
                <span><el-icon><Star /></el-icon>{{ video.likes_count }}</span>
                <span><el-icon><ChatDotRound /></el-icon>{{ video.comments_count }}</span>
              </div>
              <span>{{ formatDate(video.created_at) }}</span>
            </div>
            <div class="actions">
              <el-button v-if="video.status === 'pending_subtitle_edit'" size="small" type="primary" @click="continueEditSubtitle(video)">继续编辑字幕</el-button>
              <el-button v-if="video.status === 'taken_down' || video.status === 'rejected'" size="small" type="warning" @click="resubmitReview(video)">重新提交审核</el-button>
              <el-button v-if="video.status !== 'taken_down'" size="small" text @click="viewVideo(video)">查看</el-button>
              <el-button v-if="video.status !== 'taken_down'" size="small" text @click="editVideo(video)">编辑</el-button>
              <el-button size="small" text type="danger" @click="deleteVideo(video)">删除</el-button>
            </div>
          </div>
        </li>
        <li v-if="videos.length > 0 && videos.length < 5 && statusFilter !== 'taken_down' && statusFilter !== 'rejected' && statusFilter !== 'failed'" class="card-item guide" @click="goToUpload">
          <span class="plus">+</span>
          <span>上传更多视频</span>
        </li>
      </ul>
    </div>
    
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 30]"
        layout="total, sizes, prev, pager, next"
        :total="totalVideos"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, Star, ChatDotRound, Plus, CircleCheck, Clock, CircleClose, Upload, Loading, WarningFilled, Delete, ArrowDown } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { getMyVideos, deleteVideo as deleteVideoApi } from '@/api/video'
import { getStatusText, getStatusClass } from '@/utils/videoStatus'
import service from '@/api/user'
import '@/styles/videoStatus.css'

const router = useRouter()
const loading = ref(false)
const videos = ref([])
const totalVideos = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const statusFilter = ref('')
const sortOption = ref('-created_at')

// 批量选择相关
const selectedVideos = ref([])
const selectAll = ref(false)

// 计算是否为半选状态
const isIndeterminate = computed(() => {
  return selectedVideos.value.length > 0 && selectedVideos.value.length < videos.value.length
})

// 全选/取消全选
const handleSelectAll = (val) => {
  if (val) {
    selectedVideos.value = videos.value.map(v => v.id)
  } else {
    selectedVideos.value = []
  }
}

// 切换单个视频选择状态
const toggleSelect = (videoId) => {
  const index = selectedVideos.value.indexOf(videoId)
  if (index > -1) {
    selectedVideos.value.splice(index, 1)
  } else {
    selectedVideos.value.push(videoId)
  }
  // 更新全选状态
  selectAll.value = selectedVideos.value.length === videos.value.length
}

// 判断视频是否被选中
const isSelected = (videoId) => {
  return selectedVideos.value.includes(videoId)
}

// 批量删除
const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedVideos.value.length} 个视频吗？删除后将移至回收站，30天内可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const deletePromises = selectedVideos.value.map(id => deleteVideoApi(id))
    await Promise.all(deletePromises)
    
    ElMessage.success(`已将 ${selectedVideos.value.length} 个视频移至回收站`)
    selectedVideos.value = []
    selectAll.value = false
    fetchVideos()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 批量操作命令处理
const handleBatchCommand = (command) => {
  switch (command) {
    case 'export':
      exportSelectedVideos()
      break
    case 'download':
      downloadSelectedVideos()
      break
  }
}

// 导出选中视频数据
const exportSelectedVideos = () => {
  const selectedData = videos.value.filter(v => selectedVideos.value.includes(v.id))
  const csvContent = [
    ['标题', '播放量', '点赞数', '评论数', '状态', '创建时间'].join(','),
    ...selectedData.map(v => [
      `"${v.title}"`,
      v.views_count,
      v.likes_count,
      v.comments_count,
      statusText(v.status),
      formatDate(v.created_at)
    ].join(','))
  ].join('\n')
  
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `视频数据_${new Date().getTime()}.csv`
  link.click()
  
  ElMessage.success('数据导出成功')
}

// 下载选中视频
const downloadSelectedVideos = () => {
  ElMessage.info('批量下载功能开发中...')
  // 这里可以实现批量下载逻辑
}

const fetchVideos = async () => {
  loading.value = true
  try {
    const params = { page: currentPage.value, page_size: pageSize.value }
    if (searchQuery.value) params.search = searchQuery.value
    if (statusFilter.value) params.status = statusFilter.value
    if (sortOption.value) params.ordering = sortOption.value
    const response = await getMyVideos(params)
    videos.value = response.results
    totalVideos.value = response.count
    // 清空选择状态
    selectedVideos.value = []
    selectAll.value = false
  } catch (error) {
    ElMessage.error('获取视频列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => { currentPage.value = 1; fetchVideos() }
const handleCurrentChange = () => fetchVideos()
const handleSizeChange = () => fetchVideos()
const goToUpload = () => router.push({ path: '/user/dashboard', query: { activeTab: 'upload' } })
const viewVideo = (video) => router.push(`/video/${video.id}`)
const editVideo = (video) => router.push(`/user/videos/edit/${video.id}`)

const continueEditSubtitle = (video) => {
  router.push({
    path: '/creator/subtitle',
    query: {
      videoId: video.id,
      mode: 'edit_before_transcode'
    }
  })
}

const resubmitReview = async (video) => {
  try {
    await ElMessageBox.confirm(
      `确定要重新提交视频「${video.title}」进行审核吗？`,
      '重新提交审核',
      {
        confirmButtonText: '确定提交',
        cancelButtonText: '取消',
        type: 'info',
      }
    )
    
    loading.value = true
    await service({
      url: `/videos/videos/${video.id}/resubmit-review/`,
      method: 'post'
    })
    
    ElMessage.success('已重新提交审核，请等待管理员审核')
    fetchVideos()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('提交失败')
      console.error(error)
    }
  } finally {
    loading.value = false
  }
}

const deleteVideo = async (video) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除视频「${video.title}」吗？删除后将移至回收站，30天内可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteVideoApi(video.id)
    ElMessage.success('已移至回收站')
    fetchVideos()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const formatDuration = (s) => {
  if (!s) return '00:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec < 10 ? '0' : ''}${sec}`
}
const formatDate = (d) => d ? d.slice(0, 10) : ''

onMounted(fetchVideos)
</script>

<style scoped>
.uploaded-videos-container {
  padding: 20px;
  text-align: left;
}
.head-title .left h1 { font-size: 28px; margin-bottom: 8px; }
.breadcrumb { display: flex; gap: 8px; list-style: none; padding: 0; margin: 0; }
.breadcrumb a { color: #999; text-decoration: none; }
.breadcrumb a.active { color: #409eff; }

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 20px 0 16px;
  flex-wrap: wrap;
  gap: 12px;
}
.toolbar-left {
  display: flex;
  gap: 12px;
  align-items: center;
}
.toolbar-right {
  display: flex;
  align-items: center;
}
.search-input { width: 240px; }

.video-list { margin-top: 16px; }

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  list-style: none;
  padding: 0;
  margin: 0;
}

.card-item {
  display: flex;
  flex-direction: column;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
  transition: all 0.2s;
  position: relative;
}

.card-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }

.card-item.selected {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.card-item .select-checkbox {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 10;
}

.card-item .select-checkbox :deep(.el-checkbox__inner) {
  width: 20px;
  height: 20px;
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid #dcdfe6;
  border-radius: 4px;
}

.card-item .select-checkbox :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #409eff;
  border-color: #409eff;
}

.card-item .select-checkbox :deep(.el-checkbox__inner::after) {
  border-width: 2px;
  height: 10px;
  left: 5px;
  top: 0px;
  width: 5px;
}

.card-item .thumb {
  width: 100%;
  padding-top: 56.25%; /* 16:9 比例 */
  position: relative;
  background: #000;
  cursor: pointer;
}

.card-item .thumb .el-image { 
  position: absolute;
  top: 0;
  left: 0;
  width: 100%; 
  height: 100%; 
}

.card-item .thumb .time {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0,0,0,0.75);
  color: #fff;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
}

.card-item .thumb .status {
  position: absolute;
  top: 8px;
  left: 8px;
}

.card-item .info {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-item .info .title {
  font-size: 14px;
  font-weight: 500;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}
.card-item .info .title:hover { color: #409eff; }

.card-item .info .meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.card-item .info .stats {
  display: flex;
  gap: 10px;
}
.card-item .info .stats span { display: flex; align-items: center; gap: 2px; }

.card-item .info .actions {
  display: flex;
  gap: 6px;
}

.card-item.guide {
  min-height: 260px;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #909399;
}

.card-item.guide .plus { font-size: 40px; }
.card-item.guide:hover { color: #409eff; border-color: #409eff; }

.pagination-container { margin-top: 24px; display: flex; justify-content: center; }

/* 动画定义 */
@keyframes subtleSlideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-slide-up {
  animation: subtleSlideUp 0.4s ease-out both;
}

@media (max-width: 600px) {
  .card-grid { grid-template-columns: 1fr; }
  .toolbar { flex-direction: column; align-items: stretch; }
  .toolbar-left { flex-direction: column; }
  .search-input { width: 100%; }
}
</style>
