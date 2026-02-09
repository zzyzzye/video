<template>
  <div class="immersive-player-page" @wheel="handleWheel">
    <div class="main-stage" :class="{ 'sidebar-open': showSidebar }">
    <!-- 视频滑动容器 -->
    <div class="video-slider" :style="sliderStyle" :class="{ 'transitioning': isTransitioning }">
      <!-- 上一个视频（预览） -->
      <div class="video-slide prev-slide" v-if="prevVideo">
        <div class="slide-preview">
          <img :src="prevVideo.thumbnail || defaultThumbnail" alt="" />
          <div class="slide-title">{{ prevVideo.title }}</div>
        </div>
      </div>
      
      <!-- 当前视频 -->
      <div class="video-slide current-slide">
        <div class="video-container" ref="artPlayerRef"></div>
        
        <!-- 自定义字幕覆盖层 -->
        <div class="custom-subtitle-overlay" v-if="currentSubtitle && !isCleanMode" :style="computedSubtitleStyle">
          <div class="subtitle-main" :style="mainTextStyle" v-if="currentSubtitle.text">
            {{ currentSubtitle.text }}
          </div>
          <div class="subtitle-sub" :style="subTextStyle" v-if="currentSubtitle.translation">
            {{ currentSubtitle.translation }}
          </div>
        </div>
      </div>
      
      <!-- 下一个视频（预览） -->
      <div class="video-slide next-slide" v-if="nextVideo">
        <div class="slide-preview">
          <img :src="nextVideo.thumbnail || defaultThumbnail" alt="" />
          <div class="slide-title">{{ nextVideo.title }}</div>
        </div>
      </div>
    </div>

    <!-- 顶部导航栏 -->
    <div class="top-bar" :class="{ 'hidden': isCleanMode }">
      <div class="top-left">
        <button class="back-btn" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
        </button>
      </div>
      <div class="top-right">
        <button class="top-btn" @click="showMoreMenu = !showMoreMenu">
          <el-icon><MoreFilled /></el-icon>
        </button>
        <!-- 更多菜单 -->
        <transition name="fade">
          <div class="more-menu" v-if="showMoreMenu">
            <div class="menu-item" @click="reportVideo">
              <el-icon><WarningFilled /></el-icon>
              <span>举报</span>
            </div>
            <div class="menu-item" @click="notInterested">
              <el-icon><CircleClose /></el-icon>
              <span>不感兴趣</span>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- 视频播放器 - 移除，已移到slider中 -->

    <!-- 右侧互动栏 -->
    <div class="side-actions" :class="{ 'hidden': isCleanMode }">
      <div class="action-item avatar-item" @click.stop="toggleUserPanel">
        <div class="avatar-link">
          <el-avatar :size="48" :src="videoData.creatorAvatar || defaultAvatar"></el-avatar>
          <div class="follow-badge" v-if="!isSubscribed" @click.stop="toggleSubscribe">
            <el-icon><Plus /></el-icon>
          </div>
        </div>
      </div>

      <div class="action-item" :class="{ 'active': isLiked }" @click="toggleLike">
        <div class="action-icon">
          <svg viewBox="0 0 1024 1024"><path d="M885.9 533.7c16.8-22.2 26.1-49.4 26.1-77.7 0-44.9-25.1-87.4-65.5-111.1a67.67 67.67 0 0 0-34.3-9.3H572.4l6-122.9c1.4-29.7-9.1-57.9-29.5-79.4-20.5-21.5-48.1-33.4-77.9-33.4-52 0-98 35-111.8 85.1l-85.9 311h-.3v428h472.3c9.2 0 18.2-1.8 26.5-5.4 47.6-20.3 78.3-66.8 78.3-118.4 0-12.6-1.8-25-5.4-37 16.8-22.2 26.1-49.4 26.1-77.7 0-12.6-1.8-25-5.4-37 16.8-22.2 26.1-49.4 26.1-77.7-.2-12.6-2-25.1-5.6-37.1zM112 528v364c0 17.7 14.3 32 32 32h65V496h-65c-17.7 0-32 14.3-32 32z"/></svg>
        </div>
        <span class="action-count">{{ videoData.likes }}</span>
      </div>

      <div class="action-item" :class="{ 'active': isDisliked }" @click="toggleDislike">
        <div class="action-icon">
          <svg viewBox="0 0 1024 1024"><path d="M885.9 490.3c3.6-12 5.4-24.4 5.4-37 0-28.3-9.3-55.5-26.1-77.7 3.6-12 5.4-24.4 5.4-37 0-28.3-9.3-55.5-26.1-77.7 3.6-12 5.4-24.4 5.4-37 0-51.6-30.7-98.1-78.3-118.4a66.1 66.1 0 0 0-26.5-5.4H273.5c-9.2 0-18.2 1.8-26.5 5.4-47.6 20.3-78.3 66.8-78.3 118.4v428h.3l85.8 310.8C268.7 969 314.7 1004 366.7 1004c29.7 0 57.4-11.8 77.9-33.4 20.5-21.5 31-49.7 29.5-79.4l-6-122.9h239.9c12.1 0 23.9-3.2 34.3-9.3 40.4-23.5 65.5-66.1 65.5-111 0-28.3-9.3-55.5-26.1-77.7zM112 132v364c0 17.7 14.3 32 32 32h65V100h-65c-17.7 0-32 14.3-32 32z"/></svg>
        </div>
      </div>

      <div class="action-item" @click.stop="toggleCommentPanel">
        <div class="action-icon">
          <svg viewBox="0 0 1024 1024"><path d="M573 421c-23.1 0-41 17.9-41 40s17.9 40 41 40c21.1 0 39-17.9 39-40s-17.9-40-39-40zM293 421c-23.1 0-41 17.9-41 40s17.9 40 41 40c21.1 0 39-17.9 39-40s-17.9-40-39-40z"/><path d="M894 345c-48.1-66-115.3-110.1-189-130v0.1c-17.1-19-36.4-36.5-58-52.1-163.7-119-393.5-82.7-513 81-96.3 133-92.2 311.9 6 439l0.8 132.6c0 3.2 0.5 6.4 1.5 9.4 5.3 16.9 23.3 26.2 40.1 20.9L309 781c66.8 28.5 139.8 37.1 210.3 26.5 3.8-0.6 7.5-1.2 11.2-1.9 118.3-20.4 219.8-96.2 275.5-198.2 56.6-103.6 62.8-225.5 17-334.4zM576.8 736.4c-3.4 0.6-6.8 1.2-10.2 1.7-66.2 10.7-134.6 2.1-197-24.8l-22.6-9.7-177.8 59.3 1.4-134.8-12.1-15.8c-84.8-109.9-87.8-263.7-5.2-377.1 102.8-141 302.7-172.5 444.3-70.1 141.6 102.5 172.5 302.7 70.1 444.3-49.5 68.4-123.9 113.6-207.9 127z"/></svg>
        </div>
        <span class="action-count">{{ videoData.commentCount }}</span>
      </div>

      <div class="action-item" :class="{ 'active': isCollected }" @click="toggleCollect">
        <div class="action-icon">
          <svg viewBox="0 0 1024 1024"><path d="M908.1 353.1l-253.9-36.9L540.7 86.1c-3.1-6.3-8.2-11.4-14.5-14.5-15.8-7.8-35-1.3-42.9 14.5L369.8 316.2l-253.9 36.9c-7 1-13.4 4.3-18.3 9.3-12.3 12.7-12.1 32.9 0.6 45.3l183.7 179.1-43.4 252.9c-1.2 6.9-0.1 14.1 3.2 20.3 8.2 15.6 27.6 21.7 43.2 13.4L512 754l227.1 119.4c6.2 3.3 13.4 4.4 20.3 3.2 17.4-3 29.1-19.5 26.1-36.9l-43.4-252.9 183.7-179.1c5-4.9 8.3-11.3 9.3-18.3 2.7-17.5-9.5-33.7-27-36.3z"/></svg>
        </div>
        <span class="action-count">{{ videoData.collectCount || 0 }}</span>
      </div>

      <div class="action-item" @click="shareVideo">
        <div class="action-icon">
          <svg viewBox="0 0 1024 1024"><path d="M752 664c-28.5 0-54.8 10-75.4 26.7L469.4 540.8c3.5-13.5 5.6-27.6 5.6-42.1s-2.1-28.6-5.6-42.1l207.2-149.9c20.6 16.7 46.9 26.7 75.4 26.7 66.2 0 120-53.8 120-120s-53.8-120-120-120-120 53.8-120 120c0 11.6 1.6 22.7 4.7 33.3L432.4 396.6c-23.3-30.3-59.5-49.9-100.4-49.9-70.7 0-128 57.3-128 128s57.3 128 128 128c40.9 0 77.1-19.6 100.4-49.9l204.3 149.9c-3.1 10.6-4.7 21.7-4.7 33.3 0 66.2 53.8 120 120 120s120-53.8 120-120-53.8-120-120-120z"/></svg>
        </div>
        <span class="action-count">分享</span>
      </div>
    </div>

    <!-- 左下角视频信息 -->
    <div class="video-info-overlay" :class="{ 'hidden': isCleanMode }">
      <div class="creator-row">
        <router-link :to="`/user/${videoData.creatorId}`" class="creator-name">@{{ videoData.creatorName }}</router-link>
        <span class="publish-time">· {{ videoData.publishTime }}</span>
      </div>
      <h1 class="video-title">{{ videoData.title }}</h1>
      <div class="video-description" :class="{ 'expanded': descriptionExpanded }">
        <span class="desc-text" ref="descTextRef">{{ videoData.description }}</span><span class="expand-btn" v-if="showExpandBtn && !descriptionExpanded" @click="descriptionExpanded = true">...展开</span><span class="collapse-btn" v-if="descriptionExpanded" @click="descriptionExpanded = false"> 收起</span>
      </div>
      <div class="video-tags">
        <span class="tag" v-if="videoData.category">#{{ typeof videoData.category === 'object' ? videoData.category.name : videoData.category }}</span>
        <span class="tag" v-for="tag in videoData.tags?.slice(0, 3)" :key="tag.id || tag">#{{ typeof tag === 'object' ? tag.name : tag }}</span>
      </div>
      <div class="ai-actions">
        <router-link v-if="videoData.collection" :to="`/collection/${videoData.collection.id}`" class="ai-btn collection-btn">
          <svg viewBox="0 0 1024 1024" width="16" height="16"><path fill="currentColor" d="M880 112H144c-17.7 0-32 14.3-32 32v736c0 17.7 14.3 32 32 32h736c17.7 0 32-14.3 32-32V144c0-17.7-14.3-32-32-32zM368 744c0 4.4-3.6 8-8 8h-80c-4.4 0-8-3.6-8-8V280c0-4.4 3.6-8 8-8h80c4.4 0 8 3.6 8 8v464zm192-280c0 4.4-3.6 8-8 8h-80c-4.4 0-8-3.6-8-8V280c0-4.4 3.6-8 8-8h80c4.4 0 8 3.6 8 8v184zm192 72c0 4.4-3.6 8-8 8h-80c-4.4 0-8-3.6-8-8V280c0-4.4 3.6-8 8-8h80c4.4 0 8 3.6 8 8v256z"/></svg>
          <span>{{ videoData.collection.name }}</span>
          <span class="collection-index">{{ videoData.collectionIndex }}/{{ videoData.collection.count }}</span>
        </router-link>
        <button class="ai-btn" @click="aiSummarize">
          <svg viewBox="0 0 1024 1024" width="16" height="16"><path fill="currentColor" d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z"/><path fill="currentColor" d="M464 336a48 48 0 1 0 96 0 48 48 0 1 0-96 0zm72 112h-48c-4.4 0-8 3.6-8 8v272c0 4.4 3.6 8 8 8h48c4.4 0 8-3.6 8-8V456c0-4.4-3.6-8-8-8z"/></svg>
          <span>AI总结</span>
        </button>
        <button v-if="isPaused" class="ai-btn" @click="aiRecognizeFrame">
          <svg viewBox="0 0 1024 1024" width="16" height="16"><path fill="currentColor" d="M942.2 486.2C847.4 286.5 704.1 186 512 186c-192.2 0-335.4 100.5-430.2 300.3a60.3 60.3 0 0 0 0 51.5C176.6 737.5 319.9 838 512 838c192.2 0 335.4-100.5 430.2-300.3 7.7-16.2 7.7-35 0-51.5zM512 766c-161.3 0-279.4-81.8-362.7-254C232.6 339.8 350.7 258 512 258c161.3 0 279.4 81.8 362.7 254C791.5 684.2 673.4 766 512 766zm-4-430c-97.2 0-176 78.8-176 176s78.8 176 176 176 176-78.8 176-176-78.8-176-176-176zm0 288c-61.9 0-112-50.1-112-112s50.1-112 112-112 112 50.1 112 112-50.1 112-112 112z"/></svg>
          <span>识别画面</span>
        </button>
      </div>
    </div>

    <!-- 上次播放位置气泡 -->
    <transition name="bubble">
      <div class="last-play-bubble" v-if="showLastPlayBubble" :style="{ left: lastPlayPosition + '%' }" @click="jumpToLastPlay">
        <span>上次看到这里</span>
        <div class="bubble-arrow"></div>
      </div>
    </transition>

    <!-- 自定义 Toast 提示 -->
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

    <!-- 右侧侧边栏：与视频平级（占据布局，不覆盖视频） -->
    <div class="sidebar-wrapper" :class="{ open: showSidebar }">
      <div class="comment-panel" v-show="showSidebar" @click.stop>
        <div class="panel-header">
          <div class="panel-tabs">
            <button class="tab-btn" :class="{ active: sidebarTab === 'user' }" @click.stop="sidebarTab = 'user'">作者</button>
            <button class="tab-btn" :class="{ active: sidebarTab === 'comments' }" @click.stop="sidebarTab = 'comments'">
              评论 {{ videoData.commentCount }}
            </button>
          </div>
          <button class="close-btn" @click="closeSidebar"><el-icon><Close /></el-icon></button>
        </div>

        <!-- 作者信息 -->
        <div v-if="sidebarTab === 'user'" class="user-panel">
          <div class="user-header">
            <el-avatar :size="56" :src="videoData.creatorAvatar || defaultAvatar" />
            <div class="user-meta">
              <div class="user-name">@{{ videoData.creatorName }}</div>
              <div class="user-sub">
                <span class="publish-time">· {{ videoData.publishTime }}</span>
              </div>
            </div>
          </div>
          <div class="user-actions">
            <el-button type="primary" size="small" @click="toggleSubscribe">
              {{ isSubscribed ? '已关注' : '关注' }}
            </el-button>
            <el-button size="small" @click="goToUserDetail">查看主页</el-button>
          </div>
          <div class="user-tip">TA 的视频</div>

          <div class="user-videos" v-loading="authorLoading">
            <div class="user-videos-grid" v-if="authorVideos.length">
              <div
                v-for="video in authorVideos"
                :key="video.id"
                class="user-video-card"
                @click="goToVideo(video.id)"
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
            <div class="user-videos-empty" v-else-if="!authorLoading">
              暂无视频
            </div>
          </div>
        </div>

        <!-- 评论 -->
        <div v-else class="comments-panel">
          <div class="comment-form">
            <el-avatar :size="36" :src="userAvatar || defaultAvatar"></el-avatar>
            <div class="input-wrapper">
              <el-input v-model="commentText" placeholder="发一条友善的评论" @keyup.enter="addComment" />
              <el-button type="primary" size="small" :disabled="!commentText.trim()" @click="addComment">发送</el-button>
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
                  <span class="action" :class="{ 'active': comment.isLiked }" @click="toggleCommentLike(comment)">
                    <el-icon><CaretTop /></el-icon>{{ comment.likes || '' }}
                  </span>
                  <span class="action" @click="replyToComment(comment)">回复</span>
                </div>
              </div>
            </div>
            <div class="no-comments" v-if="comments.length === 0"><p>暂无评论，快来抢沙发~</p></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onBeforeUnmount, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '@/store/user';
