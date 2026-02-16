<template>
  <div class="ai-moderation-container animate__animated animate__fadeIn animate__faster">
    <PageHeader 
      title="AI 智能审核" 
      :breadcrumb="[{ label: '管理后台', path: '/admin' }, { label: 'AI 审核' }]"
      class="animate__animated animate__fadeInDown animate__faster"
    >
      <template #actions>
        <div class="header-actions animate__animated animate__fadeInRight animate__faster">
          <el-button @click="helpVisible = true" type="info" plain>
            <el-icon><QuestionFilled /></el-icon> 参数说明
          </el-button>
          <el-select v-model="statusFilter" placeholder="审核状态" clearable @change="handleFilterChange" style="width: 140px;">
            <el-option label="全部状态" value="" />
            <el-option label="待审核" value="pending" />
            <el-option label="审核中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
          <el-select v-model="resultFilter" placeholder="审核结果" clearable @change="handleFilterChange" style="width: 140px;">
            <el-option label="全部结果" value="" />
            <el-option label="安全" value="safe" />
            <el-option label="不安全" value="unsafe" />
            <el-option label="不确定" value="uncertain" />
          </el-select>
          <el-button type="primary" @click="batchModerate" :disabled="selectedVideos.length === 0">
            <el-icon><Cpu /></el-icon> 批量审核 ({{ selectedVideos.length }})
          </el-button>
        </div>
      </template>
    </PageHeader>

    <StatsCards :stats="stats" class="animate__animated animate__fadeInUp animate__faster" />

    <!-- 审核列表 -->
    <div class="moderation-list animate__animated animate__fadeInUp animate__fast">
      <el-table 
        v-loading="loading" 
        :data="moderationList" 
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column label="视频" width="300">
          <template #default="{ row }">
            <div class="video-cell">
              <el-image 
                :src="row.video.thumbnail || '/placeholder.jpg'" 
                fit="cover" 
                class="video-thumb"
              >
                <template #error>
                  <div class="image-error">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
              <div class="video-info">
                <div class="video-title">{{ row.video.title }}</div>
                <div class="video-meta">
                  <span>{{ row.video.user?.username }}</span>
                  <span>{{ formatDate(row.video.created_at) }}</span>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="审核状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="审核结果" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.result" :type="getResultType(row.result)">
              {{ getResultText(row.result) }}
            </el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="置信度" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.confidence > 0">{{ (row.confidence * 100).toFixed(1) }}%</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="风险评分" width="280">
          <template #default="{ row }">
            <div class="risk-scores" v-if="row.status === 'completed'">
              <div class="score-item">
                <span class="score-label">中风险+</span>
                <el-progress 
                  :percentage="row.medium_score * 100" 
                  :color="getScoreColor(row.medium_score)"
                  :show-text="false"
                />
                <span class="score-value">{{ (row.medium_score * 100).toFixed(0) }}%</span>
              </div>
              <div class="score-item">
                <span class="score-label">高风险</span>
                <el-progress 
                  :percentage="row.high_score * 100" 
                  :color="getScoreColor(row.high_score)"
                  :show-text="false"
                />
                <span class="score-value">{{ (row.high_score * 100).toFixed(0) }}%</span>
              </div>
            </div>
            <span v-else class="text-muted">待审核</span>
          </template>
        </el-table-column>
        
        <el-table-column label="问题帧" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.flagged_frames?.length > 0" type="danger" size="small">
              {{ row.flagged_frames.length }} 帧
            </el-tag>
            <span v-else class="text-muted">无</span>
          </template>
        </el-table-column>
        
        <el-table-column label="审核时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="row.status === 'pending' || row.status === 'failed'" 
              type="primary" 
              size="small" 
              @click="moderateVideo(row)"
            >
              <el-icon><Cpu /></el-icon> 开始审核
            </el-button>
            <el-button 
              v-if="row.status === 'completed'" 
              type="info" 
              size="small" 
              @click="viewDetail(row)"
            >
              <el-icon><View /></el-icon> 查看详情
            </el-button>
            <el-button 
              v-if="row.status === 'processing'" 
              type="warning" 
              size="small" 
              disabled
            >
              <el-icon><Loading /></el-icon> 审核中
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="total > 0">
      <el-pagination 
        v-model:current-page="currentPage" 
        v-model:page-size="pageSize" 
        :page-sizes="[10, 20, 50, 100]" 
        layout="total, sizes, prev, pager, next, jumper" 
        :total="total" 
        @size-change="handleSizeChange" 
        @current-change="handleCurrentChange" 
      />
    </div>

    <ModerationConfigDialog
      v-model="configVisible"
      :title="configTitle"
      :config="moderationConfig"
      :loading="loading"
      @confirm="confirmModerate"
    />

    <ModerationDetailDialog
      v-model="detailVisible"
      :detail="currentDetail"
      :get-status-type="getStatusType"
      :get-status-text="getStatusText"
      :get-result-type="getResultType"
      :get-result-text="getResultText"
      :get-score-color="getScoreColor"
      :get-score-level="getScoreLevel"
      :format-date-time="formatDateTime"
      :format-time="formatTime"
      @submit-review="handleReviewAction('submit')"
      @revoke-review="handleReviewAction('revoke')"
      @re-moderate="handleReModerate"
    />

    <HelpDialog v-model="helpVisible" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { 
  Cpu, View, Picture, QuestionFilled
} from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
  getAIModerationList, 
  getAIModerationDetail,
  submitAIModeration, 
  batchAIModeration,
  submitAIReview,
  revokeAIReview
} from '@/api/admin';

