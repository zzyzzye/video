<template>
  <div class="review-container animate__animated animate__fadeIn animate__faster">
    <PageHeader 
      title="视频审核管理" 
      :breadcrumb="[{ label: '管理后台', path: '/admin' }, { label: '视频审核' }]"
      class="animate__animated animate__fadeInDown animate__faster"
    >
      <template #actions>
        <div class="header-actions animate__animated animate__fadeInRight animate__faster">
          <el-select v-model="statusFilter" placeholder="审核状态" @change="handleFilterChange">
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
          <el-input v-model="searchKeyword" placeholder="搜索视频标题/上传者" class="search-input" @keyup.enter="handleSearch" clearable>
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>
      </template>
    </PageHeader>
    
    <!-- 审核列表表格 -->
    <div class="review-table animate__animated animate__fadeInUp animate__fast">
      <el-table 
        v-loading="loading" 
        :data="videoList" 
        style="width: 100%"
        :row-style="{ height: '100px' }"
        @row-click="handlePreview"
      >
        <el-table-column label="视频" width="350">
          <template #default="{ row }">
            <div class="video-cell">
              <div class="video-thumb">
                <el-image 
                  :src="row.thumbnail || '/placeholder.jpg'" 
                  fit="cover" 
                  class="thumb-img"
                >
                  <template #error>
                    <div class="image-error">
                      <el-icon><Picture /></el-icon>
                    </div>
                  </template>
                </el-image>
                <span class="duration-badge" v-if="row.duration">{{ formatDuration(row.duration) }}</span>
                <span class="resolution-badge" v-if="row.resolution_label">{{ row.resolution_label }}</span>
              </div>
              <div class="video-info">
                <div class="video-title">{{ row.title }}</div>
                <div class="video-meta">
                  <span class="author">{{ row.user?.username || '未知' }}</span>
                  <span class="separator">·</span>
                  <span class="time">{{ formatRelativeTime(row.created_at) }}</span>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="分辨率" width="115" align="center">
          <template #default="{ row }">
            <div class="info-cell" v-if="row.width">
              <el-icon class="info-icon resolution-icon"><Monitor /></el-icon>
              <span class="info-value">{{ row.width }}×{{ row.height }}</span>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="宽高比" width="100" align="center">
          <template #default="{ row }">
            <div class="info-cell" v-if="row.aspect_ratio">
              <el-icon class="info-icon ratio-icon"><Calendar /></el-icon>
              <span class="info-value">{{ row.aspect_ratio }}</span>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="编码" width="90" align="center">
          <template #default="{ row }">
            <div class="info-cell" v-if="row.video_codec">
              <el-icon class="info-icon codec-icon"><VideoCamera /></el-icon>
              <span class="info-value">{{ row.video_codec.toUpperCase() }}</span>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="码率" width="100" align="center">
          <template #default="{ row }">
            <div class="info-cell" v-if="row.bitrate">
              <el-icon class="info-icon bitrate-icon"><Monitor /></el-icon>
              <span class="info-value">{{ row.bitrate }}k</span>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="大小" width="130" align="center">
          <template #default="{ row }">
            <div class="info-cell" v-if="row.file_size_display">
              <el-icon class="info-icon size-icon"><Files /></el-icon>
              <span class="info-value">{{ row.file_size_display }}</span>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="时长" width="85" align="center">
          <template #default="{ row }">
            <div class="info-cell" v-if="row.duration">
              <el-icon class="info-icon duration-icon"><Timer /></el-icon>
              <span class="info-value">{{ formatDuration(row.duration) }}</span>
            </div>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="简介" width="270">
          <template #default="{ row }">
            <div class="description-cell">{{ row.description || '暂无简介' }}</div>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" min-width="180" align="center">
          <template #default="{ row }">
            <div class="action-btns" @click.stop>
              <template v-if="row.status === 'pending'">
                <el-button type="success" size="small" @click="handleApprove(row)">
                  <el-icon><Check /></el-icon> 通过
                </el-button>
                <el-button style="margin-left: 0;" type="danger" size="small" @click="handleReject(row)">
                   <el-icon><Close /></el-icon> 拒绝
                </el-button>
              </template>
              <el-button v-else type="primary" size="small" plain @click="handlePreview(row)">
                <el-icon style="margin-right: 5px;"><View /></el-icon> 详情
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="total > 0">
      <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next, jumper" :total="total" @size-change="handleSizeChange" @current-change="handleCurrentChange" />
    </div>
    
    <!-- 预览对话框 -->
    <el-dialog v-model="previewVisible" title="" width="90%" top="5vh" :before-close="handleClosePreview" class="preview-dialog" destroy-on-close append-to-body>
      <div v-if="currentVideo" class="video-preview">
        <div class="preview-left">
          <div class="video-player">
            <div v-if="videoUrl" ref="artPlayerRef" class="art-player-container"></div>
            <div v-else class="no-video">
              <div class="no-video-content">
                <el-icon class="no-video-icon"><Picture /></el-icon>
                <h4>视频文件不可用</h4>
                <el-button v-if="!currentVideo.hls_file && currentVideo.status === 'pending'" type="primary" @click="triggerProcessing">触发转码</el-button>
              </div>
            </div>
          </div>
        </div>
        <div class="preview-right">
          <div class="video-header">
            <h2 class="dialog-title">{{ currentVideo.title }}</h2>
            <el-tag :type="getStatusType(currentVideo.status)" size="large">{{ getStatusText(currentVideo.status) }}</el-tag>
          </div>
          <div class="meta-detail">
            <span><el-icon><User /></el-icon>{{ currentVideo.user?.username }}</span>
            <span><el-icon><Clock /></el-icon>{{ formatDate(currentVideo.created_at) }}</span>
          </div>
          <el-divider />
          <div class="info-section">
            <h4>技术参数</h4>
            <div class="tech-grid">
              <div><span class="label">分辨率</span><span class="value">{{ currentVideo.width }}×{{ currentVideo.height }}</span></div>
              <div><span class="label">宽高比</span><span class="value">{{ currentVideo.aspect_ratio || '-' }}</span></div>
              <div><span class="label">时长</span><span class="value">{{ formatDuration(currentVideo.duration) }}</span></div>
              <div><span class="label">帧率</span><span class="value">{{ currentVideo.frame_rate }}fps</span></div>
              <div><span class="label">视频编码</span><span class="value">{{ currentVideo.video_codec?.toUpperCase() }}</span></div>
              <div><span class="label">音频编码</span><span class="value">{{ currentVideo.audio_codec?.toUpperCase() }}</span></div>
              <div><span class="label">码率</span><span class="value">{{ currentVideo.bitrate }}kbps</span></div>
              <div><span class="label">大小</span><span class="value">{{ currentVideo.file_size_display }}</span></div>
            </div>
          </div>
          <el-divider />
          <div class="info-section"><h4>简介</h4><p>{{ currentVideo.description || '暂无' }}</p></div>
          <div class="info-section" v-if="currentVideo.category"><h4>分类</h4><el-tag type="info">{{ currentVideo.category.name }}</el-tag></div>
          <div class="info-section" v-if="currentVideo.tags?.length"><h4>标签</h4><div class="tags-list"><el-tag v-for="t in currentVideo.tags" :key="t.id" size="small">{{ t.name }}</el-tag></div></div>
          <div class="review-section" v-if="currentVideo.status === 'pending'">
            <el-divider />
            <h4>审核</h4>
            <el-input v-model="reviewForm.remark" type="textarea" :rows="2" placeholder="备注（可选）" />
            <div class="review-btns">
              <el-button type="success" size="large" @click="confirmApprove"><el-icon><Check /></el-icon> 通过</el-button>
              <el-button type="danger" size="large" @click="confirmReject"><el-icon><Close /></el-icon> 拒绝</el-button>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
    
    <!-- 拒绝对话框 -->
    <el-dialog v-model="rejectDialogVisible" title="拒绝原因" width="480px" append-to-body>
      <el-form :model="rejectForm" :rules="rejectRules" ref="rejectFormRef" label-width="80px">
        <el-form-item label="原因" prop="reasonType">
          <el-select v-model="rejectForm.reasonType" placeholder="选择" style="width:100%">
            <el-option label="内容违规" value="违规内容" /><el-option label="版权问题" value="版权问题" />
            <el-option label="画质太差" value="画质太差" /><el-option label="内容低质" value="内容低质" /><el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="rejectForm.reasonType === 'other'" label="说明" prop="customReason">
          <el-input v-model="rejectForm.customReason" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="rejectDialogVisible = false">取消</el-button><el-button type="primary" @click="submitReject">确定</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch, onBeforeUnmount, nextTick } from 'vue';
