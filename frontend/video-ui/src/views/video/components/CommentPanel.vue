<template>
  <div class="comments-panel">
    <div class="comment-form">
      <el-avatar :size="36" :src="userAvatar || defaultAvatar"></el-avatar>
      <div class="input-wrapper">
        <el-input 
          v-model="commentText" 
          placeholder="发一条友善的评论" 
          @keyup.enter="handleAddComment" 
        />
        <el-button 
          type="primary" 
          size="small" 
          :disabled="!commentText.trim()" 
          @click="handleAddComment"
        >
          发送
        </el-button>
      </div>
    </div>
    
    <div class="comment-list">
      <div v-for="comment in comments" :key="comment.id" class="comment-item">
        <el-avatar :size="36" :src="comment.userAvatar || defaultAvatar"></el-avatar>
        <div class="comment-content">
          <div class="comment-header">
            <span class="username">{{ comment.username }}</span>
            <span class="comment-time">{{ comment.time }}</span>
          </div>
          <div class="comment-text">{{ comment.text }}</div>
          <div class="comment-actions">
            <span 
              class="action" 
              :class="{ 'active': comment.isLiked }" 
              @click="$emit('toggle-comment-like', comment)"
            >
              <el-icon><CaretTop /></el-icon>{{ comment.likes || '' }}
            </span>
            <span class="action" @click="$emit('reply-comment', comment)">回复</span>
          </div>
        </div>
      </div>
      
      <div class="no-comments" v-if="comments.length === 0">
        <p>暂无评论，快来抢沙发~</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { CaretTop } from '@element-plus/icons-vue';

const props = defineProps({
  comments: { type: Array, default: () => [] },
  userAvatar: String
});

const emit = defineEmits(['add-comment', 'toggle-comment-like', 'reply-comment']);

const commentText = ref('');
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';

const handleAddComment = () => {
  if (commentText.value.trim()) {
    emit('add-comment', commentText.value);
    commentText.value = '';
  }
};
</script>

<style scoped>
.comments-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.comment-form {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  align-items: center;
}

.input-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.comment-form .el-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: none;
  border-radius: 20px;
}

.comment-form .el-input :deep(.el-input__inner) {
  color: #fff;
}

.comment-form .el-input :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.4);
}

.comment-form .el-button {
  border-radius: 20px;
  background: linear-gradient(135deg, #00a1d6 0%, #00b5e5 100%);
  border: none;
}

.comment-form .el-button:hover {
  background: linear-gradient(135deg, #00b5e5 0%, #00c8f8 100%);
}

.comment-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.comment-list::-webkit-scrollbar {
  width: 6px;
}

.comment-list::-webkit-scrollbar-track {
  background: transparent;
}

.comment-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.comment-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.comment-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-content {
  flex: 1;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #00a1d6;
}

.comment-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.comment-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.6;
  margin-bottom: 8px;
}

.comment-actions {
  display: flex;
  gap: 16px;
}

.action {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: color 0.2s;
}

.action:hover,
.action.active {
  color: #00a1d6;
}

.no-comments {
  text-align: center;
  padding: 60px 0;
  color: rgba(255, 255, 255, 0.4);
}

.no-comments p {
  margin: 0;
}
</style>
