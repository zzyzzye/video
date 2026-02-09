import { ref, computed } from 'vue';
import service from '@/api/user';

export function useVideoSlider(videoId) {
  const videoList = ref([]);
  const currentIndex = ref(-1);
  const slideOffset = ref(0);
  const isTransitioning = ref(false);
  let wheelLock = false;

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

  // 获取视频列表
  const fetchVideoList = async () => {
    try {
      const response = await service({
        url: '/videos/videos/',
        method: 'get',
        params: { page_size: 20 }
      });
      videoList.value = response.results || [];
      currentIndex.value = videoList.value.findIndex(v => v.id == videoId.value);
    } catch (error) {
      console.error('获取视频列表失败:', error);
    }
  };

  // 滚轮切换视频
  const handleWheel = (e, slideCallback) => {
    if (wheelLock || isTransitioning.value) return;
    
    const delta = e.deltaY;
    if (Math.abs(delta) < 50) return;
    
    if (delta > 0 && nextVideo.value) {
      slideToVideo('next', slideCallback);
    } else if (delta < 0 && prevVideo.value) {
      slideToVideo('prev', slideCallback);
    }
  };

  // 切换到指定视频
  const slideToVideo = async (direction, slideCallback) => {
    wheelLock = true;
    isTransitioning.value = true;
    
    const targetVideo = direction === 'next' ? nextVideo.value : prevVideo.value;
    if (!targetVideo) {
      wheelLock = false;
      isTransitioning.value = false;
      return;
    }
    
    // 预加载视频数据
    let preloadedData = null;
    try {
      const response = await service({
        url: `/videos/videos/${targetVideo.id}/`,
        method: 'get'
      });
      preloadedData = response;
    } catch (e) {
      console.error('预加载失败', e);
    }
    
    const vh = window.innerHeight;
    slideOffset.value = direction === 'next' ? -vh : vh;
    
    setTimeout(async () => {
      // 执行回调，更新所有数据
      if (preloadedData && slideCallback) {
        await slideCallback(targetVideo, preloadedData);
      }
      
      // 更新当前索引
      currentIndex.value = videoList.value.findIndex(v => v.id == targetVideo.id);
      
      // 重置动画状态
      isTransitioning.value = false;
      slideOffset.value = 0;
      
      // 静默更新 URL
      window.history.replaceState({}, '', `/video/${targetVideo.id}`);
      
      setTimeout(() => { wheelLock = false; }, 300);
    }, 400);
  };

  return {
    videoList,
    currentIndex,
    prevVideo,
    nextVideo,
    slideOffset,
    isTransitioning,
    sliderStyle,
    fetchVideoList,
    handleWheel,
    slideToVideo
  };
}