import { Search, Picture, User, Clock, Check, Close, View, Monitor, VideoCamera, Timer, Files, Calendar } from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { formatDate } from '@/utils/format';
import { getPendingVideos, getReviewedVideos, approveVideo, rejectVideo } from '@/api/admin';
import Artplayer from 'artplayer';
import Hls from 'hls.js';

// 列表数据
const loading = ref(false);
const videoList = ref([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);
const statusFilter = ref('pending');
const searchKeyword = ref('');

// 预览相关
const previewVisible = ref(false);
const currentVideo = ref(null);
const reviewForm = reactive({ remark: '' });
const artPlayerRef = ref(null);
let art = null;

// 拒绝对话框
const rejectDialogVisible = ref(false);
const rejectFormRef = ref(null);
const rejectForm = reactive({ 
  reasonType: '', 
  customReason: '' 
});
const rejectRules = { 
  reasonType: [{ required: true, message: '请选择', trigger: 'change' }], 
  customReason: [{ required: true, message: '请输入', trigger: 'blur' }] 
};

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '00:00';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  
  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }
  return `${m}:${String(s).padStart(2, '0')}`;
};

// 格式化相对时间
const formatRelativeTime = (dateStr) => {
  if (!dateStr) return '';
  const diff = (Date.now() - new Date(dateStr)) / 1000;
  
  if (diff < 60) return '刚刚';
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
  if (diff < 2592000) return `${Math.floor(diff / 86400)}天前`;
  
  return formatDate(dateStr);
};

