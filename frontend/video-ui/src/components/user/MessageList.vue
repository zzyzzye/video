<template>
  <div class="message-list">
    <el-empty 
      v-if="!loading && messages.length === 0" 
      description="暂无消息"
    >
      <template #image>
        <el-icon :size="80" color="#c0c4cc"><Bell /></el-icon>
      </template>
    </el-empty>
    
    <el-skeleton 
      v-else-if="loading" 
      :rows="2" 
      animated 
      :count="3"
      style="margin-bottom: 12px"
    />
    
    <template v-else>
      <div 
        v-for="message in messages" 
        :key="message.id"
        class="message-item"
        :class="[{ 'unread': !message.read }, `type-${message.type || 'system'}`]"
      >
        <div class="message-icon">
          <el-icon v-if="message.type === 'system'" :size="20"><Bell /></el-icon>
          <el-icon v-else-if="message.type === 'interaction'" :size="20"><ChatDotRound /></el-icon>
          <el-icon v-else-if="message.type === 'private'" :size="20"><Message /></el-icon>
          <el-icon v-else :size="20"><Bell /></el-icon>
        </div>
        
        <div class="message-body">
          <div class="message-header">
            <span class="message-title">
              <span class="unread-dot" v-if="!message.read"></span>
              {{ message.title }}
            </span>
            <span class="message-time">{{ formatTime(message.created_at) }}</span>
          </div>
          
          <div class="message-content">{{ message.content }}</div>
          
          <div class="message-footer">
            <div class="message-links">
              <el-button 
                v-if="message.source_id && message.source_type === 'video'"
                type="primary" 
                link 
                size="small"
                @click="goToSource(message.source_id, message.source_type)"
              >
                查看视频
              </el-button>
              <el-button 
                v-if="message.type === 'private' && message.sender"
                type="primary" 
                link 
                size="small"
                @click="replyMessage(message)"
              >
                回复
              </el-button>
            </div>
            
            <div class="message-ops">
              <el-button 
                v-if="!message.read" 
                type="info" 
                link 
                size="small"
                @click="markAsRead(message.id)"
              >
                标为已读
              </el-button>
              <el-popconfirm
                title="确定删除？"
                @confirm="deleteMessage(message.id)"
                confirm-button-text="删除"
                cancel-button-text="取消"
              >
                <template #reference>
                  <el-button type="danger" link size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>
        </div>
      </div>
    </template>
    
    <!-- 回复对话框 -->
    <el-dialog
      v-model="replyDialogVisible"
      title="回复消息"
      width="500px"
    >
      <div class="reply-dialog-content" v-if="currentMessage">
        <div class="original-message">
          <div class="sender-info" v-if="currentMessage.sender">
            <el-avatar :size="40" :src="currentMessage.sender.avatar"></el-avatar>
            <div class="sender-name">{{ currentMessage.sender.username }}</div>
          </div>
          <div class="original-content">{{ currentMessage.content }}</div>
        </div>
        
        <el-form :model="replyForm" ref="replyFormRef">
          <el-form-item prop="content" :rules="[{ required: true, message: '请输入回复内容', trigger: 'blur' }]">
            <el-input
              v-model="replyForm.content"
              type="textarea"
              :rows="4"
              placeholder="请输入回复内容"
              resize="none"
            />
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="replyDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitReply" :loading="replyLoading">发送</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';

import { Bell, ChatDotRound, Message } from '@element-plus/icons-vue';

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['read', 'delete']);
const router = useRouter();

// 回复相关
const replyDialogVisible = ref(false);
const replyLoading = ref(false);
const currentMessage = ref(null);
const replyFormRef = ref(null);
const replyForm = ref({
  content: '',
  receiverId: null
});

// 标记消息为已读
const markAsRead = (messageId) => {
  emit('read', messageId);
};

// 删除消息
const deleteMessage = (messageId) => {
  emit('delete', messageId);
};

// 跳转到消息来源
const goToSource = (sourceId, sourceType) => {
  if (sourceType === 'video') {
    router.push(`/video/${sourceId}`);
  }
};

// 格式化时间
const formatTime = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now - date;
  
  // 小于1分钟
  if (diff < 60 * 1000) {
    return '刚刚';
  }
  // 小于1小时
  if (diff < 60 * 60 * 1000) {
    return Math.floor(diff / (60 * 1000)) + '分钟前';
  }
  // 小于24小时
  if (diff < 24 * 60 * 60 * 1000) {
    return Math.floor(diff / (60 * 60 * 1000)) + '小时前';
  }
  // 小于7天
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    return Math.floor(diff / (24 * 60 * 60 * 1000)) + '天前';
  }
  // 超过7天显示具体日期
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
};

// 回复消息
const replyMessage = (message) => {
  currentMessage.value = message;
  replyForm.value.receiverId = message.sender?.id;
  replyForm.value.content = '';
  replyDialogVisible.value = true;
};

// 提交回复
const submitReply = () => {
  replyFormRef.value?.validate(async (valid) => {
    if (!valid) return;
    
    try {
      replyLoading.value = true;
      // 实际项目中应该调用API
      await new Promise(resolve => setTimeout(resolve, 800));
      
      ElMessage.success('回复发送成功');
      replyDialogVisible.value = false;
      
      // 标记原消息为已读
      if (currentMessage.value && !currentMessage.value.read) {
        markAsRead(currentMessage.value.id);
      }
    } catch (error) {
      ElMessage.error('发送失败');
    } finally {
      replyLoading.value = false;
    }
  });
};
</script>

<style scoped>
.message-list {
  max-width: 700px;
}

.message-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s;
}

.message-item:hover {
  background: #fafafa;
  margin: 0 -12px;
  padding: 14px 12px;
}

.message-item:last-child {
  border-bottom: none;
}

.message-item.unread .message-title {
  font-weight: 600;
}

.message-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.message-item.type-system .message-icon { background: #409eff; }
.message-item.type-interaction .message-icon { background: #67c23a; }
.message-item.type-private .message-icon { background: #e6a23c; }

.message-body {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.message-title {
  font-size: 14px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 6px;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
  flex-shrink: 0;
}

.message-time {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

.message-content {
  font-size: 13px;
  line-height: 1.5;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-item.unread .message-content {
  color: #606266;
}

.message-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 6px;
}

.message-links, .message-ops {
  display: flex;
  gap: 8px;
}

/* 回复对话框样式 */
.original-message {
  background: var(--el-fill-color-lighter);
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.sender-info {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.sender-name {
  font-weight: 500;
  margin-left: 10px;
}

.original-content {
  color: var(--el-text-color-secondary);
  line-height: 1.5;
  font-size: 13px;
}
</style> 