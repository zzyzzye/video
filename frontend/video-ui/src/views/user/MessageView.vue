<template>
  <div class="dashboard-content">
    <PageHeader 
      title="消息通知" 
      :breadcrumb="[{ label: '个人中心' }, { label: '消息通知' }]" 
    />

    <div class="message-container">
      <!-- 左侧：消息列表 -->
      <div class="message-sidebar">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <el-tab-pane label="全部" name="all" />
          <el-tab-pane label="系统" name="system" />
          <el-tab-pane label="互动" name="interaction" />
          <el-tab-pane label="私信" name="private" />
        </el-tabs>
        
        <div class="list-actions">
          <el-button text size="small" @click="markAllRead" :disabled="!hasUnread">
            <el-icon><Check /></el-icon> 全部已读
          </el-button>
          <el-button text size="small" type="danger" @click="clearMessages" :disabled="messages.length === 0">
            <el-icon><Delete /></el-icon> 清空
          </el-button>
        </div>

        <el-scrollbar class="message-list-scroll">
          <div v-if="loading" class="loading-state">
            <el-skeleton :rows="3" animated />
          </div>
          <el-empty v-else-if="currentMessages.length === 0" description="暂无消息" :image-size="60" />
          <div v-else class="message-list">
            <div 
              v-for="msg in currentMessages" 
              :key="msg.id"
              class="message-item"
              :class="{ active: selectedMessage?.id === msg.id, unread: !msg.read }"
              @click="selectMessage(msg)"
            >
              <div class="msg-icon" :class="`type-${msg.type || 'system'}`">
                <el-icon v-if="msg.type === 'system'"><Bell /></el-icon>
                <el-icon v-else-if="msg.type === 'interaction'"><ChatDotRound /></el-icon>
                <el-icon v-else-if="msg.type === 'private'"><Message /></el-icon>
                <el-icon v-else><Bell /></el-icon>
              </div>
              <div class="msg-info">
                <div class="msg-title">
                  <span class="unread-dot" v-if="!msg.read"></span>
                  {{ msg.title }}
                </div>
                <div class="msg-preview">{{ msg.content }}</div>
                <div class="msg-time">{{ formatTime(msg.created_at) }}</div>
              </div>
            </div>
          </div>
        </el-scrollbar>
      </div>

      <!-- 右侧：消息详情 -->
      <div class="message-detail">
        <template v-if="selectedMessage">
          <div class="detail-header">
            <h3>{{ selectedMessage.title }}</h3>
            <span class="detail-time">{{ formatFullTime(selectedMessage.created_at) }}</span>
          </div>
          <el-divider />
          <div class="detail-content">
            <p>{{ selectedMessage.content }}</p>
          </div>
          <div class="detail-actions">
            <el-button 
              v-if="selectedMessage.source_id && selectedMessage.source_type === 'video'"
              type="primary"
              @click="goToSource(selectedMessage.source_id)"
            >
              查看视频
            </el-button>
            <el-button @click="deleteCurrentMessage">删除消息</el-button>
          </div>
        </template>
        <div v-else class="empty-detail">
          <el-icon :size="48" color="#c0c4cc"><Notification /></el-icon>
          <p>选择一条消息查看详情</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Check, Delete, Bell, ChatDotRound, Message, Notification } from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import { 
  getNotifications, 
  markNotificationAsRead, 
  markAllNotificationsAsRead,
  deleteNotification,
  clearAllNotifications
} from '@/api/user';
import { useEventBus } from '@/utils/eventBus';

const router = useRouter();
const activeTab = ref('all');
const loading = ref(false);
const messages = ref([]);
const selectedMessage = ref(null);
const eventBus = useEventBus();

const hasUnread = computed(() => messages.value.some(msg => !msg.read));

const currentMessages = computed(() => {
  if (activeTab.value === 'all') return messages.value;
  return messages.value.filter(msg => msg.type === activeTab.value);
});

onMounted(() => fetchMessages());

