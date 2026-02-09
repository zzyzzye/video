import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useUserStore } from '@/store/user';
import service from '@/api/user';

export function useComments(videoId, formatTimeAgo) {
  const userStore = useUserStore();
  const comments = ref([]);

  const fetchComments = async () => {
    try {
      const response = await service({
        url: '/videos/comments/',
        method: 'get',
        params: { video_id: videoId.value }
      });
      
      comments.value = (response.results || []).map(c => ({
        id: c.id,
        username: c.user?.username || '匿名用户',
        userAvatar: c.user?.avatar || '',
        text: c.text,
        time: formatTimeAgo(c.created_at),
        likes: c.likes_count || 0,
        isLiked: false
      }));
    } catch (error) {
      console.error('获取评论失败:', error);
    }
  };

  const addComment = async (text) => {
    if (!text.trim()) return;
    
    try {
      const response = await service({
        url: '/videos/comments/',
        method: 'post',
        data: { video: videoId.value, text }
      });
      
      comments.value.unshift({
        id: response.id,
        username: userStore.userInfo?.username || '我',
        userAvatar: userStore.userInfo?.avatar || '',
        text: text,
        time: '刚刚',
        likes: 0,
        isLiked: false
      });
      
      ElMessage.success('评论成功');
      return true;
    } catch (error) {
      ElMessage.error('评论失败');
      return false;
    }
  };

  const toggleCommentLike = (comment) => {
    comment.isLiked = !comment.isLiked;
    comment.likes += comment.isLiked ? 1 : -1;
  };

  return {
    comments,
    fetchComments,
    addComment,
    toggleCommentLike
  };
}

export function useDanmaku(videoId) {
  const danmakuList = ref([]);

  const fetchDanmaku = async () => {
    try {
      const response = await service({
        url: '/videos/danmaku/',
        method: 'get',
        params: { video_id: videoId.value }
      });
      
      danmakuList.value = (response.results || response || []).map(d => ({
        text: d.text || d.content,
        time: d.time || d.timestamp || 0,
        color: d.color || '#ffffff',
        mode: d.mode || 0
      }));
    } catch (error) {
      danmakuList.value = [];
    }
  };

  const sendDanmaku = async (danmaku) => {
    try {
      await service({
        url: '/videos/danmaku/',
        method: 'post',
        data: {
          video: videoId.value,
          text: danmaku.text,
          time: danmaku.time,
          color: danmaku.color || '#ffffff',
          mode: danmaku.mode || 0
        }
      });
    } catch (error) {
      console.error('发送弹幕失败:', error);
    }
  };

  return {
    danmakuList,
    fetchDanmaku,
    sendDanmaku
  };
}
