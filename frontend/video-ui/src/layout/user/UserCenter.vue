<template>
  <!-- SIDEBAR -->
  <user-sidebar :role="userRole" :is-collapsed="isSidebarCollapsed" />
  
  <!-- 移动设备上的背景遮罩 -->
  <div 
    class="sidebar-overlay" 
    v-if="!isSidebarCollapsed && isMobile" 
    @click="toggleSidebar"
  ></div>
  
  <!-- CONTENT -->
  <section id="content" :class="{ 'sidebar-hide': isSidebarCollapsed }">
    <!-- NAVBAR -->
    <nav>
      <el-icon class="bx bx-menu" @click="toggleSidebar"><Fold /></el-icon>
      
      <!-- 右侧用户信息和通知 -->
      <div class="nav-right">
        <!-- 投稿按钮 -->
        <a href="#" class="upload-btn" @click.prevent="goToCreator">
          <el-icon><Upload /></el-icon>
          <span>投稿</span>
        </a>
        
        <!-- Notification Bell -->
        <a href="#" class="notification" @click.prevent="toggleNotificationMenu">
          <el-icon class="bx"><Bell /></el-icon>
          <span class="num" v-if="unreadNotifications > 0">{{ unreadNotifications > 99 ? '99+' : unreadNotifications }}</span>
        </a>
        <div class="notification-menu" :class="{ 'show': showNotificationMenu }">
          <h4>通知消息 <span v-if="unreadNotifications > 0" class="unread-count">{{ unreadNotifications }} 条未读</span></h4>
          <ul v-if="recentNotifications.length > 0">
            <li v-for="notification in recentNotifications" :key="notification.id" :class="{ 'unread': !notification.read }">
              <a href="#" @click.prevent="handleNotificationClick(notification)">
                <el-icon><Bell /></el-icon>
                <div class="notification-content">
                  <span class="notification-title">{{ notification.title }}</span>
                  <span class="notification-time">{{ formatNotificationTime(notification.created_at) }}</span>
                </div>
              </a>
            </li>
          </ul>
          <div class="notification-empty" v-else>
            <span>暂无消息</span>
          </div>
          <div class="notification-footer">
            <a href="#" @click.prevent="navigateTo('/user/message')">查看全部消息</a>
          </div>
        </div>
        
        <!-- Profile Menu -->
        <a href="#" class="profile" @click.prevent="toggleProfileMenu">
          <img :src="userAvatar || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'" alt="Profile">
        </a>
        <div class="profile-menu" :class="{ 'show': showProfileMenu }">
          <h4>用户选项</h4>
          <ul>
            <li>
              <a href="#" @click.prevent="navigateTo('/user/profile')">
                <el-icon><User /></el-icon>
                <span>个人中心</span>
              </a>
            </li>
            <li>
              <a href="#" @click.prevent="navigateTo('/user/settings')">
                <el-icon><Setting /></el-icon>
                <span>设置</span>
              </a>
            </li>
            <li>
              <a href="#" @click.prevent="logout">
                <el-icon><SwitchButton /></el-icon>
                <span>退出登录</span>
              </a>
            </li>
          </ul>
        </div>
      </div>
    </nav>
    <!-- NAVBAR -->
    
    <!-- MAIN -->
    <main>
      <router-view v-slot="{ Component }">
        <component 
          :is="Component" 
          :key="route.fullPath + new Date().getTime()" 
        />
      </router-view>
    </main>
    <!-- MAIN -->
  </section>
  <!-- CONTENT -->
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '@/store/user';
import { useNotificationStore } from '@/store/notification';
import UserSidebar from '@/layout/user/UserSidebar.vue';
import { 
  Refresh, FullScreen, Fold, Expand, 
  Search, Bell, User, Setting, SwitchButton, Upload
} from '@element-plus/icons-vue';

const userStore = useUserStore();
const notificationStore = useNotificationStore();
const router = useRouter();
const route = useRoute();

// 移动设备检测
const isMobile = ref(window.innerWidth <= 768);
const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768;
};

// 侧边栏状态
const SIDEBAR_STATE_KEY = 'userSidebarCollapsed';
const isSidebarCollapsed = ref(localStorage.getItem(SIDEBAR_STATE_KEY) === 'true');

const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
  localStorage.setItem(SIDEBAR_STATE_KEY, isSidebarCollapsed.value);
};

// 监听侧边栏状态变化，保存到localStorage
watch(isSidebarCollapsed, (newValue) => {
  localStorage.setItem(SIDEBAR_STATE_KEY, newValue);
});

