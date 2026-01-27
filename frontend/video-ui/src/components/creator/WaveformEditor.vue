<template>
  <div class="waveform-editor">
    <div class="waveform-controls">
      <el-button-group size="small">
        <el-button @click="handlePlay">
          <el-icon><VideoPlay v-if="!isPlaying" /><VideoPause v-else /></el-icon>
        </el-button>
        <el-button @click="handleStop">
          <el-icon><RefreshLeft /></el-icon>
        </el-button>
      </el-button-group>
      
      <div class="waveform-info">
        <span class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
      </div>

      <div class="waveform-zoom">
        <el-button size="small" circle @click="handleZoomOut">
          <el-icon><Minus /></el-icon>
        </el-button>
        <span>{{ zoom }}%</span>
        <el-button size="small" circle @click="handleZoomIn">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>
    </div>

    <div ref="waveformRef" class="waveform-container"></div>
    <div ref="timelineRef" class="waveform-timeline"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import WaveSurfer from 'wavesurfer.js';
import TimelinePlugin from 'wavesurfer.js/dist/plugins/timeline.esm.js';
import { VideoPlay, VideoPause, RefreshLeft, Minus, Plus } from '@element-plus/icons-vue';

const props = defineProps({
  url: {
    type: String,
    required: true
  },
  waveColor: {
    type: String,
    default: '#3b82f6'
  },
  progressColor: {
    type: String,
    default: '#1e40af'
  },
  height: {
    type: Number,
    default: 128
  }
});

const emit = defineEmits(['ready', 'timeupdate', 'play', 'pause', 'finish']);

const waveformRef = ref(null);
const timelineRef = ref(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const zoom = ref(100);

let wavesurfer = null;

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

onMounted(() => {
  if (waveformRef.value && props.url) {
    wavesurfer = WaveSurfer.create({
      container: waveformRef.value,
      waveColor: props.waveColor,
      progressColor: props.progressColor,
      cursorColor: '#ef4444',
      cursorWidth: 2,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      height: props.height,
      normalize: true,
      backend: 'WebAudio',
      plugins: [
        TimelinePlugin.create({
          container: timelineRef.value,
          primaryColor: '#9ca3af',
          secondaryColor: '#6b7280',
          primaryFontColor: '#9ca3af',
          secondaryFontColor: '#6b7280'
        })
      ]
    });

    wavesurfer.load(props.url);

    wavesurfer.on('ready', () => {
      duration.value = wavesurfer.getDuration();
      emit('ready', wavesurfer);
    });

    wavesurfer.on('audioprocess', (time) => {
      currentTime.value = time;
      emit('timeupdate', time);
    });

    wavesurfer.on('play', () => {
      isPlaying.value = true;
      emit('play');
    });

    wavesurfer.on('pause', () => {
      isPlaying.value = false;
      emit('pause');
    });

    wavesurfer.on('finish', () => {
      isPlaying.value = false;
      emit('finish');
    });
  }
});

onBeforeUnmount(() => {
  if (wavesurfer) {
    wavesurfer.destroy();
  }
});

watch(() => props.url, (newUrl) => {
  if (wavesurfer && newUrl) {
    wavesurfer.load(newUrl);
  }
});

const handlePlay = () => {
  if (wavesurfer) {
    wavesurfer.playPause();
  }
};

const handleStop = () => {
  if (wavesurfer) {
    wavesurfer.stop();
  }
};

const handleZoomIn = () => {
  if (zoom.value < 200 && wavesurfer) {
    zoom.value += 10;
    wavesurfer.zoom(zoom.value);
  }
};

const handleZoomOut = () => {
  if (zoom.value > 50 && wavesurfer) {
    zoom.value -= 10;
    wavesurfer.zoom(zoom.value);
  }
};

defineExpose({
  play: () => wavesurfer?.play(),
  pause: () => wavesurfer?.pause(),
  stop: () => wavesurfer?.stop(),
  seekTo: (progress) => wavesurfer?.seekTo(progress),
  getCurrentTime: () => wavesurfer?.getCurrentTime() || 0,
  getDuration: () => wavesurfer?.getDuration() || 0,
  getInstance: () => wavesurfer
});
</script>

<style scoped>
.waveform-editor {
  width: 100%;
  background: #1a1a1a;
  border-radius: 8px;
  padding: 16px;
}

.waveform-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.waveform-info {
  flex: 1;
}

.time-display {
  color: #9ca3af;
  font-size: 13px;
  font-family: monospace;
}

.waveform-zoom {
  display: flex;
  align-items: center;
  gap: 8px;
}

.waveform-zoom span {
  color: #9ca3af;
  font-size: 12px;
  min-width: 40px;
  text-align: center;
}

.waveform-container {
  width: 100%;
  background: #252525;
  border-radius: 6px;
  overflow: hidden;
}

.waveform-timeline {
  margin-top: 8px;
}

:deep(wave) {
  overflow: visible !important;
}
</style>
