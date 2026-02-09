<template>
  <div class="side-actions" :class="{ 'hidden': isCleanMode }">
    <!-- 头像 -->
    <div class="action-item avatar-item" @click.stop="$emit('toggle-user-panel')">
      <div class="avatar-link">
        <el-avatar :size="48" :src="creatorAvatar || defaultAvatar"></el-avatar>
        <div 
          class="follow-badge" 
          v-if="!isSubscribed && !isOwnVideo" 
          @click.stop="$emit('toggle-subscribe')"
        >
          <el-icon><Plus /></el-icon>
        </div>
      </div>
    </div>

    <!-- 点赞 -->
    <div class="action-item" :class="{ 'active': isLiked }" @click="$emit('toggle-like')">
      <div class="action-icon">
        <svg viewBox="0 0 1024 1024">
          <path d="M885.9 533.7c16.8-22.2 26.1-49.4 26.1-77.7 0-44.9-25.1-87.4-65.5-111.1a67.67 67.67 0 0 0-34.3-9.3H572.4l6-122.9c1.4-29.7-9.1-57.9-29.5-79.4-20.5-21.5-48.1-33.4-77.9-33.4-52 0-98 35-111.8 85.1l-85.9 311h-.3v428h472.3c9.2 0 18.2-1.8 26.5-5.4 47.6-20.3 78.3-66.8 78.3-118.4 0-12.6-1.8-25-5.4-37 16.8-22.2 26.1-49.4 26.1-77.7 0-12.6-1.8-25-5.4-37 16.8-22.2 26.1-49.4 26.1-77.7-.2-12.6-2-25.1-5.6-37.1zM112 528v364c0 17.7 14.3 32 32 32h65V496h-65c-17.7 0-32 14.3-32 32z"/>
        </svg>
      </div>
      <span class="action-count">{{ likes }}</span>
    </div>

    <!-- 点踩 -->
    <div class="action-item" :class="{ 'active': isDisliked }" @click="$emit('toggle-dislike')">
      <div class="action-icon">
        <svg viewBox="0 0 1024 1024">
          <path d="M885.9 490.3c3.6-12 5.4-24.4 5.4-37 0-28.3-9.3-55.5-26.1-77.7 3.6-12 5.4-24.4 5.4-37 0-28.3-9.3-55.5-26.1-77.7 3.6-12 5.4-24.4 5.4-37 0-51.6-30.7-98.1-78.3-118.4a66.1 66.1 0 0 0-26.5-5.4H273.5c-9.2 0-18.2 1.8-26.5 5.4-47.6 20.3-78.3 66.8-78.3 118.4v428h.3l85.8 310.8C268.7 969 314.7 1004 366.7 1004c29.7 0 57.4-11.8 77.9-33.4 20.5-21.5 31-49.7 29.5-79.4l-6-122.9h239.9c12.1 0 23.9-3.2 34.3-9.3 40.4-23.5 65.5-66.1 65.5-111 0-28.3-9.3-55.5-26.1-77.7zM112 132v364c0 17.7 14.3 32 32 32h65V100h-65c-17.7 0-32 14.3-32 32z"/>
        </svg>
      </div>
    </div>

    <!-- 评论 -->
    <div class="action-item" @click.stop="$emit('toggle-comment-panel')">
      <div class="action-icon">
        <svg viewBox="0 0 1024 1024">
          <path d="M573 421c-23.1 0-41 17.9-41 40s17.9 40 41 40c21.1 0 39-17.9 39-40s-17.9-40-39-40zM293 421c-23.1 0-41 17.9-41 40s17.9 40 41 40c21.1 0 39-17.9 39-40s-17.9-40-39-40z"/><path d="M894 345c-48.1-66-115.3-110.1-189-130v0.1c-17.1-19-36.4-36.5-58-52.1-163.7-119-393.5-82.7-513 81-96.3 133-92.2 311.9 6 439l0.8 132.6c0 3.2 0.5 6.4 1.5 9.4 5.3 16.9 23.3 26.2 40.1 20.9L309 781c66.8 28.5 139.8 37.1 210.3 26.5 3.8-0.6 7.5-1.2 11.2-1.9 118.3-20.4 219.8-96.2 275.5-198.2 56.6-103.6 62.8-225.5 17-334.4zM576.8 736.4c-3.4 0.6-6.8 1.2-10.2 1.7-66.2 10.7-134.6 2.1-197-24.8l-22.6-9.7-177.8 59.3 1.4-134.8-12.1-15.8c-84.8-109.9-87.8-263.7-5.2-377.1 102.8-141 302.7-172.5 444.3-70.1 141.6 102.5 172.5 302.7 70.1 444.3-49.5 68.4-123.9 113.6-207.9 127z"/>
        </svg>
      </div>
      <span class="action-count">{{ commentCount }}</span>
    </div>

    <!-- 收藏 -->
    <div class="action-item" :class="{ 'active': isCollected }" @click="$emit('toggle-collect')">
      <div class="action-icon">
        <svg viewBox="0 0 1024 1024">
          <path d="M908.1 353.1l-253.9-36.9L540.7 86.1c-3.1-6.3-8.2-11.4-14.5-14.5-15.8-7.8-35-1.3-42.9 14.5L369.8 316.2l-253.9 36.9c-7 1-13.4 4.3-18.3 9.3-12.3 12.7-12.1 32.9 0.6 45.3l183.7 179.1-43.4 252.9c-1.2 6.9-0.1 14.1 3.2 20.3 8.2 15.6 27.6 21.7 43.2 13.4L512 754l227.1 119.4c6.2 3.3 13.4 4.4 20.3 3.2 17.4-3 29.1-19.5 26.1-36.9l-43.4-252.9 183.7-179.1c5-4.9 8.3-11.3 9.3-18.3 2.7-17.5-9.5-33.7-27-36.3z"/>
        </svg>
      </div>
      <span class="action-count">{{ collectCount }}</span>
    </div>

    <!-- 分享 -->
    <div class="action-item" @click="$emit('share')">
      <div class="action-icon">
        <svg viewBox="0 0 1024 1024">
          <path d="M752 664c-28.5 0-54.8 10-75.4 26.7L469.4 540.8c3.5-13.5 5.6-27.6 5.6-42.1s-2.1-28.6-5.6-42.1l207.2-149.9c20.6 16.7 46.9 26.7 75.4 26.7 66.2 0 120-53.8 120-120s-53.8-120-120-120-120 53.8-120 120c0 11.6 1.6 22.7 4.7 33.3L432.4 396.6c-23.3-30.3-59.5-49.9-100.4-49.9-70.7 0-128 57.3-128 128s57.3 128 128 128c40.9 0 77.1-19.6 100.4-49.9l204.3 149.9c-3.1 10.6-4.7 21.7-4.7 33.3 0 66.2 53.8 120 120 120s120-53.8 120-120-53.8-120-120-120z"/>
        </svg>
      </div>
      <span class="action-count">分享</span>
    </div>
  </div>