import { ArrowLeft, MoreFilled, Plus, Close, CaretTop, VideoPlay, VideoPause, InfoFilled, WarningFilled, CircleClose } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import service from '@/api/user';
import Artplayer from 'artplayer';
import Hls from 'hls.js';
import artplayerPluginDanmuku from 'artplayer-plugin-danmuku';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const videoId = ref(route.params.id);
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';
const artPlayerRef = ref(null);
let art = null;
let hideControlsTimer = null;
let lastPlayedTime = 0; // 上次播放位置
let wheelLock = false; // 防止滚轮连续触发
const defaultThumbnail = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 9"><rect fill="%23333" width="16" height="9"/></svg>';

const userAvatar = computed(() => userStore.userInfo?.avatar || defaultAvatar);
const isSubscribed = ref(false);
const isLiked = ref(false);
const isDisliked = ref(false);
const isCollected = ref(false);
const isPaused = ref(true); // 视频是否暂停
const descriptionExpanded = ref(false);
const showExpandBtn = ref(false);
const descTextRef = ref(null);
const commentText = ref('');
const showControls = ref(true);
const isCleanMode = ref(false); // 清屏模式
const showCommentPanel = ref(false); // 已废弃，改用 showSidebar
const showMoreMenu = ref(false);
const showSidebar = ref(false);
const sidebarTab = ref('user'); // 'user' | 'comments'
const loading = ref(true);
const showLastPlayBubble = ref(false);
const lastPlayPosition = ref(0); // 百分比位置
const videoList = ref([]); // 视频列表
const currentIndex = ref(-1); // 当前视频在列表中的索引
const slideOffset = ref(0); // 滑动偏移量
const isTransitioning = ref(false); // 是否正在过渡动画
const authorVideos = ref([]); // 作者视频
const authorVideosLoaded = ref(false);
const authorLoading = ref(false);

