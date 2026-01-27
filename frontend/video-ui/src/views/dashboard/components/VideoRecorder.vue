<template>
  <div class="record-area">
    <div class="video-container">
      <video ref="videoPreview" class="video-preview" autoplay muted></video>
      <div v-if="isRecording" class="recording-indicator">
        <div class="recording-dot"></div>
        <span>录制中: {{ recordingTime }}</span>
      </div>
      <div v-if="!hasCamera && !cameraError" class="camera-loading">
        <div class="loading-icon">
          <el-icon><Loading /></el-icon>
        </div>
        <span>正在启动摄像头...</span>
      </div>
    </div>
    
    <div class="record-controls">
      <el-button 
        type="primary" 
        :disabled="!hasCamera || isRecording" 
        @click="startRecording"
      >
        <el-icon><VideoCamera /></el-icon> 开始录制
      </el-button>
      <el-button 
        type="danger" 
        :disabled="!isRecording" 
        @click="stopRecording"
      >
        <el-icon><VideoPause /></el-icon> 停止录制
      </el-button>
      <el-button 
        type="success" 
        :disabled="!recordedBlob" 
        @click="handleSave"
      >
        <el-icon><Check /></el-icon> 保存视频
      </el-button>
    </div>
    
    <div v-if="cameraError" class="camera-error">
      <el-alert
        title="无法访问摄像头"
        type="error"
        description="请确保您的设备有摄像头并且已授权访问权限。"
        show-icon
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount, nextTick } from 'vue';
import { VideoCamera, VideoPause, Check, Loading } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['save']);

// 状态
const videoPreview = ref(null);
const hasCamera = ref(false);
const cameraError = ref(false);
const isRecording = ref(false);
const recordingTime = ref('00:00');
const recordedBlob = ref(null);
const mediaRecorder = ref(null);
const recordingTimer = ref(null);
const recordingSeconds = ref(0);
const mediaStream = ref(null);

// 初始化摄像头
const initCamera = async () => {
  hasCamera.value = false;
  cameraError.value = false;
  
  if (mediaStream.value) {
    stopCamera();
  }
  
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('您的浏览器不支持摄像头访问');
    }
    
    mediaStream.value = await navigator.mediaDevices.getUserMedia({ 
      video: { width: { ideal: 1280 }, height: { ideal: 720 } }, 
      audio: true 
    });
    
    await nextTick();
    
    if (!videoPreview.value) {
      throw new Error('无法找到视频预览元素');
    }
    
    videoPreview.value.srcObject = mediaStream.value;
    hasCamera.value = true;
    
    videoPreview.value.onloadedmetadata = () => {
      videoPreview.value.play().catch(e => console.error('视频播放失败:', e));
    };
  } catch (err) {
    console.error('摄像头访问失败:', err);
    hasCamera.value = false;
    cameraError.value = true;
    ElMessage.error(`无法访问摄像头: ${err.message || '请确保您的设备有摄像头并且已授权访问权限'}`);
  }
};

// 停止摄像头
const stopCamera = () => {
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop());
    mediaStream.value = null;
    
    if (videoPreview.value) {
      videoPreview.value.srcObject = null;
    }
    
    if (isRecording.value) {
      stopRecording();
    }
    
    hasCamera.value = false;
  }
};

// 开始录制
const startRecording = () => {
  if (!hasCamera.value || !mediaStream.value) return;
  
  mediaRecorder.value = new MediaRecorder(mediaStream.value);
  const chunks = [];
  
  mediaRecorder.value.ondataavailable = (e) => {
    if (e.data.size > 0) chunks.push(e.data);
  };
  
  mediaRecorder.value.onstop = () => {
    recordedBlob.value = new Blob(chunks, { type: 'video/webm' });
  };
  
  mediaRecorder.value.start();
  isRecording.value = true;
  recordingSeconds.value = 0;
  
  recordingTimer.value = setInterval(() => {
    recordingSeconds.value++;
    const mins = Math.floor(recordingSeconds.value / 60).toString().padStart(2, '0');
    const secs = (recordingSeconds.value % 60).toString().padStart(2, '0');
    recordingTime.value = `${mins}:${secs}`;
  }, 1000);
};

// 停止录制
const stopRecording = () => {
  if (!isRecording.value) return;
  
  mediaRecorder.value.stop();
  isRecording.value = false;
  clearInterval(recordingTimer.value);
  
  ElMessage.success('录制完成');
};

// 保存录制
const handleSave = () => {
  if (!recordedBlob.value) return;
  
  const videoFile = new File([recordedBlob.value], 'recorded-video.webm', { 
    type: 'video/webm'
  });
  
  emit('save', videoFile);
  recordedBlob.value = null;
};

// 暴露方法给父组件
defineExpose({
  initCamera,
  stopCamera
});

// 清理
onBeforeUnmount(() => {
  stopCamera();
  if (recordingTimer.value) {
    clearInterval(recordingTimer.value);
  }
});
</script>

<style scoped>
.record-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 24px;
  background: #fafbfc;
  border-radius: 12px;
}

.video-container {
  width: 100%;
  max-width: 640px;
  position: relative;
  background-color: #000;
  border-radius: 12px;
  overflow: hidden;
  margin: 0 auto 20px;
  border: 3px solid #e5e7eb;
  min-height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.video-preview {
  width: 100%;
  height: 100%;
  aspect-ratio: 16 / 9;
  background-color: #000;
  display: block;
}

.recording-indicator {
  position: absolute;
  top: 16px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.95) 0%, rgba(220, 38, 38, 0.95) 100%);
  color: #fff;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.recording-dot {
  width: 12px;
  height: 12px;
  background-color: #ffffff;
  border-radius: 50%;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.8; }
}

.camera-loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
}

.loading-icon {
  font-size: 48px;
  margin-bottom: 16px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.record-controls {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.camera-error {
  width: 100%;
  max-width: 640px;
}
</style>
