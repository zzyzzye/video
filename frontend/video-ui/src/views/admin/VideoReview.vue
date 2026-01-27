<template>
  <div class="video-review-container">
    <PageHeader 
      title="视频审核" 
      :breadcrumb="[{ label: '管理后台' }, { label: '视频审核' }]"
    >
      <template #actions>
        <el-input
          placeholder="搜索视频标题或上传者"
          v-model="searchQuery"
          class="search-input"
          prefix-icon="el-icon-search"
          clearable
          @clear="loadVideos"
          @keyup.enter.native="loadVideos"
        ></el-input>
        <el-button type="primary" @click="loadVideos">搜索</el-button>
      </template>
    </PageHeader>
    
    <el-tabs v-model="activeTab" @tab-click="handleTabChange">
      <el-tab-pane label="待审核" name="pending">
        <div class="video-list-container">
          <el-table
            v-loading="loading"
            :data="videos"
            style="width: 100%"
            @row-click="handleRowClick"
          >
            <el-table-column prop="id" label="ID" width="80"></el-table-column>
            <el-table-column label="缩略图" width="120">
              <template slot-scope="scope">
                <el-image
                  v-if="scope.row.thumbnail"
                  style="width: 100px; height: 56px"
                  :src="scope.row.thumbnail"
                  fit="cover"
                  :preview-src-list="[scope.row.thumbnail]"
                ></el-image>
                <div v-else class="thumbnail-placeholder-small">
                  <el-icon><VideoCamera /></el-icon>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" show-overflow-tooltip></el-table-column>
            <el-table-column prop="user.username" label="上传者"></el-table-column>
            <el-table-column label="时长">
              <template slot-scope="scope">
                {{ formatDuration(scope.row.duration) }}
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="上传时间" width="180">
              <template slot-scope="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template slot-scope="scope">
                <el-button
                  size="mini"
                  type="primary"
                  @click.stop="previewVideo(scope.row)"
                >预览</el-button>
                <el-button
                  size="mini"
                  type="success"
                  @click.stop="approveVideo(scope.row)"
                >通过</el-button>
                <el-button
                  size="mini"
                  type="danger"
                  @click.stop="rejectVideo(scope.row)"
                >拒绝</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination-container">
            <el-pagination
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
              :current-page="currentPage"
              :page-sizes="[10, 20, 50, 100]"
              :page-size="pageSize"
              layout="total, sizes, prev, pager, next, jumper"
              :total="total"
            ></el-pagination>
          </div>
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="已审核" name="reviewed">
        <div class="filter-container">
          <el-radio-group v-model="reviewStatus" @change="loadVideos">
            <el-radio-button label="approved">已通过</el-radio-button>
            <el-radio-button label="rejected">已拒绝</el-radio-button>
          </el-radio-group>
        </div>
        
        <div class="video-list-container">
          <el-table
            v-loading="loading"
            :data="videos"
            style="width: 100%"
            @row-click="handleRowClick"
          >
            <el-table-column prop="id" label="ID" width="80"></el-table-column>
            <el-table-column label="缩略图" width="120">
              <template slot-scope="scope">
                <el-image
                  v-if="scope.row.thumbnail"
                  style="width: 100px; height: 56px"
                  :src="scope.row.thumbnail"
                  fit="cover"
                  :preview-src-list="[scope.row.thumbnail]"
                ></el-image>
                <div v-else class="thumbnail-placeholder-small">
                  <el-icon><VideoCamera /></el-icon>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" show-overflow-tooltip></el-table-column>
            <el-table-column prop="user.username" label="上传者"></el-table-column>
            <el-table-column label="状态" width="100">
              <template slot-scope="scope">
                <el-tag :type="scope.row.status === 'approved' ? 'success' : 'danger'">
                  {{ scope.row.status === 'approved' ? '已通过' : '已拒绝' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="review_remark" label="审核备注" show-overflow-tooltip></el-table-column>
            <el-table-column prop="reviewed_at" label="审核时间" width="180">
              <template slot-scope="scope">
                {{ formatDate(scope.row.reviewed_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template slot-scope="scope">
                <el-button
                  size="mini"
                  type="primary"
                  @click.stop="previewVideo(scope.row)"
                >预览</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination-container">
            <el-pagination
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
              :current-page="currentPage"
              :page-sizes="[10, 20, 50, 100]"
              :page-size="pageSize"
              layout="total, sizes, prev, pager, next, jumper"
              :total="total"
            ></el-pagination>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
    
    <!-- 视频预览对话框 -->
    <el-dialog
      title="视频预览"
      :visible.sync="previewDialogVisible"
      width="70%"
      :before-close="handleClosePreview"
    >
      <div class="video-preview-container" v-if="currentVideo">
        <div class="video-player-wrapper">
          <!-- 只有当videoUrl有效时才渲染播放器 -->
          <video-player 
            v-if="videoUrl"
            :src="videoUrl"
            :poster="currentVideo.thumbnail"
            type="application/x-mpegURL"
            @error="handlePlayerError"
          ></video-player>
          <div v-else class="no-video-message">
            <el-alert
              title="视频文件不可用"
              type="warning"
              :closable="false"
              show-icon
            >
              <template #default>
                <div v-if="!currentVideo.hls_file">
                  <p>该视频尚未完成处理或HLS文件不存在</p>
                  <p style="margin-top: 8px; font-size: 12px;">
                    视频状态: {{ getStatusText(currentVideo.status) }}
                  </p>
                  <p style="margin-top: 4px; font-size: 12px; color: #909399;">
                    请等待视频处理完成后再预览
                  </p>
                </div>
                <div v-else>
                  <p>视频文件路径无效</p>
                  <p style="margin-top: 8px; font-size: 12px;">
                    HLS路径: {{ currentVideo.hls_file }}
                  </p>
                </div>
              </template>
            </el-alert>
          </div>
        </div>
        
        <div class="video-info">
          <h3>{{ currentVideo.title }}</h3>
          <p class="video-description">{{ currentVideo.description || '暂无描述' }}</p>
          
          <!-- 临时调试信息 -->
          <div style="background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 4px;">
            <p style="color: #e74c3c; font-weight: bold;">调试信息：</p>
            <p><strong>hls_file原始值：</strong>{{ currentVideo.hls_file }}</p>
            <p><strong>hls_file类型：</strong>{{ typeof currentVideo.hls_file }}</p>
            <p><strong>计算后的videoUrl：</strong>{{ videoUrl }}</p>
            <p><strong>videoUrl类型：</strong>{{ typeof videoUrl }}</p>
          </div>
          
          <div class="video-meta">
            <p><strong>上传者：</strong>{{ currentVideo.user?.username || '未知用户' }}</p>
            <p><strong>上传者ID：</strong>{{ currentVideo.user?.id || '-' }}</p>
            <p><strong>上传时间：</strong>{{ formatDate(currentVideo.created_at) }}</p>
            <p><strong>时长：</strong>{{ formatDuration(currentVideo.duration) }}</p>
            <p><strong>分类：</strong>{{ currentVideo.category?.name || '未分类' }}</p>
            <p><strong>标签：</strong>
              <el-tag v-for="tag in currentVideo.tags" :key="tag.id" size="small" style="margin-right: 5px;">
                {{ tag.name }}
              </el-tag>
              <span v-if="!currentVideo.tags || currentVideo.tags.length === 0">无标签</span>
            </p>
            <p><strong>视频状态：</strong>{{ getStatusText(currentVideo.status) }}</p>
            <p><strong>HLS文件：</strong>{{ currentVideo.hls_file || '未生成' }}</p>
          </div>
        </div>
        
        <div class="review-actions" v-if="currentVideo.status === 'pending'">
          <el-form ref="reviewForm" :model="reviewForm" label-width="80px">
            <el-form-item label="审核备注" prop="remark">
              <el-input
                type="textarea"
                v-model="reviewForm.remark"
                :rows="4"
                placeholder="请输入审核备注，拒绝时必填"
              ></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="success" @click="confirmApprove">通过审核</el-button>
              <el-button type="danger" @click="confirmReject">拒绝视频</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { getPendingVideos, getReviewedVideos, approveVideo, rejectVideo } from '@/api/admin';
import VideoPlayer from '@/components/video/VideoPlayer.vue';
import PageHeader from '@/components/common/PageHeader.vue';

export default {
  name: 'VideoReview',
  components: {
    VideoPlayer,
    PageHeader
  },
  data() {
    return {
      activeTab: 'pending',
      videos: [],
      loading: false,
      currentPage: 1,
      pageSize: 20,
      total: 0,
      searchQuery: '',
      reviewStatus: 'approved',
      previewDialogVisible: false,
      currentVideo: null,
      reviewForm: {
        remark: ''
      }
    };
  },
  computed: {
    videoUrl() {
      if (!this.currentVideo || !this.currentVideo.hls_file) {
        return null;
      }
      
      // 获取API基础URL
      const baseURL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000';
      
      // 构建完整URL - hls_file已经是正确的相对路径
      return `${baseURL}/media/${this.currentVideo.hls_file}`;
    }
  },
  created() {
    this.loadVideos();
  },
  methods: {
    getStatusText(status) {
      const statusMap = {
        'uploading': '上传中',
        'processing': '处理中',
        'ready': '就绪',
        'failed': '失败',
        'pending': '待审核',
        'approved': '已通过',
        'rejected': '已拒绝'
      };
      return statusMap[status] || status;
    },
    
    loadVideos() {
      this.loading = true;
      
      const params = {
        page: this.currentPage,
        page_size: this.pageSize,
        search: this.searchQuery || undefined
      };
      
      let request;
      if (this.activeTab === 'pending') {
        request = getPendingVideos(params);
      } else {
        params.status = this.reviewStatus;
        request = getReviewedVideos(params);
      }
      
      request
        .then(response => {
          this.videos = response.results;
          this.total = response.count;
        })
        .catch(error => {
          console.error('加载视频列表失败:', error);
          console.error('错误详情:', error.response?.data);
          this.$message.error('加载视频列表失败');
        })
        .finally(() => {
          this.loading = false;
        });
    },
    
    handleTabChange() {
      this.currentPage = 1;
      this.loadVideos();
    },
    
    handleSizeChange(size) {
      this.pageSize = size;
      this.loadVideos();
    },
    
    handleCurrentChange(page) {
      this.currentPage = page;
      this.loadVideos();
    },
    
    handleRowClick(row) {
      this.previewVideo(row);
    },
    
    previewVideo(video) {
      this.currentVideo = video;
      this.reviewForm.remark = '';
      this.previewDialogVisible = true;
    },
    
    handleClosePreview() {
      this.previewDialogVisible = false;
      this.currentVideo = null;
    },
    
    handlePlayerError(error) {
      console.error('视频播放器错误:', error);
      this.$message.error('视频加载失败，请检查视频文件是否存在或稍后重试');
    },
    
    approveVideo(video) {
      this.currentVideo = video;
      this.reviewForm.remark = '';
      this.confirmApprove();
    },
    
    rejectVideo(video) {
      this.currentVideo = video;
      this.reviewForm.remark = '';
      this.previewDialogVisible = true;
      
      // 滚动到备注输入框
      this.$nextTick(() => {
        const textarea = this.$el.querySelector('.review-actions textarea');
        if (textarea) {
          textarea.focus();
        }
      });
    },
    
    confirmApprove() {
      const videoId = this.currentVideo.id;
      const remark = this.reviewForm.remark;
      
      this.$confirm('确定通过该视频的审核吗?', '审核确认', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'success'
      }).then(() => {
        this.loading = true;
        approveVideo(videoId, { remark })
          .then(() => {
            this.$message.success('视频审核通过成功');
            this.previewDialogVisible = false;
            this.loadVideos();
          })
          .catch(error => {
            console.error('审核操作失败:', error);
            this.$message.error('审核操作失败: ' + (error.message || '未知错误'));
          })
          .finally(() => {
            this.loading = false;
          });
      }).catch(() => {});
    },
    
    confirmReject() {
      const videoId = this.currentVideo.id;
      const reason = this.reviewForm.remark;
      
      if (!reason) {
        this.$message.warning('拒绝视频时必须提供拒绝原因');
        return;
      }
      
      this.$confirm('确定拒绝该视频吗?', '审核确认', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.loading = true;
        rejectVideo(videoId, { reason })
          .then(() => {
            this.$message.success('视频已拒绝');
            this.previewDialogVisible = false;
            this.loadVideos();
          })
          .catch(error => {
            console.error('审核操作失败:', error);
            this.$message.error('审核操作失败: ' + (error.message || '未知错误'));
          })
          .finally(() => {
            this.loading = false;
          });
      }).catch(() => {});
    },
    
    formatDate(dateString) {
      if (!dateString) return '-';
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    },
    
    formatDuration(seconds) {
      if (!seconds) return '00:00';
      
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const secs = Math.floor(seconds % 60);
      
      if (hours > 0) {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
      } else {
        return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
      }
    }
  }
};
</script>

<style scoped>
.video-review-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-input {
  width: 300px;
}

.filter-container {
  margin-bottom: 20px;
}

.video-list-container {
  margin-top: 10px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.video-preview-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.video-player-wrapper {
  width: 100%;
  background-color: #000;
  border-radius: 4px;
  overflow: hidden;
}

.no-video-message {
  padding: 20px;
  background-color: #000;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-info {
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.video-description {
  margin: 10px 0;
  color: #606266;
  white-space: pre-line;
}

.video-meta {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.review-actions {
  margin-top: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.thumbnail-placeholder-small {
  width: 100px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 4px;
}

.thumbnail-placeholder-small .el-icon {
  font-size: 24px;
}
</style> 