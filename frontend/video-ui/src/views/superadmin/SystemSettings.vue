<template>
  <div class="system-settings animate__animated animate__fadeIn animate__faster">
    <PageHeader 
      title="系统设置" 
      :breadcrumb="[
        { label: '超级管理员', path: '/superadmin/monitor' },
        { label: '系统设置' }
      ]"
      class="animate__animated animate__fadeInDown animate__faster"
    >
      <template #actions>
        <el-button type="primary" @click="loadAllData" :loading="loading" class="animate__animated animate__fadeInRight animate__faster">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </template>
    </PageHeader>

    <div v-loading="loading" class="content-wrapper">
      <!-- 硬件资源概览 -->
      <div class="section animate__animated animate__fadeInUp animate__fast">
        <div class="section-header">
          <el-icon><Monitor /></el-icon>
          <span>硬件资源概览</span>
        </div>
        
        <el-row :gutter="15">
          <!-- CPU -->
          <el-col :span="6">
            <div class="stat-card animate__animated animate__zoomIn animate__faster" style="animation-delay: 0.05s">
              <div class="stat-icon cpu">
                <el-icon><Cpu /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">CPU 使用率</div>
                <div class="stat-value">{{ currentCpuUsage }}%</div>
                <el-progress 
                  :percentage="parseFloat(currentCpuUsage)" 
                  :color="getProgressColor(parseFloat(currentCpuUsage))"
                  :show-text="false"
                  :stroke-width="6"
                />
              </div>
            </div>
          </el-col>

          <!-- 内存 -->
          <el-col :span="6">
            <div class="stat-card animate__animated animate__zoomIn animate__faster" style="animation-delay: 0.1s">
              <div class="stat-icon memory">
                <el-icon><Coin /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">内存使用率</div>
                <div class="stat-value">{{ systemInfo.memory?.percent?.toFixed(1) }}%</div>
                <el-progress 
                  :percentage="systemInfo.memory?.percent" 
                  :color="getProgressColor(systemInfo.memory?.percent)"
                  :show-text="false"
                  :stroke-width="6"
                />
                <div class="stat-detail">
                  {{ systemInfo.memory?.used_gb }} / {{ systemInfo.memory?.total_gb }} GB
                </div>
              </div>
            </div>
          </el-col>

          <!-- 磁盘 -->
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon disk">
                <el-icon><FolderOpened /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">磁盘使用率</div>
                <div class="stat-value">{{ systemInfo.disk?.percent?.toFixed(1) }}%</div>
                <el-progress 
                  :percentage="systemInfo.disk?.percent" 
                  :color="getProgressColor(systemInfo.disk?.percent)"
                  :show-text="false"
                  :stroke-width="6"
                />
                <div class="stat-detail">
                  {{ systemInfo.disk?.used_gb }} / {{ systemInfo.disk?.total_gb }} GB
                </div>
              </div>
            </div>
          </el-col>

          <!-- GPU -->
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon gpu">
                <el-icon><VideoCamera /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">GPU 使用率</div>
                <div class="stat-value" v-if="systemInfo.gpu && systemInfo.gpu.length > 0">
                  {{ systemInfo.gpu[0].load }}%
                </div>
                <div class="stat-value" v-else>N/A</div>
                <el-progress 
                  v-if="systemInfo.gpu && systemInfo.gpu.length > 0"
                  :percentage="systemInfo.gpu[0].load" 
                  :color="getProgressColor(systemInfo.gpu[0].load)"
                  :show-text="false"
                  :stroke-width="6"
                />
                <div class="stat-detail" v-if="systemInfo.gpu && systemInfo.gpu.length > 0">
                  {{ systemInfo.gpu[0].memory_used.toFixed(0) }} / {{ systemInfo.gpu[0].memory_total.toFixed(0) }} MB
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <el-row :gutter="15">
        <!-- 左侧列 -->
        <el-col :span="12">
          <!-- 系统信息 -->
          <div class="section">
            <div class="section-header">
              <el-icon><Platform /></el-icon>
              <span>系统信息</span>
            </div>
            <el-table :data="systemOverview" size="small" :show-header="false" class="compact-table">
              <el-table-column prop="label" width="140" class-name="label-col" />
              <el-table-column prop="value" class-name="value-col" show-overflow-tooltip />
            </el-table>
          </div>

          <!-- CPU 详情 -->
          <div class="section">
            <div class="section-header">
              <el-icon><Cpu /></el-icon>
              <span>CPU 详情</span>
            </div>
            <el-table :data="cpuDetails" size="small" :show-header="false" class="compact-table">
              <el-table-column prop="label" width="140" class-name="label-col" />
              <el-table-column prop="value" class-name="value-col" show-overflow-tooltip />
            </el-table>
          </div>

          <!-- GPU 详情 -->
          <div class="section" v-if="systemInfo.gpu && systemInfo.gpu.length > 0">
            <div class="section-header">
              <el-icon><VideoCamera /></el-icon>
              <span>GPU 详情</span>
            </div>
            
            <template v-for="(gpu, index) in systemInfo.gpu" :key="gpu.id">
              <div v-if="index > 0" style="margin-top: 15px;"></div>
              
              <el-descriptions :title="`GPU ${gpu.id}: ${gpu.name}`" :column="2" border size="small">
                <el-descriptions-item label="GPU 负载">
                  <el-tag :type="gpu.load > 80 ? 'danger' : 'success'" size="small">
                    {{ gpu.load }}%
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="显存利用率">
                  <el-tag :type="gpu.memory_util > 80 ? 'danger' : 'success'" size="small">
                    {{ gpu.memory_util }}%
                  </el-tag>
                </el-descriptions-item>
                
                <el-descriptions-item label="显存使用">
                  {{ gpu.memory_used.toFixed(0) }} / {{ gpu.memory_total.toFixed(0) }} MB
                </el-descriptions-item>
                <el-descriptions-item label="显存占用率">
                  {{ gpu.memory_percent.toFixed(1) }}%
                </el-descriptions-item>
                
                <el-descriptions-item label="GPU 温度">
                  <el-tag :type="gpu.temperature > 80 ? 'danger' : gpu.temperature > 70 ? 'warning' : 'success'" size="small">
                    {{ gpu.temperature }}°C
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="风扇转速" v-if="gpu.fan_speed !== null">
                  {{ gpu.fan_speed }}%
                </el-descriptions-item>
                <el-descriptions-item label="风扇转速" v-else>
                  N/A
                </el-descriptions-item>
                
                <el-descriptions-item label="功耗" v-if="gpu.power_usage !== null">
                  {{ gpu.power_usage }} W / {{ gpu.power_limit }} W
                </el-descriptions-item>
                <el-descriptions-item label="功耗" v-else>
                  N/A
                </el-descriptions-item>
                <el-descriptions-item label="性能状态" v-if="gpu.performance_state">
                  {{ gpu.performance_state }}
                </el-descriptions-item>
                <el-descriptions-item label="性能状态" v-else>
                  N/A
                </el-descriptions-item>
                
                <el-descriptions-item label="图形时钟" v-if="gpu.graphics_clock">
                  {{ gpu.graphics_clock }} MHz
                  <span v-if="gpu.max_graphics_clock" style="color: #909399;">
                    (最大: {{ gpu.max_graphics_clock }} MHz)
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="图形时钟" v-else>
                  N/A
                </el-descriptions-item>
                
                <el-descriptions-item label="SM 时钟" v-if="gpu.sm_clock">
                  {{ gpu.sm_clock }} MHz
                  <span v-if="gpu.max_sm_clock" style="color: #909399;">
                    (最大: {{ gpu.max_sm_clock }} MHz)
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="SM 时钟" v-else>
                  N/A
                </el-descriptions-item>
                
                <el-descriptions-item label="显存时钟" v-if="gpu.memory_clock">
                  {{ gpu.memory_clock }} MHz
                  <span v-if="gpu.max_memory_clock" style="color: #909399;">
                    (最大: {{ gpu.max_memory_clock }} MHz)
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="显存时钟" v-else>
                  N/A
                </el-descriptions-item>
                
                <el-descriptions-item label="PCIe 链路" v-if="gpu.pcie_gen">
                  Gen{{ gpu.pcie_gen }} x{{ gpu.pcie_width }}
                  <span v-if="gpu.max_pcie_gen" style="color: #909399;">
                    (最大: Gen{{ gpu.max_pcie_gen }} x{{ gpu.max_pcie_width }})
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="PCIe 链路" v-else>
                  N/A
                </el-descriptions-item>
                
                <el-descriptions-item label="计算能力" v-if="gpu.compute_capability">
                  {{ gpu.compute_capability }}
                </el-descriptions-item>
                <el-descriptions-item label="计算能力" v-else>
                  N/A
                </el-descriptions-item>
                
                <el-descriptions-item label="驱动版本">
                  {{ gpu.driver }}
                </el-descriptions-item>
                <el-descriptions-item label="CUDA 版本" v-if="gpu.cuda_version">
                  {{ gpu.cuda_version }}
                </el-descriptions-item>
                <el-descriptions-item label="CUDA 版本" v-else>
                  N/A
                </el-descriptions-item>
                
                <el-descriptions-item label="UUID" :span="2">
                  <span style="font-size: 12px; font-family: monospace;">{{ gpu.uuid }}</span>
                </el-descriptions-item>
              </el-descriptions>
            </template>
          </div>

          <!-- 数据库 -->
          <div class="section">
            <div class="section-header">
              <el-icon><DataLine /></el-icon>
              <span>数据库</span>
            </div>
            <el-table :data="databaseInfo" size="small" :show-header="false" class="compact-table">
              <el-table-column prop="label" width="140" class-name="label-col" />
              <el-table-column prop="value" class-name="value-col" show-overflow-tooltip />
            </el-table>
          </div>

          <!-- Redis -->
          <div class="section">
            <div class="section-header">
              <el-icon><Connection /></el-icon>
              <span>Redis 缓存</span>
            </div>
            <el-table :data="redisInfo" size="small" :show-header="false" class="compact-table">
              <el-table-column prop="label" width="140" class-name="label-col" />
              <el-table-column prop="value" class-name="value-col">
                <template #default="scope">
                  <el-tag v-if="scope.row.label === '连接状态'" 
                    :type="scope.row.value === '已连接' ? 'success' : 'danger'" size="small">
                    {{ scope.row.value }}
                  </el-tag>
                  <span v-else>{{ scope.row.value }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-col>

        <!-- 右侧列 -->
        <el-col :span="12">
          <!-- Django 配置 -->
          <div class="section">
            <div class="section-header">
              <el-icon><Setting /></el-icon>
              <span>Django 配置</span>
            </div>
            <el-table :data="djangoConfig" size="small" :show-header="false" class="compact-table">
              <el-table-column prop="label" width="140" class-name="label-col" />
              <el-table-column prop="value" class-name="value-col">
                <template #default="scope">
                  <el-tag v-if="scope.row.label === '调试模式'" 
                    :type="scope.row.value === '开启' ? 'warning' : 'success'" size="small">
                    {{ scope.row.value }}
                  </el-tag>
                  <span v-else>{{ scope.row.value }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- Celery 配置 -->
          <div class="section">
            <div class="section-header">
              <el-icon><Timer /></el-icon>
              <span>Celery 任务队列</span>
            </div>
            <el-table :data="celeryConfig" size="small" :show-header="false" class="compact-table">
              <el-table-column prop="label" width="140" class-name="label-col" />
              <el-table-column prop="value" class-name="value-col" show-overflow-tooltip />
            </el-table>
          </div>

          <!-- 缓存配置 -->
          <div class="section">
            <div class="section-header">
              <el-icon><Box /></el-icon>
              <span>缓存配置</span>
            </div>
            <el-table :data="cacheConfig" size="small" :show-header="false" class="compact-table">
              <el-table-column prop="label" width="140" class-name="label-col" />
              <el-table-column prop="value" class-name="value-col" show-overflow-tooltip />
            </el-table>
          </div>

          <!-- 邮件配置 -->
          <div class="section">
            <div class="section-header">
              <el-icon><Message /></el-icon>
              <span>邮件配置</span>
            </div>
            <el-table :data="emailConfig" size="small" :show-header="false" class="compact-table">
              <el-table-column prop="label" width="140" class-name="label-col" />
              <el-table-column prop="value" class-name="value-col">
                <template #default="scope">
                  <el-tag v-if="scope.row.label === 'SSL 加密'" 
                    :type="scope.row.value === '启用' ? 'success' : 'info'" size="small">
                    {{ scope.row.value }}
                  </el-tag>
                  <span v-else>{{ scope.row.value }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- JWT 配置 -->
          <div class="section">
            <div class="section-header">
              <el-icon><Key /></el-icon>
              <span>JWT 认证</span>
            </div>
            <el-table :data="jwtConfig" size="small" :show-header="false" class="compact-table">
              <el-table-column prop="label" width="140" class-name="label-col" />
              <el-table-column prop="value" class-name="value-col" />
            </el-table>
          </div>

          <!-- 媒体存储 -->
          <div class="section">
            <div class="section-header">
              <el-icon><Picture /></el-icon>
              <span>媒体存储</span>
            </div>
            <el-table :data="mediaInfo" size="small" :show-header="false" class="compact-table">
              <el-table-column prop="label" width="140" class-name="label-col" />
              <el-table-column prop="value" class-name="value-col" show-overflow-tooltip />
            </el-table>
          </div>
        </el-col>
      </el-row>

      <!-- 路径配置 -->
      <div class="section">
        <div class="section-header">
          <el-icon><FolderOpened /></el-icon>
          <span>路径配置</span>
        </div>
        <el-table :data="pathConfig" size="small" :show-header="false" class="compact-table">
          <el-table-column prop="label" width="140" class-name="label-col" />
          <el-table-column prop="value" class-name="value-col" show-overflow-tooltip />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { 
  Monitor, Cpu, Coin, FolderOpened, DataLine, Connection, 
  VideoCamera, Setting, Message, Timer, Key, Refresh, Platform, Picture, Box
} from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import service from '@/api/user';

const loading = ref(false);
const systemInfo = ref({});
const configInfo = ref({});
const currentCpuUsage = ref(0);

const systemOverview = computed(() => {
  if (!systemInfo.value.system) return [];
  const sys = systemInfo.value.system;
  return [
    { label: '操作系统', value: `${sys.os} ${sys.os_release}` },
    { label: '系统版本', value: sys.os_version },
    { label: '系统架构', value: sys.architecture },
    { label: '处理器型号', value: sys.processor || '未知' },
    { label: 'Python 版本', value: getPythonVersion(sys.python_version) },
    { label: 'Django 版本', value: sys.django_version },
  ];
});

const cpuDetails = computed(() => {
  if (!systemInfo.value.cpu) return [];
  const cpu = systemInfo.value.cpu;
  const info = [
    { label: '物理核心数', value: `${cpu.cpu_count} 核` },
    { label: '逻辑核心数', value: `${cpu.cpu_count_logical} 核` },
  ];
  
  if (cpu.cpu_freq) {
    info.push(
      { label: '当前频率', value: `${(cpu.cpu_freq.current / 1000).toFixed(2)} GHz` },
      { label: '最大频率', value: `${(cpu.cpu_freq.max / 1000).toFixed(2)} GHz` },
      { label: '最小频率', value: `${(cpu.cpu_freq.min / 1000).toFixed(2)} GHz` }
    );
  }
  
  // 计算平均 CPU 使用率
  if (cpu.cpu_percent && cpu.cpu_percent.length > 0) {
    const avg = cpu.cpu_percent.reduce((a, b) => a + b, 0) / cpu.cpu_percent.length;
    currentCpuUsage.value = avg.toFixed(1);
  }
  
  return info;
});

const databaseInfo = computed(() => {
  if (!systemInfo.value.database) return [];
  const db = systemInfo.value.database;
  return [
    { label: '数据库类型', value: getDatabaseType(db.engine) },
    { label: '数据库名称', value: db.name },
    { label: '主机地址', value: `${db.host}:${db.port}` },
    { label: '数据库版本', value: db.version?.split(' ')[0] || db.version },
    { label: '当前连接数', value: db.connections },
    { label: '数据库大小', value: `${db.size_mb} MB` },
  ];
});

const redisInfo = computed(() => {
  if (!systemInfo.value.redis) return [];
  const redis = systemInfo.value.redis;
  
  if (redis.status !== 'connected') {
    return [
      { label: '连接状态', value: '未连接' },
      { label: '错误信息', value: redis.error || '无法连接' },
    ];
  }
  
  return [
    { label: '连接状态', value: '已连接' },
    { label: 'Redis 版本', value: redis.version },
    { label: '内存使用', value: redis.used_memory_human },
    { label: '客户端连接数', value: redis.connected_clients },
    { label: '运行时长', value: `${redis.uptime_in_days} 天` },
  ];
});

const djangoConfig = computed(() => {
  if (!systemInfo.value.django) return [];
  const django = systemInfo.value.django;
  return [
    { label: '调试模式', value: django.debug ? '开启' : '关闭' },
    { label: '密钥长度', value: `${django.secret_key_length} 字符` },
    { label: '允许的主机', value: django.allowed_hosts?.join(', ') || '所有' },
    { label: '已安装应用', value: `${django.installed_apps_count} 个` },
    { label: '中间件数量', value: `${django.middleware_count} 个` },
    { label: '语言代码', value: django.language_code },
    { label: '时区设置', value: django.time_zone },
    { label: '静态文件 URL', value: django.static_url },
    { label: '媒体文件 URL', value: django.media_url },
  ];
});

const celeryConfig = computed(() => {
  if (!configInfo.value.celery) return [];
  const celery = configInfo.value.celery;
  return [
    { label: '消息代理', value: celery.broker_url },
    { label: '结果后端', value: celery.result_backend },
    { label: '时区设置', value: celery.timezone || 'UTC' },
    { label: '子进程最大任务数', value: celery.max_tasks_per_child },
    { label: '子进程最大内存', value: `${celery.max_memory_per_child_mb} MB` },
  ];
});

const cacheConfig = computed(() => {
  if (!configInfo.value.cache) return [];
  const cache = configInfo.value.cache;
  return [
    { label: '缓存后端', value: getCacheBackend(cache.backend) },
    { label: '缓存位置', value: cache.location },
    { label: '默认超时', value: `${cache.timeout} 秒` },
  ];
});

const emailConfig = computed(() => {
  if (!configInfo.value.email) return [];
  const email = configInfo.value.email;
  return [
    { label: '邮件后端', value: getEmailBackend(email.backend) },
    { label: 'SMTP 服务器', value: email.host },
    { label: 'SMTP 端口', value: email.port },
    { label: 'SSL 加密', value: email.use_ssl ? '启用' : '禁用' },
    { label: '发件人地址', value: email.from_email },
  ];
});

const jwtConfig = computed(() => {
  if (!configInfo.value.jwt) return [];
  return [
    { label: '访问令牌有效期', value: `${configInfo.value.jwt.access_token_lifetime_days} 天` },
    { label: '刷新令牌有效期', value: `${configInfo.value.jwt.refresh_token_lifetime_days} 天` },
    { label: '令牌算法', value: 'HS256' },
  ];
});

const mediaInfo = computed(() => {
  if (!systemInfo.value.media) return [];
  const media = systemInfo.value.media;
  return [
    { label: '存储根目录', value: media.media_root },
    { label: '总存储大小', value: `${media.total_size_gb} GB` },
    { label: '视频文件数量', value: `${media.video_count} 个` },
    { label: '平均文件大小', value: media.video_count > 0 
      ? `${((media.total_size_gb * 1024) / media.video_count).toFixed(2)} MB` 
      : '0 MB' 
    },
  ];
});

const pathConfig = computed(() => {
  if (!configInfo.value.media) return [];
  const media = configInfo.value.media;
  return [
    { label: '媒体 URL 前缀', value: media.media_url },
    { label: '媒体根目录', value: media.media_root },
    { label: '视频上传路径', value: media.video_upload_path },
    { label: '视频处理路径', value: media.video_processed_path },
    { label: '视频缩略图路径', value: media.video_thumbnail_path },
  ];
});

const loadSystemInfo = async () => {
  try {
    const response = await service({
      url: '/users/system/info/',
      method: 'get'
    });
    systemInfo.value = response;
  } catch (error) {
    console.error('加载系统信息失败:', error);
    ElMessage.error('加载系统信息失败');
  }
};

const loadConfigInfo = async () => {
  try {
    const response = await service({
      url: '/users/system/config/',
      method: 'get'
    });
    configInfo.value = response;
  } catch (error) {
    console.error('加载配置信息失败:', error);
    ElMessage.error('加载配置信息失败');
  }
};

const loadAllData = async () => {
  loading.value = true;
  try {
    await Promise.all([
      loadSystemInfo(),
      loadConfigInfo()
    ]);
  } finally {
    loading.value = false;
  }
};

const getPythonVersion = (version) => {
  if (!version) return '';
  const match = version.match(/(\d+\.\d+\.\d+)/);
  return match ? match[1] : version;
};

const getDatabaseType = (engine) => {
  if (!engine) return '';
  if (engine.includes('mysql')) return 'MySQL';
  if (engine.includes('postgresql')) return 'PostgreSQL';
  if (engine.includes('sqlite')) return 'SQLite';
  return engine;
};

const getCacheBackend = (backend) => {
  if (!backend) return '';
  if (backend.includes('redis')) return 'Redis';
  if (backend.includes('memcached')) return 'Memcached';
  if (backend.includes('locmem')) return '本地内存';
  if (backend.includes('dummy')) return '虚拟缓存';
  return backend.split('.').pop();
};

const getEmailBackend = (backend) => {
  if (!backend) return '';
  if (backend.includes('smtp')) return 'SMTP';
  if (backend.includes('console')) return '控制台';
  if (backend.includes('filebased')) return '文件';
  return backend.split('.').pop();
};

const getProgressColor = (percent) => {
  if (percent < 60) return '#67c23a';
  if (percent < 80) return '#e6a23c';
  return '#f56c6c';
};

onMounted(() => {
  loadAllData();
});
</script>

<style scoped>
.system-settings {
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

.section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e4e7ed;
}

.section-header .el-icon {
  font-size: 16px;
  color: #2196f3;
}

/* 统计卡片 */
.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
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

.stat-icon.cpu {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.memory {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.disk {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.gpu {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 6px;
}

.stat-detail {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
}

/* 紧凑表格 */
.compact-table {
  font-size: 13px;
}

:deep(.compact-table .el-table__body-wrapper) {
  border-radius: 4px;
}

:deep(.compact-table td) {
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.compact-table tr:last-child td) {
  border-bottom: none;
}

:deep(.compact-table .label-col) {
  color: #606266;
  font-weight: 500;
  background: #fafafa;
}

:deep(.compact-table .value-col) {
  color: #303133;
  font-weight: 500;
}

:deep(.compact-table .cell) {
  padding: 0 12px;
  line-height: 24px;
}

:deep(.el-progress) {
  width: 100%;
}

:deep(.el-progress__text) {
  display: none;
}
</style>
