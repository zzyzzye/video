import { ref } from 'vue';
import service from '@/api/user';

export function useSubtitles(videoId) {
  const subtitleList = ref([]);
  const subtitleStyle = ref({
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

  const fetchSubtitles = async () => {
    try {
      const response = await service({
        url: `/videos/videos/${videoId.value}/subtitles/`,
        method: 'get'
      });
      
      const subtitles = response.subtitles || [];
      subtitleList.value = subtitles.map(sub => ({
        start: sub.startTime || sub.start_time,
        end: sub.endTime || sub.end_time,
        text: sub.text || '',
        translation: sub.translation || ''
      }));
      
      if (response.style) {
        subtitleStyle.value = { ...subtitleStyle.value, ...response.style };
      }
      
      console.log(`加载了 ${subtitleList.value.length} 条字幕`);
    } catch (error) {
      console.error('获取字幕失败:', error);
      subtitleList.value = [];
    }
  };

  return {
    subtitleList,
    subtitleStyle,
    fetchSubtitles
  };
}
