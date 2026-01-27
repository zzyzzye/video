<template>
  <div class="ai-moderation-container">
    <PageHeader 
      title="AI 智能审核" 
      :breadcrumb="[{ label: '管理后台', path: '/admin' }, { label: 'AI 审核' }]"
    >
      <template #actions>
        <div class="header-actions">
          <el-select v-model="statusFilter" placeholder="审核状态" @change="handleFilterChange">
            <el-option label="全部" value="" />
            <el-option label="待审核" value="pending" />
            <el-option label="审核中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
          <el-select v-model="resultFilter" placeholder="审核结果" @change="handleFilterChange">
            <el-option label="全部" value="" />
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

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon pending">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.pending }}</div>
          <div class="stat-label">待审核</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon processing">
          <el-icon><Loading /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.processing }}</div>
          <div class="stat-label">审核中</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon safe">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.safe }}</div>
          <div class="stat-label">安全内容</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon unsafe">
          <el-icon><CircleClose /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.unsafe }}</div>
          <div class="stat-label">不安全内容</div>
        </div>
      </div>
    </div>

    <!-- 审核列表 -->
    <div class="moderation-list">
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
                <span class="score-label">NSFW</span>
                <el-progress 
                  :percentage="row.nsfw_score * 100" 
                  :color="getScoreColor(row.nsfw_score)"
                  :show-text="false"
                />
                <span class="score-value">{{ (row.nsfw_score * 100).toFixed(0) }}</span>
              </div>
              <div class="score-item">
                <span class="score-label">暴力</span>
                <el-progress 
                  :percentage="row.violence_score * 100" 
                  :color="getScoreColor(row.violence_score)"
                  :show-text="false"
                />
                <span class="score-value">{{ (row.violence_score * 100).toFixed(0) }}</span>
              </div>
              <div class="score-item">
                <span class="score-label">敏感</span>
                <el-progress 
                  :percentage="row.sensitive_score * 100" 
                  :color="getScoreColor(row.sensitive_score)"
                  :show-text="false"
                />
                <span class="score-value">{{ (row.sensitive_score * 100).toFixed(0) }}</span>
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

    <!-- 详情对话框 -->
    <el-dialog 
      v-model="detailVisible" 
      title="AI 审核详情" 
      width="900px" 
      destroy-on-close
    >
      <div v-if="currentDetail" class="detail-content">
        <div class="detail-section">
          <h3>视频信息</h3>
          <div class="video-detail">
            <el-image 
              :src="currentDetail.video.thumbnail" 
              fit="cover" 
              style="width: 200px; height: 112px; border-radius: 8px;"
            />
            <div class="video-detail-info">
              <h4>{{ currentDetail.video.title }}</h4>
              <p>上传者: {{ currentDetail.video.user?.username }}</p>
              <p>上传时间: {{ formatDateTime(currentDetail.video.created_at) }}</p>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="detail-section">
          <h3>审核结果</h3>
          <div class="result-summary">
            <div class="result-item">
              <span class="label">审核状态:</span>
              <el-tag :type="getStatusType(currentDetail.status)">
                {{ getStatusText(currentDetail.status) }}
              </el-tag>
            </div>
            <div class="result-item">
              <span class="label">审核结果:</span>
              <el-tag :type="getResultType(currentDetail.result)">
                {{ getResultText(currentDetail.result) }}
              </el-tag>
            </div>
            <div class="result-item">
              <span class="label">置信度:</span>
              <span class="value">{{ (currentDetail.confidence * 100).toFixed(2) }}%</span>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="detail-section">
          <h3>风险评分</h3>
          <div class="risk-detail">
            <div class="risk-item">
              <div class="risk-header">
                <span class="risk-name">NSFW 内容</span>
                <span class="risk-score" :class="getScoreLevel(currentDetail.nsfw_score)">
                  {{ (currentDetail.nsfw_score * 100).toFixed(1) }}
                </span>
              </div>
              <el-progress 
                :percentage="currentDetail.nsfw_score * 100" 
                :color="getScoreColor(currentDetail.nsfw_score)"
              />
            </div>
            <div class="risk-item">
              <div class="risk-header">
                <span class="risk-name">暴力内容</span>
                <span class="risk-score" :class="getScoreLevel(currentDetail.violence_score)">
                  {{ (currentDetail.violence_score * 100).toFixed(1) }}
                </span>
              </div>
              <el-progress 
                :percentage="currentDetail.violence_score * 100" 
                :color="getScoreColor(currentDetail.violence_score)"
              />
            </div>
            <div class="risk-item">
              <div class="risk-header">
                <span class="risk-name">敏感内容</span>
                <span class="risk-score" :class="getScoreLevel(currentDetail.sensitive_score)">
                  {{ (currentDetail.sensitive_score * 100).toFixed(1) }}
                </span>
              </div>
              <el-progress 
                :percentage="currentDetail.sensitive_score * 100" 
                :color="getScoreColor(currentDetail.sensitive_score)"
              />
            </div>
          </div>
        </div>

        <el-divider v-if="currentDetail.flagged_frames?.length > 0" />

        <div class="detail-section" v-if="currentDetail.flagged_frames?.length > 0">
          <h3>问题帧 ({{ currentDetail.flagged_frames.length }})</h3>
          <div class="flagged-frames">
            <div 
              v-for="(frame, index) in currentDetail.flagged_frames" 
              :key="index" 
              class="frame-item"
            >
              <div class="frame-time">{{ formatTime(frame.timestamp) }}</div>
              <div class="frame-reason">{{ frame.reason || '检测到问题内容' }}</div>
            </div>
          </div>
        </div>

        <el-divider v-if="currentDetail.error_message" />

        <div class="detail-section" v-if="currentDetail.error_message">
          <h3>错误信息</h3>
          <el-alert type="error" :closable="false">
            {{ currentDetail.error_message }}
          </el-alert>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { 
  Clock, Loading, CircleCheck, CircleClose, Cpu, View, Picture 
} from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import service from '@/api/user';

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
const currentDetail = ref(null);

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

    // TODO: 替换为实际的 API 接口
    const response = await service({
      url: '/ai/moderation/list/',
      method: 'get',
      params
    });

    moderationList.value = response.results || [];
    total.value = response.count || 0;
    
    // 更新统计数据
    if (response.stats) {
      Object.assign(stats, response.stats);
    }
  } catch (error) {
    console.error('获取审核列表失败:', error);
    // 模拟数据
    moderationList.value = generateMockData();
    total.value = moderationList.value.length;
  } finally {
    loading.value = false;
  }
};

