<template>
  <div class="video-player-wrapper">
    <div class="video-container" ref="artPlayerRef"></div>
    
    <!-- 自定义字幕覆盖层 -->
    <div 
      class="custom-subtitle-overlay" 
      v-if="currentSubtitle && !isCleanMode" 
      :style="computedSubtitleStyle"
    >
      <div class="subtitle-main" :style="mainTextStyle" v-if="currentSubtitle.text">
        {{ currentSubtitle.text }}
      </div>
      <div class="subtitle-sub" :style="subTextStyle" v-if="currentSubtitle.translation">
        {{ currentSubtitle.translation }}
      </div>
    </div>

    <!-- 播放/暂停状态提示 -->
    <transition name="play-status">
      <div class="play-status-indicator" v-if="showPlayStatus">
        <el-icon :size="80">
          <VideoPlay v-if="isPlaying" />
          <VideoPause v-else />
        </el-icon>
      </div>
    </transition>

    <!-- 画质切换提示 -->
    <transition name="quality-toast">
      <div class="quality-toast" v-if="showQualityToast">
        {{ qualityToastText }}
      </div>
    </transition>

    <!-- 上次播放位置气泡 -->
    <transition name="bubble">
      <div 
        class="last-play-bubble" 
        v-if="showLastPlayBubble" 
        :style="{ left: lastPlayPosition + '%' }" 
        @click="jumpToLastPlay"
      >
        <span>上次看到这里</span>
        <div class="bubble-arrow"></div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import Artplayer from 'artplayer';
import Hls from 'hls.js';
import artplayerPluginDanmuku from 'artplayer-plugin-danmuku';
import { VideoPlay, VideoPause } from '@element-plus/icons-vue';

const props = defineProps({
  videoId: [String, Number],
  hlsUrl: String,
  posterUrl: String,
  danmakuList: { type: Array, default: () => [] },
  subtitleList: { type: Array, default: () => [] },
  subtitleStyle: { type: Object, default: () => ({}) },
  isCleanMode: Boolean
});

const emit = defineEmits(['play', 'pause', 'timeupdate', 'ready', 'danmaku-send']);

const artPlayerRef = ref(null);
let art = null;
const currentSubtitle = ref(null);
const showLastPlayBubble = ref(false);
const lastPlayPosition = ref(0);
let lastPlayedTime = 0;

// 播放状态提示
const showPlayStatus = ref(false);
const isPlaying = ref(false);
let playStatusTimer = null;

// 画质切换提示
const showQualityToast = ref(false);
const qualityToastText = ref('');
let qualityToastTimer = null;

// 计算字幕样式
const computedSubtitleStyle = computed(() => {
  const style = props.subtitleStyle;
  return {
    fontSize: `${style.fontSize || 20}px`,
    letterSpacing: `${style.letterSpacing || 0}px`,
    bottom: `${style.bottomDistance || 50}px`,
    fontFamily: style.fontFamily || 'Source Han Sans',
    fontWeight: style.isBold ? 'bold' : 'normal',
    fontStyle: style.isItalic ? 'italic' : 'normal',
    textShadow: style.hasShadow 
      ? `${style.shadowOffset || 2}px ${style.shadowOffset || 2}px ${(style.shadowOffset || 2) * 2}px rgba(0, 0, 0, ${(style.shadowOpacity || 80) / 100})`
      : 'none'
  };
});

const mainTextStyle = computed(() => ({
  color: props.subtitleStyle.mainColor || '#ffffff',
  WebkitTextStroke: `${props.subtitleStyle.strokeWidth || 2}px ${props.subtitleStyle.mainBorderColor || '#000000'}`
}));

const subTextStyle = computed(() => ({
  color: props.subtitleStyle.subColor || '#ffff00',
  WebkitTextStroke: `${props.subtitleStyle.strokeWidth || 2}px ${props.subtitleStyle.subBorderColor || '#000000'}`
}));

// 更新当前字幕
const updateCurrentSubtitle = () => {
  if (!art || props.subtitleList.length === 0) {
    currentSubtitle.value = null;
    return;
  }
  
  const currentTime = art.currentTime;
  const subtitle = props.subtitleList.find(
    sub => currentTime >= sub.start && currentTime < sub.end
  );
  
  currentSubtitle.value = subtitle || null;
};

