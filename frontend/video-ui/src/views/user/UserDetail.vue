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

      <!-- 用户信息卡片 -->
      <div class="user-info-card">
        <div class="container">
          <div class="user-header">
            <!-- 头像 -->
            <div class="avatar-section">
              <el-avatar :size="100" :src="userData.avatar || defaultAvatar">
                <el-icon :size="40"><User /></el-icon>
              </el-avatar>
              <div v-if="userData.is_vip" class="vip-badge">
                <el-icon><Trophy /></el-icon>
              </div>
            </div>

            <!-- 用户信息 -->
            <div class="info-section">
              <div class="name-row">
                <h1 class="username">{{ userData.username }}</h1>
                <el-tag v-if="userData.is_vip" type="warning" size="small">VIP</el-tag>
                <el-tag v-if="userData.role === 'admin'" type="danger" size="small">管理员</el-tag>
              </div>

              <div class="bio">{{ userData.bio || '这个人很懒，什么都没有留下~' }}</div>

              <!-- 统计数据 -->
              <div class="stats-row">
                <div class="stat-item">
                  <span class="value">{{ formatNumber(userData.followers_count || 0) }}</span>
                  <span class="label">粉丝</span>
                </div>
                <div class="stat-item">
                  <span class="value">{{ formatNumber(userData.following_count || 0) }}</span>
                  <span class="label">关注</span>
                </div>
                <div class="stat-item">
                  <span class="value">{{ formatNumber(totalViews) }}</span>
                  <span class="label">播放</span>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="action-section">
              <el-button
                v-if="!isCurrentUser"
                :type="isSubscribed ? 'default' : 'primary'"
                :loading="subscribeLoading"
                @click="toggleSubscribe"
              >
                {{ isSubscribed ? '已关注' : '+ 关注' }}
              </el-button>
              <el-button v-if="isCurrentUser" type="primary" @click="$router.push('/user/profile')">
                编辑资料
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="container">
        <div class="content-tabs">
          <el-tabs v-model="activeTab">
            <!-- 视频作品 -->
            <el-tab-pane name="videos">
              <template #label>
                <span class="tab-label">
                  <el-icon><VideoCamera /></el-icon>
                  视频 {{ userVideos.length }}
                </span>
              </template>

              <div v-if="userVideos.length === 0" class="empty-state">
                <el-empty description="暂无视频作品">
                  <el-button v-if="isCurrentUser" type="primary" @click="$router.push('/dashboard/create')">
                    上传视频
                  </el-button>
                </el-empty>
              </div>

              <div v-else class="videos-list">
                <div v-for="video in userVideos" :key="video.id" class="video-card" @click="goToVideo(video.id)">
                  <div class="video-cover">
                    <el-image :src="video.thumbnail" fit="cover" lazy>
                      <template #error>
                        <div class="image-error">
                          <el-icon><VideoCamera /></el-icon>
                        </div>
                      </template>
                    </el-image>
                    <div class="duration">{{ formatDuration(video.duration) }}</div>
                  </div>
                  <div class="video-content">
                    <h3 class="video-title">{{ video.title }}</h3>
                    <div class="video-stats">
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

              <div class="about-content">
                <div class="info-card">
                  <h3 class="card-title">基本信息</h3>
                  <div class="info-list">
                    <div class="info-row">
                      <span class="label">用户名</span>
                      <span class="value">{{ userData.username }}</span>
                    </div>
                    <div class="info-row" v-if="userData.email">
                      <span class="label">邮箱</span>
                      <span class="value">{{ userData.email }}</span>
                    </div>
                    <div class="info-row" v-if="userData.gender">
                      <span class="label">性别</span>
                      <span class="value">{{ userData.gender === 'M' ? '男' : userData.gender === 'F' ? '女' : '其他' }}</span>
                    </div>
                    <div class="info-row" v-if="userData.birthday">
                      <span class="label">生日</span>
                      <span class="value">{{ formatDate(userData.birthday) }}</span>
                    </div>
                  </div>
                </div>

                <div class="info-card">
                  <h3 class="card-title">账号信息</h3>
                  <div class="info-list">
                    <div class="info-row">
                      <span class="label">注册时间</span>
                      <span class="value">{{ formatDateTime(userData.created_at) }}</span>
                    </div>
                    <div class="info-row">
                      <span class="label">会员状态</span>
                      <span class="value">
                        <el-tag v-if="userData.is_vip" type="warning" size="small">VIP会员</el-tag>
                        <el-tag v-else type="info" size="small">普通用户</el-tag>
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
.user-detail-page {
  min-height: 100vh;
  background: #f4f5f7;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.loading-icon {
  animation: rotate 1.5s linear infinite;
  margin-bottom: 20px;
  color: #409eff;
}

@keyframes rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.user-banner {
  height: 200px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.user-info-card {
  background: white;
  margin-top: -80px;
  position: relative;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.user-header {
  display: flex;
  align-items: flex-start;
  padding: 24px 0;
  gap: 24px;
}

.avatar-section {
  position: relative;
  flex-shrink: 0;
}

.avatar-section .el-avatar {
  border: 4px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
  color: #fff;
  font-size: 14px;
}

.info-section {
  flex: 1;
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.username {
  font-size: 24px;
  font-weight: 600;
  color: #18191c;
  margin: 0;
}

.bio {
  color: #61666d;
  font-size: 14px;
  margin-bottom: 16px;
}

.stats-row {
  display: flex;
  gap: 32px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-item .value {
  font-size: 20px;
  font-weight: 600;
  color: #18191c;
}

.stat-item .label {
  font-size: 13px;
  color: #9499a0;
}

.action-section {
  flex-shrink: 0;
  padding-top: 8px;
}

.content-tabs {
  background: white;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

:deep(.el-tabs__header) {
  margin: 0;
  padding: 0 24px;
  border-bottom: 1px solid #e3e5e7;
}

:deep(.el-tabs__item) {
  height: 48px;
  line-height: 48px;
  color: #61666d;
}

:deep(.el-tabs__item.is-active) {
  color: #00a1d6;
}

:deep(.el-tabs__active-bar) {
  height: 2px;
  background: #00a1d6;
}

:deep(.el-tabs__content) {
  padding: 24px;
}

.videos-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.video-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.video-card:hover {
  transform: translateY(-4px);
}

.video-cover {
  position: relative;
  width: 100%;
  padding-bottom: 62.5%;
  background: #f1f2f3;
  border-radius: 8px;
  overflow: hidden;
}

.video-cover .el-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #f1f2f3;
  color: #c9ccd0;
  font-size: 32px;
}

.duration {
  position: absolute;
  bottom: 6px;
  right: 6px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.video-content {
  padding: 8px 0;
}

.video-title {
  font-size: 14px;
  font-weight: 500;
  color: #18191c;
  margin: 0 0 6px 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  height: 40px;
}

.video-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #9499a0;
}

.video-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.about-content {
  max-width: 800px;
}

.info-card {
  background: #fafafa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #18191c;
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid #e3e5e7;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
}

.info-row .label {
  color: #61666d;
  font-size: 14px;
}

.info-row .value {
  color: #18191c;
  font-size: 14px;
  font-weight: 500;
}

@media (max-width: 768px) {
  .user-banner {
    height: 120px;
  }

  .user-info-card {
    margin-top: -60px;
  }

  .user-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .stats-row {
    justify-content: center;
  }

  .action-section {
    width: 100%;
  }

  .videos-list {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }

  .info-row {
    flex-direction: column;
    gap: 4px;
  }
}
</style>
