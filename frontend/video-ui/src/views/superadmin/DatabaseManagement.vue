<template>
  <div class="database-management animate__animated animate__fadeIn animate__faster">
    <PageHeader 
      title="数据库管理" 
      :breadcrumb="[
        { label: '超级管理员', path: '/superadmin/monitor' },
        { label: '数据库管理' }
      ]"
      class="animate__animated animate__fadeInDown animate__faster"
    >
      <template #actions>
        <el-button type="success" @click="backupDatabase" :loading="backing" class="animate__animated animate__fadeInRight animate__faster">
          <el-icon><Download /></el-icon>
          备份数据库
        </el-button>
        <el-button type="primary" @click="loadDatabaseInfo" class="animate__animated animate__fadeInRight animate__faster">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </template>
    </PageHeader>

    <div class="content-wrapper">
      <!-- 数据库概览 -->
      <el-row :gutter="20" class="stats-row animate__animated animate__fadeInUp animate__fast">
        <el-col :span="6">
          <div class="stat-card animate__animated animate__zoomIn animate__faster" style="animation-delay: 0.05s">
            <div class="stat-icon database">
              <el-icon><Coin /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">数据库大小</div>
              <div class="stat-value">{{ dbInfo.size_mb }} MB</div>
            </div>
          </div>
        </el-col>

        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon tables">
              <el-icon><Grid /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">数据表数量</div>
              <div class="stat-value">{{ dbInfo.table_count }}</div>
            </div>
          </div>
        </el-col>

        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon connections">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">活动连接</div>
              <div class="stat-value">{{ connectionCount }}</div>
            </div>
          </div>
        </el-col>

        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon backups">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">备份文件</div>
              <div class="stat-value">{{ backupList.length }}</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 标签页 -->
      <el-tabs v-model="activeTab" class="tabs-container">
        <!-- 数据表 -->
        <el-tab-pane label="数据表" name="tables">
          <el-alert
            title="数据表维护说明"
            type="info"
            :closable="false"
            style="margin-bottom: 20px;"
          >
            <template #default>
              <div style="line-height: 2;">
                <p style="margin-bottom: 8px;">
                  <strong style="color: #409EFF;">优化（OPTIMIZE）：</strong>
                  整理表碎片，回收未使用空间，重新组织数据。
                  <span style="color: #67C23A;">可减少 20-50% 磁盘占用，提升 10-30% 查询速度。</span>
                </p>
                <p style="margin-bottom: 8px; padding-left: 20px; color: #606266; font-size: 13px;">
                  适用场景：频繁增删改的表（如 videos_video、users_user、videos_comment）
                </p>
                
                <p style="margin-bottom: 8px;">
                  <strong style="color: #409EFF;">分析（ANALYZE）：</strong>
                  更新表的统计信息和键值分布，帮助 MySQL 优化器选择更好的查询计划。
                  <span style="color: #67C23A;">提升复杂查询性能，不锁表。</span>
                </p>
                <p style="margin-bottom: 8px; padding-left: 20px; color: #606266; font-size: 13px;">
                  适用场景：数据量大幅变化后、添加新索引后、查询性能下降时
                </p>
                
                <p style="margin-bottom: 8px;">
                  <strong style="color: #E6A23C;">修复（REPAIR）：</strong>
                  修复损坏的表和索引。
                  <span style="color: #F56C6C;">会锁表，仅在表出现错误时使用！</span>
                </p>
                <p style="margin-bottom: 8px; padding-left: 20px; color: #606266; font-size: 13px;">
                  适用场景：服务器异常关机、磁盘错误、表损坏报错
                </p>
                
                <p style="color: #E6A23C; margin-top: 15px; padding: 10px; background: #FDF6EC; border-radius: 4px;">
                  <strong>维护建议：</strong>
                  每周对活跃表执行"分析" | 每月对大表执行"优化" | 出错时才使用"修复"
                </p>
              </div>
            </template>
          </el-alert>

          <div class="filter-section">
            <el-input
              v-model="tableSearch"
              placeholder="搜索表名"
              style="width: 300px;"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            
            <div class="batch-actions" v-if="selectedTables.length > 0">
              <el-button type="primary" size="small" @click="batchOptimize">
                批量优化 ({{ selectedTables.length }})
              </el-button>
              <el-button type="info" size="small" @click="batchAnalyze">
                批量分析 ({{ selectedTables.length }})
              </el-button>
            </div>
          </div>

          <el-table 
            v-loading="loading"
            :data="filteredTables" 
            style="width: 100%"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="name" label="表名" min-width="200">
              <template #default="{ row }">
                <el-button 
                  type="text" 
                  @click="openTableDetail(row.name)"
                  style="font-weight: 500; color: #409EFF;"
                >
                  {{ row.name }}
                </el-button>
              </template>
            </el-table-column>
            <el-table-column prop="rows" label="行数" width="120" align="right">
              <template #default="{ row }">
                {{ formatNumber(row.rows) }}
              </template>
            </el-table-column>
            <el-table-column prop="size_mb" label="大小 (MB)" width="120" align="right">
              <template #default="{ row }">
                {{ row.size_mb.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="data_mb" label="数据 (MB)" width="120" align="right">
              <template #default="{ row }">
                {{ row.data_mb.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="index_mb" label="索引 (MB)" width="120" align="right">
              <template #default="{ row }">
                {{ row.index_mb.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="engine" label="引擎" width="100" />
            <el-table-column label="操作" width="350" fixed="right">
              <template #default="{ row }">
                <el-tooltip placement="top">
                  <template #content>
                    <div style="max-width: 250px;">
                      整理碎片，回收空间<br/>
                      可减少 20-50% 磁盘占用<br/>
                      提升 10-30% 查询速度
                    </div>
                  </template>
                  <el-button type="primary" size="small" @click="optimizeTable(row.name)">
                    优化
                  </el-button>
                </el-tooltip>
                
                <el-tooltip placement="top">
                  <template #content>
                    <div style="max-width: 250px;">
                      更新统计信息<br/>
                      帮助优化器选择更好的查询计划<br/>
                      提升复杂查询性能
                    </div>
                  </template>
                  <el-button type="info" size="small" @click="analyzeTable(row.name)">
                    分析
                  </el-button>
                </el-tooltip>
                
                <el-tooltip placement="top">
                  <template #content>
                    <div style="max-width: 250px;">
                      修复损坏的表和索引<br/>
                      <span style="color: #F56C6C;">⚠️ 会锁表，慎用！</span><br/>
                      仅在表出现错误时使用
                    </div>
                  </template>
                  <el-button type="warning" size="small" @click="repairTable(row.name)">
                    修复
                  </el-button>
                </el-tooltip>
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="暂无数据表" />
            </template>
          </el-table>
        </el-tab-pane>

        <!-- 备份管理 -->
        <el-tab-pane label="备份管理" name="backups">
          <div class="backup-actions">
            <el-button type="success" @click="backupDatabase" :loading="backing">
              <el-icon><Download /></el-icon>
              创建备份
            </el-button>
            <el-button type="primary" @click="loadBackups">
              <el-icon><Refresh /></el-icon>
              刷新列表
            </el-button>
          </div>

          <el-table 
            v-loading="loadingBackups"
            :data="backupList" 
            style="width: 100%"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
          >
            <el-table-column prop="filename" label="文件名" min-width="300" />
            <el-table-column prop="size_mb" label="大小 (MB)" width="120" align="right" />
            <el-table-column prop="created_at" label="创建时间" width="200">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-popconfirm
                  title="确定要恢复此备份吗？这将覆盖当前数据库！"
                  @confirm="restoreBackup(row.filename)"
                >
                  <template #reference>
                    <el-button type="warning" size="small">
                      恢复
                    </el-button>
                  </template>
                </el-popconfirm>
                <el-button type="info" size="small" @click="downloadBackup(row)">
                  下载
                </el-button>
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="暂无备份文件">
                <el-button type="primary" @click="backupDatabase">创建第一个备份</el-button>
              </el-empty>
            </template>
          </el-table>
        </el-tab-pane>

        <!-- 数据库状态 -->
        <el-tab-pane label="数据库状态" name="status">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="数据库引擎">{{ dbInfo.engine }}</el-descriptions-item>
            <el-descriptions-item label="数据库名称">{{ dbInfo.name }}</el-descriptions-item>
            <el-descriptions-item label="主机地址">{{ dbInfo.host }}</el-descriptions-item>
            <el-descriptions-item label="端口">{{ dbInfo.port }}</el-descriptions-item>
            <el-descriptions-item label="版本" :span="2">{{ dbInfo.version }}</el-descriptions-item>
          </el-descriptions>

          <div class="status-section" v-if="dbStatus.status">
            <h3>关键指标</h3>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="运行时间">
                {{ formatUptime(dbStatus.status.uptime) }}
              </el-descriptions-item>
              <el-descriptions-item label="当前连接数">
                {{ dbStatus.status.threads_connected }}
              </el-descriptions-item>
              <el-descriptions-item label="运行中线程">
                {{ dbStatus.status.threads_running }}
              </el-descriptions-item>
              <el-descriptions-item label="总查询数">
                {{ formatNumber(dbStatus.status.queries) }}
              </el-descriptions-item>
              <el-descriptions-item label="慢查询数">
                {{ formatNumber(dbStatus.status.slow_queries) }}
              </el-descriptions-item>
              <el-descriptions-item label="总连接数">
                {{ formatNumber(dbStatus.status.connections) }}
              </el-descriptions-item>
              <el-descriptions-item label="接收字节">
                {{ formatBytes(dbStatus.status.bytes_received) }}
              </el-descriptions-item>
              <el-descriptions-item label="发送字节">
                {{ formatBytes(dbStatus.status.bytes_sent) }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-tab-pane>

        <!-- 连接管理 -->
        <el-tab-pane label="连接管理" name="connections">
          <div class="connection-actions">
            <el-button type="primary" @click="loadConnections">
              <el-icon><Refresh /></el-icon>
              刷新连接
            </el-button>
          </div>

          <el-table 
            v-loading="loadingConnections"
            :data="connections" 
            style="width: 100%"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
          >
            <el-table-column prop="Id" label="ID" width="80" />
            <el-table-column prop="User" label="用户" width="120" />
            <el-table-column prop="Host" label="主机" width="150" />
            <el-table-column prop="db" label="数据库" width="150" />
            <el-table-column prop="Command" label="命令" width="100" />
            <el-table-column prop="Time" label="时间(秒)" width="100" />
            <el-table-column prop="State" label="状态" min-width="150" show-overflow-tooltip />
            <el-table-column prop="Info" label="信息" min-width="200" show-overflow-tooltip />
            <template #empty>
              <el-empty description="暂无活动连接" />
            </template>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 表详情对话框 -->
    <el-dialog
      v-model="tableDetailVisible"
      :width="dialogWidth"
      :top="isFullscreen ? '0' : '5vh'"
      :fullscreen="isFullscreen"
      destroy-on-close
      :class="{ 'fullscreen-dialog': isFullscreen }"
    >
      <template #header>
        <div class="dialog-header">
          <span class="dialog-title">表详情 - {{ currentTableName }}</span>
          <div class="dialog-actions">
            <el-button-group size="small" class="size-buttons">
              <el-tooltip content="小窗口 (70%)" placement="bottom">
                <el-button 
                  @click="setDialogSize('70%')" 
                  :type="dialogWidth === '70%' && !isFullscreen ? 'primary' : ''"
                >
                  小
                </el-button>
              </el-tooltip>
              <el-tooltip content="中窗口 (85%)" placement="bottom">
                <el-button 
                  @click="setDialogSize('85%')" 
                  :type="dialogWidth === '85%' && !isFullscreen ? 'primary' : ''"
                >
                  中
                </el-button>
              </el-tooltip>
              <el-tooltip content="大窗口 (95%)" placement="bottom">
                <el-button 
                  @click="setDialogSize('95%')" 
                  :type="dialogWidth === '95%' && !isFullscreen ? 'primary' : ''"
                >
                  大
                </el-button>
              </el-tooltip>
            </el-button-group>
            <el-divider direction="vertical" />
            <el-tooltip :content="isFullscreen ? '退出全屏 (ESC / F11)' : '全屏 (F11)'" placement="bottom">
              <el-button 
                size="small" 
                @click="toggleFullscreen"
                :type="isFullscreen ? 'primary' : ''"
              >
                <el-icon>
                  <FullScreen v-if="!isFullscreen" />
                  <Close v-else />
                </el-icon>
                {{ isFullscreen ? '退出全屏' : '全屏' }}
              </el-button>
            </el-tooltip>
          </div>
        </div>
      </template>
      <el-tabs v-model="detailTab" v-loading="loadingDetail">
        <!-- 表结构 -->
        <el-tab-pane label="表结构" name="structure">
          <el-table 
            :data="tableStructure" 
            style="width: 100%"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
            :max-height="isFullscreen ? 'calc(100vh - 280px)' : '500'"
          >
            <el-table-column prop="Field" label="字段名" width="200" />
            <el-table-column prop="Type" label="类型" width="150" />
            <el-table-column prop="Null" label="允许NULL" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.Null === 'YES' ? 'success' : 'danger'" size="small">
                  {{ row.Null }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="Key" label="键" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.Key === 'PRI'" type="danger" size="small">主键</el-tag>
                <el-tag v-else-if="row.Key === 'UNI'" type="warning" size="small">唯一</el-tag>
                <el-tag v-else-if="row.Key === 'MUL'" type="info" size="small">索引</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="Default" label="默认值" width="150" show-overflow-tooltip />
            <el-table-column prop="Extra" label="额外" min-width="150" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>

        <!-- 索引 -->
        <el-tab-pane label="索引" name="indexes">
          <el-table 
            :data="tableIndexes" 
            style="width: 100%"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
            :max-height="isFullscreen ? 'calc(100vh - 280px)' : '500'"
          >
            <el-table-column prop="Key_name" label="索引名" width="200" />
            <el-table-column prop="Column_name" label="列名" width="200" />
            <el-table-column prop="Index_type" label="索引类型" width="120" />
            <el-table-column prop="Non_unique" label="唯一性" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.Non_unique === 0 ? 'success' : 'info'" size="small">
                  {{ row.Non_unique === 0 ? '唯一' : '非唯一' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="Cardinality" label="基数" width="120" align="right" />
            <el-table-column prop="Seq_in_index" label="序列" width="80" align="center" />
          </el-table>
        </el-tab-pane>

        <!-- 数据预览 -->
        <el-tab-pane label="数据预览" name="data">
          <div class="data-preview-header">
            <span>显示前 {{ tableData.length }} 条记录</span>
            <el-button type="primary" size="small" @click="loadTableData(currentTableName)">
              刷新数据
            </el-button>
          </div>
          <el-table 
            :data="tableData" 
            style="width: 100%"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
            :max-height="isFullscreen ? 'calc(100vh - 330px)' : '500'"
            border
          >
            <el-table-column 
              v-for="col in tableColumns" 
              :key="col"
              :prop="col" 
              :label="col" 
              min-width="150"
              show-overflow-tooltip
            />
            <template #empty>
              <el-empty description="表中暂无数据" />
            </template>
          </el-table>
        </el-tab-pane>

        <!-- 表信息 -->
        <el-tab-pane label="表信息" name="info">
          <el-descriptions :column="2" border v-if="tableInfo">
            <el-descriptions-item label="表名">{{ tableInfo.name }}</el-descriptions-item>
            <el-descriptions-item label="引擎">{{ tableInfo.engine }}</el-descriptions-item>
            <el-descriptions-item label="行数">{{ formatNumber(tableInfo.rows) }}</el-descriptions-item>
            <el-descriptions-item label="平均行长度">{{ tableInfo.avg_row_length }} 字节</el-descriptions-item>
            <el-descriptions-item label="数据大小">{{ tableInfo.data_mb.toFixed(2) }} MB</el-descriptions-item>
            <el-descriptions-item label="索引大小">{{ tableInfo.index_mb.toFixed(2) }} MB</el-descriptions-item>
            <el-descriptions-item label="总大小">{{ tableInfo.size_mb.toFixed(2) }} MB</el-descriptions-item>
            <el-descriptions-item label="自增值">{{ tableInfo.auto_increment || '-' }}</el-descriptions-item>
            <el-descriptions-item label="字符集">{{ tableInfo.collation || '-' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDateTime(tableInfo.create_time) }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ formatDateTime(tableInfo.update_time) }}</el-descriptions-item>
            <el-descriptions-item label="注释" :span="2">{{ tableInfo.comment || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="tableDetailVisible = false">关闭</el-button>
        <el-button type="primary" @click="optimizeTable(currentTableName)">优化表</el-button>
        <el-button type="info" @click="analyzeTable(currentTableName)">分析表</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
  Download, Refresh, Search, Coin, Grid, Connection, FolderOpened, FullScreen, Close
} from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import service from '@/api/user';

const loading = ref(false);
const backing = ref(false);
const loadingBackups = ref(false);
const loadingConnections = ref(false);
const loadingDetail = ref(false);
const activeTab = ref('tables');
const tableSearch = ref('');
const selectedTables = ref([]);

const tableDetailVisible = ref(false);
const currentTableName = ref('');
const detailTab = ref('structure');
const tableStructure = ref([]);
const tableIndexes = ref([]);
const tableData = ref([]);
const tableColumns = ref([]);
const tableInfo = ref(null);
const isFullscreen = ref(false);
const dialogWidth = ref('90%');

const dbInfo = ref({
  engine: '',
  name: '',
  host: '',
  port: '',
  version: '',
  size_mb: 0,
  table_count: 0,
  tables: []
});

const backupList = ref([]);
const connections = ref([]);
const connectionCount = ref(0);
const dbStatus = ref({
  status: null
});

const filteredTables = computed(() => {
  const tables = dbInfo.value.tables || [];
  if (!tableSearch.value) return tables;
  return tables.filter(table => 
    table.name.toLowerCase().includes(tableSearch.value.toLowerCase())
  );
});

const loadDatabaseInfo = async () => {
  loading.value = true;
  try {
    const response = await service({
      url: '/users/database/info/',
      method: 'get'
    });
    dbInfo.value = {
      ...response,
      tables: response.tables || []
    };
  } catch (error) {
    console.error('加载数据库信息失败:', error);
    ElMessage.error(error.response?.data?.detail || '加载数据库信息失败');
  } finally {
    loading.value = false;
  }
};

const loadBackups = async () => {
  loadingBackups.value = true;
  try {
    const response = await service({
      url: '/users/database/backups/',
      method: 'get'
    });
    backupList.value = response.backups || [];
  } catch (error) {
    console.error('加载备份列表失败:', error);
    ElMessage.error(error.response?.data?.detail || '加载备份列表失败');
  } finally {
    loadingBackups.value = false;
  }
};

const loadConnections = async () => {
  loadingConnections.value = true;
  try {
    const response = await service({
      url: '/users/database/connections/',
      method: 'get'
    });
    connections.value = response.connections || [];
    connectionCount.value = response.count || 0;
  } catch (error) {
    console.error('加载连接信息失败:', error);
    ElMessage.error(error.response?.data?.detail || '加载连接信息失败');
  } finally {
    loadingConnections.value = false;
  }
};

const loadStatus = async () => {
  try {
    const response = await service({
      url: '/users/database/status/',
      method: 'get'
    });
    dbStatus.value = response;
  } catch (error) {
    console.error('加载数据库状态失败:', error);
    ElMessage.error(error.response?.data?.detail || '加载数据库状态失败');
  }
};

const backupDatabase = async () => {
  backing.value = true;
  try {
    const response = await service({
      url: '/users/database/backup/',
      method: 'post'
    });
    ElMessage.success(response.message);
    loadBackups();
  } catch (error) {
    console.error('备份失败:', error);
    ElMessage.error(error.response?.data?.detail || '备份失败');
  } finally {
    backing.value = false;
  }
};

const restoreBackup = async (filename) => {
  try {
    const response = await service({
      url: '/users/database/restore/',
      method: 'post',
      data: { filename }
    });
    ElMessage.success(response.message);
    loadDatabaseInfo();
  } catch (error) {
    console.error('恢复失败:', error);
    ElMessage.error(error.response?.data?.detail || '恢复失败');
  }
};

const optimizeTable = async (tableName) => {
  try {
    const response = await service({
      url: '/users/database/optimize/',
      method: 'post',
      data: { table: tableName }
    });
    ElMessage.success(response.message || '优化成功');
    await loadDatabaseInfo();
  } catch (error) {
    console.error('优化失败:', error);
    ElMessage.error(error.response?.data?.detail || '优化失败');
  }
};

const analyzeTable = async (tableName) => {
  try {
    const response = await service({
      url: '/users/database/analyze/',
      method: 'post',
      data: { table: tableName }
    });
    ElMessage.success(response.message || '分析成功');
  } catch (error) {
    console.error('分析失败:', error);
    ElMessage.error(error.response?.data?.detail || '分析失败');
  }
};

const repairTable = async (tableName) => {
  try {
    await ElMessageBox.confirm(
      `确定要修复表 ${tableName} 吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    const response = await service({
      url: '/users/database/repair/',
      method: 'post',
      data: { table: tableName }
    });
    ElMessage.success(response.message || '修复成功');
    await loadDatabaseInfo();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('修复失败:', error);
      ElMessage.error(error.response?.data?.detail || '修复失败');
    }
  }
};

const downloadBackup = async (backup) => {
  try {
    // 创建下载链接
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const downloadUrl = `${baseURL}/api/users/database/download-backup/?filename=${encodeURIComponent(backup.filename)}`;
    
    // 创建隐藏的 a 标签进行下载
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = backup.filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    ElMessage.success('开始下载备份文件');
  } catch (error) {
    console.error('下载失败:', error);
    ElMessage.error('下载失败');
  }
};

const formatNumber = (num) => {
  return new Intl.NumberFormat('zh-CN').format(num);
};

const formatBytes = (bytes) => {
  const mb = bytes / (1024 * 1024);
  if (mb > 1024) {
    return `${(mb / 1024).toFixed(2)} GB`;
  }
  return `${mb.toFixed(2)} MB`;
};

const formatUptime = (seconds) => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${days}天 ${hours}小时 ${minutes}分钟`;
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

const handleSelectionChange = (selection) => {
  selectedTables.value = selection;
};

const batchOptimize = async () => {
  if (selectedTables.value.length === 0) {
    ElMessage.warning('请先选择要优化的表');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要优化选中的 ${selectedTables.value.length} 个表吗？`,
      '批量优化',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    );

    loading.value = true;
    let successCount = 0;
    let failCount = 0;

    for (const table of selectedTables.value) {
      try {
        await service({
          url: '/users/database/optimize/',
          method: 'post',
          data: { table: table.name }
        });
        successCount++;
      } catch (error) {
        console.error(`优化表 ${table.name} 失败:`, error);
        failCount++;
      }
    }

    ElMessage.success(`批量优化完成：成功 ${successCount} 个，失败 ${failCount} 个`);
    await loadDatabaseInfo();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量优化失败:', error);
      ElMessage.error('批量优化失败');
    }
  } finally {
    loading.value = false;
  }
};

const batchAnalyze = async () => {
  if (selectedTables.value.length === 0) {
    ElMessage.warning('请先选择要分析的表');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要分析选中的 ${selectedTables.value.length} 个表吗？`,
      '批量分析',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    );

    loading.value = true;
    let successCount = 0;
    let failCount = 0;

    for (const table of selectedTables.value) {
      try {
        await service({
          url: '/users/database/analyze/',
          method: 'post',
          data: { table: table.name }
        });
        successCount++;
      } catch (error) {
        console.error(`分析表 ${table.name} 失败:`, error);
        failCount++;
      }
    }

    ElMessage.success(`批量分析完成：成功 ${successCount} 个，失败 ${failCount} 个`);
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量分析失败:', error);
      ElMessage.error('批量分析失败');
    }
  } finally {
    loading.value = false;
  }
};

const openTableDetail = async (tableName) => {
  currentTableName.value = tableName;
  tableDetailVisible.value = true;
  detailTab.value = 'structure';
  isFullscreen.value = false;
  dialogWidth.value = '90%';
  
  await Promise.all([
    loadTableStructure(tableName),
    loadTableIndexes(tableName),
    loadTableInfo(tableName)
  ]);
};

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
  if (isFullscreen.value) {
    dialogWidth.value = '100%';
  } else {
    dialogWidth.value = '90%';
  }
};

const setDialogSize = (size) => {
  isFullscreen.value = false;
  dialogWidth.value = size;
};

const loadTableStructure = async (tableName) => {
  loadingDetail.value = true;
  try {
    const response = await service({
      url: '/users/database/table-structure/',
      method: 'get',
      params: { table: tableName }
    });
    tableStructure.value = response.structure || [];
  } catch (error) {
    console.error('加载表结构失败:', error);
    ElMessage.error(error.response?.data?.detail || '加载表结构失败');
  } finally {
    loadingDetail.value = false;
  }
};

const loadTableIndexes = async (tableName) => {
  try {
    const response = await service({
      url: '/users/database/table-indexes/',
      method: 'get',
      params: { table: tableName }
    });
    tableIndexes.value = response.indexes || [];
  } catch (error) {
    console.error('加载索引信息失败:', error);
    ElMessage.error(error.response?.data?.detail || '加载索引信息失败');
  }
};

const loadTableData = async (tableName) => {
  loadingDetail.value = true;
  try {
    const response = await service({
      url: '/users/database/table-data/',
      method: 'get',
      params: { table: tableName, limit: 100 }
    });
    tableData.value = response.data || [];
    tableColumns.value = response.columns || [];
  } catch (error) {
    console.error('加载表数据失败:', error);
    ElMessage.error(error.response?.data?.detail || '加载表数据失败');
  } finally {
    loadingDetail.value = false;
  }
};

const loadTableInfo = async (tableName) => {
  try {
    const table = dbInfo.value.tables.find(t => t.name === tableName);
    if (table) {
      tableInfo.value = {
        ...table,
        create_time: table.create_time,
        update_time: table.update_time
      };
    }
  } catch (error) {
    console.error('加载表信息失败:', error);
  }
};

// 监听详情标签切换，按需加载数据
watch(detailTab, (newTab) => {
  if (newTab === 'data' && tableData.value.length === 0) {
    loadTableData(currentTableName.value);
  }
});

// 监听对话框显示状态，添加键盘事件
watch(tableDetailVisible, (visible) => {
  if (visible) {
    document.addEventListener('keydown', handleKeydown);
  } else {
    document.removeEventListener('keydown', handleKeydown);
    // 重置状态
    tableStructure.value = [];
    tableIndexes.value = [];
    tableData.value = [];
    tableColumns.value = [];
  }
});

const handleKeydown = (e) => {
  // ESC 键退出全屏或关闭对话框
  if (e.key === 'Escape') {
    if (isFullscreen.value) {
      toggleFullscreen();
      e.preventDefault();
    }
  }
  // F11 切换全屏
  if (e.key === 'F11') {
    toggleFullscreen();
    e.preventDefault();
  }
};

onMounted(() => {
  loadDatabaseInfo();
  loadBackups();
  loadConnections();
  loadStatus();
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
});
</script>

<style scoped>
.database-management {
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

.stat-icon.database {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.tables {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.connections {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.backups {
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

.tabs-container {
  margin-top: 20px;
}

.filter-section {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.batch-actions {
  display: flex;
  gap: 10px;
}

.backup-actions,
.connection-actions {
  margin-bottom: 20px;
}

.status-section {
  margin-top: 20px;
}

.status-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 15px;
}

.data-preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 20px;
}

.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.dialog-actions {
  display: flex;
  align-items: center;
  gap: 5px;
}

.size-buttons {
  margin-right: 5px;
}

.size-buttons .el-button {
  min-width: 50px;
}

.fullscreen-dialog :deep(.el-dialog__body) {
  height: calc(100vh - 140px);
  overflow-y: auto;
}

.fullscreen-dialog :deep(.el-dialog) {
  margin: 0 !important;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.fullscreen-dialog :deep(.el-dialog__header) {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.fullscreen-dialog :deep(.el-dialog__footer) {
  padding: 15px 20px;
  border-top: 1px solid #e4e7ed;
}
</style>