// 通知菜单 - 使用 store
const unreadNotifications = computed(() => notificationStore.unreadCount);
const recentNotifications = computed(() => notificationStore.recentNotifications);
const showNotificationMenu = ref(false);
const toggleNotificationMenu = () => {
  showNotificationMenu.value = !showNotificationMenu.value;
  showProfileMenu.value = false; // 关闭个人菜单
  if (showNotificationMenu.value) {
    notificationStore.fetchRecentNotifications();
  }
};

// 格式化通知时间
const formatNotificationTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60 * 1000) return '刚刚'
  if (diff < 60 * 60 * 1000) return Math.floor(diff / (60 * 1000)) + '分钟前'
  if (diff < 24 * 60 * 60 * 1000) return Math.floor(diff / (60 * 60 * 1000)) + '小时前'
  return Math.floor(diff / (24 * 60 * 60 * 1000)) + '天前'
}

// 处理通知点击
const handleNotificationClick = async (notification) => {
  if (!notification.read) {
    await notificationStore.markAsRead(notification.id)
  }
  showNotificationMenu.value = false
  if (notification.source_type === 'video' && notification.source_id) {
    router.push(`/video/${notification.source_id}`)
  } else {
    router.push('/user/message')
  }
}

// 个人菜单
const showProfileMenu = ref(false);
const toggleProfileMenu = () => {
  showProfileMenu.value = !showProfileMenu.value;
  showNotificationMenu.value = false; // 关闭通知菜单
};

// 点击外部关闭菜单
const handleClickOutside = (event) => {
  if (!event.target.closest('.notification') && !event.target.closest('.notification-menu')) {
    showNotificationMenu.value = false;
  }
  if (!event.target.closest('.profile') && !event.target.closest('.profile-menu')) {
    showProfileMenu.value = false;
  }
};

// 导航函数
const navigateTo = (path) => {
  // 使用 router.push 并添加时间戳查询参数，强制刷新组件
  if (route.path !== path) {
    router.push({ path, query: { _t: Date.now() } }).catch(err => {
      if (err.name !== 'NavigationDuplicated') {
        console.error(err);
      }
    });
  }
  showProfileMenu.value = false;
};

// 跳转到创作者中心
const goToCreator = () => {
  router.push('/user/dashboard/create');
};

// 退出登录
const logout = () => {
  notificationStore.reset();
  userStore.logout();
  router.push('/login');
};

// 获取用户角色和头像
const userRole = computed(() => userStore.role || 'user');
const userAvatar = computed(() => userStore.avatar || '');

// 组件挂载处理
const handleComponentMounted = () => {
  // Component mounted
};

// 响应式调整侧边栏函数
const adjustSidebar = () => {
  if (window.innerWidth <= 576) {
    isSidebarCollapsed.value = true;
    localStorage.setItem(SIDEBAR_STATE_KEY, 'true');
  } else {
    // 如果屏幕变宽，仅在没有用户明确设置时恢复默认状态
    const savedState = localStorage.getItem(SIDEBAR_STATE_KEY);
    if (savedState === null) {
      isSidebarCollapsed.value = false;
    }
  }
};

onMounted(() => {
  // 添加点击外部关闭菜单的事件监听
  window.addEventListener('click', handleClickOutside);
  
  // 初始化时调整侧边栏
  adjustSidebar();
  
  // 添加移动设备检测
  checkMobile();
  window.addEventListener('resize', checkMobile);
  window.addEventListener('resize', adjustSidebar);
});

onUnmounted(() => {
  window.removeEventListener('click', handleClickOutside);
  window.removeEventListener('resize', adjustSidebar);
  window.removeEventListener('resize', checkMobile);
});

</script>

<style>
/* 全局变量 */
:root {
  --light: #F9F9F9;
  --blue: #3C91E6;
  --light-blue: #CFE8FF;
  --grey: #eee;
  --dark-grey: #AAAAAA;
  --dark: #342E37;
  --red: #DB504A;
  --yellow: #FFCE26;
  --light-yellow: #FFF2C6;
  --orange: #FD7238;
  --light-orange: #FFE0D3;
}

html, body {
  margin: 0;
  padding: 0;
  overflow: hidden;
  height: 100%;
  width: 100%;
}

body {
  background: var(--grey);
  font-family: 'Lato', sans-serif;
}
</style>

<style scoped>
/* CONTENT */
#content {
  position: relative;
  width: calc(100% - 250px);
  left: 250px;
  transition: .3s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

#content.sidebar-hide {
  width: calc(100% - 64px);
  left: 64px;
}

