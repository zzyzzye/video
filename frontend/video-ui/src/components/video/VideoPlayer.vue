<template>
  <div class="video-player-container">
    <video
      ref="videoPlayer"
      class="video-js vjs-default-skin vjs-big-play-centered"
      controls
      preload="auto"
      :poster="poster"
      :width="width"
      :height="height"
      data-setup="{}"
    >
      <source :src="src" :type="type" />
      <p class="vjs-no-js">
        您的浏览器不支持HTML5视频，请升级浏览器或启用JavaScript。
      </p>
    </video>
  </div>
</template>

<script>
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import '@videojs/http-streaming';

export default {
  name: 'VideoPlayer',
  props: {
    src: {
      type: String,
      required: true
    },
    type: {
      type: String,
      default: 'application/x-mpegURL' // HLS格式
    },
    poster: {
      type: String,
      default: ''
    },
    width: {
      type: [Number, String],
      default: '100%'
    },
    height: {
      type: [Number, String],
      default: 'auto'
    },
    autoplay: {
      type: Boolean,
      default: false
    },
    options: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      player: null
    };
  },
  mounted() {
    this.initPlayer();
  },
  beforeDestroy() {
    if (this.player) {
      this.player.dispose();
      this.player = null;
    }
  },
  watch: {
    src(newSrc) {
      if (this.player && newSrc) {
        this.player.src({ src: newSrc, type: this.type });
      }
    }
  },
  methods: {
    initPlayer() {
      if (!this.$refs.videoPlayer) {
        console.error('视频元素未找到');
        return;
      }

      // 检查src是否有效
      if (!this.src || this.src === 'undefined' || this.src === 'null') {
        console.error('视频源无效:', this.src);
        this.$emit('error', { code: 4, message: '视频源无效' });
        return;
      }

      // 合并默认选项和自定义选项
      const options = {
        controls: true,
        fluid: true,
        preload: 'auto',
        autoplay: this.autoplay,
        poster: this.poster,
        html5: {
          vhs: {
            overrideNative: true,
            withCredentials: false
          },
          nativeVideoTracks: false,
          nativeAudioTracks: false,
          nativeTextTracks: false
        },
        ...this.options
      };

      // 创建播放器实例
      this.player = videojs(this.$refs.videoPlayer, options, () => {
        this.$emit('ready', this.player);
      });

      // 注册事件监听
      this.player.on('play', () => this.$emit('play'));
      this.player.on('pause', () => this.$emit('pause'));
      this.player.on('ended', () => this.$emit('ended'));
      this.player.on('timeupdate', () => {
        if (this.player) {
          this.$emit('timeupdate', {
            currentTime: this.player.currentTime(),
            duration: this.player.duration()
          });
        }
      });
      this.player.on('error', (error) => {
        console.error('视频播放器错误:', error);
        console.error('错误详情:', this.player.error());
        console.error('当前src:', this.src);
        this.$emit('error', error);
      });
    }
  }
};
</script>

<style scoped>
.video-player-container {
  width: 100%;
  margin: 0 auto;
  position: relative;
  overflow: hidden;
  border-radius: 8px;
}

/* 自定义样式 */
:deep(.vjs-default-skin) {
  border-radius: 8px;
}

:deep(.vjs-big-play-button) {
  font-size: 3em;
  line-height: 1.5em;
  height: 1.5em;
  width: 3em;
  display: block;
  position: absolute;
  top: 50%;
  left: 50%;
  padding: 0;
  margin-left: -1.5em;
  margin-top: -0.75em;
  cursor: pointer;
  opacity: 1;
  border-radius: 0.3em;
  transition: all 0.4s;
}
</style> 