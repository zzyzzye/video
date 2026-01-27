<template>
  <div class="dashboard-content">
    <PageHeader 
      title="我的评论" 
      :breadcrumb="[{ label: '视频管理' }, { label: '我的评论' }]"
    />

    <div class="comments-section">
      <el-card v-if="loading" class="loading-card">
        <el-skeleton :rows="5" animated />
      </el-card>
      
      <el-empty v-else-if="comments.length === 0" description="暂无评论记录" />
      
      <div v-else class="comments-list">
        <el-card v-for="comment in comments" :key="comment.id" class="comment-card">
          <div class="comment-header">
            <div class="video-info">
              <el-image :src="comment.video.cover" class="video-cover" fit="cover"></el-image>
              <div class="video-title">
                <router-link :to="`/video/${comment.video.id}`">{{ comment.video.title }}</router-link>
              </div>
            </div>
            <div class="comment-actions">
              <el-button type="danger" size="small" text @click="deleteComment(comment.id)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
          <div class="comment-content">
            <p>{{ comment.content }}</p>
          </div>
          <div class="comment-footer">
            <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
            <div class="comment-stats">
              <span class="likes">
                <el-icon><Star /></el-icon>
                {{ comment.likes_count }}
              </span>
              <span class="replies">
                <el-icon><ChatDotRound /></el-icon>
                {{ comment.replies_count }}
              </span>
            </div>
          </div>
        </el-card>
        
        <el-pagination
          v-if="total > pageSize"
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          prev-text="上一页"
          next-text="下一页"
          :popper-props="{
            popperClass: 'custom-pagination-dropdown'
          }"
        >
          <template #total>
            共 <strong>{{ total }}</strong> 条
          </template>
          <template #sizes="{ size }">
            {{ size }}条/页
          </template>
        </el-pagination>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Delete, Star, ChatDotRound } from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import axios from 'axios';
import { getToken } from '@/utils/auth';

// 评论列表数据
const comments = ref([]);
const loading = ref(true);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 获取评论列表
const fetchComments = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/users/comments/', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      },
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });
    
    comments.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error('获取评论列表失败:', error);
    ElMessage.error('获取评论列表失败，请重试');
  } finally {
    loading.value = false;
  }
};

// 删除评论
const deleteComment = (commentId) => {
  ElMessageBox.confirm(
    '确定要删除这条评论吗？',
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        await axios.delete(`/api/users/comments/${commentId}/`, {
          headers: {
            'Authorization': `Bearer ${getToken()}`
          }
        });
        ElMessage.success('评论删除成功');
        fetchComments(); // 重新加载评论列表
      } catch (error) {
        console.error('删除评论失败:', error);
        ElMessage.error('删除评论失败，请重试');
      }
    })
    .catch(() => {
      // 用户取消删除
    });
};

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val;
  fetchComments();
};

const handleCurrentChange = (val) => {
  currentPage.value = val;
  fetchComments();
};

onMounted(() => {
  fetchComments();
});
</script>

<style scoped>
/* 仪表盘内容容器 */
.dashboard-content {
  width: 100%;
  min-height: 100%;
  padding: 24px;
  box-sizing: border-box;
  overflow-x: hidden;
  background-color: var(--grey);
}

/* 头部标题 */
.head-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  grid-gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.head-title .left h1 {
  font-size: 36px;
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--dark, #342E37);
}

.head-title .left .breadcrumb {
  display: flex;
  align-items: center;
  grid-gap: 16px;
  list-style: none;
  padding: 0;
  margin: 0;
}

.head-title .left .breadcrumb li {
  color: var(--dark, #342E37);
}

.head-title .left .breadcrumb li a {
  color: var(--dark-grey, #AAAAAA);
  pointer-events: none;
  text-decoration: none;
}

.head-title .left .breadcrumb li a.active {
  color: var(--blue, #3C91E6);
  pointer-events: unset;
}

/* 评论部分 */
.comments-section {
  background: var(--light, #F9F9F9);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-card {
  margin-bottom: 16px;
  border: none;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.comment-card:last-child {
  margin-bottom: 0;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.video-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.video-cover {
  width: 80px;
  height: 45px;
  border-radius: 4px;
}

.video-title {
  font-weight: 500;
}

.video-title a {
  color: var(--dark, #342E37);
  text-decoration: none;
}

.video-title a:hover {
  color: var(--blue, #3C91E6);
}

.comment-content {
  margin-bottom: 12px;
}

.comment-content p {
  margin: 0;
  line-height: 1.6;
}

.comment-footer {
  display: flex;
  justify-content: space-between;
  color: var(--dark-grey, #AAAAAA);
  font-size: 14px;
}

.comment-stats {
  display: flex;
  gap: 16px;
}

.likes, .replies {
  display: flex;
  align-items: center;
  gap: 4px;
}

.loading-card {
  padding: 20px;
  margin-bottom: 0;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .dashboard-content {
    padding: 16px;
  }
  
  .head-title {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .comments-section {
    padding: 16px;
  }
  
  .comment-header {
    flex-direction: column;
    gap: 8px;
  }
  
  .comment-actions {
    align-self: flex-end;
  }
}

@media screen and (max-width: 576px) {
  .head-title .left h1 {
    font-size: 28px;
  }
  
  .video-info {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .comment-footer {
    flex-direction: column;
    gap: 8px;
  }
}
</style> 