// 子组件
import StatsCards from './components/StatsCards.vue';
import ModerationConfigDialog from './components/ModerationConfigDialog.vue';
import ModerationDetailDialog from './components/ModerationDetailDialog.vue';
import HelpDialog from './components/HelpDialog.vue';

// 数据
const loading = ref(false);
const moderationList = ref([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);
const statusFilter = ref('');
const resultFilter = ref('');
const selectedVideos = ref([]);
const detailVisible = ref(false);
const helpVisible = ref(false);
const configVisible = ref(false);
const configTitle = ref('AI 审核参数配置');
const currentDetail = ref(null);
const currentModerationVideo = ref(null);

const moderationConfig = reactive({
  threshold_level: 'medium',
  threshold: 0.6,
  fps: 1
});

// 统计数据
const stats = reactive({
  pending: 0,
  processing: 0,
  safe: 0,
  unsafe: 0
});

// 获取审核列表
const fetchModerationList = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    };
    if (statusFilter.value) params.status = statusFilter.value;
    if (resultFilter.value) params.result = resultFilter.value;

    const response = await getAIModerationList(params);

    moderationList.value = response.results || [];
    total.value = response.count || 0;
    
    // 更新统计数据
    if (response.stats) {
      Object.assign(stats, response.stats);
    }
  } catch (error) {
    console.error('获取审核列表失败:', error);
    ElMessage.error('获取审核列表失败');
  } finally {
    loading.value = false;
  }
};

// 审核单个视频
const moderateVideo = (row) => {
  currentModerationVideo.value = row;
  configTitle.value = 'AI 审核参数配置 - ' + row.video.title;
  configVisible.value = true;
};

// 批量审核
const batchModerate = () => {
  if (selectedVideos.value.length === 0) {
    ElMessage.warning('请先选择要审核的视频');
    return;
  }
  currentModerationVideo.value = null;
  configTitle.value = '批量审核参数配置 (' + selectedVideos.value.length + ' 个视频)';
  configVisible.value = true;
};

// 确认审核
const confirmModerate = async () => {
  try {
    loading.value = true;
    configVisible.value = false;
    
    if (currentModerationVideo.value) {
      await submitAIModeration({
        video_id: currentModerationVideo.value.video.id,
        ...moderationConfig
      });
    } else {
      const videoIds = selectedVideos.value.map(function(v) { return v.video.id; });
      await batchAIModeration({
        video_ids: videoIds,
        ...moderationConfig
      });
    }

    ElMessage.success('审核任务已提交');
    fetchModerationList();
  } catch (error) {
    console.error('提交审核任务失败:', error);
    ElMessage.error('提交审核任务失败');
  } finally {
    loading.value = false;
  }
};

