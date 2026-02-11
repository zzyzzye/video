<template>
  <header class="douyin-nav">
    <div class="nav-wrapper">
      <!-- 左侧：Logo -->
      <div class="nav-left">
        <div class="logo" @click="goHome">
          <span class="logo-icon">📺</span>
          <span class="logo-text">MindPalette</span>
        </div>
      </div>

      <!-- 中间：搜索框 -->
      <div class="nav-center">
        <div class="search-container">
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="搜索你感兴趣的视频"
            @keyup.enter="handleSearch"
            @focus="searchFocused = true"
            @blur="searchFocused = false"
          />
          <button class="search-button" @click="handleSearch">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M7.33333 12.6667C10.2789 12.6667 12.6667 10.2789 12.6667 7.33333C12.6667 4.38781 10.2789 2 7.33333 2C4.38781 2 2 4.38781 2 7.33333C2 10.2789 4.38781 12.6667 7.33333 12.6667Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M14 14L11.1 11.1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 右侧：用户操作 -->
      <div class="nav-right">
        <!-- 未登录状态 -->
        <template v-if="!isLoggedIn">
          <button class="btn-secondary" @click="goLogin">登录</button>
        </template>

        <!-- 已登录状态 -->
        <template v-else>
          <!-- 上传按钮 -->
          <button class="btn-upload" @click="goUpload">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M9 3.75V14.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <path d="M5.25 7.5L9 3.75L12.75 7.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M3.75 14.25H14.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            <span>投稿</span>
          </button>

          <!-- 消息按钮 -->
          <div class="notification-wrapper" v-click-outside="closeNotificationMenu">
            <button class="icon-button" @click="toggleNotificationMenu" title="消息通知">
              <el-icon :size="20">
                <Bell />
              </el-icon>
              <span v-if="unreadCount > 0" class="badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
            </button>
            
            <!-- 消息下拉菜单 -->
            <transition name="dropdown">
              <div v-if="showNotificationMenu" class="notification-dropdown">
                <div class="notification-header">
                  <span class="notification-title">消息通知</span>
                  <span v-if="unreadCount > 0" class="unread-tag">{{ unreadCount }} 条未读</span>
                </div>
                
                <div class="notification-list" v-if="recentNotifications.length > 0">
                  <div 
                    v-for="notification in recentNotifications" 
                    :key="notification.id"
                    class="notification-item"
                    :class="{ 'unread': !notification.read }"
                    @click="handleNotificationClick(notification)"
                  >
                    <div class="notification-dot" v-if="!notification.read"></div>
                    <div class="notification-content">
                      <div class="notification-item-title">{{ notification.title }}</div>
                      <div class="notification-item-desc">{{ notification.content }}</div>
                      <div class="notification-item-time">{{ formatNotificationTime(notification.created_at) }}</div>
                    </div>
                  </div>
                </div>
                
                <div class="notification-empty" v-else>
                  <el-icon :size="32" color="#9ca3af"><Bell /></el-icon>
                  <p>暂无消息</p>
                </div>
                
                <div class="notification-footer">
                  <span @click="goMessages">查看全部消息</span>
                </div>
              </div>
            </transition>
          </div>

          <!-- 用户菜单 -->
          <div class="user-menu" @click="toggleUserMenu" v-click-outside="closeUserMenu">
            <img :src="userAvatar" alt="头像" class="avatar" />
            
            <!-- 下拉菜单 -->
            <transition name="dropdown">
              <div v-if="showUserMenu" class="dropdown-menu">
                <div class="dropdown-header">
                  <img :src="userAvatar" alt="头像" class="dropdown-avatar" />
                  <div class="dropdown-user-info">
                    <div class="dropdown-username">{{ userName }}</div>
                    <div class="dropdown-userid">编号：{{ userId }}</div>
                  </div>
                </div>
                
                <div class="dropdown-divider"></div>
                
                <div class="dropdown-item" @click="goProfile">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M13.3333 14V12.6667C13.3333 11.9594 13.0524 11.2811 12.5523 10.781C12.0522 10.281 11.3739 10 10.6667 10H5.33333C4.62609 10 3.94781 10.281 3.44772 10.781C2.94762 11.2811 2.66667 11.9594 2.66667 12.6667V14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M8 7.33333C9.47276 7.33333 10.6667 6.13943 10.6667 4.66667C10.6667 3.19391 9.47276 2 8 2C6.52724 2 5.33333 3.19391 5.33333 4.66667C5.33333 6.13943 6.52724 7.33333 8 7.33333Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <span>个人主页</span>
                </div>
                
                <div class="dropdown-item" @click="goMyVideos">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M14.6667 7.38667V4.66667C14.6667 3.19391 13.4728 2 12 2H4C2.52724 2 1.33333 3.19391 1.33333 4.66667V11.3333C1.33333 12.8061 2.52724 14 4 14H7.38" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M10.6667 12L12.6667 14L15.3333 10.6667" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <span>作品管理</span>
                </div>
                
                <div class="dropdown-item" @click="goCollections">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M8 2L9.545 5.13L13 5.635L10.5 8.07L11.09 11.51L8 9.885L4.91 11.51L5.5 8.07L3 5.635L6.455 5.13L8 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <span>我的收藏</span>
                </div>
                
                <div class="dropdown-divider"></div>
                
                <div class="dropdown-item" @click="handleLogout">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M6 14H3.33333C2.97971 14 2.64057 13.8595 2.39052 13.6095C2.14048 13.3594 2 13.0203 2 12.6667V3.33333C2 2.97971 2.14048 2.64057 2.39052 2.39052C2.64057 2.14048 2.97971 2 3.33333 2H6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M10.6667 11.3333L14 8L10.6667 4.66667" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M14 8H6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <span>退出登录</span>
                </div>
              </div>
            </transition>
          </div>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { useNotificationStore } from '@/store/notification'
