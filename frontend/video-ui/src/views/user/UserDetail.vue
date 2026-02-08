<template>
  <div class="user-detail-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="loading-icon" :size="50"><Loading /></el-icon>
      <p>加载中...</p>
    </div>

    <!-- 用户不存在 -->
    <div v-else-if="userNotFound" class="error-container">
      <el-icon class="error-icon"><User /></el-icon>
      <h3>用户不存在</h3>
      <p>您要查看的用户可能已被删除或不存在。</p>
      <el-button type="primary" @click="$router.go(-1)">返回</el-button>
    </div>

    <!-- 用户详情内容 -->
    <div v-else class="user-content">
      <!-- 顶部横幅 -->
      <div class="user-banner"></div>

      <!-- 用户信息区域 -->
      <div class="container">
        <div class="user-info-section">
          <!-- 头像 -->
          <div class="avatar-wrapper">
            <el-avatar :size="120" :src="userData.avatar || defaultAvatar">
              <el-icon :size="50"><User /></el-icon>
            </el-avatar>
            <div v-if="userData.is_vip" class="vip-badge">
              <el-icon><Trophy /></el-icon>
            </div>
          </div>

          <!-- 用户信息 -->
          <div class="user-info">
            <div class="user-name-row">
              <h1 class="username">{{ userData.username }}</h1>
              <el-tag v-if="userData.is_vip" type="warning" size="small" effect="plain">VIP</el-tag>
              <el-tag v-if="userData.role === 'admin'" type="danger" size="small" effect="plain">管理员</el-tag>
            </div>
            <p class="user-bio">{{ userData.bio || '这个人很懒，什么都没有留下~' }}</p>

            <!-- 统计数据 -->
            <div class="user-stats">
              <div class="stat-item">
                <div class="stat-value">{{ formatNumber(userData.followers_count || 0) }}</div>
                <div class="stat-label">粉丝</div>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item">
                <div class="stat-value">{{ formatNumber(userData.following_count || 0) }}</div>
                <div class="stat-label">关注</div>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item">
                <div class="stat-value">{{ formatNumber(totalViews) }}</div>
                <div class="stat-label">播放</div>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="user-actions">
            <el-button
              v-if="!isCurrentUser"
              :type="isSubscribed ? 'default' : 'primary'"
              :loading="subscribeLoading"
              size="large"
              @click="toggleSubscribe"
            >
              {{ isSubscribed ? '已关注' : '+ 关注' }}
            </el-button>
            <el-button v-if="isCurrentUser" type="primary" size="large" @click="$router.push('/user/profile')">
              编辑资料
            </el-button>
          </div>
        </div>

        <!-- 内容标签页 -->
        <div class="content-section">
          <el-tabs v-model="activeTab" class="user-tabs">
            <!-- 视频作品 -->
            <el-tab-pane name="videos">
              <template #label>
                <span class="tab-label">
                  <el-icon><VideoCamera /></el-icon>
                  视频
                </span>
              </template>

              <div v-if="userVideos.length === 0" class="empty-state">
                <el-empty description="暂无视频作品">
                  <el-button v-if="isCurrentUser" type="primary" @click="$router.push('/dashboard/create')">
                    上传视频
                  </el-button>
                </el-empty>
              </div>

              <div v-else class="videos-grid">
                <div v-for="video in userVideos" :key="video.id" class="video-item" @click="goToVideo(video.id)">
                  <div class="video-thumbnail">
                    <el-image :src="video.thumbnail" fit="cover" lazy>
                      <template #error>
                        <div class="thumbnail-error">
                          <el-icon><VideoCamera /></el-icon>
                        </div>
                      </template>
                    </el-image>
                    <span class="video-duration">{{ formatDuration(video.duration) }}</span>
                  </div>
                  <div class="video-info">
                    <h3 class="video-title">{{ video.title }}</h3>
                    <div class="video-meta">
                      <span><el-icon><View /></el-icon> {{ formatNumber(video.views_count) }}</span>
                      <span>{{ formatRelativeTime(video.created_at) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <!-- 个人资料 -->
            <el-tab-pane name="about">
              <template #label>
                <span class="tab-label">
                  <el-icon><InfoFilled /></el-icon>
                  资料
                </span>
              </template>

              <div class="about-section">
                <!-- 基本信息 -->
                <div class="info-block">
                  <h3 class="block-title">基本信息</h3>
                  <div class="info-items">
                    <div class="info-item">
                      <span class="item-label">用户名</span>
                      <span class="item-value">{{ userData.username }}</span>
                    </div>
                    <div class="info-item" v-if="userData.email">
                      <span class="item-label">邮箱</span>
                      <span class="item-value">{{ userData.email }}</span>
                    </div>
                    <div class="info-item" v-if="userData.gender">
                      <span class="item-label">性别</span>
                      <span class="item-value">{{ userData.gender === 'M' ? '男' : userData.gender === 'F' ? '女' : '其他' }}</span>
                    </div>
                    <div class="info-item" v-if="userData.birthday">
                      <span class="item-label">生日</span>
                      <span class="item-value">{{ formatDate(userData.birthday) }}</span>
                    </div>
                  </div>
                </div>

                <!-- 账号信息 -->
                <div class="info-block">
                  <h3 class="block-title">账号信息</h3>
                  <div class="info-items">
                    <div class="info-item">
                      <span class="item-label">注册时间</span>
                      <span class="item-value">{{ formatDateTime(userData.created_at) }}</span>
                    </div>
                    <div class="info-item">
                      <span class="item-label">会员状态</span>
                      <span class="item-value">
                        <el-tag v-if="userData.is_vip" type="warning" size="small" effect="plain">VIP会员</el-tag>
                        <el-tag v-else type="info" size="small" effect="plain">普通用户</el-tag>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getUserById, subscribeUser, unsubscribeUser, getUserVideos, checkSubscriptionStatus } from '@/api/user'
import { getToken } from '@/utils/auth'
import { useUserStore } from '@/store/user'
import { User, VideoCamera, View, Trophy, InfoFilled, Loading } from '@element-plus/icons-vue'

export default {
  name: 'UserDetail',
  components: { User, VideoCamera, View, Trophy, InfoFilled, Loading },
  setup() {
    return { userStore: useUserStore() }
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
    },
    totalViews() {
      return this.userVideos.reduce((sum, video) => sum + (video.views_count || 0), 0)
    }
  },
  created() {
    this.loadUserData()
  },
  methods: {
    async loadUserData() {
      try {
        this.loading = true
        const userResponse = await getUserById(this.userId)
        this.userData = userResponse

        const videosResponse = await getUserVideos(this.userId)
        this.userVideos = videosResponse.results || []

        if (!this.isCurrentUser) {
          const response = await checkSubscriptionStatus(this.userId)
          this.isSubscribed = response.is_subscribed
        }
      } catch (error) {
        if (error.response?.status === 404) {
          this.userNotFound = true
        } else {
          this.$message.error('加载失败')
        }
      } finally {
        this.loading = false
      }
    },

    async toggleSubscribe() {
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
        this.$message.error('操作失败')
      } finally {
        this.subscribeLoading = false
      }
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
      if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿'
      if (num >= 10000) return (num / 10000).toFixed(1) + '万'
      return num.toString()
    },

    formatDate(dateString) {
      if (!dateString) return ''
      return new Date(dateString).toLocaleDateString('zh-CN')
    },

    formatDateTime(dateString) {
      if (!dateString) return ''
      return new Date(dateString).toLocaleString('zh-CN')
    },

    formatRelativeTime(dateString) {
      if (!dateString) return ''
      const diff = Date.now() - new Date(dateString)
      const days = Math.floor(diff / 86400000)
      if (days > 365) return Math.floor(days / 365) + '年前'
      if (days > 30) return Math.floor(days / 30) + '个月前'
      if (days > 0) return days + '天前'
      const hours = Math.floor(diff / 3600000)
      if (hours > 0) return hours + '小时前'
      const minutes = Math.floor(diff / 60000)
      if (minutes > 0) return minutes + '分钟前'
      return '刚刚'
    }
  }
}
</script>