// 计算上下视频
const prevVideo = computed(() => {
  if (videoList.value.length === 0 || currentIndex.value <= 0) return null;
  return videoList.value[currentIndex.value - 1];
});

const nextVideo = computed(() => {
  if (videoList.value.length === 0 || currentIndex.value >= videoList.value.length - 1) return null;
  return videoList.value[currentIndex.value + 1];
});

// 滑动样式
const sliderStyle = computed(() => ({
  transform: `translateY(${slideOffset.value}px)`
}));

const videoData = ref({
  id: videoId.value, title: '', description: '', views: '0', likes: '0',
  commentCount: 0, collectCount: 0, publishTime: '', creatorName: '',
  creatorId: null, creatorAvatar: '', category: null, tags: [], hls_file: '', thumbnail: '',
  collection: null, collectionIndex: 0 // 合集信息
});

const comments = ref([]);
const danmakuList = ref([]);
const subtitleList = ref([]); // 字幕列表
const currentSubtitle = ref(null); // 当前显示的字幕
const subtitleStyle = ref({
  // 默认样式
  mainColor: '#ffffff',
  mainBorderColor: '#000000',
  subColor: '#ffff00',
  subBorderColor: '#000000',
  fontSize: 20,
  letterSpacing: 0,
  bottomDistance: 50,
  hasShadow: true,
  shadowOpacity: 80,
  strokeWidth: 2,
  shadowOffset: 2,
  fontFamily: 'Source Han Sans',
  isBold: false,
  isItalic: false
});
const toasts = ref([]);
let toastId = 0;

// 显示 Toast 提示
const showToast = (message, icon = 'info') => {
  const id = ++toastId;
  toasts.value.push({ id, message, icon });
  // 最多保留2个
  if (toasts.value.length > 2) {
    toasts.value.shift();
  }
  // 2秒后自动消失
  setTimeout(() => {
    const index = toasts.value.findIndex(t => t.id === id);
    if (index > -1) toasts.value.splice(index, 1);
  }, 2000);
};

const handleMouseMove = () => {
  showControls.value = true;
  clearTimeout(hideControlsTimer);
  hideControlsTimer = setTimeout(() => { if (art && art.playing) showControls.value = false; }, 3000);
};