</template>

<script setup>
import { Plus } from '@element-plus/icons-vue';

defineProps({
  creatorAvatar: String,
  isSubscribed: Boolean,
  isOwnVideo: Boolean,
  isLiked: Boolean,
  isDisliked: Boolean,
  isCollected: Boolean,
  likes: [String, Number],
  commentCount: [String, Number],
  collectCount: [String, Number],
  isCleanMode: Boolean
});

defineEmits([
  'toggle-user-panel',
  'toggle-subscribe',
  'toggle-like',
  'toggle-dislike',
  'toggle-comment-panel',
  'toggle-collect',
  'share'
]);

const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';
</script>

<style scoped>
.side-actions {
  position: absolute;
  right: 16px;
  bottom: 85px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  z-index: 100;
  transition: opacity 0.3s, transform 0.3s;
}

.side-actions.hidden {
  opacity: 0;
  transform: translateX(20px);
  pointer-events: none;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: transform 0.2s;
}

.action-item:hover {
  transform: scale(1.1);
}

.action-item.active .action-icon svg {
  fill: #FB7299;
}

.avatar-item {
  margin-bottom: 8px;
}

.avatar-link {
  position: relative;
  display: block;
}

.avatar-link .el-avatar {
  border: 2px solid #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.follow-badge {
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 20px;
  background: #FB7299;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  border: 2px solid #000;
}

.action-icon {
  width: 44px;
  height: 44px;
  background: rgba(255,255,255,0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.action-icon svg {
  width: 24px;
  height: 24px;
  fill: #fff;
}

.action-count {
  font-size: 12px;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}
</style>