<style scoped>
/* 基础布局 */
.user-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* 加载和错误状态 */
.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  color: #666;
}

.loading-icon {
  animation: rotate 1.5s linear infinite;
  margin-bottom: 16px;
  color: #409eff;
}

.error-icon {
  font-size: 64px;
  color: #909399;
  margin-bottom: 16px;
}

.error-container h3 {
  font-size: 20px;
  color: #303133;
  margin-bottom: 8px;
}

.error-container p {
  color: #909399;
  margin-bottom: 20px;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 顶部横幅 */
.user-banner {
  height: 180px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 用户信息区域 */
.user-info-section {
  background: white;
  margin-top: -60px;
  padding: 24px 32px 32px;
  border-radius: 4px;
  margin-bottom: 16px;
  display: flex;
  align-items: flex-start;
  gap: 24px;
}

/* 头像 */
.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}

.avatar-wrapper .el-avatar {
  border: 4px solid white;
}

.vip-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 28px;
  height: 28px;
  background: #ffd700;
  border-radius: 50%;
  border: 3px solid white;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
}

/* 用户信息 */
.user-info {
  flex: 1;
  min-width: 0;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.username {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.user-bio {
  color: #606266;
  font-size: 14px;
  margin: 0 0 16px 0;
  line-height: 1.6;
}

/* 统计数据 */
.user-stats {
  display: flex;
  align-items: center;
  gap: 24px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 2px;
}

.stat-divider {
  width: 1px;
  height: 24px;
  background: #dcdfe6;
}

/* 操作按钮 */
.user-actions {
  flex-shrink: 0;
  padding-top: 8px;
}

.user-actions .el-button {
  min-width: 100px;
}

/* 内容区域 */
.content-section {
  background: white;
  border-radius: 4px;
  padding: 0;
}

.user-tabs {
  padding: 0;
}

:deep(.el-tabs__header) {
  margin: 0;
  padding: 0 24px;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

:deep(.el-tabs__item) {
  height: 50px;
  line-height: 50px;
  color: #606266;
  font-size: 14px;
  padding: 0 16px;
}

:deep(.el-tabs__item.is-active) {
  color: #409eff;
  font-weight: 500;
}

:deep(.el-tabs__active-bar) {
  height: 2px;
  background: #409eff;
}

:deep(.el-tabs__content) {
  padding: 24px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 空状态 */
.empty-state {
  padding: 60px 20px;
  text-align: center;
}

/* 视频网格 */
.videos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
}

.video-item {
  cursor: pointer;
  transition: all 0.2s;
}

.video-item:hover {
  transform: translateY(-2px);
}

.video-item:hover .video-title {
  color: #409eff;
}

/* 视频缩略图 */
.video-thumbnail {
  position: relative;
  width: 100%;
  padding-bottom: 62.5%;
  background: #f5f7fa;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.video-thumbnail .el-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.thumbnail-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  color: #c0c4cc;
  font-size: 32px;
}

.video-duration {
  position: absolute;
  bottom: 6px;
  right: 6px;
  background: rgba(0, 0, 0, 0.75);
  color: white;
  padding: 2px 6px;
  border-radius: 2px;
  font-size: 12px;
}

/* 视频信息 */
.video-info {
  padding: 0;
}

.video-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 6px 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 40px;
  transition: color 0.2s;
}

.video-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.video-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 资料区域 */
.about-section {
  max-width: 800px;
}

.info-block {
  background: #fafafa;
  border-radius: 4px;
  padding: 20px;
  margin-bottom: 16px;
}

.block-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.info-items {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.item-label {
  color: #606266;
  font-size: 14px;
}

.item-value {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-banner {
    height: 120px;
  }

  .user-info-section {
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin-top: -50px;
    padding: 20px;
  }

  .avatar-wrapper .el-avatar {
    width: 100px !important;
    height: 100px !important;
  }

  .user-name-row {
    justify-content: center;
  }

  .username {
    font-size: 20px;
  }

  .user-stats {
    justify-content: center;
  }

  .user-actions {
    width: 100%;
    padding-top: 0;
  }

  .user-actions .el-button {
    width: 100%;
  }

  :deep(.el-tabs__header) {
    padding: 0 16px;
  }

  :deep(.el-tabs__content) {
    padding: 16px;
  }

  .videos-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
  }

  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}

@media (max-width: 480px) {
  .container {
    padding: 0 12px;
  }

  .user-info-section {
    padding: 16px;
  }

  .user-stats {
    gap: 16px;
  }

  .stat-value {
    font-size: 18px;
  }

  .videos-grid {
    grid-template-columns: 1fr;
  }
}
</style>
