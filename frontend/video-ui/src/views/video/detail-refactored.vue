<template>
  <div class="immersive-player-page" @wheel="handleWheel">
    <div class="main-stage" :class="{ 'sidebar-open': showSidebar }">
      <!-- 视频滑动容器 -->
      <VideoSlider
        :prev-video="prevVideo"
        :next-video="nextVideo"
        :slider-style="sliderStyle"
        :is-transitioning="isTransitioning"
      >
        <!-- 视频播放器 -->
        <VideoPlayer
          ref="playerRef"
          :video-id="videoId"
          :hls-url="videoData.hls_file"
          :poster-url="videoData.thumbnail"
          :danmaku-list="danmakuList"
          :subtitle-list="subtitleList"
          :subtitle-style="subtitleStyle"
          :is-clean-mode="isCleanMode"
          @play="isPaused = false"
          @pause="isPaused = true"
          @danmaku-send="sendDanmaku"
        />
      </VideoSlider>

      <!-- 顶部导航栏 -->
      <TopBar
        :is-clean-mode="isCleanMode"
        :is-own-video="isOwnVideo"
        :video-id="videoId"
        @go-back="goBack"
        @report="reportVideo"
        @not-interested="notInterested"
      />

      <!-- 右侧互动栏 -->
      <VideoActions
        :creator-avatar="videoData.creatorAvatar"
        :is-subscribed="isSubscribed"
        :is-own-video="isOwnVideo"
        :is-liked="isLiked"
        :is-disliked="isDisliked"
        :is-collected="isCollected"
        :likes="videoData.likes"
        :comment-count="videoData.commentCount"
        :collect-count="videoData.collectCount"
        :is-clean-mode="isCleanMode"
        @toggle-user-panel="openSidebar('user')"
        @toggle-subscribe="toggleSubscribe"
        @toggle-like="toggleLike"
        @toggle-dislike="toggleDislike"
        @toggle-comment-panel="openSidebar('comments')"
        @toggle-collect="toggleCollect"
        @share="shareVideo"
      />

      <!-- 左下角视频信息 -->
      <VideoInfo
        :video-data="videoData"
        :is-paused="isPaused"
        :is-clean-mode="isCleanMode"
        @ai-summarize="aiSummarize"
        @ai-recognize="aiRecognizeFrame"
      />

      <!-- Toast 提示 -->
      <div class="toast-container">
        <transition-group name="toast">
          <div v-for="toast in toasts" :key="toast.id" class="toast-item">
            <el-icon v-if="toast.icon === 'play'"><VideoPlay /></el-icon>
            <el-icon v-else-if="toast.icon === 'pause'"><VideoPause /></el-icon>
            <el-icon v-else><InfoFilled /></el-icon>
            <span>{{ toast.message }}</span>
          </div>
        </transition-group>
      </div>
    </div>

    <!-- 右侧侧边栏 -->
    <Sidebar
      :show="showSidebar"
      :active-tab="sidebarTab"
      :comment-count="videoData.commentCount"
      :creator-name="videoData.creatorName"
      :creator-avatar="videoData.creatorAvatar"
      :publish-time="videoData.publishTime"
      :is-own-video="isOwnVideo"
      :is-subscribed="isSubscribed"
      :author-videos="authorVideos"
      :author-loading="authorLoading"
      :comments="comments"
      :user-avatar="userAvatar"
      @close="showSidebar = false"
      @update:active-tab="sidebarTab = $event"
      @toggle-subscribe="toggleSubscribe"
      @go-to-user-detail="goToUserDetail"
      @go-to-video="goToVideo"
      @add-comment="handleAddComment"
      @toggle-comment-like="toggleCommentLike"
      @reply-comment="replyToComment"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '@/store/user';
import { VideoPlay, VideoPause, InfoFilled } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import service from '@/api/user';

// 组件导入
import TopBar from './components/TopBar.vue';
import VideoPlayer from './components/VideoPlayer.vue';
import VideoActions from './components/VideoActions.vue';
import VideoInfo from './components/VideoInfo.vue';
import Sidebar from './components/Sidebar.vue';
import VideoSlider from './components/VideoSlider.vue';

// Composables
import { useVideoDetail } from './composables/useVideoDetail';
import { useSubtitles } from './composables/useSubtitles';
import { useComments, useDanmaku } from './composables/useComments';
import { useVideoSlider } from './composables/useVideoSlider';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const videoId = ref(route.params.id);

// 使用 composables
const {
  videoData,
  isOwnVideo,
  isSubscribed,
  isLiked,
  isDisliked,
  isCollected,
  loading,
  fetchVideoDetail,
  recordView,
  toggleSubscribe,
  toggleLike,
  toggleDislike,
  toggleCollect,
  shareVideo,
  formatNumber,
  formatDate,
  formatTimeAgo
} = useVideoDetail(videoId);

const { subtitleList, subtitleStyle, fetchSubtitles } = useSubtitles(videoId);
const { comments, fetchComments, addComment, toggleCommentLike } = useComments(videoId, formatTimeAgo);
const { danmakuList, fetchDanmaku, sendDanmaku } = useDanmaku(videoId);
const {
  videoList,
  prevVideo,
  nextVideo,
  sliderStyle,
  isTransitioning,
  fetchVideoList,
  handleWheel: handleVideoWheel
} = useVideoSlider(videoId);

