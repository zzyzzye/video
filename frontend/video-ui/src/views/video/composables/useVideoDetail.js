import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store/user';
import { ElMessage } from 'element-plus';
import service from '@/api/user';

export function useVideoDetail(videoId) {
  const router = useRouter();
  const userStore = useUserStore();
  
  const videoData = ref({
    id: videoId.value,
    title: '',
    description: '',
    views: '0',
    likes: '0',
    commentCount: 0,
    collectCount: 0,
    publishTime: '',
    creatorName: '',
    creatorId: null,
    creatorAvatar: '',
    category: null,
    tags: [],
    hls_file: '',
    thumbnail: '',
    collection: null,
    collectionIndex: 0
  });

  const isOwnVideo = computed(() => {
    return userStore.isLoggedIn && 
           videoData.value.creatorId && 
           userStore.userId === videoData.value.creatorId;
  });

  const isSubscribed = ref(false);
  const isLiked = ref(false);
  const isDisliked = ref(false);
  const isCollected = ref(false);
  const loading = ref(true);

  // 格式化函数
  const formatNumber = (n) => {
    if (!n) return '0';
    if (n >= 10000) return (n/10000).toFixed(1)+'万';
    if (n >= 1000) return (n/1000).toFixed(1)+'K';
    return n.toString();
  };

  const formatDate = (s) => {
    if (!s) return '';
    const d = new Date(s);
    const diff = Math.floor((Date.now()-d)/(1000*60*60*24));
    if (diff===0) return '今天';
    if (diff===1) return '昨天';
    if (diff<7) return `${diff}天前`;
    return `${d.getMonth()+1}-${d.getDate()}`;
  };

  const formatTimeAgo = (s) => {
    if (!s) return '';
    const diff = Date.now()-new Date(s).getTime();
    const m = Math.floor(diff/60000);
    if (m<1) return '刚刚';
    if (m<60) return `${m}分钟前`;
    const h = Math.floor(m/60);
    if (h<24) return `${h}小时前`;
    return formatDate(s);
  };

  // 获取视频详情
  const fetchVideoDetail = async () => {
    try {
      loading.value = true;
      const response = await service({
        url: `/videos/videos/${videoId.value}/`,
        method: 'get'
      });
      
      videoData.value = {
        id: response.id,
        title: response.title,
        description: response.description || '',
        views: formatNumber(response.views_count),
        likes: formatNumber(response.likes_count),
        commentCount: response.comments_count || 0,
        collectCount: response.favorites_count || 0,
        publishTime: formatDate(response.published_at || response.created_at),
        creatorName: response.user?.username || '未知用户',
        creatorId: response.user?.id,
        creatorAvatar: response.user?.avatar || '',
        category: response.category,
        tags: response.tags || [],
        hls_file: response.hls_file,
        thumbnail: response.thumbnail
      };
      
      isLiked.value = response.is_liked || false;
      isCollected.value = response.is_favorited || false;
      
      return videoData.value;
    } catch (error) {
      console.error('获取视频详情失败:', error);
      ElMessage.error('获取视频详情失败');
      throw error;
    } finally {
      loading.value = false;
    }
  };

  // 记录观看
  const recordView = async () => {
    try {
      await service({
        url: `/videos/videos/${videoId.value}/view/`,
        method: 'post',
        data: { watched_duration: 0 }
      });
    } catch (error) {
      console.error('记录观看失败:', error);
    }
  };

  // 互动操作
  const toggleSubscribe = async () => {
    try {
      if (isSubscribed.value) {
        await service({
          url: `/users/${videoData.value.creatorId}/unfollow/`,
          method: 'post'
        });
        isSubscribed.value = false;
        ElMessage.success('已取消关注');
      } else {
        await service({
          url: `/users/${videoData.value.creatorId}/follow/`,
          method: 'post'
        });
        isSubscribed.value = true;
        ElMessage.success('关注成功');
      }
    } catch (error) {
      ElMessage.error('操作失败');
    }
  };

  const toggleLike = async () => {
    try {
      if (isLiked.value) {
        await service({
          url: `/videos/videos/${videoId.value}/unlike/`,
          method: 'post'
        });
        isLiked.value = false;
        videoData.value.likes = formatNumber(
          parseInt(videoData.value.likes.replace(/[^0-9]/g, '')) - 1
        );
      } else {
        await service({
          url: `/videos/videos/${videoId.value}/like/`,
          method: 'post'
        });
        if (isDisliked.value) isDisliked.value = false;
        isLiked.value = true;
        videoData.value.likes = formatNumber(
          parseInt(videoData.value.likes.replace(/[^0-9]/g, '')) + 1
        );
      }
    } catch (error) {
      ElMessage.error('操作失败');
    }
  };

  const toggleDislike = () => {
    if (isDisliked.value) {
      isDisliked.value = false;
    } else {
      if (isLiked.value) {
        isLiked.value = false;
        videoData.value.likes = formatNumber(
          parseInt(videoData.value.likes.replace(/[^0-9]/g, '')) - 1
        );
      }
      isDisliked.value = true;
    }
  };

  const toggleCollect = async () => {
    try {
      const prev = !!isCollected.value;
      const res = await service({
        url: `/videos/collections/${videoId.value}/toggle/`,
        method: 'post'
      });
      const next = typeof res?.is_collected === 'boolean' ? res.is_collected : !prev;
      isCollected.value = next;
      
      const currentCount = Number(videoData.value.collectCount || 0) || 0;
      videoData.value.collectCount = next ? currentCount + 1 : Math.max(currentCount - 1, 0);
      ElMessage.success(next ? '收藏成功' : '已取消收藏');
    } catch (error) {
      ElMessage.error('操作失败');
    }
  };

  const shareVideo = () => {
    navigator.clipboard.writeText(window.location.href)
      .then(() => ElMessage.success('链接已复制'));
  };

  return {
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
  };
}