// 生成模拟数据
const generateMockData = () => {
  return Array.from({ length: 10 }, (_, i) => ({
    id: i + 1,
    video: {
      id: i + 1,
      title: `测试视频 ${i + 1}`,
      thumbnail: '',
      user: { username: '测试用户' },
      created_at: new Date().toISOString()
    },
    status: ['pending', 'processing', 'completed', 'failed'][Math.floor(Math.random() * 4)],
    result: ['safe', 'unsafe', 'uncertain'][Math.floor(Math.random() * 3)],
    confidence: Math.random(),
    nsfw_score: Math.random() * 0.3,
    violence_score: Math.random() * 0.2,
    sensitive_score: Math.random() * 0.25,
    flagged_frames: Math.random() > 0.7 ? [
      { timestamp: 10.5, reason: '检测到敏感内容' },
      { timestamp: 25.3, reason: '检测到不适宜内容' }
    ] : [],
    error_message: '',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }));
};

// 审核单个视频
const moderateVideo = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认对视频「${row.video.title}」进行 AI 审核？`,
      '确认审核',
      { type: 'warning' }
    );

    loading.value = true;
    await service({
      url: `/ai/moderate/video/${row.video.id}/`,
      method: 'post'
    });

    ElMessage.success('审核任务已提交，请稍后查看结果');
    fetchModerationList();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('提交审核任务失败');
    }
  } finally {
    loading.value = false;
  }
};

// 批量审核
const batchModerate = async () => {
  try {
    await ElMessageBox.confirm(
      `确认对选中的 ${selectedVideos.value.length} 个视频进行批量审核？`,
      '批量审核',
      { type: 'warning' }
    );

    loading.value = true;
    const videoIds = selectedVideos.value.map(v => v.video.id);
    
    await service({
      url: '/ai/moderate/batch/',
      method: 'post',
      data: { video_ids: videoIds }
    });

    ElMessage.success(`已提交 ${videoIds.length} 个审核任务`);
    selectedVideos.value = [];
    fetchModerationList();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量审核失败');
    }
  } finally {
    loading.value = false;
  }
};

// 查看详情
const viewDetail = (row) => {
  currentDetail.value = row;
  detailVisible.value = true;
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
  return `${date.getMonth() + 1}-${date.getDate()}`;
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
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.stat-icon.pending {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.stat-icon.processing {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
}

.stat-icon.safe {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: #fff;
}

.stat-icon.unsafe {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: #fff;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #18191c;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #9499a0;
}

/* 列表 */
.moderation-list {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.video-cell {
  display: flex;
  gap: 12px;
  align-items: center;
}

.video-thumb {
  width: 120px;
  height: 68px;
  border-radius: 6px;
  flex-shrink: 0;
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
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #9499a0;
}

.text-muted {
  color: #9499a0;
}

/* 风险评分 */
.risk-scores {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-label {
  width: 40px;
  font-size: 12px;
  color: #61666d;
}

.score-item .el-progress {
  flex: 1;
}

.score-value {
  width: 30px;
  text-align: right;
  font-size: 12px;
  color: #61666d;
  font-weight: 500;
}

/* 分页 */
.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  background: #fff;
  padding: 12px;
  border-radius: 8px;
}

/* 详情对话框 */
.detail-content {
  padding: 10px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #18191c;
  margin: 0 0 16px 0;
}

.video-detail {
  display: flex;
  gap: 16px;
}

.video-detail-info h4 {
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 12px 0;
}

.video-detail-info p {
  font-size: 14px;
  color: #61666d;
  margin: 6px 0;
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.result-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-item .label {
  font-size: 13px;
  color: #9499a0;
}

.result-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #18191c;
}

.risk-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.risk-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.risk-name {
  font-size: 14px;
  color: #61666d;
}

.risk-score {
  font-size: 18px;
  font-weight: 600;
}

.risk-score.low {
  color: #67c23a;
}

.risk-score.medium {
  color: #e6a23c;
}

.risk-score.high {
  color: #f56c6c;
}

.flagged-frames {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.frame-item {
  padding: 12px;
  background: #f6f7f8;
  border-radius: 6px;
  border-left: 3px solid #f56c6c;
}

.frame-time {
  font-size: 14px;
  font-weight: 600;
  color: #18191c;
  margin-bottom: 6px;
}

.frame-reason {
  font-size: 13px;
  color: #61666d;
}
</style>
