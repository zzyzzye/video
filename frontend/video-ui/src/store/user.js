import { defineStore } from 'pinia';
import { getToken, setToken, removeToken } from '@/utils/auth';

// 从localStorage加载用户信息
const loadUserFromStorage = () => {
  try {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      return JSON.parse(savedUser);
    }
  } catch (error) {
    console.error('Failed to load user from localStorage:', error);
  }
  return null;
};

// 保存用户信息到localStorage
const saveUserToStorage = (userData) => {
  try {
    localStorage.setItem('user', JSON.stringify(userData));
  } catch (error) {
    console.error('Failed to save user to localStorage:', error);
  }
};

// 从localStorage获取初始状态
const savedUser = loadUserFromStorage();

export const useUserStore = defineStore('user', {
  state: () => ({
    isLoggedIn: !!getToken(),
    userId: savedUser?.userId || null,
    username: savedUser?.username || '',
    email: savedUser?.email || '',
    avatar: savedUser?.avatar || '',
    role: savedUser?.role || 'user', // 默认为普通用户
    userInfo: savedUser?.userInfo || {},
  }),
  
  actions: {
    loginAction(userData) {
      if (!userData || !userData.id) {
        console.error('Invalid user data in loginAction:', userData);
        return false;
      }
      
      this.isLoggedIn = true;
      this.userId = userData.id;
      this.username = userData.username;
      this.email = userData.email || '';
      this.avatar = userData.avatar || '';
      this.role = userData.role || 'user';
      this.userInfo = userData;
      
      // 保存到localStorage
      saveUserToStorage({
        userId: this.userId,
        username: this.username,
        email: this.email,
        avatar: this.avatar,
        role: this.role,
        userInfo: this.userInfo
      });
      
      return true;
    },
    
    logoutAction() {
      this.isLoggedIn = false;
      this.userId = null;
      this.username = '';
      this.email = '';
      this.avatar = '';
      this.role = 'user';
      this.userInfo = {};
      // 清除token和localStorage
      removeToken();
      localStorage.removeItem('user');
    },
    
    // 退出登录
    logout() {
      this.logoutAction();
    },
    
    updateUserInfo(userInfo) {
      this.userInfo = { ...this.userInfo, ...userInfo };
      
      // 更新基本信息
      if (userInfo.username) this.username = userInfo.username;
      if (userInfo.email) this.email = userInfo.email;
      if (userInfo.avatar) this.avatar = userInfo.avatar;
      if (userInfo.role) this.role = userInfo.role;
      
      // 更新localStorage
      saveUserToStorage({
        userId: this.userId,
        username: this.username,
        email: this.email,
        avatar: this.avatar,
        role: this.role,
        userInfo: this.userInfo
      });
    },
    
    // 设置用户信息
    setUserInfo(userInfo) {
      this.updateUserInfo(userInfo);
    },
    
    // 设置用户头像
    setAvatar(avatarUrl) {
      this.avatar = avatarUrl;
      this.userInfo.avatar = avatarUrl;
      
      // 更新localStorage
      saveUserToStorage({
        userId: this.userId,
        username: this.username,
        email: this.email,
        avatar: this.avatar,
        role: this.role,
        userInfo: this.userInfo
      });
    }
  },
  
  getters: {
    isAdmin: (state) => {
      return state.role === 'admin' || state.role === 'superadmin';
    },
    isSuperAdmin: (state) => state.role === 'superadmin'
  }
}); 