<template>
  <div class="sidebar-wrapper" :class="{ open: show }">
    <div class="comment-panel" v-show="show" @click.stop>
      <div class="panel-header">
        <div class="panel-tabs">
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'user' }" 
            @click.stop="$emit('update:activeTab', 'user')"
          >
            作者
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'comments' }" 
            @click.stop="$emit('update:activeTab', 'comments')"
          >
            评论 {{ commentCount }}
          </button>
        </div>
        <button class="close-btn" @click="$emit('close')">
          <el-icon><Close /></el-icon>
        </button>
      </div>

      <!-- 作者信息 -->
      <UserPanel
        v-if="activeTab === 'user'"
        :creator-name="creatorName"
        :creator-avatar="creatorAvatar"
        :publish-time="publishTime"
        :is-own-video="isOwnVideo"
        :is-subscribed="isSubscribed"
        :videos="authorVideos"
        :loading="authorLoading"
        @toggle-subscribe="$emit('toggle-subscribe')"
        @go-to-user-detail="$emit('go-to-user-detail')"
        @go-to-video="$emit('go-to-video', $event)"
      />

      <!-- 评论 -->
      <CommentPanel
        v-else
        :comments="comments"
        :user-avatar="userAvatar"
        @add-comment="$emit('add-comment', $event)"
        @toggle-comment-like="$emit('toggle-comment-like', $event)"
        @reply-comment="$emit('reply-comment', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { Close } from '@element-plus/icons-vue';
import UserPanel from './UserPanel.vue';
import CommentPanel from './CommentPanel.vue';

defineProps({
  show: Boolean,
  activeTab: String,
  commentCount: [String, Number],
  creatorName: String,
  creatorAvatar: String,
  publishTime: String,
  isOwnVideo: Boolean,
  isSubscribed: Boolean,
  authorVideos: Array,
  authorLoading: Boolean,
  comments: Array,
  userAvatar: String
});

defineEmits([
  'close',
  'update:activeTab',
  'toggle-subscribe',
  'go-to-user-detail',
  'go-to-video',
  'add-comment',
  'toggle-comment-like',
  'reply-comment'
]);
</script>

<style scoped>
.sidebar-wrapper {
  width: 0;
  height: 100%;
  overflow: hidden;
  flex: 0 0 auto;
  transition: width 0.3s ease;
}

.sidebar-wrapper.open {
  width: 460px;
}

.comment-panel {
  position: relative;
  width: 460px;
  height: 100%;
  background: linear-gradient(135deg, rgba(20, 25, 35, 0.98) 0%, rgba(30, 35, 50, 0.98) 100%);
  backdrop-filter: blur(20px);
  z-index: 1;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 30px rgba(0,0,0,0.5);
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  transform: translateX(100%);
  transition: transform 0.3s ease;
}

.sidebar-wrapper.open .comment-panel {
  transform: translateX(0);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.panel-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab-btn {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.85);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.tab-btn.active {
  background: rgba(0, 161, 214, 0.25);
  border-color: rgba(0, 161, 214, 0.35);
  color: #fff;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

@media (max-width: 768px) {
  .sidebar-wrapper.open {
    width: 100%;
  }
  
  .comment-panel {
    width: 100%;
  }
}
</style>