// 格式化短日期
const formatShortDate = (dateStr) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hour = String(date.getHours()).padStart(2, '0');
  const minute = String(date.getMinutes()).padStart(2, '0');
  return `${month}-${day} ${hour}:${minute}`;
};

// 视频URL
const videoUrl = computed(() => {
  if (!currentVideo.value?.hls_file) return null;
  const baseUrl = import.meta.env.VITE_APP_API_BASE_URL || 'http://localhost:8000';
  return `${baseUrl}/media/${currentVideo.value.hls_file}`;
});

// 初始化播放器
const initPlayer = () => {
  if (!artPlayerRef.value || !videoUrl.value) return;
  
  if (art) {
    art.destroy();
    art = null;
  }
  
  art = new Artplayer({
    container: artPlayerRef.value,
    url: videoUrl.value,
    poster: currentVideo.value?.thumbnail || '',
    volume: 0.7,
    autoplay: true,
    pip: true,
    screenshot: true,
    setting: true,
    playbackRate: true,
    aspectRatio: true,
    fullscreen: true,
    fullscreenWeb: true,
    miniProgressBar: true,
    mutex: true,
    backdrop: true,
    playsInline: true,
    theme: '#00a1d6',
    lang: 'zh-cn',
    moreVideoAttr: {
      crossOrigin: 'anonymous'
    },
    customType: {
      m3u8: (video, url, art) => {
        if (Hls.isSupported()) {
          if (art.hls) art.hls.destroy();
          const hls = new Hls();
          hls.loadSource(url);
          hls.attachMedia(video);
          art.hls = hls;
          art.on('destroy', () => hls.destroy());
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
          video.src = url;
        }
      }
    }
  });
};