/* NAVBAR */
nav {
  height: 70px;
  background: var(--light);
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  left: 0;
  z-index: 1000;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

nav .bx.bx-menu {
  cursor: pointer;
  font-size: 24px;
  color: var(--dark);
}

nav .nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

nav .nav-right .upload-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

nav .nav-right .upload-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

nav .nav-right .upload-btn .el-icon {
  font-size: 16px;
}

nav .nav-right .notification {
  position: relative;
  cursor: pointer;
}

nav .nav-right .notification .bx {
  font-size: 24px;
  color: var(--dark);
}

/* Dropdown menus */
nav .notification-menu, 
nav .profile-menu {
  position: absolute;
  top: 110%;
  right: 0;
  background: var(--light);
  width: 240px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  padding: 0;
  transform: scale(0);
  transform-origin: top right;
  transition: transform .3s ease;
  z-index: 2000;
  overflow: hidden;
}

nav .notification-menu.show, 
nav .profile-menu.show {
  transform: scale(1);
}

nav .notification-menu h4, 
nav .profile-menu h4 {
  margin: 0;
  padding: 12px 15px;
  background-color: #f5f9ff;
  color: #2196f3;
  font-size: 15px;
  font-weight: 500;
  border-bottom: 1px solid rgba(33, 150, 243, 0.1);
}

nav .notification-menu ul, 
nav .profile-menu ul {
  width: 100%;
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 300px;
  overflow-y: auto;
}

nav .notification-menu ul li, 
nav .profile-menu ul li {
  padding: 0;
  margin: 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

nav .notification-menu ul li:last-child, 
nav .profile-menu ul li:last-child {
  border-bottom: none;
}

nav .notification-menu ul li a, 
nav .profile-menu ul li a {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  color: var(--dark);
  text-decoration: none;
  transition: all 0.2s ease;
}

nav .notification-menu ul li a:hover, 
nav .profile-menu ul li a:hover {
  background-color: rgba(33, 150, 243, 0.05);
  color: #2196f3;
}

nav .notification-menu ul li a .el-icon, 
nav .profile-menu ul li a .el-icon {
  margin-right: 10px;
  font-size: 18px;
  color: #2196f3;
  opacity: 0.8;
}

nav .notification-menu ul li a:hover .el-icon, 
nav .profile-menu ul li a:hover .el-icon {
  opacity: 1;
}

nav .notification-menu ul li a span, 
nav .profile-menu ul li a span {
  flex: 1;
}

/* 通知内容样式 */
nav .notification-menu ul li.unread {
  background-color: rgba(33, 150, 243, 0.08);
}

nav .notification-menu ul li a .notification-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

nav .notification-menu ul li a .notification-title {
  font-size: 13px;
  color: var(--dark);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

nav .notification-menu ul li a .notification-time {
  font-size: 11px;
  color: var(--dark-grey);
}

nav .notification-menu h4 .unread-count {
  font-size: 12px;
  color: #fff;
  background: var(--red);
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 8px;
  font-weight: 500;
}

nav .notification-menu .notification-empty {
  padding: 30px 15px;
  text-align: center;
  color: var(--dark-grey);
  font-size: 13px;
}

nav .notification-menu .notification-footer {
  padding: 10px 15px;
  text-align: center;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  background: #f9f9f9;
}

nav .notification-menu .notification-footer a {
  color: #2196f3;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
}

nav .notification-menu .notification-footer a:hover {
  text-decoration: underline;
}

/* 通知图标的数字指示器 */
nav .nav-right .notification .num {
  position: absolute;
  top: -5px;
  right: -5px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--red);
  color: white;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

nav .nav-right .profile {
  position: relative;
  cursor: pointer;
}

nav .nav-right .profile img {
  width: 36px;
  height: 36px;
  object-fit: cover;
  border-radius: 50%;
}

/* MAIN */
main {
  flex: 1;
  padding: 0;
  overflow-y: auto;
  overflow-x: hidden; /* 防止横向滚动 */
}

/* 修改滚动条样式 */
main::-webkit-scrollbar {
  width: 8px;
}

main::-webkit-scrollbar-track {
  background: transparent;
}

main::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

main::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}

/* 侧边栏遮罩层 */
.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.4);
  z-index: 1500;
  display: block;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media screen and (max-width: 992px) {
  #content {
    width: calc(100% - 64px);
    left: 64px;
  }
  
  #content.sidebar-hide {
    width: 100%;
    left: 0;
  }
}

@media screen and (max-width: 768px) {
  #content {
    width: 100%;
    left: 0;
  }
  
  nav {
    padding: 0 16px;
  }
  
  nav .nav-right {
    gap: 8px;
  }
  
  nav .nav-right .upload-btn span {
    display: none;
  }
  
  nav .nav-right .upload-btn {
    padding: 8px 12px;
  }
  
  nav .nav-right .profile img {
    width: 32px;
    height: 32px;
  }
  
  main {
    padding: 16px;
  }
}
</style> 