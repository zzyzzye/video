<template>
  <div class="user-detail-page-full">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-full animate__animated animate__fadeIn">
      <el-icon class="loading-icon-spin" :size="40"><Loading /></el-icon>
      <span>正在加载个人空间...</span>
    </div>

    <!-- 用户不存在 -->
    <div v-else-if="userNotFound" class="error-full animate__animated animate__fadeIn">
      <el-result icon="error" title="用户未找到" sub-title="该用户可能已注销或地址有误">
        <template #extra>
          <el-button type="primary" @click="$router.push('/')">回到首页</el-button>
        </template>
      </el-result>
    </div>

    <div v-else class="page-layout">
      <!-- 左侧紧凑侧边栏 -->
      <aside class="user-aside animate__animated animate__fadeInLeft">
        <div class="aside-scroll">
          <div class="user-profile-compact">
            <div class="avatar-wrap animate__animated animate__zoomIn">
              <el-avatar :size="100" :src="userData.avatar || defaultAvatar" class="profile-avatar" />
              <div v-if="userData.is_vip" class="vip-tag-abs animate__animated animate__bounceIn animate__delay-1s">VIP</div>
            </div>
            <h1 class="profile-name animate__animated animate__fadeInUp">{{ userData.username }}</h1>
            <p class="profile-bio animate__animated animate__fadeInUp animate__delay-1s">{{ userData.bio || '暂无介绍' }}</p>

            <div class="profile-actions-full animate__animated animate__fadeInUp animate__delay-1s">
              <template v-if="!isCurrentUser">
                <el-button
                  :type="isSubscribed ? 'info' : 'primary'"
                  :loading="subscribeLoading"
                  class="action-btn-full"
                  @click="toggleSubscribe"
                >
                  {{ isSubscribed ? '已关注' : '关注作者' }}
                </el-button>
                <el-button class="action-btn-full" plain>私信</el-button>
              </template>
              <el-button 
                v-else 
                type="primary" 
                class="action-btn-full"
                @click="$router.push('/user/profile')"
              >
                修改个人资料
              </el-button>
            </div>

            <div class="stat-grid-compact animate__animated animate__fadeInUp animate__delay-1s">
              <div class="stat-item-c">
                <span class="v">{{ formatNumber(userData.followers_count || 0) }}</span>
                <span class="l">粉丝</span>
              </div>
              <div class="stat-item-c">
                <span class="v">{{ formatNumber(userData.following_count || 0) }}</span>
                <span class="l">关注</span>
              </div>
              <div class="stat-item-c">
                <span class="v">{{ formatNumber(totalViews) }}</span>
                <span class="l">获赞</span>
              </div>
            </div>
          </div>

          <nav class="aside-nav">
            <div 
              v-for="(tab, index) in tabs" 
              :key="tab.name"
              :class="['nav-item', { active: activeTab === tab.name }]"
              class="animate__animated animate__fadeInLeft"
              :style="{ animationDelay: `${0.2 + index * 0.1}s` }"
              @click="activeTab = tab.name"
            >
              <el-icon><component :is="tab.icon" /></el-icon>
              <span>{{ tab.label }}</span>
              <span v-if="tab.count !== undefined" class="nav-count">{{ tab.count }}</span>
            </div>
          </nav>

          <div class="aside-footer animate__animated animate__fadeIn animate__delay-2s">
            <div class="footer-info">
              <p><span>UID</span> {{ userData.id }}</p>
              <p><span>注册于</span> {{ formatDate(userData.created_at) }}</p>
            </div>
          </div>
        </div>
      </aside>

      <!-- 右侧主内容区 -->
      <main class="main-content-full animate__animated animate__fadeInRight">
        <!-- 视频列表 -->
        <div v-if="activeTab === 'videos'" class="content-view">
          <header class="view-header animate__animated animate__fadeInDown">
            <h2 class="view-title">投稿视频</h2>
            <div class="view-tools">
              <el-select v-model="sortOrder" size="small" style="width: 100px">
                <el-option label="最新发布" value="new" />
                <el-option label="最多播放" value="hot" />
              </el-select>
            </div>
          </header>

          <div v-if="userVideos.length === 0" class="empty-compact animate__animated animate__fadeIn">
            <el-empty :image-size="120" description="这里空空如也" />
          </div>

          <div v-else class="compact-grid">
            <div 
              v-for="(video, index) in sortedVideos" 
              :key="video.id" 
              class="video-card-tight animate__animated animate__fadeInUp"
              :style="{ animationDelay: `${index * 0.05}s` }"
              @click="goToVideo(video.id)"
            >
              <div class="thumb-tight">
                <el-image 
                  :src="video.thumbnail || '/src/assets/default-avatar.png'" 
                  fit="cover" 
                  lazy
                >
                  <template #error>
                    <div class="image-error">
                      <el-icon><Picture /></el-icon>
                    </div>
                  </template>
                </el-image>
                <div v-if="video.duration" class="duration-abs">{{ formatDuration(video.duration) }}</div>
                <div class="play-overlay">
                  <el-icon><CaretRight /></el-icon>
                </div>
              </div>
              <div class="info-tight">
                <h3 class="title-tight" :title="video.title">{{ video.title }}</h3>
                <div class="meta-tight">
                  <span class="play-count">
                    <el-icon><View /></el-icon>
                    {{ formatNumber(video.views_count) }}
                  </span>
                  <span class="time-tight">{{ formatRelativeTime(video.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 收藏列表 -->
        <div v-else-if="activeTab === 'collect'" class="content-view">
          <header class="view-header animate__animated animate__fadeInDown">
            <h2 class="view-title">收藏夹</h2>
          </header>
          <div class="animate__animated animate__fadeIn">
            <el-empty description="暂无公开收藏" />
          </div>
        </div>

        <!-- 个人资料 -->
        <div v-else-if="activeTab === 'info'" class="content-view">
          <header class="view-header animate__animated animate__fadeInDown">
            <h2 class="view-title">个人信息</h2>
          </header>
          <div class="info-details-compact">
            <div class="info-group animate__animated animate__fadeInUp">
              <label>基本资料</label>
              <div class="info-row-c">
                <span class="label">用户名</span>
                <span class="val">{{ userData.username }}</span>
              </div>
              <div class="info-row-c">
                <span class="label">性别</span>
                <span class="val">{{ userData.gender === 'M' ? '男' : userData.gender === 'F' ? '女' : '保密' }}</span>
              </div>
              <div class="info-row-c" v-if="userData.birthday">
                <span class="label">生日</span>
                <span class="val">{{ formatDate(userData.birthday) }}</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import { getUserById, subscribeUser, unsubscribeUser, checkSubscriptionStatus, getUserVideos } from '@/api/user'
import { getCollections } from '@/api/video'
import { getToken } from '@/utils/auth'
import { useUserStore } from '@/store/user'
import { 
  User, VideoCamera, View, Trophy, InfoFilled, 
  Loading, Star, CaretRight, Collection, Picture 
} from '@element-plus/icons-vue'

export default {
  name: 'UserDetail',
  components: { 
    User, VideoCamera, View, Trophy, InfoFilled, 
    Loading, Star, CaretRight, Collection, Picture 
  },
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
      sortOrder: 'new',
      defaultAvatar: '/src/assets/default-avatar.png',
      tabs: [
        { label: '投稿作品', name: 'videos', icon: 'VideoCamera', count: 0 },
        { label: '我的收藏', name: 'collect', icon: 'Star' },
        { label: '关于作者', name: 'info', icon: 'InfoFilled' }
      ]
    }
  },
  computed: {
    userId() {
      return this.$route.params.id
    },
    isCurrentUser() {
      return this.userData.id && getToken() && String(this.userData.id) === String(this.userStore.userId)
    },
    totalViews() {
      if (!Array.isArray(this.userVideos)) return 0
      return this.userVideos.reduce((sum, video) => sum + (video.views_count || 0), 0)
    },
    sortedVideos() {
      if (!Array.isArray(this.userVideos)) return []
      const videos = [...this.userVideos]
      if (this.sortOrder === 'new') {
        return videos.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      } else {
        return videos.sort((a, b) => b.views_count - a.views_count)
      }
    }
  },
  watch: {
    userVideos: {
      handler(val) {
        const videoTab = this.tabs.find(t => t.name === 'videos')
        if (videoTab) videoTab.count = val.length
      },
      immediate: true
    }
  },
  created() {
    this.loadUserData()
  },
  methods: {
    async loadUserData() {
      try {
        this.loading = true
        
        // 获取用户信息
        const userResponse = await getUserById(this.userId)
        this.userData = userResponse

        // 获取该用户的公开视频（已发布且审核通过）
        const videosResponse = await getUserVideos(this.userId, {
          is_published: true,
          status: 'approved'
        })
        
        // 处理分页响应
        if (videosResponse && videosResponse.results) {
          this.userVideos = videosResponse.results
        } else if (Array.isArray(videosResponse)) {
          this.userVideos = videosResponse
        } else {
          this.userVideos = []
        }

        // 如果是当前用户，加载收藏夹数量
        if (this.isCurrentUser) {
          try {
            const collectionsResponse = await getCollections()
            const collections = collectionsResponse.results || collectionsResponse || []
            const collectTab = this.tabs.find(t => t.name === 'collect')
            if (collectTab) collectTab.count = collections.length
          } catch (error) {
            console.error('加载收藏夹失败:', error)
          }
        }

        // 检查关注状态
        if (!this.isCurrentUser && getToken()) {
          try {
            const response = await checkSubscriptionStatus(this.userId)
            this.isSubscribed = response.is_subscribed
          } catch (error) {
            console.error('检查关注状态失败:', error)
          }
        }
      } catch (error) {
        console.error('加载用户数据失败:', error)
        if (error.response?.status === 404) {
          this.userNotFound = true
        } else {
          this.$message.error('加载失败，请稍后重试')
        }
      } finally {
        this.loading = false
      }
    },

    async toggleSubscribe() {
      if (!getToken()) {
        this.$message.warning('请先登录')
        this.$router.push('/login')
        return
      }
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
/* 100% 宽度紧凑布局样式 */
.user-detail-page-full {
  height: 100%;
  min-height: 100%;
  background-color: #f9f9f9;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.loading-full, .error-full {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fff;
}

.loading-icon-spin {
  animation: spin 1s linear infinite;
  color: #00aeec;
  margin-bottom: 12px;
}

.page-layout {
  display: flex;
  height: 100%;
  width: 100%;
}

/* 侧边栏样式 */
.user-aside {
  width: 280px;
  background: #fff;
  border-right: 1px solid #e3e5e7;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  z-index: 10;
}

.aside-scroll {
  flex: 1;
  overflow-y: auto;
  scrollbar-width: thin;
}

.user-profile-compact {
  padding: 32px 24px 24px;
  text-align: center;
  border-bottom: 1px solid #f1f2f3;
}

.avatar-wrap {
  position: relative;
  display: inline-block;
  margin-bottom: 16px;
}

.profile-avatar {
  border: 3px solid #f1f2f3;
}

.vip-tag-abs {
  position: absolute;
  bottom: 0;
  right: 0;
  background: #fb7299;
  color: #fff;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  border: 2px solid #fff;
  font-weight: bold;
}

.profile-name {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 8px;
  color: #18191c;
}

.profile-bio {
  font-size: 12px;
  color: #9499a0;
  line-height: 1.5;
  margin: 0 0 20px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-clamp: 2;
  overflow: hidden;
}

.profile-actions-full {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 24px;
}

.action-btn-full {
  width: 100%;
  margin: 0 !important;
  font-weight: 500;
}

.stat-grid-compact {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-item-c {
  display: flex;
  flex-direction: column;
}

.stat-item-c .v {
  font-size: 15px;
  font-weight: bold;
  color: #18191c;
}

.stat-item-c .l {
  font-size: 11px;
  color: #9499a0;
}

/* 侧边导航 */
.aside-nav {
  padding: 16px 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: #61666d;
  font-size: 14px;
  margin-bottom: 4px;
}

.nav-item:hover {
  background: #f1f2f3;
}

.nav-item.active {
  background: #00aeec15;
  color: #00aeec;
  font-weight: 600;
}

.nav-count {
  margin-left: auto;
  font-size: 11px;
  background: #f1f2f3;
  color: #9499a0;
  padding: 2px 8px;
  border-radius: 10px;
}

.aside-footer {
  padding: 24px;
  margin-top: auto;
}

.footer-info {
  font-size: 12px;
  color: #9499a0;
}

.footer-info p {
  margin: 4px 0;
  display: flex;
  justify-content: space-between;
}

/* 主内容区样式 */
.main-content-full {
  flex: 1;
  background: #fff;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.content-view {
  padding: 24px 32px;
  max-width: 1600px; /* 适当限制最大宽度以保持阅读舒适度 */
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.view-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

/* 紧凑视频网格 */
.compact-grid {
  display: grid;
  /* 动态列数，从最小 180px 开始自动填充 */
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 16px;
}

.video-card-tight {
  cursor: pointer;
  transition: transform 0.2s;
}

.video-card-tight:hover {
  transform: translateY(-2px);
}

.thumb-tight {
  position: relative;
  aspect-ratio: 16/10;
  border-radius: 6px;
  overflow: hidden;
  background: #f1f2f3;
}

.thumb-tight .el-image {
  width: 100%;
  height: 100%;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #f5f5f5;
  color: #ccc;
  font-size: 40px;
}

.duration-abs {
  position: absolute;
  bottom: 6px;
  right: 6px;
  background: rgba(0,0,0,0.7);
  color: #fff;
  font-size: 11px;
  padding: 2px 4px;
  border-radius: 4px;
}

.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
  color: #fff;
  font-size: 40px;
}

.video-card-tight:hover .play-overlay {
  opacity: 1;
}

.info-tight {
  padding: 8px 0 0;
}

.title-tight {
  font-size: 13px;
  font-weight: 500;
  margin: 0 0 6px;
  line-height: 1.4;
  height: 36px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-clamp: 2;
  overflow: hidden;
  color: #18191c;
}

.meta-tight {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #9499a0;
}

.play-count {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 详情信息 */
.info-details-compact {
  max-width: 600px;
}

.info-group {
  margin-bottom: 32px;
}

.info-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #9499a0;
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.info-row-c {
  display: flex;
  padding: 12px 0;
  border-bottom: 1px solid #f1f2f3;
  font-size: 14px;
}

.info-row-c .label {
  width: 100px;
  color: #61666d;
}

.info-row-c .val {
  color: #18191c;
  font-weight: 500;
}

@keyframes spin {
  from { transform: rotate(0); }
  to { transform: rotate(360deg); }
}

/* 响应式 */
@media (max-width: 900px) {
  .user-aside {
    width: 220px;
  }
}

@media (max-width: 768px) {
  .user-detail-page-full {
    height: auto;
    overflow: visible;
  }
  .page-layout {
    flex-direction: column;
  }
  .user-aside {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e3e5e7;
  }
  .aside-scroll {
    overflow-y: visible;
  }
  .user-profile-compact {
    padding: 24px;
  }
  .aside-nav {
    display: flex;
    padding: 8px;
    overflow-x: auto;
  }
  .nav-item {
    margin-bottom: 0;
    white-space: nowrap;
  }
  .aside-footer {
    display: none;
  }
  .main-content-full {
    overflow-y: visible;
  }
  .content-view {
    padding: 16px;
  }
  .compact-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
}
</style>
