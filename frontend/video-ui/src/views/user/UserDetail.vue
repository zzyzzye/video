<template>
  <div class="user-detail-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- 用户不存在 -->
    <div v-else-if="userNotFound" class="error-container">
      <el-icon class="error-icon"><User /></el-icon>
      <h3>用户不存在</h3>
      <p>您要查看的用户可能已被删除或不存在。</p>
      <el-button @click="$router.go(-1)">返回</el-button>
    </div>

    <!-- 用户详情内容 -->
    <div v-else class="user-content">
      <!-- 用户信息头部 -->
      <div class="user-header">
        <div class="user-avatar-section">
          <el-avatar :size="120" :src="userData.avatar || defaultAvatar">
            <el-icon><User /></el-icon>
          </el-avatar>
        </div>

        <div class="user-info-section">
          <div class="user-name-row">
            <h1 class="user-name">{{ userData.username }}</h1>
            <span v-if="userData.is_vip" class="vip-badge">VIP</span>
          </div>

          <div class="user-stats">
            <div class="stat-item">
              <span class="stat-value">{{ userData.following_count || 0 }}</span>
              <span class="stat-label">关注</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ userData.followers_count || 0 }}</span>
              <span class="stat-label">粉丝</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ userVideos.length }}</span>
              <span class="stat-label">视频</span>
            </div>
          </div>

          <div class="user-bio" v-if="userData.bio">
            <p>{{ userData.bio }}</p>
          </div>

          <div class="user-actions">
            <el-button
              v-if="!isCurrentUser"
              :type="isSubscribed ? 'default' : 'primary'"
              :loading="subscribeLoading"
              @click="toggleSubscribe"
            >
              <el-icon><Plus v-if="!isSubscribed" /><Check v-else /></el-icon>
              <span>{{ isSubscribed ? '已关注' : '关注' }}</span>
            </el-button>
          </div>
        </div>
      </div>

      <!-- 标签页 -->
      <div class="user-tabs">
        <el-tabs v-model="activeTab" @tab-click="handleTabClick">
          <el-tab-pane label="视频" name="videos">
            <!-- 视频列表 -->
            <div v-if="userVideos.length === 0" class="empty-state">
              <el-icon class="empty-icon"><VideoCamera /></el-icon>
              <p>暂无视频</p>
            </div>

            <div v-else class="videos-grid">
              <div
                v-for="(video, index) in userVideos"
                :key="video.id"
                class="video-item"
                :style="{ animationDelay: `${index * 0.05}s` }"
                @click="goToVideo(video.id)"
              >
                <div class="video-cover-wrapper">
                  <el-image
                    :src="video.thumbnail"
                    fit="cover"
                    class="video-cover"
                    lazy
                  >
                    <template #error>
                      <div class="cover-error">
                        <el-icon><VideoCamera /></el-icon>
                      </div>
                    </template>
                  </el-image>

                  <!-- 播放时长 -->
                  <div class="video-duration-overlay">
                    <el-icon class="play-icon-small"><VideoPlay /></el-icon>
                    <span>{{ formatDuration(video.duration) }}</span>
                  </div>

                  <!-- 分辨率标识 -->
                  <div v-if="video.resolution_label" class="resolution-badge" :class="video.resolution_label.toLowerCase()">
                    {{ video.resolution_label }}
                  </div>
                </div>

                <div class="video-info">
                  <h4 class="video-title">{{ video.title }}</h4>
                  <div class="video-stats">
                    <span>{{ formatNumber(video.views_count) }} 次观看</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="关于" name="about">
            <div class="about-section">
              <div class="info-item" v-if="userData.gender">
                <label>性别：</label>
                <span>{{ userData.gender === 'M' ? '男' : userData.gender === 'F' ? '女' : '其他' }}</span>
              </div>
              <div class="info-item" v-if="userData.birthday">
                <label>生日：</label>
                <span>{{ formatDate(userData.birthday) }}</span>
              </div>
              <div class="info-item" v-if="userData.website">
                <label>网站：</label>
                <a :href="userData.website" target="_blank" rel="noopener noreferrer">{{ userData.website }}</a>
              </div>
              <div class="info-item">
                <label>注册时间：</label>
                <span>{{ formatDate(userData.created_at) }}</span>
              </div>
              <div class="info-item" v-if="userData.last_login">
                <label>最后登录：</label>
                <span>{{ formatDate(userData.last_login) }}</span>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script>
import { getUserById, subscribeUser, unsubscribeUser, getUserVideos, checkSubscriptionStatus } from '@/api/user'
import { getToken } from '@/utils/auth'
import { useUserStore } from '@/store/user'
import { User, VideoCamera, VideoPlay, Plus, Check } from '@element-plus/icons-vue'

