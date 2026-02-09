<template>
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
      <slot></slot>
    </div>
    
    <!-- 下一个视频（预览） -->
    <div class="video-slide next-slide" v-if="nextVideo">
      <div class="slide-preview">
        <img :src="nextVideo.thumbnail || defaultThumbnail" alt="" />
        <div class="slide-title">{{ nextVideo.title }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  prevVideo: Object,
  nextVideo: Object,
  sliderStyle: Object,
  isTransitioning: Boolean
});

const defaultThumbnail = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 9"><rect fill="%23333" width="16" height="9"/></svg>';
</script>

<style scoped>
.video-slider {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
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

.slide-title {
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
</style>