// 本地状态
const playerRef = ref(null);
const isPaused = ref(true);
const isCleanMode = ref(false);
const showSidebar = ref(false);
const sidebarTab = ref('user');
const authorVideos = ref([]);
const authorLoading = ref(false);
const toasts = ref([]);
let toastId = 0;

const userAvatar = computed(() => userStore.userInfo?.avatar || '');

// Toast 提示
const showToast = (message, icon = 'info') => {
  const id = ++toastId;
  toasts.value.push({ id, message, icon });
  if (toasts.value.length > 2) toasts.value.shift();
  setTimeout(() => {
    const index = toasts.value.findIndex(t => t.id === id);
    if (index > -1) toasts.value.splice(index, 1);
  }, 2000);
};

// 侧边栏操作
const openSidebar = (tab) => {
  sidebarTab.value = tab;
  showSidebar.value = true;
  if (tab === 'user' && authorVideos.value.length === 0) {
    fetchAuthorVideos();
  }
};

// 获取作者视频
const fetchAuthorVideos = async () => {
  if (!videoData.value.creatorId || authorLoading.value) return;
  authorLoading.value = true;
  try {
    const response = await service({
      url: '/videos/videos/',
      method: 'get',
      params: { user_id: videoData.value.creatorId, page_size: 30 }
    });
    authorVideos.value = response.results || response || [];
  } catch (error) {
    console.error('获取作者视频失败:', error);
    authorVideos.value = [];
  } finally {
    authorLoading.value = false;
  }
};

// 导航操作
const goBack = () => router.back();
const goToVideo = (id) => { if (id) router.push(`/video/${id}`); };
const goToUserDetail = () => {
  if (!videoData.value.creatorId) return;
  router.push(`/user/${videoData.value.creatorId}`);
};

// 举报和不感兴趣
const reportVideo = () => {
  // 举报成功的提示已在 ReportDialog 中处理
};
const notInterested = () => ElMessage.success('已标记为不感兴趣');

// AI 功能
const aiSummarize = () => ElMessage.info('AI正在分析视频内容...');
const aiRecognizeFrame = () => ElMessage.info('AI正在识别当前画面...');

// 评论操作
const handleAddComment = async (text) => {
  const success = await addComment(text);
  if (success) {
    videoData.value.commentCount += 1;
  }
};

const replyToComment = (comment) => {
  ElMessage.info(`回复 @${comment.username}`);
};

// 滚轮切换视频
const handleWheel = (e) => {
  handleVideoWheel(e, async (targetVideo, preloadedData) => {
    // 先更新数据再切换路由，减少闪烁
    videoData.value = {
      id: preloadedData.id,
      title: preloadedData.title,
      description: preloadedData.description || '',
      views: formatNumber(preloadedData.views_count),
      likes: formatNumber(preloadedData.likes_count),
      commentCount: preloadedData.comments_count || 0,
      collectCount: preloadedData.favorites_count || 0,
      publishTime: formatDate(preloadedData.published_at || preloadedData.created_at),
      creatorName: preloadedData.user?.username || '未知用户',
      creatorId: preloadedData.user?.id,
      creatorAvatar: preloadedData.user?.avatar || '',
      category: preloadedData.category,
      tags: preloadedData.tags || [],
      hls_file: preloadedData.hls_file,
      thumbnail: preloadedData.thumbnail
    };
    
    // 重置作者视频
    authorVideos.value = [];
    
    // 更新状态
    isLiked.value = preloadedData.is_liked || false;
    isCollected.value = preloadedData.is_favorited || false;
    videoId.value = targetVideo.id;
    
    // 重新初始化播放器
    if (playerRef.value) {
      playerRef.value.destroy();
    }
    
    // 重新加载数据
    await fetchDanmaku();
    await fetchSubtitles();
    fetchComments();
    recordView();
    
    // 如果侧边栏打开且在作者tab，重新加载作者视频
    if (showSidebar.value && sidebarTab.value === 'user') {
      fetchAuthorVideos();
    }
  });
};

// 初始化
onMounted(async () => {
  await fetchDanmaku();
  await fetchSubtitles();
  await fetchVideoDetail();
  fetchComments();
  recordView();
  fetchVideoList();
});

onBeforeUnmount(() => {
  if (playerRef.value) {
    playerRef.value.destroy();
  }
});
</script>

<style scoped>
.immersive-player-page {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: #000;
  overflow: hidden;
  display: flex;
  flex-direction: row;
}

.main-stage {
  position: relative;
  flex: 1;
  height: 100%;
  overflow: hidden;
}

.toast-container {
  position: absolute;
  top: 80px;
  right: 20px;
  z-index: 300;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(12px);
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  white-space: nowrap;
}

.toast-item .el-icon {
  font-size: 18px;
  color: #00a1d6;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(40px);
}

@media (max-width: 768px) {
  .immersive-player-page {
    flex-direction: column;
  }
  
  .main-stage {
    width: 100%;
  }
}
</style>