import { Bell } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const notificationStore = useNotificationStore()

const searchQuery = ref('')
const searchFocused = ref(false)
const showUserMenu = ref(false)
const showNotificationMenu = ref(false)

const isLoggedIn = computed(() => userStore.isLoggedIn)
const userAvatar = computed(() => userStore.avatar || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png')
const userName = computed(() => userStore.username || '用户')
const userId = computed(() => userStore.userId || '000000')
const unreadCount = computed(() => notificationStore.unreadCount)
const recentNotifications = computed(() => notificationStore.recentNotifications)

// 格式化通知时间
const formatNotificationTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60 * 1000) return '刚刚'
  if (diff < 60 * 60 * 1000) return Math.floor(diff / (60 * 1000)) + '分钟前'
  if (diff < 24 * 60 * 60 * 1000) return Math.floor(diff / (60 * 60 * 1000)) + '小时前'
  if (diff < 7 * 24 * 60 * 60 * 1000) return Math.floor(diff / (24 * 60 * 60 * 1000)) + '天前'
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

// 处理通知点击
const handleNotificationClick = async (notification) => {
  // 标记为已读
  if (!notification.read) {
    await notificationStore.markAsRead(notification.id)
  }
  
  // 跳转
  showNotificationMenu.value = false
  if (notification.source_type === 'video' && notification.source_id) {
    router.push(`/video/${notification.source_id}`)
  } else {
    router.push('/user/message')
  }
}

// 切换消息菜单
const toggleNotificationMenu = () => {
  showNotificationMenu.value = !showNotificationMenu.value
  if (showNotificationMenu.value) {
    notificationStore.fetchRecentNotifications()
  }
}

// 关闭消息菜单
const closeNotificationMenu = () => {
  showNotificationMenu.value = false
}

// 点击外部关闭菜单的指令
const vClickOutside = {
  mounted(el, binding) {
    el.clickOutsideEvent = (event) => {
      if (!(el === event.target || el.contains(event.target))) {
        binding.value()
      }
    }
    document.addEventListener('click', el.clickOutsideEvent)
  },
  unmounted(el) {
    document.removeEventListener('click', el.clickOutsideEvent)
  }
}

const goHome = () => {
  router.push('/')
}

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({
      path: '/search',
      query: { q: searchQuery.value }
    })
  }
}

const goLogin = () => {
  router.push('/login')
}

const goUpload = () => {
  router.push('/user/dashboard')
  showUserMenu.value = false
}

const goMessages = () => {
  showNotificationMenu.value = false
  router.push('/user/message')
}

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

const closeUserMenu = () => {
  showUserMenu.value = false
}

const goProfile = () => {
  router.push('/user/profile')
  showUserMenu.value = false
}

const goMyVideos = () => {
  router.push('/user/videos/uploaded')
  showUserMenu.value = false
}

const goCollections = () => {
  router.push('/user/videos/collection')
  showUserMenu.value = false
}

const handleLogout = () => {
  notificationStore.reset()
  userStore.logout()
  showUserMenu.value = false
  router.push('/')
}

// 监听登录状态
watch(isLoggedIn, (newVal) => {
  if (newVal) {
    notificationStore.init()
  } else {
    notificationStore.reset()
  }
})

onMounted(() => {
  if (isLoggedIn.value) {
    notificationStore.init()
  }
})
</script>

