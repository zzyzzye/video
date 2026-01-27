<template>
  <div class="uploaded-videos-container">
    <PageHeader 
      title="已上传视频" 
      :breadcrumb="[{ label: '视频管理' }, { label: '已上传视频' }]"
    />

    <div class="toolbar">
      <div class="toolbar-left">
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
      <el-tab-pane name="approved">
        <template #label><el-icon><CircleCheck /></el-icon> 已通过</template>
      </el-tab-pane>
      <el-tab-pane name="pending">
        <template #label><el-icon><Clock /></el-icon> 待审核</template>
      </el-tab-pane>
      <el-tab-pane name="rejected">
        <template #label><el-icon><CircleClose /></el-icon> 已拒绝</template>
      </el-tab-pane>
    </el-tabs>
    
    <div v-loading="loading" class="video-list">
      <el-empty v-if="!loading && videos.length === 0" description="暂无上传视频" />
      
      <ul class="card-grid">
        <li v-for="video in videos" :key="video.id" class="card-item">
          <div class="thumb" @click="viewVideo(video)">
            <el-image :src="video.thumbnail" fit="cover" />
            <span class="time">{{ formatDuration(video.duration) }}</span>
            <span class="status" :class="video.status">{{ statusText(video.status) }}</span>
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
              <el-button size="small" text @click="viewVideo(video)">查看</el-button>
              <el-button size="small" text @click="editVideo(video)">编辑</el-button>
              <el-button size="small" text type="danger" @click="deleteVideo(video)">删除</el-button>
            </div>
          </div>
        </li>
        <li v-if="videos.length > 0 && videos.length < 5" class="card-item guide" @click="goToUpload">
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, Star, ChatDotRound, Plus, CircleCheck, Clock, CircleClose } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { getMyVideos, deleteVideo as deleteVideoApi } from '@/api/video'

const router = useRouter()
const loading = ref(false)
const videos = ref([])
const totalVideos = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const statusFilter = ref('')
const sortOption = ref('-created_at')

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

const statusText = (status) => {
  const map = { approved: '已通过', pending: '待审核', rejected: '已拒绝' }
  return map[status] || status
}

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
  transition: box-shadow 0.2s;
}

.card-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }

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
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  color: #fff;
}
.card-item .thumb .status.approved { background: #67c23a; }
.card-item .thumb .status.pending { background: #e6a23c; }
.card-item .thumb .status.rejected { background: #f56c6c; }

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

@media (max-width: 600px) {
  .card-grid { grid-template-columns: 1fr; }
  .toolbar { flex-direction: column; align-items: stretch; }
  .toolbar-left { flex-direction: column; }
  .search-input { width: 100%; }
}
</style>