const fetchMessages = async () => {
  loading.value = true;
  try {
    const res = await getNotifications({ type: 'all' });
    messages.value = res.results || res;
  } catch {
    ElMessage.error('获取消息列表失败');
  } finally {
    loading.value = false;
  }
};

const selectMessage = async (msg) => {
  selectedMessage.value = msg;
  if (!msg.read) {
    try {
      await markNotificationAsRead(msg.id);
      msg.read = true;
      eventBus.emit('update-unread-messages');
    } catch {}
  }
};

const markAsRead = async (id) => {
  try {
    await markNotificationAsRead(id);
    const msg = messages.value.find(m => m.id === id);
    if (msg) msg.read = true;
    eventBus.emit('update-unread-messages');
  } catch {}
};

const markAllRead = async () => {
  try {
    await markAllNotificationsAsRead();
    messages.value.forEach(msg => msg.read = true);
    ElMessage.success('已全部标为已读');
    eventBus.emit('update-unread-messages');
  } catch {}
};

const deleteCurrentMessage = async () => {
  if (!selectedMessage.value) return;
  try {
    await deleteNotification(selectedMessage.value.id);
    const wasUnread = !selectedMessage.value.read;
    messages.value = messages.value.filter(m => m.id !== selectedMessage.value.id);
    selectedMessage.value = null;
    ElMessage.success('已删除');
    if (wasUnread) eventBus.emit('update-unread-messages');
  } catch {}
};

const clearMessages = () => {
  ElMessageBox.confirm('确定清空所有消息？', '提示', { type: 'warning' })
    .then(async () => {
      await clearAllNotifications();
      messages.value = [];
      selectedMessage.value = null;
      ElMessage.success('已清空');
      eventBus.emit('update-unread-messages');
    }).catch(() => {});
};

const handleTabChange = () => {
  selectedMessage.value = null;
};

const goToSource = (id) => router.push(`/video/${id}`);

const formatTime = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now - date;
  if (diff < 60 * 1000) return '刚刚';
  if (diff < 60 * 60 * 1000) return Math.floor(diff / 60000) + '分钟前';
  if (diff < 24 * 60 * 60 * 1000) return Math.floor(diff / 3600000) + '小时前';
  if (diff < 7 * 24 * 60 * 60 * 1000) return Math.floor(diff / 86400000) + '天前';
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
};

const formatFullTime = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString('zh-CN');
};
</script>

<style scoped>
.dashboard-content {
  padding: 24px;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.message-container {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* 左侧列表 */
.message-sidebar {
  width: 340px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #f0f0f0;
}

.message-sidebar :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 16px;
}

.list-actions {
  display: flex;
  justify-content: space-between;
  padding: 8px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.message-list-scroll {
  flex: 1;
}

.message-list {
  padding: 8px 0;
}

.message-item {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s;
}

.message-item:hover { background: #f5f7fa; }
.message-item.active { background: #ecf5ff; }

.msg-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.msg-icon.type-system { background: #409eff; }
.msg-icon.type-interaction { background: #67c23a; }
.msg-icon.type-private { background: #e6a23c; }

.msg-info { flex: 1; min-width: 0; }

.msg-title {
  font-size: 14px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.message-item.unread .msg-title { font-weight: 600; }

.unread-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #f56c6c;
  flex-shrink: 0;
}

.msg-preview {
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.msg-time {
  font-size: 11px;
  color: #c0c4cc;
}

/* 右侧详情 */
.message-detail {
  flex: 1;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.detail-time {
  font-size: 13px;
  color: #909399;
}

.detail-content {
  flex: 1;
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
}

.detail-actions {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.empty-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}

.empty-detail p {
  margin-top: 12px;
  font-size: 14px;
}

.loading-state {
  padding: 16px;
}

@media (max-width: 768px) {
  .message-container { flex-direction: column; }
  .message-sidebar { width: 100%; border-right: none; border-bottom: 1px solid #f0f0f0; }
  .message-list-scroll { max-height: 300px; }
}
</style>