<style scoped>
/* Dashboard风格导航栏 */
.douyin-nav {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.nav-wrapper {
  max-width: 1920px;
  margin: 0 auto;
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 左侧 Logo */
.nav-left {
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  transition: opacity 0.2s;
}

.logo:hover {
  opacity: 0.8;
}

.logo-icon {
  font-size: 32px;
  line-height: 1;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: #3b82f6;
  letter-spacing: -0.5px;
}

/* 中间搜索框 */
.nav-center {
  flex: 1;
  max-width: 560px;
  margin: 0 40px;
}

.search-container {
  position: relative;
  display: flex;
  align-items: center;
  background: #f3f4f6;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
  border: 1px solid transparent;
}

.search-container:hover {
  background: #e5e7eb;
}

.search-container:focus-within {
  background: #ffffff;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-input {
  flex: 1;
  height: 40px;
  padding: 0 16px;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: #111827;
  font-weight: 500;
}

.search-input::placeholder {
  color: #9ca3af;
  font-weight: 400;
}

.search-button {
  width: 48px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.search-button:hover {
  color: #3b82f6;
}

/* 右侧操作区 */
.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

/* 按钮样式 - Dashboard风格 */
.btn-secondary {
  height: 36px;
  padding: 0 24px;
  border: 1px solid #3b82f6;
  border-radius: 8px;
  background: #ffffff;
  color: #3b82f6;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-secondary:hover {
  background: #3b82f6;
  color: #ffffff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-upload {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 20px;
  border: none;
  border-radius: 8px;
  background: #3b82f6;
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-upload:hover {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.btn-upload svg {
  width: 18px;
  height: 18px;
}

/* 图标按钮 - Dashboard风格 */
.icon-button {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  border-radius: 50%;
  transition: all 0.2s;
}

.icon-button:hover {
  background: #f3f4f6;
  color: #3b82f6;
}

.icon-button svg {
  transition: transform 0.2s;
}

.icon-button:hover :deep(.el-icon) {
  transform: scale(1.1);
}

.badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  /* padding: 0 4px; */
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ef4444;
  color: #ffffff;
  font-size: 10px;
  font-weight: 700;
  /* line-height: 1; */
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3);
  border-radius: 50%;
}

/* 消息通知下拉菜单 */
.notification-wrapper {
  position: relative;
}

.notification-dropdown {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  width: 320px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  z-index: 100;
}

.notification-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.notification-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.unread-tag {
  font-size: 12px;
  color: #3b82f6;
  background: #eff6ff;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.notification-list {
  max-height: 320px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f3f4f6;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item:hover {
  background: #f9fafb;
}

.notification-item.unread {
  background: #eff6ff;
}

.notification-item.unread:hover {
  background: #dbeafe;
}

.notification-dot {
  width: 8px;
  height: 8px;
  background: #3b82f6;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-item-title {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-item-desc {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-item-time {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
}

.notification-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #9ca3af;
}

.notification-empty p {
  margin-top: 8px;
  font-size: 13px;
}

.notification-footer {
  padding: 12px 16px;
  text-align: center;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.notification-footer span {
  font-size: 13px;
  color: #3b82f6;
  cursor: pointer;
  font-weight: 500;
}

.notification-footer span:hover {
  text-decoration: underline;
}

/* 用户菜单 */
.user-menu {
  position: relative;
  cursor: pointer;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e5e7eb;
  transition: all 0.3s;
}

.user-menu:hover .avatar {
  border-color: #3b82f6;
  transform: scale(1.05);
}

/* 下拉菜单 - Dashboard风格 */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  width: 240px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  z-index: 100;
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #eff6ff 0%, #f3f4f6 100%);
  border-bottom: 1px solid #e5e7eb;
}

.dropdown-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

.dropdown-user-info {
  flex: 1;
  min-width: 0;
}

.dropdown-username {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-userid {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.dropdown-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 8px 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: #374151;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.dropdown-item:hover {
  background: #f3f4f6;
  color: #3b82f6;
  padding-left: 20px;
}

.dropdown-item svg {
  width: 16px;
  height: 16px;
  color: #6b7280;
  flex-shrink: 0;
  transition: color 0.2s;
}

.dropdown-item:hover svg {
  color: #3b82f6;
}

/* 下拉菜单动画 - Dashboard风格 */
.dropdown-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-leave-active {
  transition: all 0.2s ease-in;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-12px) scale(0.95);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}

/* 响应式 */
@media (max-width: 1024px) {
  .nav-center {
    margin: 0 24px;
  }
}

@media (max-width: 768px) {
  .nav-wrapper {
    padding: 0 12px;
  }

  .logo-text {
    display: none;
  }

  .nav-center {
    margin: 0 16px;
    max-width: none;
  }

  .search-input {
    font-size: 13px;
  }

  .btn-upload span {
    display: none;
  }

  .btn-upload {
    width: 40px;
    height: 40px;
    padding: 0;
    justify-content: center;
    border-radius: 50%;
  }

  .icon-button {
    width: 36px;
    height: 36px;
  }

  .dropdown-menu {
    width: 200px;
  }
}

@media (max-width: 480px) {
  .nav-center {
    margin: 0 8px;
  }

  .search-container {
    height: 36px;
  }

  .search-input {
    height: 36px;
    padding: 0 12px;
    font-size: 12px;
  }

  .search-button {
    width: 40px;
    height: 36px;
  }

  .btn-secondary {
    height: 32px;
    padding: 0 16px;
    font-size: 13px;
  }
}
</style>
