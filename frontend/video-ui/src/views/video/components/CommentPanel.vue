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
            <button 
              class="action-btn like-btn" 
              :class="{ 'liked': comment.isLiked }" 
              @click="$emit('toggle-comment-like', comment)"
              :title="comment.isLiked ? '取消点赞' : '点赞'"
            >
              <el-icon class="like-icon" :class="{ 'filled': comment.isLiked }">
                <StarFilled v-if="comment.isLiked" />
                <Star v-else />
              </el-icon>
              <span class="like-count">{{ formatLikeCount(comment.likes) }}</span>
            </button>
            <button class="action-btn reply-btn" @click="$emit('reply-comment', comment)">
              <el-icon><ChatDotRound /></el-icon>
              <span>回复</span>
            </button>
          </div>
        </div>
      </div>
      
      <div class="no-comments" v-if="comments.length === 0">
        <el-icon class="empty-icon"><ChatLineRound /></el-icon>
        <p>暂无评论，快来抢沙发~</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Star, StarFilled, ChatDotRound, ChatLineRound } from '@element-plus/icons-vue';

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

// 格式化点赞数
const formatLikeCount = (count) => {
  if (!count || count === 0) return '点赞';
  if (count >= 10000) return `${(count / 10000).toFixed(1)}万`;
  if (count >= 1000) return `${(count / 1000).toFixed(1)}k`;
  return count.toString();
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
  gap: 12px;
  margin-top: 4px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
}

.action-btn:active {
  transform: translateY(0);
}

/* 点赞按钮 */
.like-btn {
  position: relative;
}

.like-btn .like-icon {
  font-size: 15px;
  transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.like-btn:hover .like-icon {
  transform: scale(1.2);
}

/* 未点赞状态 - 空心爱心 */
.like-btn .like-icon:not(.filled) :deep(svg) {
  fill: none;
  stroke: currentColor;
  stroke-width: 2px;
}

/* 已点赞状态 - 实心爱心 */
.like-btn.liked {
  color: #ff4d6d;
  background: rgba(255, 77, 109, 0.12);
  border-color: rgba(255, 77, 109, 0.3);
}

.like-btn.liked .like-icon.filled :deep(svg) {
  fill: currentColor;
  stroke: none;
  animation: likeAnimation 0.5s ease;
}

@keyframes likeAnimation {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.3);
  }
  100% {
    transform: scale(1);
  }
}

.like-btn.liked:hover {
  background: rgba(255, 77, 109, 0.18);
  border-color: rgba(255, 77, 109, 0.4);
  color: #ff2d5d;
}

.like-count {
  font-size: 12px;
  font-weight: 500;
  min-width: 32px;
  text-align: center;
}

/* 回复按钮 */
.reply-btn:hover {
  color: #00a1d6;
  border-color: rgba(0, 161, 214, 0.3);
  background: rgba(0, 161, 214, 0.1);
}

/* 空状态 */
.no-comments {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: rgba(255, 255, 255, 0.4);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.3;
}

.no-comments p {
  margin: 0;
  font-size: 14px;
}
</style>