// 销毁播放器
const destroyPlayer = () => {
  if (art) {
    art.destroy();
    art = null;
  }
};

// 监听预览对话框
watch(previewVisible, async (visible) => {
  if (visible && videoUrl.value) {
    await nextTick();
    initPlayer();
  } else {
    destroyPlayer();
  }
});

// 获取视频列表
const fetchVideoList = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchKeyword.value
    };
    
    const res = statusFilter.value === 'pending' 
      ? await getPendingVideos(params)
      : await getReviewedVideos({ ...params, status: statusFilter.value });
    
    videoList.value = res.results || [];
    total.value = res.count || 0;
  } catch (error) {
    ElMessage.error('获取失败');
  } finally {
    loading.value = false;
  }
};

// 状态相关
const getStatusType = (status) => {
  const typeMap = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  };
  return typeMap[status] || 'info';
};

const getStatusText = (status) => {
  const textMap = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝'
  };
  return textMap[status] || '未知';
};

// 预览视频
const handlePreview = (video) => {
  currentVideo.value = video;
  previewVisible.value = true;
};

// 关闭预览
const handleClosePreview = () => {
  destroyPlayer();
  previewVisible.value = false;
  currentVideo.value = null;
  reviewForm.remark = '';
};

// 通过审核
const handleApprove = (video) => {
  ElMessageBox.confirm(`通过「${video.title}」？`, '确认', { type: 'success' })
    .then(() => {
      approveVideo(video.id).then(() => {
        ElMessage.success('已通过');
        fetchVideoList();
      });
    })
    .catch(() => {});
};

// 确认通过（预览对话框内）
const confirmApprove = () => {
  if (!currentVideo.value) return;
  
  ElMessageBox.confirm('确认通过？', '确认', { type: 'success' })
    .then(() => {
      approveVideo(currentVideo.value.id, reviewForm.remark).then(() => {
        ElMessage.success('已通过');
        previewVisible.value = false;
        fetchVideoList();
      });
    })
    .catch(() => {});
};

// 拒绝审核
const handleReject = (video) => {
  currentVideo.value = video;
  rejectForm.reasonType = '';
  rejectForm.customReason = '';
  rejectDialogVisible.value = true;
};

// 确认拒绝（预览对话框内）
const confirmReject = () => {
  if (currentVideo.value) {
    handleReject(currentVideo.value);
  }
};

// 提交拒绝
const submitReject = () => {
  rejectFormRef.value?.validate((valid) => {
    if (valid) {
      const reason = rejectForm.reasonType === 'other' 
        ? rejectForm.customReason 
        : rejectForm.reasonType;
      
      rejectVideo(currentVideo.value.id, reason).then(() => {
        ElMessage.success('已拒绝');
        rejectDialogVisible.value = false;
        previewVisible.value = false;
        fetchVideoList();
      });
    }
  });
};

// 触发转码
const triggerProcessing = async () => {
  try {
    await fetch(`http://localhost:8000/api/videos/videos/${currentVideo.value.id}/process/`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    });
    ElMessage.success('已提交');
    setTimeout(fetchVideoList, 3000);
  } catch (error) {
    ElMessage.error('失败');
  }
};

// 筛选和搜索
const handleFilterChange = () => {
  currentPage.value = 1;
  fetchVideoList();
};

const handleSearch = () => {
  currentPage.value = 1;
  fetchVideoList();
};

// 分页
const handleSizeChange = (size) => {
  pageSize.value = size;
  fetchVideoList();
};

const handleCurrentChange = (page) => {
  currentPage.value = page;
  fetchVideoList();
};

