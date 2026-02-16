<template>
  <div class="report-management-container animate__animated animate__fadeIn animate__faster">
    <PageHeader 
      title="举报处理" 
      :breadcrumb="[{ label: '管理后台' }, { label: '举报处理' }]"
      class="animate__animated animate__fadeInDown animate__faster"
    />
    
    <!-- 统计卡片 -->
    <div class="stats-section animate__animated animate__fadeInUp animate__fast">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-card animate__animated animate__zoomIn animate__faster">
            <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_reports }}</div>
              <div class="stat-label">总举报数</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card animate__animated animate__zoomIn animate__faster">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.pending_reports }}</div>
              <div class="stat-label">待处理</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card animate__animated animate__zoomIn animate__faster">
            <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.resolved_reports }}</div>
              <div class="stat-label">已处理</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card animate__animated animate__zoomIn animate__faster">
            <div class="stat-icon" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.today_reports }}</div>
              <div class="stat-label">今日新增</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <!-- 搜索和筛选区域 -->
    <div class="filter-section animate__animated animate__fadeInUp animate__fast">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-input
            v-model="filters.search"
            placeholder="搜索视频标题或举报人"
            clearable
            @keyup.enter="loadReports"
            size="large"
            class="animate__animated animate__fadeInLeft animate__faster"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.status" placeholder="状态筛选" clearable @change="loadReports" size="large" class="animate__animated animate__fadeInLeft animate__faster">
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已处理" value="resolved" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.reason" placeholder="举报原因" clearable @change="loadReports" size="large" class="animate__animated animate__fadeInLeft animate__faster">
            <el-option label="违法违规" value="illegal" />
            <el-option label="色情低俗" value="vulgar" />
            <el-option label="血腥暴力" value="violence" />
            <el-option label="垃圾广告" value="spam" />
            <el-option label="侵权" value="copyright" />
            <el-option label="虚假误导" value="misleading" />
            <el-option label="人身攻击" value="harassment" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="loadReports" size="large" style="width: 100%;" class="animate__animated animate__fadeInRight animate__faster">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-col>
        <el-col :span="4">
          <el-button type="danger" @click="batchTakedown" size="large" style="width: 100%;" :disabled="selectedReports.length === 0" class="animate__animated animate__fadeInRight animate__faster">
            批量下架
          </el-button>
        </el-col>
      </el-row>
    </div>
    
    <!-- 举报列表 -->
    <div class="table-section animate__animated animate__fadeInUp animate__fast">
      <el-table
        :data="reports"
        style="width: 100%"
        v-loading="loading"
        element-loading-text="加载中..."
        :row-class-name="tableRowClassName"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column prop="id" label="ID" width="80" align="center" />
        
        <el-table-column label="视频信息" min-width="250">
          <template #default="{ row }">
            <div class="video-info-cell">
              <div class="video-details">
                <div class="video-title">{{ row.video_title }}</div>
                <div class="video-id">视频ID: {{ row.video }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="举报人" width="200">
          <template #default="{ row }">
            <div class="reporter-info-cell">
              <el-avatar 
                :size="40" 
                :src="row.reporter.avatar ? `http://localhost:8000${row.reporter.avatar}` : ''" 
                class="reporter-avatar"
              >
                {{ row.reporter.username.charAt(0).toUpperCase() }}
              </el-avatar>
              <div class="reporter-details">
                <div class="reporter-name">{{ row.reporter.username }}</div>
                <div class="reporter-email">{{ row.reporter.email || '-' }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="举报原因" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getReasonTagType(row.reason)" effect="dark">
              {{ row.reason_display }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="详细描述" min-width="200">
          <template #default="{ row }">
            <div class="description-cell">
              {{ row.description || '无详细描述' }}
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="dark">
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="处理人" width="120" align="center">
          <template #default="{ row }">
            <div v-if="row.handler" class="handler-cell">
              <div class="handler-name">{{ row.handler.username }}</div>
            </div>
            <span v-else class="no-handler">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="处理结果" min-width="180">
          <template #default="{ row }">
            <div v-if="row.handle_result" class="handle-result-cell">
              {{ row.handle_result }}
            </div>
            <span v-else class="no-result">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="举报时间" width="180">
          <template #default="{ row }">
            <div class="time-cell">
              <div>{{ formatDate(row.created_at, 'date') }}</div>
              <div class="time-sub">{{ formatDate(row.created_at, 'time') }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="处理时间" width="180">
          <template #default="{ row }">
            <div v-if="row.handled_at" class="time-cell">
              <div>{{ formatDate(row.handled_at, 'date') }}</div>
              <div class="time-sub">{{ formatDate(row.handled_at, 'time') }}</div>
            </div>
            <span v-else class="no-time">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="250" fixed="right" align="center">
          <template #default="{ row }">
            <el-button 
              v-if="row.status === 'pending'" 
              type="danger" 
              size="small" 
              @click="handleReport(row, 'takedown')"
            >
              下架视频
            </el-button>
            <el-button 
              v-if="row.status === 'pending'" 
              type="success" 
              size="small" 
              @click="handleReport(row, 'reject')"
            >
              驳回举报
            </el-button>
            <el-button 
              size="small" 
              @click="viewDetail(row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 分页 -->
    <div class="pagination-section" v-if="reports.length > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        background
      />
    </div>
    
    <!-- 处理对话框 -->
    <el-dialog 
      v-model="handleDialogVisible" 
      :title="getDialogTitle()"
      width="600px"
      :close-on-click-modal="false"
      class="animate__animated animate__zoomIn animate__faster"
      append-to-body
    >
      <div v-if="currentReport" class="dialog-report-info animate__animated animate__fadeIn">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="视频标题">
            {{ currentReport.video_title }}
          </el-descriptions-item>
          <el-descriptions-item label="举报人">
            {{ currentReport.reporter.username }}
          </el-descriptions-item>
          <el-descriptions-item label="举报原因">
            <el-tag :type="getReasonTagType(currentReport.reason)" effect="dark">
              {{ currentReport.reason_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="详细描述">
            {{ currentReport.description || '无' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      
      <el-form :model="handleForm" label-width="100px" style="margin-top: 20px;">
        <el-form-item :label="getFormLabel()">
          <el-input 
            v-model="handleForm.handle_result" 
            type="textarea" 
            :rows="4"
            :placeholder="getFormPlaceholder()"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleDialogVisible = false" size="large">取消</el-button>
          <el-button 
            :type="getButtonType()" 
            @click="submitHandle" 
            :loading="submitting"
            size="large"
          >
            确认{{ getActionText() }}
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 详情对话框 -->
    <el-dialog 
      v-model="detailDialogVisible" 
      title="举报详情"
      width="1200px"
      :close-on-click-modal="false"
      top="5vh"
      class="animate__animated animate__zoomIn animate__faster"
      append-to-body
    >
      <div v-if="currentReport" class="report-detail-content animate__animated animate__fadeIn">
        <el-row :gutter="24">
          <!-- 左侧：视频预览 -->
          <el-col :span="14">
            <div class="video-preview-section">
              <div class="section-title">被举报视频</div>
              
              <div v-if="currentReport.videoDetail" class="video-player-wrapper">
                <div v-if="currentReport.videoDetail.hls_file" ref="artPlayerRef" class="art-player-container"></div>
                <div v-else class="no-video">
                  <el-icon :size="60"><VideoCamera /></el-icon>
                  <div>视频处理中或不可用</div>
                </div>
                
                <div class="video-info-card">
                  <div class="video-title-large">{{ currentReport.videoDetail.title }}</div>
                  
                  <!-- 视频作者信息 -->
                  <div class="video-author-section">
                    <el-avatar 
                      :size="40" 
                      :src="currentReport.videoDetail.user?.avatar ? `http://localhost:8000${currentReport.videoDetail.user.avatar}` : ''"
                    >
                      {{ currentReport.videoDetail.user?.username?.charAt(0).toUpperCase() }}
                    </el-avatar>
                    <div class="author-info-detail">
                      <div class="author-name-large">{{ currentReport.videoDetail.user?.username }}</div>
                      <div class="author-email">{{ currentReport.videoDetail.user?.email || '-' }}</div>
                    </div>
                  </div>
                  
                  <div class="video-meta">
                    <span><el-icon><View /></el-icon> {{ currentReport.videoDetail.views_count || 0 }} 观看</span>
                    <span><el-icon><Star /></el-icon> {{ currentReport.videoDetail.likes_count || 0 }} 点赞</span>
                    <span><el-icon><ChatDotRound /></el-icon> {{ currentReport.videoDetail.comments_count || 0 }} 评论</span>
                  </div>
                  
                  <div class="video-description">
                    {{ currentReport.videoDetail.description || '无描述' }}
                  </div>
                </div>
              </div>
              
              <div v-else-if="videoLoadError" class="video-error">
                <el-icon :size="60" color="#f56c6c"><WarningFilled /></el-icon>
                <div class="error-text">视频已被删除或不存在</div>
                <div class="error-subtext">视频ID: {{ currentReport.video }}</div>
              </div>
              
              <div v-else class="loading-video">
                <el-icon class="is-loading" :size="40"><Loading /></el-icon>
                <div>加载视频信息中...</div>
              </div>
            </div>
          </el-col>
          
          <!-- 右侧：举报信息 -->
          <el-col :span="10">
            <div class="report-info-section">
              <div class="section-title">举报信息</div>
              
              <div class="reporter-card">
                <el-avatar 
                  :size="50" 
                  :src="currentReport.reporter.avatar ? `http://localhost:8000${currentReport.reporter.avatar}` : ''"
                >
                  {{ currentReport.reporter.username.charAt(0).toUpperCase() }}
                </el-avatar>
                <div class="reporter-info">
                  <div class="reporter-label">举报人</div>
                  <div class="reporter-name-large">{{ currentReport.reporter.username }}</div>
                  <div class="reporter-email-large">{{ currentReport.reporter.email || '-' }}</div>
                </div>
              </div>
              
              <div class="report-details-scroll">
                <div class="report-details-list">
                  <div class="detail-item">
                    <div class="detail-label">举报ID</div>
                    <div class="detail-value">#{{ currentReport.id }}</div>
                  </div>
                  
                  <div class="detail-item">
                    <div class="detail-label">视频标题</div>
                    <div class="detail-value">{{ currentReport.video_title }}</div>
                  </div>
                  
                  <div class="detail-item">
                    <div class="detail-label">举报原因</div>
                    <div class="detail-value">
                      <el-tag :type="getReasonTagType(currentReport.reason)" effect="dark">
                        {{ currentReport.reason_display }}
                      </el-tag>
                    </div>
                  </div>
                  
                  <div class="detail-item">
                    <div class="detail-label">举报状态</div>
                    <div class="detail-value">
                      <el-tag :type="getStatusType(currentReport.status)" effect="dark">
                        {{ currentReport.status_display }}
                      </el-tag>
                    </div>
                  </div>
                  
                  <div class="detail-item">
                    <div class="detail-label">举报时间</div>
                    <div class="detail-value time-value">{{ formatDate(currentReport.created_at) }}</div>
                  </div>
                  
                  <div class="detail-item full-width">
                    <div class="detail-label">详细描述</div>
                    <div class="detail-value description-box">
                      {{ currentReport.description || '无详细描述' }}
                    </div>
                  </div>
                  
                  <template v-if="currentReport.handler">
                    <el-divider style="margin: 16px 0;" />
                    
                    <div class="detail-item">
                      <div class="detail-label">处理人</div>
                      <div class="detail-value">{{ currentReport.handler.username }}</div>
                    </div>
                    
                    <div class="detail-item">
                      <div class="detail-label">处理时间</div>
                      <div class="detail-value time-value">{{ formatDate(currentReport.handled_at) }}</div>
                    </div>
                    
                    <div class="detail-item full-width">
                      <div class="detail-label">处理结果</div>
                      <div class="detail-value description-box">
                        {{ currentReport.handle_result || '无' }}
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialogVisible = false" size="large">关闭</el-button>
          <el-button 
            v-if="currentReport?.status === 'pending' && !videoLoadError" 
            type="danger" 
            @click="handleReport(currentReport, 'takedown'); detailDialogVisible = false"
            size="large"
          >
            下架视频
          </el-button>
          <el-button 
            v-if="currentReport?.status === 'pending'" 
            type="success" 
            @click="handleReport(currentReport, 'reject'); detailDialogVisible = false"
            size="large"
          >
            驳回举报
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch, nextTick, onBeforeUnmount } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
  Search, Refresh, Warning, Clock, CircleCheck, TrendCharts,
  VideoCamera, View, Star, ChatDotRound, Loading, WarningFilled
} from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import service from '@/api/user';
import Artplayer from 'artplayer';
import Hls from 'hls.js';

const loading = ref(false);
const reports = ref([]);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const selectedReports = ref([]);

const filters = reactive({
  status: '',
  reason: '',
  search: ''
});

const handleDialogVisible = ref(false);
const detailDialogVisible = ref(false);
const handleAction = ref('');
const currentReport = ref(null);
const submitting = ref(false);
const artPlayerRef = ref(null);
const videoLoadError = ref(false);
let art = null;

const handleForm = reactive({
  handle_result: ''
});

// 统计数据
const stats = ref({
  total_reports: 0,
  pending_reports: 0,
  resolved_reports: 0,
  today_reports: 0
});

// 计算统计数据
const calculateStats = () => {
  stats.value.total_reports = reports.value.length;
  stats.value.pending_reports = reports.value.filter(r => r.status === 'pending').length;
  stats.value.resolved_reports = reports.value.filter(r => r.status === 'resolved').length;
  
  const today = new Date().toDateString();
  stats.value.today_reports = reports.value.filter(r => {
    const reportDate = new Date(r.created_at).toDateString();
    return reportDate === today;
  }).length;
};

// 加载举报列表
const loadReports = async () => {
  loading.value = true;
  try {
    const params = {};
    if (filters.status) params.status = filters.status;
    if (filters.reason) params.reason = filters.reason;
    if (filters.search) params.search = filters.search;
    
    const response = await service({
      url: '/videos/admin/reports/',
      method: 'get',
      params
    });
    
    reports.value = response;
    total.value = response.length;
    calculateStats();
  } catch (error) {
    ElMessage.error('加载举报列表失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 分页处理
const handleSizeChange = (newSize) => {
  pageSize.value = newSize;
  currentPage.value = 1;
};

const handleCurrentChange = (newPage) => {
  currentPage.value = newPage;
};

// 处理举报
const handleReport = (report, action) => {
  currentReport.value = report;
  handleAction.value = action;
  handleForm.handle_result = '';
  handleDialogVisible.value = true;
};

// 提交处理
const submitHandle = async () => {
  submitting.value = true;
  try {
    await service({
      url: `/videos/admin/reports/${currentReport.value.id}/handle/`,
      method: 'post',
      data: {
        action: handleAction.value,
        handle_result: handleForm.handle_result
      }
    });
    
    const actionText = handleAction.value === 'takedown' ? '下架' : (handleAction.value === 'resolve' ? '处理' : '驳回');
    ElMessage.success(`${actionText}成功`);
    handleDialogVisible.value = false;
    loadReports();
  } catch (error) {
    ElMessage.error('操作失败');
    console.error(error);
  } finally {
    submitting.value = false;
  }
};

// 批量下架
const batchTakedown = async () => {
  if (selectedReports.value.length === 0) {
    ElMessage.warning('请先选择要下架的举报');
    return;
  }
  
  ElMessageBox.confirm(
    `确定要下架选中的 ${selectedReports.value.length} 个视频吗？`,
    '批量下架',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    let successCount = 0;
    let failCount = 0;
    
    for (const report of selectedReports.value) {
      try {
        await service({
          url: `/videos/admin/reports/${report.id}/handle/`,
          method: 'post',
          data: {
            action: 'takedown',
            handle_result: '批量下架'
          }
        });
        successCount++;
      } catch (error) {
        failCount++;
        console.error(`下架举报 ${report.id} 失败:`, error);
      }
    }
    
    ElMessage.success(`批量下架完成：成功 ${successCount} 个${failCount > 0 ? `，失败 ${failCount} 个` : ''}`);
    loadReports();
  }).catch(() => {
    // 取消操作
  });
};

// 选择变化
const handleSelectionChange = (selection) => {
  selectedReports.value = selection.filter(r => r.status === 'pending');
};

// 获取对话框标题
const getDialogTitle = () => {
  const titleMap = {
    takedown: '下架视频',
    reject: '驳回举报'
  };
  return titleMap[handleAction.value] || '处理举报';
};

// 获取表单标签
const getFormLabel = () => {
  const labelMap = {
    takedown: '下架原因',
    reject: '驳回原因'
  };
  return labelMap[handleAction.value] || '处理结果';
};

// 获取表单占位符
const getFormPlaceholder = () => {
  const placeholderMap = {
    takedown: '请输入下架原因（必填）',
    reject: '请输入驳回原因（选填）'
  };
  return placeholderMap[handleAction.value] || '请输入处理结果';
};

// 获取按钮类型
const getButtonType = () => {
  const typeMap = {
    takedown: 'danger',
    reject: 'success'
  };
  return typeMap[handleAction.value] || 'primary';
};

// 获取操作文本
const getActionText = () => {
  const textMap = {
    takedown: '下架',
    reject: '驳回'
  };
  return textMap[handleAction.value] || '处理';
};

// 查看详情
const viewDetail = async (report) => {
  currentReport.value = report;
  videoLoadError.value = false;
  
  // 加载视频详情
  try {
    const videoResponse = await service({
      url: `/videos/videos/${report.video}/`,
      method: 'get'
    });
    currentReport.value.videoDetail = videoResponse;
  } catch (error) {
    console.error('加载视频详情失败:', error);
    videoLoadError.value = true;
    currentReport.value.videoDetail = null;
  }
  
  detailDialogVisible.value = true;
};

// 视频URL
const videoUrl = computed(() => {
  if (!currentReport.value?.videoDetail?.hls_file) return null;
  const baseUrl = 'http://localhost:8000';
  return `${baseUrl}/media/${currentReport.value.videoDetail.hls_file}`;
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
    poster: currentReport.value?.videoDetail?.thumbnail ? `http://localhost:8000${currentReport.value.videoDetail.thumbnail}` : '',
    volume: 0.7,
    autoplay: false,
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

// 监听对话框显示状态
watch(detailDialogVisible, async (visible) => {
  if (visible && videoUrl.value) {
    await nextTick();
    initPlayer();
  } else {
    destroyPlayer();
  }
});

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    pending: 'warning',
    processing: 'info',
    resolved: 'success',
    rejected: 'danger'
  };
  return typeMap[status] || 'info';
};

// 获取原因标签类型
const getReasonTagType = (reason) => {
  const typeMap = {
    illegal: 'danger',
    vulgar: 'danger',
    violence: 'danger',
    spam: 'warning',
    copyright: 'warning',
    misleading: 'warning',
    harassment: 'danger',
    other: 'info'
  };
  return typeMap[reason] || 'info';
};

// 表格行类名
const tableRowClassName = ({ row }) => {
  if (row.status === 'pending') return 'pending-row';
  if (row.status === 'resolved') return 'resolved-row';
  if (row.status === 'rejected') return 'rejected-row';
  return '';
};

// 格式化日期
const formatDate = (dateString, type = 'full') => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  
  if (type === 'date') {
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  }
  
  if (type === 'time') {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

onMounted(() => {
  loadReports();
});

onBeforeUnmount(() => {
  destroyPlayer();
});
</script>

<style scoped>
.report-management-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
  position: relative;
}

/* 统计卡片 */
.stats-section {
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
  animation-duration: 0.6s;
}

.stat-card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  color: #fff;
  font-size: 28px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

/* 筛选区域 */
.filter-section {
  margin-bottom: 20px;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

/* 表格区域 */
.table-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

/* 视频信息单元格 */
.video-info-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.video-details {
  flex: 1;
  min-width: 0;
}

.video-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-id {
  font-size: 12px;
  color: #999;
}

/* 举报人信息单元格 */
.reporter-info-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
}

.reporter-avatar {
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.reporter-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.reporter-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
  line-height: 1.2;
}

.reporter-email {
  font-size: 12px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
}

/* 描述单元格 */
.description-cell {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 时间单元格 */
.time-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.time-sub {
  font-size: 12px;
  color: #999;
}

.no-time {
  color: #c0c4cc;
  font-size: 13px;
}

/* 处理人单元格 */
.handler-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.handler-name {
  font-size: 14px;
  font-weight: 600;
  color: #409eff;
}

.no-handler {
  color: #c0c4cc;
  font-size: 13px;
}

/* 处理结果单元格 */
.handle-result-cell {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-result {
  color: #c0c4cc;
  font-size: 13px;
}

/* 分页 */
.pagination-section {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

/* 表格行样式 */
:deep(.el-table .pending-row) {
  background-color: #fff7e6;
}

:deep(.el-table .resolved-row) {
  background-color: #f0f9ff;
}

:deep(.el-table .rejected-row) {
  background-color: #fef0f0;
}

:deep(.el-table .el-table__cell) {
  padding: 12px 0;
}

/* 对话框样式 */
.dialog-report-info {
  margin-bottom: 20px;
}

.description-text {
  line-height: 1.6;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 详情对话框 */
.report-detail-content {
  padding: 0;
  max-height: 70vh;
  overflow: hidden;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid #409eff;
}

/* 视频预览区域 */
.video-preview-section {
  background: #f5f7fa;
  border-radius: 12px;
  padding: 16px;
  max-height: 70vh;
  overflow-y: auto;
}

.video-player-wrapper {
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 12px;
  height: 350px;
}

.art-player-container {
  width: 100%;
  height: 100%;
}

.no-video {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
  gap: 12px;
  background: #1a1a1a;
}

.loading-video {
  height: 350px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
  gap: 12px;
}

.video-error {
  height: 350px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fef0f0;
  border-radius: 8px;
  gap: 12px;
}

.error-text {
  font-size: 16px;
  font-weight: 600;
  color: #f56c6c;
}

.error-subtext {
  font-size: 13px;
  color: #999;
}

.video-info-card {
  background: #fff;
  border-radius: 8px;
  padding: 14px;
}

.video-title-large {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  line-height: 1.5;
}

.video-author-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  margin-bottom: 12px;
}

.author-info-detail {
  flex: 1;
  color: #fff;
}

.author-name-large {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
}

.author-email {
  font-size: 12px;
  opacity: 0.9;
}

.video-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 10px;
  font-size: 13px;
  color: #666;
}

.video-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.video-meta .el-icon {
  font-size: 14px;
}

.video-description {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 10px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 6px;
  max-height: 80px;
  overflow-y: auto;
}

/* 举报信息区域 */
.report-info-section {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  max-height: 70vh;
  display: flex;
  flex-direction: column;
}

.reporter-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 12px;
  color: #fff;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.reporter-info {
  flex: 1;
}

.reporter-label {
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.reporter-name-large {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.reporter-email-large {
  font-size: 13px;
  opacity: 0.9;
}

.report-details-scroll {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.report-details-scroll::-webkit-scrollbar {
  width: 6px;
}

.report-details-scroll::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.report-details-scroll::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}

.report-details-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.detail-item.full-width {
  flex-direction: column;
  gap: 8px;
}

.detail-label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
  min-width: 70px;
  flex-shrink: 0;
}

.detail-value {
  font-size: 13px;
  color: #333;
  font-weight: 500;
  text-align: right;
  flex: 1;
  word-break: break-word;
}

.detail-value.time-value {
  font-size: 12px;
}

.detail-item.full-width .detail-value {
  text-align: left;
}

.description-box {
  background: #fff;
  padding: 10px;
  border-radius: 6px;
  line-height: 1.6;
  color: #666;
  font-weight: normal;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 100px;
  overflow-y: auto;
}

.description-box::-webkit-scrollbar {
  width: 4px;
}

.description-box::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 2px;
}

:deep(.el-dialog__body) {
  padding: 20px;
  max-height: calc(90vh - 140px);
  overflow: hidden;
}

:deep(.el-divider) {
  margin: 16px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 