// 跳转到上次播放位置
const jumpToLastPlay = () => {
  if (art && lastPlayedTime > 0) {
    art.currentTime = lastPlayedTime;
    showLastPlayBubble.value = false;
    emit('timeupdate', lastPlayedTime);
  }
};

// 显示播放状态提示
const showPlayStatusIndicator = (playing) => {
  isPlaying.value = playing;
  showPlayStatus.value = true;
  
  if (playStatusTimer) clearTimeout(playStatusTimer);
  playStatusTimer = setTimeout(() => {
    showPlayStatus.value = false;
  }, 600);
};

// 显示画质切换提示
const showQualityChangeToast = (qualityText) => {
  qualityToastText.value = `已切换至 ${qualityText}`;
  showQualityToast.value = true;
  
  if (qualityToastTimer) clearTimeout(qualityToastTimer);
  qualityToastTimer = setTimeout(() => {
    showQualityToast.value = false;
  }, 2000);
};

// 获取画质标签
const getQualityLabel = (h) => {
  if (h >= 2160) return '4K 超高清 UHD';
  if (h >= 1440) return '2K 超清 QHD';
  if (h >= 1080) return '1080P 全高清 FHD';
  if (h >= 720) return '720P 高清 HD';
  if (h >= 480) return '480P 清晰';
  if (h >= 360) return '360P 流畅';
  return h + 'P';
};

// 初始化播放器
const initPlayer = () => {
  if (!artPlayerRef.value || !props.hlsUrl) return;
  if (art) {
    art.destroy();
    art = null;
  }
  
  let fullHlsUrl = props.hlsUrl;
  if (!fullHlsUrl.startsWith('http')) {
    if (!fullHlsUrl.includes('master.m3u8')) {
      const hlsParts = fullHlsUrl.split('/');
      if (hlsParts.length >= 3) {
        fullHlsUrl = `${hlsParts[0]}/${hlsParts[1]}/${hlsParts[2]}/master.m3u8`;
      }
    }
    fullHlsUrl = `http://localhost:8000/media/${fullHlsUrl}`;
  }
  
  art = new Artplayer({
    container: artPlayerRef.value,
    url: fullHlsUrl,
    poster: props.posterUrl || '',
    volume: 0.7,
    autoplay: true,
    pip: true,
    screenshot: true,
    setting: true,
    playbackRate: true,
    aspectRatio: true,
    fullscreen: true,
    fullscreenWeb: true,
    miniProgressBar: false,
    mutex: true,
    backdrop: true,
    playsInline: true,
    autoPlayback: false,
    theme: '#FB7299',
    lang: 'zh-cn',
    moreVideoAttr: { crossOrigin: 'anonymous' },
    icons: {
      state: '',
      indicator: ''
    },
    layers: [],
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
            // 去重：按分辨率高度分组，每个高度只保留一个（通常是最高码率的）
            const qualityMap = new Map();
            data.levels.forEach((level, index) => {
              const height = level.height;
              if (!qualityMap.has(height) || level.bitrate > qualityMap.get(height).bitrate) {
                qualityMap.set(height, { ...level, index });
              }
            });
            
            // 转换为画质选项数组并排序（从高到低）
            const qualities = Array.from(qualityMap.values())
              .sort((a, b) => b.height - a.height)
              .map(level => ({
                html: getQualityLabel(level.height),
                value: level.index
              }));
            
            qualities.push({ html: '自动', value: -1, default: true });
            
            art.setting.update({
              name: 'quality',
              html: '画质',
              tooltip: '自动',
              selector: qualities,
              onSelect: (item) => {
                hls.currentLevel = item.value;
                return item.html;
              }
            });
          });
          
          // 监听画质切换完成
          hls.on(Hls.Events.LEVEL_SWITCHED, (event, data) => {
            const level = hls.levels[data.level];
            if (level) {
              showQualityChangeToast(getQualityLabel(level.height));
            }
          });
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
          video.src = url;
        }
      }
    },
    plugins: [
      artplayerPluginDanmuku({
        danmuku: props.danmakuList,
        speed: 8,
        opacity: 1,
        fontSize: 25,
        color: '#FFFFFF',
        mode: 0,
        margin: [10, '25%'],
        antiOverlap: true,
        useWorker: true,
        filter: (d) => d.text.length < 50,
        lockTime: 5,
        maxLength: 100,
        theme: 'dark',
        beforeEmit: (d) => {
          if (d.text.trim()) {
            emit('danmaku-send', d);
            return true;
          }
          return false;
        }
      })
    ]
  });
  
  // 事件监听
  art.on('play', () => {
    showPlayStatusIndicator(true);
    emit('play');
  });
  art.on('pause', () => {
    showPlayStatusIndicator(false);
    emit('pause');
  });
  
  // 隐藏 Artplayer 默认的状态图标和提示层
  art.on('ready', () => {
    // 隐藏中间的播放/暂停图标
    const stateElement = art.template.$state;
    if (stateElement) {
      stateElement.style.display = 'none';
    }
    
    // 隐藏左上角的提示信息
    const noticeElement = art.template.$notice;
    if (noticeElement) {
      noticeElement.style.display = 'none';
    }
    
    // 隐藏左上角的 loading 和 indicator
    const loadingElement = art.template.$loading;
    if (loadingElement) {
      loadingElement.style.display = 'none';
    }
    
    emit('ready', art);
  });
  art.on('video:timeupdate', () => {
    updateCurrentSubtitle();
    emit('timeupdate', art.currentTime);
    
    if (art.currentTime > 5) {
      const key = `artplayer_${props.videoId}`;
      localStorage.setItem(key, JSON.stringify({ time: art.currentTime }));
    }
  });
  art.on('ready', () => {
    // 隐藏 Artplayer 默认的状态图标和提示层
    const stateElement = art.template.$state;
    if (stateElement) {
      stateElement.style.display = 'none';
    }
    
    const noticeElement = art.template.$notice;
    if (noticeElement) {
      noticeElement.style.display = 'none';
    }
    
    const loadingElement = art.template.$loading;
    if (loadingElement) {
      loadingElement.style.display = 'none';
    }
    
    const key = `artplayer_${props.videoId}`;
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
    emit('ready', art);
  });
};

