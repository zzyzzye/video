<template>
  <div class="user-panel">
    <div class="user-header">
      <el-avatar :size="56" :src="creatorAvatar || defaultAvatar" />
      <div class="user-meta">
        <div class="user-name">@{{ creatorName }}</div>
        <div class="user-sub">
          <span class="publish-time">· {{ publishTime }}</span>
        </div>
      </div>
    </div>
    
    <div class="user-actions">
      <el-button 
        v-if="!isOwnVideo" 
        type="primary" 
        size="small" 
        @click="$emit('toggle-subscribe')"
      >
        {{ isSubscribed ? '已关注' : '关注' }}
      </el-button>
      <el-button size="small" @click="$emit('go-to-user-detail')">
        查看主页
      </el-button>
    </div>
    
    <div class="user-tip">TA 的视频</div>

    <div class="user-videos" v-loading="loading">
      <div class="user-videos-grid" v-if="videos.length">
        <div
          v-for="video in videos"
          :key="video.id"
          class="user-video-card"
          @click="$emit('go-to-video', video.id)"
        >
          <div class="user-video-thumb">
            <img :src="video.thumbnail || defaultThumbnail" alt="" />
            <div class="user-video-overlay">
              <span>{{ formatNumber(video.views_count || video.views) }} 次观看</span>
            </div>
          </div>
          <div class="user-video-title">{{ video.title }}</div>
        </div>
      </div>
      
      <div class="user-videos-empty" v-else-if="!loading">
        暂无视频
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  creatorName: String,
  creatorAvatar: String,
  publishTime: String,
  isOwnVideo: Boolean,
  isSubscribed: Boolean,
  videos: { type: Array, default: () => [] },
  loading: Boolean
});

defineEmits(['toggle-subscribe', 'go-to-user-detail', 'go-to-video']);

const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';
const defaultThumbnail = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 9"><rect fill="%23333" width="16" height="9"/></svg>';

const formatNumber = (n) => {
  if (!n) return '0';
  if (n >= 10000) return (n/10000).toFixed(1)+'万';
  if (n >= 1000) return (n/1000).toFixed(1)+'K';
  return n.toString();
};
</script>

<style scoped>
.user-panel {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.user-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.user-name {
  font-size: 16px;
  color: #fff;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-sub {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.user-actions {
  display: flex;
  gap: 10px;
}

.user-tip {
  color: rgba(255, 255, 255, 0.45);
  font-size: 12px;
  line-height: 1.6;
}

.user-videos {
  margin-top: 6px;
}

.user-videos-grid {
  column-count: 2;
  column-gap: 12px;
}

.user-video-card {
  break-inside: avoid;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 12px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
}

.user-video-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.3);
  border-color: rgba(0, 161, 214, 0.35);
}

.user-video-thumb {
  position: relative;
  width: 100%;
  overflow: hidden;
}

.user-video-thumb img {
  display: block;
  width: 100%;
  height: auto;
  object-fit: cover;
  background: #111;
}

.user-video-overlay {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  padding: 6px 8px;
  background: linear-gradient(180deg, transparent, rgba(0,0,0,0.6));
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
}

.user-video-title {
  padding: 10px 10px 12px;
  color: #fff;
  font-size: 13px;
  line-height: 1.5;
}

.user-videos-empty {
  color: rgba(255, 255, 255, 0.45);
  font-size: 12px;
  padding: 16px 0;
}

.user-videos:deep(.el-loading-mask) {
  background-color: rgba(0,0,0,0.35);
}
</style>
