<template>
  <div class="system-logs">
    <PageHeader 
      title="系统日志" 
      :breadcrumb="[
        { label: '超级管理员', path: '/superadmin/monitor' },
        { label: '系统日志' }
      ]"
    >
      <template #actions>
        <el-button type="danger" @click="showClearDialog">
          <el-icon><Delete /></el-icon>
          清理旧日志
        </el-button>
        <el-button type="primary" @click="loadLogs">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </template>
    </PageHeader>

    <div class="content-wrapper">
      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon today">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">今日日志</div>
              <div class="stat-value">{{ statistics.today_count || 0 }}</div>
            </div>
          </div>
        </el-col>

        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon week">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">本周日志</div>
              <div class="stat-value">{{ statistics.week_count || 0 }}</div>
            </div>
          </div>
        </el-col>

        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon month">
              <el-icon><DataLine /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">本月日志</div>
              <div class="stat-value">{{ statistics.month_count || 0 }}</div>
            </div>
          </div>
        </el-col>

        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">总日志数</div>
              <div class="stat-value">{{ total }}</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 筛选区域 -->
      <div class="filter-section">
        <el-input
          v-model="searchQuery"
          placeholder="搜索操作者、操作、描述"
          style="width: 300px;"
          clearable
          @clear="loadLogs"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select v-model="logTypeFilter" placeholder="日志类型" style="width: 150px;" clearable @change="loadLogs">
          <el-option label="全部" value="" />
          <el-option label="登录" value="login" />
          <el-option label="登出" value="logout" />
          <el-option label="创建用户" value="user_create" />
          <el-option label="更新用户" value="user_update" />
          <el-option label="删除用户" value="user_delete" />
          <el-option label="创建管理员" value="admin_create" />
          <el-option label="更新管理员" value="admin_update" />
          <el-option label="删除管理员" value="admin_delete" />
          <el-option label="视频审核" value="video_review" />
          <el-option label="删除视频" value="video_delete" />
          <el-option label="删除评论" value="comment_delete" />
          <el-option label="处理举报" value="report_handle" />
          <el-option label="系统配置" value="system_config" />
          <el-option label="权限变更" value="permission_change" />
        </el-select>

        <el-select v-model="levelFilter" placeholder="日志级别" style="width: 120px;" clearable @change="loadLogs">
          <el-option label="全部" value="" />
          <el-option label="信息" value="info" />
          <el-option label="警告" value="warning" />
          <el-option label="错误" value="error" />
          <el-option label="严重" value="critical" />
        </el-select>

        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 240px;"
          @change="loadLogs"
        />

        <el-button type="primary" @click="loadLogs">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>

      <!-- 日志列表 -->
      <el-table 
        v-loading="loading"
        :data="logList" 
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
      >
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column label="级别" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)" size="small">
              {{ row.level_display }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.log_type_display }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="operator_username" label="操作者" width="120" />
        
        <el-table-column prop="operator_ip" label="IP 地址" width="140" />

        <el-table-column prop="module" label="模块" width="120" />

        <el-table-column prop="action" label="操作" min-width="150" show-overflow-tooltip />

        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

        <el-table-column label="目标" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.target_name">{{ row.target_name }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadLogs"
          @current-change="loadLogs"
        />
      </div>
    </div>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="日志详情"
      width="700px"
    >
      <el-descriptions :column="2" border v-if="currentLog">
        <el-descriptions-item label="ID">{{ currentLog.id }}</el-descriptions-item>
        <el-descriptions-item label="级别">
          <el-tag :type="getLevelType(currentLog.level)">{{ currentLog.level_display }}</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="类型">{{ currentLog.log_type_display }}</el-descriptions-item>
        <el-descriptions-item label="模块">{{ currentLog.module }}</el-descriptions-item>
        
        <el-descriptions-item label="操作者">{{ currentLog.operator_username }}</el-descriptions-item>
        <el-descriptions-item label="IP 地址">{{ currentLog.operator_ip || '-' }}</el-descriptions-item>
        
        <el-descriptions-item label="操作" :span="2">{{ currentLog.action }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentLog.description || '-' }}</el-descriptions-item>
        
        <el-descriptions-item label="目标类型">{{ currentLog.target_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="目标 ID">{{ currentLog.target_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="目标名称" :span="2">{{ currentLog.target_name || '-' }}</el-descriptions-item>
        
        <el-descriptions-item label="请求方法">{{ currentLog.request_method || '-' }}</el-descriptions-item>
        <el-descriptions-item label="响应代码">{{ currentLog.response_code || '-' }}</el-descriptions-item>
        <el-descriptions-item label="请求路径" :span="2">{{ currentLog.request_path || '-' }}</el-descriptions-item>
        
        <el-descriptions-item label="执行时长">
          {{ currentLog.duration ? `${currentLog.duration.toFixed(3)}s` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="时间">{{ formatDateTime(currentLog.created_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 清理日志对话框 -->
    <el-dialog
      v-model="clearDialogVisible"
      title="清理旧日志"
      width="400px"
    >
      <el-form :model="clearForm" label-width="120px">
        <el-form-item label="保留天数">
          <el-input-number v-model="clearForm.days" :min="7" :max="365" />
          <div class="form-tip">将删除 {{ clearForm.days }} 天前的所有日志</div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="clearDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="clearOldLogs" :loading="clearing">
          确定清理
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
  Search, Refresh, Delete, Calendar, TrendCharts, DataLine, Document
} from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import service from '@/api/user';

const loading = ref(false);
const clearing = ref(false);
const searchQuery = ref('');
const logTypeFilter = ref('');
const levelFilter = ref('');
const dateRange = ref([]);
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);
const logList = ref([]);
const statistics = ref({});

const detailVisible = ref(false);
const currentLog = ref(null);

const clearDialogVisible = ref(false);
const clearForm = ref({
  days: 90
});

const loadLogs = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value,
      log_type: logTypeFilter.value,
      level: levelFilter.value
    };

    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0];
      params.end_date = dateRange.value[1];
    }

    const response = await service({
      url: '/users/logs/',
      method: 'get',
      params
    });

    logList.value = response.results || [];
    total.value = response.count || 0;
  } catch (error) {
    console.error('加载日志失败:', error);
    ElMessage.error('加载日志失败');
  } finally {
    loading.value = false;
  }
};

const loadStatistics = async () => {
  try {
    const response = await service({
      url: '/users/logs/statistics/',
      method: 'get'
    });
    statistics.value = response;
  } catch (error) {
    console.error('加载统计信息失败:', error);
  }
};

const showDetail = (row) => {
  currentLog.value = row;
  detailVisible.value = true;
};

const showClearDialog = () => {
  clearDialogVisible.value = true;
};

const clearOldLogs = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要清理 ${clearForm.value.days} 天前的所有日志吗？此操作不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    clearing.value = true;
    const response = await service({
      url: '/users/logs/clear_old_logs/',
      method: 'post',
      data: {
        days: clearForm.value.days
      }
    });

    ElMessage.success(response.message);
    clearDialogVisible.value = false;
    loadLogs();
    loadStatistics();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清理日志失败:', error);
      ElMessage.error('清理日志失败');
    }
  } finally {
    clearing.value = false;
  }
};

const getLevelType = (level) => {
  const types = {
    'info': 'info',
    'warning': 'warning',
    'error': 'danger',
    'critical': 'danger'
  };
  return types[level] || 'info';
};

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

onMounted(() => {
  loadLogs();
  loadStatistics();
});
</script>

<style scoped>
.system-logs {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 70px);
}

.content-wrapper {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s;
}

.stat-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
  flex-shrink: 0;
}

.stat-icon.today {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.week {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.month {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.total {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.filter-section {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.text-muted {
  color: #909399;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
