<template>
  <div class="header">
    <div class="left-section">
      <router-link to="/" class="logo-container">
        <div class="logo-placeholder">MP</div>
      </router-link>
      <nav class="main-nav">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link to="/browse" class="nav-link">浏览</router-link>
        <el-dropdown trigger="hover" class="nav-dropdown">
          <span class="nav-link">
            分类 <i class="el-icon-arrow-down"></i>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>
                <router-link to="/category/1" class="dropdown-link">音乐</router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/category/2" class="dropdown-link">游戏</router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/category/3" class="dropdown-link">电影</router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/category/4" class="dropdown-link">教育</router-link>
              </el-dropdown-item>
              <el-dropdown-item>
                <router-link to="/category/5" class="dropdown-link">科技</router-link>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <router-link to="/my-videos" class="nav-link">我的视频</router-link>
        <router-link to="/history" class="nav-link">观看历史</router-link>
        <router-link to="/liked" class="nav-link">收藏</router-link>
        <router-link to="/watch-later" class="nav-link">稍后观看</router-link>
      </nav>
    </div>
    
    <div class="right-section">
      <div class="search-container">
        <el-button class="search-toggle" @click="showSearchInput = !showSearchInput">
          <el-icon><Search /></el-icon>
        </el-button>
        <div class="search-input-container" v-show="showSearchInput">
          <el-input
            v-model="searchQuery"
            placeholder="搜索视频..."
            class="search-input"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>
      
      <template v-if="userStore.isLoggedIn">
        <el-button class="new-video-btn" @click="goToUpload">
          新建
        </el-button>
        <el-dropdown trigger="click">
          <div class="avatar-container">
            <el-avatar :src="userStore.userInfo.avatar || defaultAvatar" />
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="goToUserProfile">
                个人主页
              </el-dropdown-item>
              <el-dropdown-item @click="goToDashboard">
                创作者仪表盘
              </el-dropdown-item>
              <el-dropdown-item @click="goToMyVideos">
                我的视频
              </el-dropdown-item>
              <el-dropdown-item @click="goToSettings">
                设置
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
      <template v-else>
        <div class="auth-buttons">
          <el-button class="login-btn" @click="goToLogin">登录</el-button>
          <el-button class="signup-btn" @click="goToRegister">注册</el-button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store/user';
import { Search } from '@element-plus/icons-vue';

const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';
const searchQuery = ref('');
const showSearchInput = ref(false);
const router = useRouter();
const userStore = useUserStore();

// 处理搜索
const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({
      path: '/search',
      query: { q: searchQuery.value }
    });
    showSearchInput.value = false;
  }
};

// 页面跳转函数
const goToUpload = () => {
  if (userStore.isLoggedIn) {
    router.push('/upload');
  } else {
    router.push('/login?redirect=/upload');
  }
};

const goToLogin = () => router.push('/auth');
const goToRegister = () => router.push('/auth?mode=register');
const goToUserProfile = () => {
  if (userStore.userId) {
    router.push(`/user/${userStore.userId}`);
  } else {
    router.push('/user/center');
  }
};
const goToMyVideos = () => router.push('/my-videos');
const goToSettings = () => router.push('/user/account');
const goToDashboard = () => router.push('/user/dashboard');

// 处理登出
const handleLogout = async () => {
  try {
    await userStore.logoutAction();
    router.push('/');
  } catch (error) {
    console.error('Logout failed:', error);
  }
};
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  background-color: var(--header-bg);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  width: 100%;
  max-width: 100vw;
  box-sizing: border-box;
  overflow-x: hidden;
}

.left-section {
  display: flex;
  align-items: center;
  overflow-x: auto;
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}

.left-section::-webkit-scrollbar {
  display: none;
}

.logo-container {
  margin-right: 24px;
  text-decoration: none;
  flex-shrink: 0;
}

.logo-placeholder {
  width: 32px;
  height: 32px;
  background-color: var(--accent-color);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  border-radius: 4px;
}

.main-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-link {
  color: var(--text-color);
  text-decoration: none;
  padding: 0 12px;
  font-size: 14px;
  font-weight: 500;
  height: 56px;
  display: flex;
  align-items: center;
  transition: color 0.2s;
  white-space: nowrap;
}

.nav-link:hover {
  color: var(--accent-color);
}

.nav-dropdown {
  height: 56px;
  display: flex;
  align-items: center;
}

.dropdown-link {
  color: var(--text-color);
  text-decoration: none;
  display: block;
  width: 100%;
}

.right-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.search-container {
  position: relative;
}

.search-toggle {
  background: transparent;
  border: none;
  color: var(--text-color);
  padding: 8px;
}

.search-input-container {
  position: absolute;
  right: 0;
  top: 100%;
  width: 280px;
  padding-top: 8px;
}

.search-input :deep(.el-input__wrapper) {
  background-color: var(--input-bg);
  border: none;
  box-shadow: none;
  border-radius: 4px;
}

.search-input :deep(.el-input__inner) {
  color: var(--text-color);
  height: 36px;
}

.search-input :deep(.el-input__prefix) {
  color: var(--text-color-tertiary);
}

.new-video-btn {
  background-color: var(--accent-color);
  color: #ffffff;
  border: none;
  border-radius: 4px;
  padding: 0 16px;
  height: 36px;
  font-weight: 500;
}

.new-video-btn:hover {
  background-color: var(--accent-color-hover);
}

.avatar-container {
  cursor: pointer;
}

.auth-buttons {
  display: flex;
  gap: 8px;
}

.login-btn {
  background: transparent;
  border: 1px solid var(--text-color);
  color: var(--text-color);
  border-radius: 4px;
  padding: 0 16px;
  height: 36px;
}

.login-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.signup-btn {
  background-color: var(--accent-color);
  color: #ffffff;
  border: none;
  border-radius: 4px;
  padding: 0 16px;
  height: 36px;
  font-weight: 500;
}

.signup-btn:hover {
  background-color: var(--accent-color-hover);
}

:deep(.el-dropdown-menu) {
  background-color: var(--dropdown-bg);
  border: none;
  border-radius: 4px;
  padding: 8px 0;
}

:deep(.el-dropdown-menu__item) {
  color: var(--text-color);
  font-size: 14px;
}

:deep(.el-dropdown-menu__item:hover) {
  background-color: var(--dropdown-hover);
}

:deep(.el-dropdown-menu__item.is-divided:before) {
  background-color: var(--divider-color);
}

@media (max-width: 992px) {
  .nav-link {
    padding: 0 8px;
    font-size: 13px;
  }
}

@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }
  
  .main-nav {
    gap: 0;
  }
  
  .search-input-container {
    width: 200px;
  }
}

@media (max-width: 480px) {
  .header {
    padding: 0 12px;
  }
  
  .auth-buttons .login-btn {
    display: none;
  }
  
  .search-input-container {
    width: 160px;
  }
}
</style> 