// 生命周期
onMounted(fetchVideoList);
onBeforeUnmount(destroyPlayer);
</script>

<style scoped>
/* 容器 */
.review-container {
  padding: 20px;
  min-height: 100%;
  background: #f5f7fa;
  position: relative;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.search-input {
  width: 350px;
}

/* 表格容器 */
.review-table {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* 表格样式 */
:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}

/* 移除表格右侧灰色填充 */
:deep(.el-table__body-wrapper .el-table__empty-block) {
  background: transparent;
}

:deep(.el-table::before) {
  display: none;
}

:deep(.el-table__inner-wrapper::after) {
  background: transparent;
}

:deep(.el-table .el-table__cell.gutter) {
  background: transparent !important;
}

/* 表格行高度 */
:deep(.el-table__row) {
  height: 100px;
  transition: all 0.2s;
}

:deep(.el-table__cell) {
  padding: 14px 12px;
  border-bottom: 1px solid #f0f2f5;
}

/* 去除最后一行的边框 */
:deep(.el-table__body tr:last-child td) {
  border-bottom: none;
}

/* 视频单元格 */
.video-cell {
  display: flex;
  gap: 12px;
  align-items: center;
}

.video-thumb {
  position: relative;
  width: 140px;
  height: 79px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background: #000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.video-cell:hover .video-thumb {
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.thumb-img {
  width: 100%;
  height: 100%;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: rgba(255, 255, 255, 0.6);
  font-size: 28px;
}

.duration-badge {
  position: absolute;
  bottom: 6px;
  right: 6px;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  color: #fff;
  padding: 3px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.resolution-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 3px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.video-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.video-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
  letter-spacing: 0.2px;
  transition: color 0.2s;
}

.video-cell:hover .video-title {
  color: #667eea;
}

.video-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #9ca3af;
}

.video-meta .author {
  color: #6b7280;
  font-weight: 600;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-meta .separator {
  color: #d1d5db;
  font-weight: 400;
}

.video-meta .time {
  flex-shrink: 0;
  font-weight: 500;
}

/* 信息值 */
.info-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.info-icon {
  font-size: 15px;
  flex-shrink: 0;
}

.resolution-icon {
  color: #667eea;
}

.codec-icon {
  color: #f59e0b;
}

.bitrate-icon {
  color: #10b981;
}

.size-icon {
  color: #8b5cf6;
}

.duration-icon {
  color: #ec4899;
}

.time-icon {
  color: #06b6d4;
}

.ratio-icon {
  color: #06b6d4;
}

.info-value {
  font-size: 13px;
  color: #374151;
  font-weight: 600;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  letter-spacing: 0.3px;
}

.text-muted {
  color: #d1d5db;
  font-size: 13px;
  font-weight: 500;
}

/* 简介单元格 */
.description-cell {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
  white-space: normal;
  font-weight: 400;
}

/* 日期单元格 */
.date-cell {
  font-size: 12px;
  color: #6b7280;
  font-weight: 600;
  font-family: 'Courier New', monospace;
  letter-spacing: 0.5px;
}

/* 操作按钮 */
.action-btns {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.action-btns .el-button {
  padding: 6px 12px;
  font-weight: 600;
  border-radius: 6px;
  transition: all 0.2s;
}

.action-btns .el-button--success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
}

.action-btns .el-button--success:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.action-btns .el-button--danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border: none;
}

.action-btns .el-button--danger:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.action-btns .el-button--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: #fff;
}

.action-btns .el-button--primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* 表格行悬停效果 */
:deep(.el-table__row) {
  cursor: pointer;
  transition: all 0.2s;
}