// 暴露方法给父组件
defineExpose({
  art: () => art,
  destroy: () => {
    if (art) {
      art.destroy();
      art = null;
    }
  }
});

watch(() => props.hlsUrl, () => {
  if (props.hlsUrl) initPlayer();
});

onMounted(() => {
  if (props.hlsUrl) initPlayer();
});

onBeforeUnmount(() => {
  if (playStatusTimer) clearTimeout(playStatusTimer);
  if (qualityToastTimer) clearTimeout(qualityToastTimer);
  if (art) {
    art.destroy();
    art = null;
  }
});
</script>

<style scoped>
.video-player-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.video-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

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

.bubble-arrow {
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

/* 播放/暂停状态指示器 */
.play-status-indicator {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 150;
  color: rgba(255, 255, 255, 0.9);
  pointer-events: none;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.5));
}

.play-status-enter-active {
  animation: playStatusIn 0.3s ease-out;
}

.play-status-leave-active {
  animation: playStatusOut 0.3s ease-in;
}

@keyframes playStatusIn {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.5);
  }
  100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

@keyframes playStatusOut {
  0% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(1.2);
  }
}

/* 画质切换提示 - 右侧滑入样式 */
.quality-toast {
  position: absolute;
  top: 80px;
  right: 20px;
  z-index: 200;
  padding: 12px 20px;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  white-space: nowrap;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  pointer-events: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.quality-toast::before {
  content: '✓';
  display: inline-block;
  width: 18px;
  height: 18px;
  background: #00a1d6;
  border-radius: 50%;
  text-align: center;
  line-height: 18px;
  font-size: 12px;
  font-weight: bold;
}

.quality-toast-enter-active {
  animation: slideInRight 0.3s ease-out;
}

.quality-toast-leave-active {
  animation: slideOutRight 0.3s ease-in;
}

@keyframes slideInRight {
  0% {
    opacity: 0;
    transform: translateX(100px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideOutRight {
  0% {
    opacity: 1;
    transform: translateX(0);
  }
  100% {
    opacity: 0;
    transform: translateX(100px);
  }
}

/* 强制隐藏 Artplayer 默认的提示元素 */
:deep(.art-state),
:deep(.art-notice),
:deep(.art-loading),
:deep(.art-indicator) {
  display: none !important;
  opacity: 0 !important;
  visibility: hidden !important;
}
</style>