export default {
  name: 'UserDetail',
  components: {
    User,
    VideoCamera,
    VideoPlay,
    Plus,
    Check
  },
  setup() {
    const userStore = useUserStore()
    return {
      userStore
    }
  },
  data() {
    return {
      loading: true,
      userNotFound: false,
      userData: {},
      userVideos: [],
      isSubscribed: false,
      subscribeLoading: false,
      activeTab: 'videos',
      defaultAvatar: '/src/assets/default-avatar.png'
    }
  },
  computed: {
    userId() {
      return this.$route.params.id
    },
    isCurrentUser() {
      return this.userData.id && getToken() && this.userData.id === this.userStore.userId
    }
  },
  created() {
    this.loadUserData()
  },
  methods: {
    async loadUserData() {
      try {
        this.loading = true
        this.userNotFound = false

        // 获取用户信息
        const userResponse = await getUserById(this.userId)
        this.userData = userResponse

        // 获取用户视频
        const videosResponse = await getUserVideos(this.userId)
        this.userVideos = videosResponse.results || []

        // 检查是否已订阅（如果不是当前用户）
        if (!this.isCurrentUser) {
          this.checkSubscriptionStatus()
        }
      } catch (error) {
        console.error('加载用户数据失败:', error)
        if (error.response?.status === 404) {
          this.userNotFound = true
        } else {
          this.$message.error('加载用户数据失败')
        }
      } finally {
        this.loading = false
      }
    },

    async checkSubscriptionStatus() {
      try {
        const response = await checkSubscriptionStatus(this.userId)
        this.isSubscribed = response.is_subscribed
      } catch (error) {
        console.error('检查订阅状态失败:', error)
        this.isSubscribed = false
      }
    },

    async toggleSubscribe() {
      if (this.isCurrentUser) return

      try {
        this.subscribeLoading = true

        if (this.isSubscribed) {
          await unsubscribeUser(this.userId)
          this.isSubscribed = false
          this.$message.success('已取消关注')
        } else {
          await subscribeUser(this.userId)
          this.isSubscribed = true
          this.$message.success('关注成功')
        }
      } catch (error) {
        console.error('操作失败:', error)
        this.$message.error(error.response?.data?.detail || '操作失败')
      } finally {
        this.subscribeLoading = false
      }
    },

    handleTabClick(tab) {
      this.activeTab = tab.props.name
    },

    goToVideo(videoId) {
      this.$router.push(`/video/${videoId}`)
    },

    formatDuration(duration) {
      if (!duration) return '00:00'

      const minutes = Math.floor(duration / 60)
      const seconds = Math.floor(duration % 60)

      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    },

    formatNumber(num) {
      if (!num) return '0'

      if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M'
      } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K'
      }

      return num.toString()
    },

    formatDate(dateString) {
      if (!dateString) return ''

      const date = new Date(dateString)
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }
  }
}
</script>

<style scoped>
.user-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: 40px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-container .error-icon {
  font-size: 64px;
  color: #909399;
  margin-bottom: 20px;
}

.error-container h3 {
  color: #303133;
  margin-bottom: 10px;
}

.error-container p {
  color: #909399;
  margin-bottom: 20px;
}

.user-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

/* 用户头部 */
.user-header {
  background: white;
  border-radius: 12px;
  padding: 40px;
  margin-bottom: 20px;
  display: flex;
  gap: 40px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.user-avatar-section {
  flex-shrink: 0;
}

.user-info-section {
  flex: 1;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.user-name {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.vip-badge {
  background: linear-gradient(135deg, #ffd700, #ffed4e);
  color: #303133;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.user-stats {
  display: flex;
  gap: 40px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.user-bio {
  margin-bottom: 20px;
}

.user-bio p {
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

.user-actions .el-button {
  min-width: 120px;
}

/* 标签页 */
.user-tabs {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

/* 视频网格 */
.videos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  padding: 20px;
}

.video-item {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  animation: fadeInUp 0.6s ease both;
}

.video-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.video-cover-wrapper {
  position: relative;
  width: 100%;
  padding-bottom: 56.25%; /* 16:9 aspect ratio */
  overflow: hidden;
}

.video-cover {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #f5f5f5;
  color: #909399;
  font-size: 32px;
}

.video-duration-overlay {
  position: absolute;
  bottom: 8px;
  left: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.play-icon-small {
  font-size: 12px;
}

.resolution-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
}

.resolution-badge.hd {
  background: rgba(255, 193, 7, 0.9);
  color: #303133;
}

.resolution-badge.fhd {
  background: rgba(76, 175, 80, 0.9);
  color: white;
}

.resolution-badge.uhd {
  background: rgba(156, 39, 176, 0.9);
  color: white;
}

.video-info {
  padding: 12px;
}

.video-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 8px 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-clamp: 2;
  overflow: hidden;
}

.video-stats {
  font-size: 12px;
  color: #909399;
}

/* 关于页面 */
.about-section {
  padding: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item label {
  font-weight: 500;
  color: #303133;
  min-width: 80px;
}

.info-item span,
.info-item a {
  color: #606266;
}

.info-item a {
  text-decoration: none;
}

.info-item a:hover {
  color: #409eff;
  text-decoration: underline;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-state p {
  font-size: 16px;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-content {
    padding: 10px;
  }

  .user-header {
    flex-direction: column;
    text-align: center;
    padding: 20px;
  }

  .user-stats {
    justify-content: center;
  }

  .videos-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 15px;
    padding: 15px;
  }
}
</style>