:deep(.el-table__row:hover) {
  background: linear-gradient(90deg, #f9fafb 0%, #ffffff 100%) !important;
  transform: translateX(2px);
}

/* 表格头部样式 */
:deep(.el-table__header-wrapper) {
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  border-radius: 8px 8px 0 0;
}

:deep(.el-table th.el-table__cell) {
  background: transparent;
  color: #6b7280;
  font-weight: 700;
  font-size: 16px;
  padding: 14px 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #e5e7eb;
}

/* 表格边框 */
:deep(.el-table--border) {
  border: none;
}

:deep(.el-table--border .el-table__cell) {
  border-right: none;
}

/* 标签样式优化 */
:deep(.el-tag) {
  font-weight: 600;
  letter-spacing: 0.3px;
  border: none;
  padding: 4px 12px;
  border-radius: 12px;
}

:deep(.el-tag--success) {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #065f46;
}

:deep(.el-tag--warning) {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
}

:deep(.el-tag--danger) {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #991b1b;
}

/* 分页 */
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  background: #fff;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* 空状态 */
:deep(.el-empty) {
  padding: 60px 0;
}


/* 预览对话框 */
:deep(.preview-dialog) {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.preview-dialog .el-dialog__header) {
  padding: 0;
  margin: 0;
  position: absolute;
  right: 10px;
  top: 10px;
  z-index: 10;
}

:deep(.preview-dialog .el-dialog__body) {
  padding: 0;
}

:deep(.preview-dialog .el-dialog__headerbtn) {
  width: 40px;
  height: 40px;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
}

:deep(.preview-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: #fff;
  font-size: 18px;
}

.video-preview {
  display: flex;
  height: 80vh;
  max-height: 800px;
}

.preview-left {
  flex: 1;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-player {
  width: 100%;
  height: 100%;
}

.art-player-container {
  width: 100%;
  height: 100%;
}

.no-video {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #111;
}

.no-video-content {
  text-align: center;
  color: #fff;
}

.no-video-icon {
  font-size: 60px;
  color: #666;
  margin-bottom: 16px;
}

.no-video-content h4 {
  margin: 0 0 16px;
  font-size: 16px;
}

.preview-right {
  width: 340px;
  flex-shrink: 0;
  background: #fff;
  padding: 20px;
  overflow-y: auto;
}

.video-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.dialog-title {
  font-size: 16px;
  font-weight: 600;
  color: #18191c;
  margin: 0;
  flex: 1;
  line-height: 1.4;
}

.meta-detail {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #9499a0;
}

.meta-detail span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.info-section {
  margin-bottom: 12px;
}

.info-section h4 {
  font-size: 13px;
  font-weight: 600;
  color: #18191c;
  margin: 0 0 8px;
}

.info-section p {
  font-size: 13px;
  color: #61666d;
  line-height: 1.5;
  margin: 0;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  background: #f6f7f8;
  padding: 10px;
  border-radius: 6px;
}

.tech-grid > div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tech-grid .label {
  font-size: 11px;
  color: #9499a0;
}

.tech-grid .value {
  font-size: 12px;
  color: #18191c;
  font-family: monospace;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.review-section h4 {
  font-size: 13px;
  font-weight: 600;
  color: #18191c;
  margin: 0 0 10px;
}

.review-btns {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.review-btns .el-button {
  flex: 1;
}

/* 响应式 */
@media (max-width: 1200px) {
  .video-preview {
    flex-direction: column;
    height: auto;
  }
  
  .preview-left {
    height: 360px;
  }
  
  .preview-right {
    width: 100%;
  }
}

@media (max-width: 900px) {
  .video-item {
    flex-direction: column;
  }
  
  .item-cover {
    width: 100%;
    height: 180px;
  }
  
  .item-info {
    border-bottom: 1px solid #f0f0f0;
  }
  
  .item-actions {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
    border-left: none;
    border-top: 1px solid #f0f0f0;
  }
  
  .action-btns {
    flex-direction: row;
    width: auto;
    gap: 10px;
  }
  
  .action-btns .el-button {
    width: auto;
  }
}

@media (max-width: 640px) {
  .header-actions {
    flex-direction: column;
  }
  
  .search-input {
    width: 100%;
  }
}
</style>