const toggleControls = () => { if (!showSidebar.value) showControls.value = !showControls.value; };
const toggleCleanMode = () => { 
  isCleanMode.value = !isCleanMode.value;
  showToast(isCleanMode.value ? '已开启清屏模式' : '已退出清屏模式', 'info');
};
const goBack = () => router.back();
const goToVideo = (id) => { if (id) router.push(`/video/${id}`); };
const closeSidebar = () => {
  showSidebar.value = false;
};

const openSidebar = (tab) => {
  sidebarTab.value = tab;
  showSidebar.value = true;
  if (tab === 'user' && !authorVideosLoaded.value) {
    fetchAuthorVideos();
  }
};

watch(showSidebar, (val) => {
  console.log('[detail.vue] showSidebar =>', val);
});

const toggleCommentPanel = () => {
  // 评论入口：只负责打开评论 tab，由右上角关闭按钮负责收起
  openSidebar('comments');
  // 立刻阻断后续可能的点击传播
  return false;
};

const toggleUserPanel = () => {
  // 头像入口：始终打开侧边栏并切到作者 tab（不做“再点关闭”），避免误触导致自动收回
  openSidebar('user');
  return false;
};

const goToUserDetail = () => {
  if (!videoData.value.creatorId) return;
  router.push(`/user/${videoData.value.creatorId}`);
};

// 举报视频
const reportVideo = () => {
  showMoreMenu.value = false;
  ElMessage.info('举报功能开发中');
};

// 不感兴趣
const notInterested = () => {
  showMoreMenu.value = false;
  ElMessage.success('已标记为不感兴趣');
};

const fetchVideoDetail = async () => {
  try {
    loading.value = true;
    const response = await service({ url: `/videos/videos/${videoId.value}/`, method: 'get' });
    videoData.value = {
      id: response.id, title: response.title, description: response.description || '',
      views: formatNumber(response.views_count), likes: formatNumber(response.likes_count),
      commentCount: response.comments_count || 0, collectCount: response.favorites_count || 0,
      publishTime: formatDate(response.published_at || response.created_at),
      creatorName: response.user?.username || '未知用户', creatorId: response.user?.id,
      creatorAvatar: response.user?.avatar || '', category: response.category,
      tags: response.tags || [], hls_file: response.hls_file, thumbnail: response.thumbnail
    };
    authorVideos.value = [];
    authorVideosLoaded.value = false;
    isLiked.value = response.is_liked || false;
    isCollected.value = response.is_favorited || false;
    if (response.hls_file) { 
      await nextTick(); 
      // 先加载字幕，再初始化播放器
      await fetchSubtitles();
      initPlayer(response.hls_file, response.thumbnail); 
    }
    // 检查描述是否溢出
    await nextTick();
    checkDescOverflow();
  } catch (error) {
    console.error('获取视频详情失败:', error);
    ElMessage.error('获取视频详情失败');
  } finally { loading.value = false; }
};

// 检查描述文字是否溢出
const checkDescOverflow = () => {
  if (descTextRef.value) {
    const el = descTextRef.value;
    showExpandBtn.value = el.scrollHeight > el.clientHeight || (videoData.value.description?.length > 60);
  }
};

const fetchComments = async () => {
  try {
    const response = await service({ url: '/videos/comments/', method: 'get', params: { video_id: videoId.value } });
    comments.value = (response.results || []).map(c => ({
      id: c.id, username: c.user?.username || '匿名用户', userAvatar: c.user?.avatar || '',
      text: c.text, time: formatTimeAgo(c.created_at), likes: c.likes_count || 0, isLiked: false
    }));
  } catch (error) { console.error('获取评论失败:', error); }
};

const fetchDanmaku = async () => {
  try {
    const response = await service({ url: '/videos/danmaku/', method: 'get', params: { video_id: videoId.value } });
    danmakuList.value = (response.results || response || []).map(d => ({
      text: d.text || d.content, time: d.time || d.timestamp || 0, color: d.color || '#ffffff', mode: d.mode || 0
    }));
  } catch (error) { danmakuList.value = []; }
};

// 获取字幕
const fetchSubtitles = async () => {
  try {
    const response = await service({ url: `/videos/videos/${videoId.value}/subtitles/`, method: 'get' });
    const subtitles = response.subtitles || [];
    // 转换字幕数据
    subtitleList.value = subtitles.map((sub, index) => ({
      start: sub.startTime || sub.start_time,
      end: sub.endTime || sub.end_time,
      text: sub.text || '',
      translation: sub.translation || ''
    }));
    
    // 加载字幕样式配置（如果有）
    if (response.style) {
      subtitleStyle.value = { ...subtitleStyle.value, ...response.style };
    }
    
    console.log(`加载了 ${subtitleList.value.length} 条字幕`);
  } catch (error) {
    console.error('获取字幕失败:', error);
    subtitleList.value = [];
  }
};

// 更新当前字幕
const updateCurrentSubtitle = () => {
  if (!art || subtitleList.value.length === 0) {
    currentSubtitle.value = null;
    return;
  }
  
  const currentTime = art.currentTime;
  const subtitle = subtitleList.value.find(
    sub => currentTime >= sub.start && currentTime < sub.end
  );
  
  currentSubtitle.value = subtitle || null;
};

// 计算字幕样式
const computedSubtitleStyle = computed(() => {
  const style = subtitleStyle.value;
  return {
    fontSize: `${style.fontSize}px`,
    letterSpacing: `${style.letterSpacing}px`,
    bottom: `${style.bottomDistance}px`,
    fontFamily: style.fontFamily,
    fontWeight: style.isBold ? 'bold' : 'normal',
    fontStyle: style.isItalic ? 'italic' : 'normal',
    textShadow: style.hasShadow 
      ? `${style.shadowOffset}px ${style.shadowOffset}px ${style.shadowOffset * 2}px rgba(0, 0, 0, ${style.shadowOpacity / 100})`
      : 'none'
  };
});

// 主字幕样式
const mainTextStyle = computed(() => ({
  color: subtitleStyle.value.mainColor,
  WebkitTextStroke: `${subtitleStyle.value.strokeWidth}px ${subtitleStyle.value.mainBorderColor}`
}));

// 副字幕样式
const subTextStyle = computed(() => ({
  color: subtitleStyle.value.subColor,
  WebkitTextStroke: `${subtitleStyle.value.strokeWidth}px ${subtitleStyle.value.subBorderColor}`
}));

const fetchAuthorVideos = async () => {
  if (!videoData.value.creatorId || authorLoading.value) return;
  authorLoading.value = true;
  try {
    const response = await service({
      url: '/videos/videos/',
      method: 'get',
      params: { user_id: videoData.value.creatorId, page_size: 30 }  // 修改为 user_id
    });
    authorVideos.value = response.results || response || [];
    authorVideosLoaded.value = true;
    authorVideosLoaded.value = true;
  } catch (error) {
    console.error('获取作者视频失败:', error);
    authorVideos.value = [];
  } finally {
    authorLoading.value = false;
  }
};

