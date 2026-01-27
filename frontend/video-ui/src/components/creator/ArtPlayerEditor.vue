<template>
  <div class="art-player-editor">
    <div ref="artRef" class="art-player-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import Artplayer from 'artplayer';
import artplayerPluginDanmuku from 'artplayer-plugin-danmuku';

const props = defineProps({
  url: {
    type: String,
    default: ''
  },
  poster: {
    type: String,
    default: ''
  },
  subtitles: {
    type: Array,
    default: () => []
  },
  aspectRatio: {
    type: String,
    default: '16:9'
  },
  autoplay: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['timeupdate', 'ready', 'play', 'pause', 'ended']);

const artRef = ref(null);
let art = null;

onMounted(() => {
  if (artRef.value) {
    art = new Artplayer({
      container: artRef.value,
      url: props.url,
      poster: props.poster,
      autoplay: props.autoplay,
      aspectRatio: props.aspectRatio,
      setting: true,
      loop: false,
      flip: true,
      playbackRate: true,
      aspectRatio: true,
      screenshot: true,
      fullscreen: true,
      fullscreenWeb: true,
      pip: true,
      mutex: true,
      theme: '#3b82f6',
      lang: 'zh-cn',
      moreVideoAttr: {
        crossOrigin: 'anonymous'
      },
      subtitle: {
        url: '',
        type: 'srt',
        style: {
          color: '#fff',
          fontSize: '24px',
          textShadow: '2px 2px 4px rgba(0, 0, 0, 0.8)'
        }
      },
      plugins: [
        artplayerPluginDanmuku({
          danmuku: [],
          speed: 5,
          opacity: 1,
          fontSize: 25,
          color: '#FFFFFF',
          mode: 0,
          margin: [10, '25%'],
          antiOverlap: true,
          useWorker: true,
          synchronousPlayback: false,
          filter: (danmu) => danmu.text.length <= 50,
          lockTime: 5,
          maxLength: 100,
          minWidth: 200,
          maxWidth: 400,
          theme: 'light'
        })
      ],
      controls: [
        {
          position: 'right',
          html: '字幕',
          tooltip: '字幕设置',
          click: function () {
            emit('subtitle-click');
          }
        }
      ]
    });

    // 事件监听
    art.on('ready', () => {
      emit('ready', art);
    });

    art.on('video:timeupdate', () => {
      emit('timeupdate', art.currentTime);
    });

    art.on('play', () => {
      emit('play');
    });

    art.on('pause', () => {
      emit('pause');
    });

    art.on('video:ended', () => {
      emit('ended');
    });
  }
});

onBeforeUnmount(() => {
  if (art && art.destroy) {
    art.destroy(false);
  }
});

// 监听 URL 变化
watch(() => props.url, (newUrl) => {
  if (art && newUrl) {
    art.switchUrl(newUrl);
  }
});

// 暴露方法给父组件
defineExpose({
  play: () => art?.play(),
  pause: () => art?.pause(),
  seek: (time) => art && (art.currentTime = time),
  getCurrentTime: () => art?.currentTime || 0,
  getDuration: () => art?.duration || 0,
  setVolume: (volume) => art && (art.volume = volume / 100),
  getVolume: () => (art?.volume || 0) * 100,
  getInstance: () => art
});
</script>

<style scoped>
.art-player-editor {
  width: 100%;
  height: 100%;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.art-player-container {
  width: 100%;
  height: 100%;
}

/* ArtPlayer 自定义样式 */
:deep(.art-video-player) {
  border-radius: 8px;
}

:deep(.art-subtitle) {
  font-family: 'Microsoft YaHei', sans-serif;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
}
</style>