// 查看详情
const viewDetail = async (row) => {
  try {
    console.log('请求审核详情，ID:', row.id);
    const response = await getAIModerationDetail(row.id);
    console.log('=== 审核详情响应 ===');
    console.log('完整响应:', response);
    console.log('视频信息:', response.video);
    if (response.video) {
      console.log('视频 ID:', response.video.id);
      console.log('视频标题:', response.video.title);
      console.log('视频用户:', response.video.user);
      console.log('视频创建时间:', response.video.created_at);
    }
    console.log('==================');
    currentDetail.value = response;
    detailVisible.value = true;
  } catch (error) {
    console.error('获取审核详情失败:', error);
    ElMessage.error('获取审核详情失败');
  }
};

// 提交人工审核/撤销审核
const handleReviewAction = async (action) => {
  try {
    const isSubmit = action === 'submit';
    const title = isSubmit ? '提交人工审核' : '撤销审核';
    const message = isSubmit ? '确认将该 AI 审核结果提交至人工审核流程？' : '确认撤销该审核结果并重新变为待处理状态？';
    
    await ElMessageBox.confirm(message, title, { type: 'warning' });
    
    loading.value = true;
    if (isSubmit) {
      await submitAIReview({ moderation_id: currentDetail.value.id });
      ElMessage.success('已成功提交至人工审核');
    } else {
      await revokeAIReview({ moderation_id: currentDetail.value.id });
      ElMessage.success('已成功撤销审核结果');
    }
    
    detailVisible.value = false;
    fetchModerationList();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败');
    }
  } finally {
    loading.value = false;
  }
};

// 重新审核
const handleReModerate = () => {
  const row = {
    id: currentDetail.value.id,
    video: currentDetail.value.video
  };
  detailVisible.value = false;
  moderateVideo(row);
};

// 选择变化
const handleSelectionChange = (selection) => {
  selectedVideos.value = selection.filter(
    item => item.status === 'pending' || item.status === 'failed'
  );
};

// 筛选变化
const handleFilterChange = () => {
  currentPage.value = 1;
  fetchModerationList();
};

// 分页
const handleSizeChange = () => {
  fetchModerationList();
};

const handleCurrentChange = () => {
  fetchModerationList();
};

// 工具函数
const getStatusType = (status) => {
  const map = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  };
  return map[status] || 'info';
};

const getStatusText = (status) => {
  const map = {
    pending: '待审核',
    processing: '审核中',
    completed: '已完成',
    failed: '失败'
  };
  return map[status] || '未知';
};

const getResultType = (result) => {
  const map = {
    safe: 'success',
    unsafe: 'danger',
    uncertain: 'warning'
  };
  return map[result] || 'info';
};

const getResultText = (result) => {
  const map = {
    safe: '安全',
    unsafe: '不安全',
    uncertain: '不确定'
  };
  return map[result] || '未知';
};

const getScoreColor = (score) => {
  if (score < 0.3) return '#67c23a';
  if (score < 0.6) return '#e6a23c';
  return '#f56c6c';
};

const getScoreLevel = (score) => {
  if (score < 0.3) return 'low';
  if (score < 0.6) return 'medium';
  return 'high';
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${month}-${day}`;
};

const formatDateTime = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
};

const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
};

onMounted(() => {
  fetchModerationList();
});
</script>

<style scoped>
.ai-moderation-container {
  padding: 20px;
  min-height: 100%;
  position: relative;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 列表容器 */
.moderation-list {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* 视频单元格 */
.video-cell {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 8px 0;
}

.video-thumb {
  width: 160px;
  height: 90px;
  border-radius: 6px;
  flex-shrink: 0;
  cursor: pointer;
  transition: opacity 0.3s;
}

.video-thumb:hover {
  opacity: 0.8;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #f5f5f5;
  color: #ccc;
  font-size: 24px;
}

.video-info {
  flex: 1;
  min-width: 0;
}

.video-title {
  font-size: 14px;
  font-weight: 500;
  color: #18191c;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.video-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #9499a0;
}

.text-muted {
  color: #9499a0;
}

/* 风险评分列 */
.risk-scores {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px 0;
}

.score-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.score-label {
  font-size: 12px;
  color: #61666d;
}

.score-item .el-progress {
  width: 180px;
}

.score-value {
  font-size: 12px;
  color: #61666d;
  font-weight: 500;
  margin-top: 2px;
}

/* 分页容器 */
.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  background: #fff;
  padding: 12px;
  border-radius: 8px;
}
</style>