const recordView = async () => {
  try { await service({ url: `/videos/videos/${videoId.value}/view/`, method: 'post', data: { watched_duration: 0 } }); }
  catch (error) { console.error('记录观看失败:', error); }
};

// 获取视频列表用于上下切换
const fetchVideoList = async () => {
  try {
    const response = await service({ url: '/videos/videos/', method: 'get', params: { page_size: 20 } });
    videoList.value = response.results || [];
    currentIndex.value = videoList.value.findIndex(v => v.id == videoId.value);
  } catch (error) { console.error('获取视频列表失败:', error); }
};

// 滚轮切换视频
const handleWheel = (e) => {
  if (wheelLock || isTransitioning.value) return;
  
  const delta = e.deltaY;
  if (Math.abs(delta) < 50) return; // 忽略小幅度滚动
  
  if (delta > 0 && nextVideo.value) {
    // 向下滚 - 下一个视频
    slideToVideo('next');
  } else if (delta < 0 && prevVideo.value) {
    // 向上滚 - 上一个视频
    slideToVideo('prev');
  }
};

const slideToVideo = async (direction) => {
  wheelLock = true;
  isTransitioning.value = true;
  
  const targetVideo = direction === 'next' ? nextVideo.value : prevVideo.value;
  if (!targetVideo) return;
  
  // 动画开始前预加载视频数据
  let preloadedData = null;
  try {
    const response = await service({ url: `/videos/videos/${targetVideo.id}/`, method: 'get' });
    preloadedData = {
      id: response.id, title: response.title, description: response.description || '',
      views: formatNumber(response.views_count), likes: formatNumber(response.likes_count),
      commentCount: response.comments_count || 0, collectCount: response.favorites_count || 0,
      publishTime: formatDate(response.published_at || response.created_at),
      creatorName: response.user?.username || '未知用户', creatorId: response.user?.id,
      creatorAvatar: response.user?.avatar || '', category: response.category,
      tags: response.tags || [], hls_file: response.hls_file, thumbnail: response.thumbnail,
      is_liked: response.is_liked, is_favorited: response.is_favorited
    };
  } catch (e) { console.error('预加载失败', e); }
  
  const vh = window.innerHeight;
  slideOffset.value = direction === 'next' ? -vh : vh;
  
  setTimeout(async () => {
    // 先更新数据再切换路由，减少闪烁
    if (preloadedData) {
      videoData.value = preloadedData;
      authorVideos.value = [];
      authorVideosLoaded.value = false;
      isLiked.value = preloadedData.is_liked || false;
      isCollected.value = preloadedData.is_favorited || false;
      videoId.value = targetVideo.id;
      currentIndex.value = videoList.value.findIndex(v => v.id == targetVideo.id);
      
      // 重新初始化播放器
      showLastPlayBubble.value = false;
      if (art) { art.destroy(); art = null; }
      await fetchDanmaku();
      await fetchSubtitles(); // 加载字幕
      if (preloadedData.hls_file) {
        await nextTick();
        initPlayer(preloadedData.hls_file, preloadedData.thumbnail);
      }
      fetchComments();
      recordView();
      checkDescOverflow();
      if (showSidebar.value && sidebarTab.value === 'user') {
        fetchAuthorVideos();
      }
    }
    
    isTransitioning.value = false;
    slideOffset.value = 0;
    
    // 静默更新 URL，不触发路由监听
    window.history.replaceState({}, '', `/video/${targetVideo.id}`);
    
    setTimeout(() => { wheelLock = false; }, 300);
  }, 400);
};

const goToNextVideo = () => {
  if (nextVideo.value) slideToVideo('next');
};

const goToPrevVideo = () => {
  if (prevVideo.value) slideToVideo('prev');
};

const initPlayer = (hlsUrl, posterUrl) => {
  if (!artPlayerRef.value) return;
  if (art) { art.destroy(); art = null; }
  
  let fullHlsUrl = hlsUrl;
  if (hlsUrl && !hlsUrl.startsWith('http')) {
    if (!hlsUrl.includes('master.m3u8')) {
      const hlsParts = hlsUrl.split('/');
      if (hlsParts.length >= 3) hlsUrl = `${hlsParts[0]}/${hlsParts[1]}/${hlsParts[2]}/master.m3u8`;
    }
    fullHlsUrl = `http://localhost:8000/media/${hlsUrl}`;
  }
  
  art = new Artplayer({
    container: artPlayerRef.value, url: fullHlsUrl, poster: posterUrl || '',
    volume: 0.7, autoplay: true, pip: true, screenshot: true, setting: true,
    playbackRate: true, aspectRatio: true, fullscreen: true, fullscreenWeb: true,
    miniProgressBar: true, mutex: true, backdrop: true, playsInline: true,
    autoPlayback: false, theme: '#FB7299', lang: 'zh-cn',
    moreVideoAttr: { crossOrigin: 'anonymous' },
    notice: { show: false },
    customType: {
      m3u8: function(video, url, art) {
        if (Hls.isSupported()) {
          if (art.hls) art.hls.destroy();
          const hls = new Hls();
          hls.loadSource(url);
          hls.attachMedia(video);
          art.hls = hls;
          art.on('destroy', () => hls.destroy());
          hls.on(Hls.Events.MANIFEST_PARSED, (event, data) => {
            const qualities = data.levels.map((level, index) => ({ html: getQualityLabel(level.height), value: index }));
            qualities.push({ html: '自动', value: -1, default: true });
            art.setting.update({ name: 'quality', html: '画质', tooltip: '自动', selector: qualities.reverse(),
              onSelect: (item) => { 
                hls.currentLevel = item.value;
                const label = item.value === -1 ? '自动' : item.html;
                showToast(`已切换至 ${label}`, 'info');
                return item.html; 
              }
            });
          });
          
          hls.on(Hls.Events.LEVEL_SWITCHED, (event, data) => {
            if (hls.currentLevel === -1) {
              const currentHeight = hls.levels[data.level]?.height;
              if (currentHeight) {
                const autoLabel = `自动(${getQualityLabel(currentHeight)})`;
                const qualitySetting = art.setting.find('quality');
                if (qualitySetting) {
                  art.setting.update({ name: 'quality', tooltip: autoLabel });
                }
              }
            }
          });
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) { video.src = url; }
      }
    },
    plugins: [
      artplayerPluginDanmuku({
        danmuku: danmakuList.value, speed: 8, opacity: 1, fontSize: 25, color: '#FFFFFF',
        mode: 0, margin: [10, '25%'], antiOverlap: true, useWorker: true,
        filter: (d) => d.text.length < 50, lockTime: 5, maxLength: 100, theme: 'dark',
        beforeEmit: (d) => !!d.text.trim()
      })
    ],
    settings: [
      { name: 'quality', html: '画质', tooltip: '自动', selector: [{ html: '自动', value: -1, default: true }] }
    ],
    controls: [
      {
        name: 'cleanMode',
        position: 'right',
        index: 1,
        html: '<div class="art-clean-btn"><svg viewBox="0 0 1024 1024" width="22" height="22"><path fill="currentColor" d="M248 154h-54c-25.4 0-46 20.6-46 46v620c0 25.4 20.6 46 46 46h54c25.4 0 46-20.6 46-46V200c0-25.4-20.6-46-46-46zm0 666h-54V200h54v620zm582-666h-54c-25.4 0-46 20.6-46 46v620c0 25.4 20.6 46 46 46h54c25.4 0 46-20.6 46-46V200c0-25.4-20.6-46-46-46zm0 666h-54V200h54v620z"/></svg></div>',
        tooltip: '清屏模式',
        click: function() {
          isCleanMode.value = !isCleanMode.value;
          showToast(isCleanMode.value ? '已开启清屏模式' : '已退出清屏模式', 'info');
          const btn = art.controls['cleanMode'];
          if (btn) {
            btn.classList.toggle('art-clean-active', isCleanMode.value);
          }
        }
      }
    ]
  });
  
  art.on('play', () => { isPaused.value = false; showToast('播放', 'play'); });
  art.on('pause', () => { isPaused.value = true; showToast('暂停', 'pause'); });
  art.on('seek', () => { if (!art.playing) art.play(); });
  
  // 监听时间更新，更新字幕
  art.on('video:timeupdate', () => {
    updateCurrentSubtitle();
    
    if (art.currentTime > 5) {
      const key = `artplayer_${videoId.value}`;
      localStorage.setItem(key, JSON.stringify({ time: art.currentTime }));
    }
  });
  
  art.on('ready', () => {
    const key = `artplayer_${videoId.value}`;
    const saved = localStorage.getItem(key);
    if (saved) {
      const data = JSON.parse(saved);
      lastPlayedTime = data.time || 0;
      if (lastPlayedTime > 5 && art.duration > 0) {
        const percent = (lastPlayedTime / art.duration) * 100;
        lastPlayPosition.value = Math.max(Math.min(percent, 95), 5);
        showLastPlayBubble.value = true;
        setTimeout(() => { showLastPlayBubble.value = false; }, 8000);
      }
    }
  });
};

// 跳转到上次播放位置
const jumpToLastPlay = () => {
  if (art && lastPlayedTime > 0) {
    art.currentTime = lastPlayedTime;
    showLastPlayBubble.value = false;
    showToast('已跳转', 'play');
  }
};

const sendDanmaku = async (text) => {
  if (!art || !text) return;
  art.plugins.artplayerPluginDanmuku.emit({ text, time: art.currentTime, color: '#ffffff', mode: 0 });
  try {
    await service({ url: '/videos/danmaku/', method: 'post',
      data: { video: videoId.value, text, time: art.currentTime, color: '#ffffff', mode: 0 }
    });
  } catch (error) { /* 弹幕发送失败 */ }
};

const getQualityLabel = (h) => {
  if (h >= 1080) return '1080P 高清';
  if (h >= 720) return '720P 高清';
  if (h >= 480) return '480P 清晰';
  if (h >= 360) return '360P 流畅';
  return h + 'P';
};

const toggleSubscribe = async () => {
  try {
    if (isSubscribed.value) {
      await service({ url: `/users/${videoData.value.creatorId}/unfollow/`, method: 'post' });
      isSubscribed.value = false; ElMessage.success('已取消关注');
    } else {
      await service({ url: `/users/${videoData.value.creatorId}/follow/`, method: 'post' });
      isSubscribed.value = true; ElMessage.success('关注成功');
    }
  } catch (error) { ElMessage.error('操作失败'); }
};

const toggleLike = async () => {
  try {
    if (isLiked.value) {
      await service({ url: `/videos/videos/${videoId.value}/unlike/`, method: 'post' });
      isLiked.value = false;
      videoData.value.likes = formatNumber(parseInt(videoData.value.likes.replace(/[^0-9]/g, '')) - 1);
    } else {
      await service({ url: `/videos/videos/${videoId.value}/like/`, method: 'post' });
      if (isDisliked.value) isDisliked.value = false;
      isLiked.value = true;
      videoData.value.likes = formatNumber(parseInt(videoData.value.likes.replace(/[^0-9]/g, '')) + 1);
    }
  } catch (error) { ElMessage.error('操作失败'); }
};

const toggleDislike = () => {
  if (isDisliked.value) { isDisliked.value = false; }
  else {
    if (isLiked.value) {
      isLiked.value = false;
      videoData.value.likes = formatNumber(parseInt(videoData.value.likes.replace(/[^0-9]/g, '')) - 1);
    }
    isDisliked.value = true;
  }
};

const toggleCollect = async () => {
  try {
    const prev = !!isCollected.value;
    const res = await service({ url: `/videos/collections/${videoId.value}/toggle/`, method: 'post' });
    const next = typeof res?.is_collected === 'boolean' ? res.is_collected : !prev;
    isCollected.value = next;
    // 维护收藏数（后端 toggle 接口不返回 count，这里做本地乐观更新）
    const currentCount = Number(videoData.value.collectCount || 0) || 0;
    videoData.value.collectCount = next ? currentCount + 1 : Math.max(currentCount - 1, 0);
    ElMessage.success(next ? '收藏成功' : '已取消收藏');
  } catch (error) { ElMessage.error('操作失败'); }
};

const shareVideo = () => { navigator.clipboard.writeText(window.location.href).then(() => ElMessage.success('链接已复制')); };
const toggleCommentLike = (c) => { c.isLiked = !c.isLiked; c.likes += c.isLiked ? 1 : -1; };
const replyToComment = (c) => { commentText.value = `@${c.username} `; };

// AI 总结视频
const aiSummarize = () => {
  ElMessage.info('AI正在分析视频内容...');
  // TODO: 调用AI接口总结视频
};

// AI 识别当前帧
const aiRecognizeFrame = () => {
  if (!art) return;
  ElMessage.info('AI正在识别当前画面...');
  // TODO: 截取当前帧并调用AI识别接口
};

const addComment = async () => {
  if (!commentText.value.trim()) return;
  try {
    const response = await service({ url: '/videos/comments/', method: 'post', data: { video: videoId.value, text: commentText.value } });
    comments.value.unshift({
      id: response.id, username: userStore.userInfo?.username || '我', userAvatar: userAvatar.value,
      text: commentText.value, time: '刚刚', likes: 0, isLiked: false
    });
    videoData.value.commentCount += 1; commentText.value = ''; ElMessage.success('评论成功');
  } catch (error) { ElMessage.error('评论失败'); }
};

const formatNumber = (n) => { if (!n) return '0'; if (n >= 10000) return (n/10000).toFixed(1)+'万'; if (n >= 1000) return (n/1000).toFixed(1)+'K'; return n.toString(); };
const formatDate = (s) => { if (!s) return ''; const d = new Date(s), diff = Math.floor((Date.now()-d)/(1000*60*60*24)); if (diff===0) return '今天'; if (diff===1) return '昨天'; if (diff<7) return `${diff}天前`; return `${d.getMonth()+1}-${d.getDate()}`; };
const formatTimeAgo = (s) => { if (!s) return ''; const diff = Date.now()-new Date(s).getTime(), m = Math.floor(diff/60000); if (m<1) return '刚刚'; if (m<60) return `${m}分钟前`; const h = Math.floor(m/60); if (h<24) return `${h}小时前`; return formatDate(s); };

onMounted(async () => { 
  await fetchDanmaku();
  await fetchSubtitles(); // 加载字幕
  fetchVideoDetail(); 
  fetchComments(); 
  recordView(); 
  fetchVideoList();
});

onBeforeUnmount(() => { 
  if (art) { art.destroy(); art = null; } 
  clearTimeout(hideControlsTimer);
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

/* 自定义字幕覆盖层 */
.custom-subtitle-overlay {
  position: absolute;
  left: 0;
  right: 0;
  text-align: center;
  z-index: 10;
  pointer-events: none;
  user-select: none;
  transition: opacity 0.2s ease;
}

.subtitle-main,
.subtitle-sub {
  display: block;
  line-height: 1.4;
  padding: 2px 8px;
  margin: 0 auto;
  max-width: 90%;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.subtitle-main {
  margin-bottom: 4px;
}

.video-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

/* 视频滑动容器 */
.video-slider {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

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

.video-slider.transitioning {
  transition: transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.video-slide {
  position: absolute;
  left: 0;
  width: 100%;
  height: 100%;
  background: #000;
}

.current-slide {
  top: 0;
}

.prev-slide {
  top: -100%;
}

.next-slide {
  top: 100%;
}

.slide-preview {
  width: 100%;
  height: 100%;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.slide-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.slide-preview .slide-title {
  position: absolute;
  bottom: 80px;
  left: 20px;
  right: 20px;
  color: #fff;
  font-size: 16px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.top-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: transparent;
  z-index: 100;
  transition: opacity 0.3s, transform 0.3s;
}

.top-bar.hidden {
  opacity: 0;
  transform: translateY(-20px);
  pointer-events: none;
}

.top-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn, .top-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255,255,255,0.1);
  border: none;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.back-btn:hover, .top-btn:hover {
  background: rgba(255,255,255,0.2);
}

.top-right {
  position: relative;
}

/* 更多菜单 */
.more-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: rgba(0,0,0,0.8);
  backdrop-filter: blur(12px);
  border-radius: 8px;
  padding: 8px 0;
  min-width: 140px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.more-menu .menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.more-menu .menu-item:hover {
  background: rgba(255,255,255,0.1);
}

.more-menu .menu-item .el-icon {
  font-size: 16px;
  color: rgba(255,255,255,0.7);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.side-actions {
  position: absolute;
  right: 16px;
  bottom: 85px; /* 调整位置，避开底部控制栏 */
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

.video-info-overlay {
  position: absolute;
  left: 20px;
  bottom: 60px;
  max-width: 30%;
  z-index: 100;
  transition: opacity 0.3s, transform 0.3s;
  text-align: left;
}

.video-info-overlay.hidden {
  opacity: 0;
  transform: translateY(20px);
  pointer-events: none;
}

.creator-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.creator-name {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  text-decoration: none;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5);
}

.creator-name:hover {
  color: #FB7299;
}

.publish-time {
  color: rgba(255,255,255,0.7);
  font-size: 13px;
}

.video-title {
  font-size: 15px;
  font-weight: 500;
  color: #fff;
  margin: 0 0 8px 0;
  line-height: 1.5;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5);
  text-align: left;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.video-title.expanded {
  -webkit-line-clamp: unset;
  display: block;
}

.video-description {
  font-size: 13px;
  color: rgba(255,255,255,0.8);
  line-height: 1.5;
  margin-bottom: 8px;
  text-align: left;
}

.video-description:not(.expanded) .desc-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.video-description.expanded .desc-text {
  display: inline;
}

.desc-text {
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}

.expand-btn {
  color: #fff;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}

.collapse-btn {
  color: rgba(255,255,255,0.7);
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}

.video-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.video-tags .tag {
  padding: 4px 10px;
  background: rgba(255,255,255,0.15);
  border-radius: 4px;
  color: #fff;
  font-size: 12px;
  backdrop-filter: blur(4px);
  cursor: pointer;
  transition: background 0.2s;
}

.video-tags .tag:hover {
  background: rgba(251,114,153,0.5);
}

/* AI 功能按钮 */
.ai-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.ai-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(8px);
  border: none;
  border-radius: 20px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.ai-btn:hover {
  background: rgba(0, 161, 214, 0.6);
}

.ai-btn svg {
  flex-shrink: 0;
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
}

.comment-panel {
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

.comment-form {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  align-items: center;
}

.comment-form .input-wrapper {
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

/* 自定义滚动条 */
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

.comment-header .username {
  font-size: 14px;
  font-weight: 500;
  color: #00a1d6;
}

.comment-header .comment-time {
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

.comment-actions .action {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: color 0.2s;
}

.comment-actions .action:hover,
.comment-actions .action.active {
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

:deep(.art-video-player) {
  width: 100% !important;
  height: 100% !important;
}

/* 清屏按钮样式 */
:deep(.art-clean-btn) {
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.8);
  transition: all 0.2s ease;
}

:deep(.art-clean-btn:hover) {
  color: #fff;
  transform: scale(1.1);
}

:deep(.art-control-cleanMode.art-clean-active .art-clean-btn) {
  color: #00a1d6;
}

:deep(.art-bottom) {
  background: linear-gradient(to top, rgba(0, 0, 0, 0.4) 0%, transparent 100%) !important;
}

/* 上次看到提示框层级 */
:deep(.art-auto-playback) {
  display: none !important;
}

/* 上次播放位置气泡 */
.last-play-bubble {
  position: absolute;
  bottom: 60px;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  z-index: 120;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.2s;
  pointer-events: auto;
}

.last-play-bubble:hover {
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}

.last-play-bubble .bubble-arrow {
  position: absolute;
  bottom: -5px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 5px solid rgba(255, 255, 255, 0.9);
}

/* 气泡动画 */
.bubble-enter-active,
.bubble-leave-active {
  transition: all 0.3s ease;
}

.bubble-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

.bubble-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-10px);
}
:deep(.art-progress-hover),
:deep(.art-progress-played) {
  background: #00a1d6 !important;
}

:deep(.art-progress-indicator) {
  background: #00a1d6 !important;
  border-color: #00a1d6 !important;
}



/* 弹幕样式见文件末尾非scoped块 */

/* 隐藏默认 notice */
:deep(.art-notice) {
  display: none !important;
}

/* 自定义 Toast 提示 */
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
  position: relative;
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

/* Toast 动画 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(40px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(40px);
}

@media (max-width: 768px) {
  .immersive-player-page { flex-direction: column; }
  .main-stage { width: 100%; }
  .sidebar-wrapper { width: 100%; height: 60vh; }
  .sidebar-wrapper.open { width: 100%; }
  .comment-panel { width: 100%; }
  .video-info-overlay { max-width: calc(100% - 80px); bottom: 80px; }
  .side-actions { bottom: 80px; right: 10px; gap: 16px; }
  .action-icon { width: 40px; height: 40px; }
  .action-icon svg { width: 20px; height: 20px; }
}
</style>

<style>
/* 弹幕模块整体样式 */
.artplayer-plugin-danmuku {
  margin-bottom: 9px;
  gap: 12px !important;
}

/* 弹幕开关和配置图标 */
.artplayer-plugin-danmuku .apd-toggle,
.artplayer-plugin-danmuku .apd-config {
  transition: all 0.2s ease !important;
}

.artplayer-plugin-danmuku .apd-toggle:hover,
.artplayer-plugin-danmuku .apd-config:hover {
  transform: scale(1.1) !important;
}

.artplayer-plugin-danmuku .apd-icon {
  fill: rgba(255, 255, 255, 0.85) !important;
  transition: all 0.2s ease !important;
}

.artplayer-plugin-danmuku .apd-icon:hover {
  fill: #00a1d6 !important;
}

/* 弹幕输入框容器 */
.artplayer-plugin-danmuku .apd-emitter {
  background: linear-gradient(135deg, rgba(30, 35, 50, 0.1) 0%, rgba(45, 50, 70, 0.1) 100%) !important;
  backdrop-filter: blur(16px) !important;
  border-radius: 24px !important;
  padding: 4px 4px 4px 12px !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
  gap: 8px !important;
  height: 40px !important;
  min-width: 380px !important;
  transition: all 0.3s ease !important;
}

.artplayer-plugin-danmuku .apd-emitter:hover {
  border-color: rgba(0, 161, 214, 0.3) !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(0, 161, 214, 0.1) !important;
}

/* 样式选择按钮 */
.artplayer-plugin-danmuku .apd-style {
  background: transparent !important;
  border: none !important;
  border-radius: 6px !important;
  padding: 4px !important;
  margin-right: 4px !important;
  transition: all 0.2s ease !important;
}

.artplayer-plugin-danmuku .apd-style:hover {
  background: rgba(255, 255, 255, 0.1) !important;
}

.artplayer-plugin-danmuku .apd-style .apd-icon {
  width: 20px !important;
  height: 20px !important;
}

/* 输入框 */
.artplayer-plugin-danmuku .apd-input {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  color: #fff !important;
  font-size: 13px !important;
  padding: 0 8px !important;
  flex: 1 !important;
  min-width: 200px !important;
  height: 100% !important;
  transition: all 0.2s ease !important;
}

.artplayer-plugin-danmuku .apd-input:focus {
  background: transparent !important;
  outline: none !important;
}

.artplayer-plugin-danmuku .apd-input::placeholder {
  color: rgba(255, 255, 255, 0.4) !important;
  font-size: 13px !important;
}

/* 发送按钮 */
.artplayer-plugin-danmuku .apd-send {
  background: linear-gradient(135deg, #00a1d6 0%, #00b5e5 100%) !important;
  color: #fff !important;
  border-radius: 20px !important;
  padding: 0 24px !important;
  height: 32px !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  border: none !important;
  cursor: pointer !important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
  letter-spacing: 0 !important;
  box-shadow: 0 2px 8px rgba(0, 161, 214, 0.3) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  white-space: nowrap !important;
  min-width: 60px !important;
}

.artplayer-plugin-danmuku .apd-send:hover {
  background: linear-gradient(135deg, #00b5e5 0%, #00c8f8 100%) !important;
  transform: scale(1.02) !important;
  box-shadow: 0 4px 16px rgba(0, 161, 214, 0.5) !important;
}

.artplayer-plugin-danmuku .apd-send:active {
  transform: scale(0.98) !important;
}

/* 锁定状态 */
.artplayer-plugin-danmuku .apd-send.apd-lock {
  background: rgba(255, 255, 255, 0.1) !important;
  color: rgba(255, 255, 255, 0.5) !important;
  box-shadow: none !important;
}

/* 配置面板样式 */
.artplayer-plugin-danmuku .apd-config-panel,
.artplayer-plugin-danmuku .apd-style-panel {
  backdrop-filter: blur(20px) !important;
}

.artplayer-plugin-danmuku .apd-config-panel .apd-config-panel-inner,
.artplayer-plugin-danmuku .apd-style-panel .apd-style-panel-inner {
  background: linear-gradient(135deg, rgba(25, 30, 45, 0.95) 0%, rgba(35, 40, 55, 0.95) 100%) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 12px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
}

/* 滑块样式 */
.artplayer-plugin-danmuku .apd-slider .apd-slider-dot {
  background: linear-gradient(135deg, #00a1d6 0%, #00b5e5 100%) !important;
  box-shadow: 0 2px 8px rgba(0, 161, 214, 0.4) !important;
  width: 14px !important;
  height: 14px !important;
}

.artplayer-plugin-danmuku .apd-slider .apd-slider-progress {
  background: linear-gradient(90deg, #00a1d6 0%, #00b5e5 100%) !important;
}

/* 颜色选择器 */
.artplayer-plugin-danmuku .apd-colors .apd-color {
  border-radius: 50% !important;
  width: 20px !important;
  height: 20px !important;
  transition: all 0.2s ease !important;
  border: 2px solid transparent !important;
}

.artplayer-plugin-danmuku .apd-colors .apd-color:hover {
  transform: scale(1.2) !important;
}

.artplayer-plugin-danmuku .apd-colors .apd-color.apd-active {
  border-color: #fff !important;
  box-shadow: 0 0 0 2px rgba(0, 161, 214, 0.5) !important;
}

/* 模式选择按钮 */
.artplayer-plugin-danmuku .apd-modes .apd-mode {
  transition: all 0.2s ease !important;
  padding: 4px 8px !important;
  border-radius: 6px !important;
}

.artplayer-plugin-danmuku .apd-modes .apd-mode:hover {
  background: rgba(0, 161, 214, 0.1) !important;
}
</style>
