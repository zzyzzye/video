import axios from 'axios';
import { getToken, getRefreshToken, setToken, removeToken } from '@/utils/auth';

// Create axios instance
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 15000
});

// Request interceptor
service.interceptors.request.use(
  config => {
    const token = getToken();
    
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Response interceptor
service.interceptors.response.use(
  response => {
    return response.data;
  },
  async error => {
    
    // 如果是401错误且没有重试过，尝试刷新token
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      
      try {
        const refreshToken = getRefreshToken();
        
        if (!refreshToken) {
          // 如果没有刷新令牌，跳转到登录页
          handleAuthError();
          return Promise.reject(error);
        }
        
        // 调用刷新令牌API
        const response = await axios.post(
          `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/token/refresh/`,
          { refresh: refreshToken }
        );
        
        const { access } = response.data;
        
        // 更新访问令牌
        setToken(access);
        
        // 使用新令牌重新发送原始请求
        error.config.headers['Authorization'] = `Bearer ${access}`;
        return axios(error.config);
      } catch (refreshError) {
        // 刷新失败，跳转到登录页
        handleAuthError();
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// 处理认证错误，跳转到登录页
function handleAuthError() {
  removeToken();
  // 避免重复跳转
  if (window.location.pathname !== '/auth' && window.location.pathname !== '/login') {
    window.location.href = '/auth?expired=1';
  }
}

// User login
export function login(data) {
  return service({
    url: '/auth/login/',
    method: 'post',
    data
  });
}

// User logout - 传递 refresh token 以加入黑名单
export function logout() {
  const refreshToken = getRefreshToken();
  return service({
    url: '/auth/logout/',
    method: 'post',
    data: { refresh: refreshToken }
  });
}

// Get user info
export function getUserInfo() {
  return service({
    url: '/users/me/',
    method: 'get'
  })
  .then(response => {
    if (!response || !response.id) {
      return Promise.reject(new Error('无效的用户信息响应'));
    }
    return response;
  })
  .catch(error => {
    console.error('获取用户信息失败:', error);
    return Promise.reject(error);
  });
}

// Get user info by ID
export function getUserById(userId) {
  return service({
    url: `/users/${userId}/`,
    method: 'get'
  })
  .then(response => {
    if (!response || !response.id) {
      return Promise.reject(new Error('无效的用户信息响应'));
    }
    return response;
  })
  .catch(error => {
    console.error('获取用户信息失败:', error);
    return Promise.reject(error);
  });
}

// Register user
export function register(data) {
  return service({
    url: '/auth/register/',
    method: 'post',
    data
  });
}

// Update user profile
export function updateUserProfile(data) {
  return service({
    url: '/users/update-profile/',
    method: 'put',
    data
  });
}

// Upload avatar
export function uploadAvatar(file) {
  const formData = new FormData();
  formData.append('avatar', file);
  
  return service({
    url: '/users/upload-avatar/',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  .then(response => {
    return response;
  })
  .catch(error => {
    console.error('Avatar upload error:', error);
    return Promise.reject(error);
  });
}

// Send verification code
export function sendVerificationCode(data) {
  return service({
    url: '/users/send-verification-code/',
    method: 'post',
    data
  });
}

// Verify email
export function verifyEmail(code) {
  return service({
    url: '/users/verify-email/',
    method: 'post',
    data: { code }
  });
}

// Change password with verification code
export function changePasswordWithCode(data) {
  return service({
    url: '/users/change-password-with-code/',
    method: 'post',
    data
  });
}

// Change email with verification code
export function changeEmailWithCode(data) {
  return service({
    url: '/users/change-email-with-code/',
    method: 'post',
    data
  });
}

// Change password (old way)
export function changePassword(data) {
  return service({
    url: '/users/change-password/',
    method: 'put',
    data
  });
}

// Send test email
export function sendTestEmail(email) {
  return service({
    url: '/users/test-email/',
    method: 'post',
    data: { email }
  });
}

// Get dashboard statistics
export function getDashboardStats() {
  return service({
    url: '/users/dashboard/stats/',
    method: 'get'
  });
}

// Get dashboard chart data
export function getDashboardChartData(days = 7) {
  return service({
    url: '/users/dashboard/chart-data/',
    method: 'get',
    params: { days }
  });
}

// 添加消息通知相关的API调用函数

/**
 * 获取消息通知列表
 * @param {Object} params 查询参数，包括type（消息类型，可选值：all, system, interaction, private）
 * @returns {Promise} 消息列表
 */
export function getNotifications(params) {
  return service({
    url: '/users/notifications/',
    method: 'get',
    params
  }).then(response => {
    // 确保返回的是数组
    return response?.results || response || [];
  }).catch(error => {
    console.error('获取消息通知失败:', error);
    return []; // 错误时返回空数组
  });
}

/**
 * 标记单个消息为已读
 * @param {Number} id 消息ID
 * @returns {Promise}
 */
export function markNotificationAsRead(id) {
  return service({
    url: `/users/notifications/${id}/mark_read/`,
    method: 'post'
  });
}

/**
 * 标记所有消息为已读
 * @returns {Promise}
 */
export function markAllNotificationsAsRead() {
  return service({
    url: '/users/notifications/mark_all_read/',
    method: 'post'
  });
}

/**
 * 删除单个消息
 * @param {Number} id 消息ID
 * @returns {Promise}
 */
export function deleteNotification(id) {
  return service({
    url: `/users/notifications/${id}/`,
    method: 'delete'
  });
}

/**
 * 清空所有消息
 * @returns {Promise}
 */
export function clearAllNotifications() {
  return service({
    url: '/users/notifications/clear_all/',
    method: 'delete'
  });
}

/**
 * 获取未读消息数量
 * @returns {Promise}
 */
export function getUnreadNotificationCount() {
  return service({
    url: '/users/notifications/unread_count/',
    method: 'get'
  });
}

/**
 * 获取通知设置
 * @returns {Promise}
 */
export function getNotificationSettings() {
  return service({
    url: '/users/notification-settings/',
    method: 'get'
  });
}

/**
 * 更新通知设置
 * @param {Object} data 通知设置数据
 * @returns {Promise}
 */
export function updateNotificationSettings(data) {
  return service({
    url: '/users/notification-settings/',
    method: 'put',
    data
  });
}

// Subscribe to user
export function subscribeUser(userId) {
  return service({
    url: `/users/${userId}/subscribe/`,
    method: 'post'
  })
  .then(response => {
    return response;
  })
  .catch(error => {
    console.error('订阅用户失败:', error);
    return Promise.reject(error);
  });
}

// Unsubscribe from user
export function unsubscribeUser(userId) {
  return service({
    url: `/users/${userId}/unsubscribe/`,
    method: 'post'
  })
  .then(response => {
    return response;
  })
  .catch(error => {
    console.error('取消订阅用户失败:', error);
    return Promise.reject(error);
  });
}

// Get user's videos
export function getUserVideos(userId, params = {}) {
  return service({
    url: `/videos/`,
    method: 'get',
    params: {
      uploader: userId,
      ...params
    }
  })
  .then(response => {
    return response;
  })
  .catch(error => {
    console.error('获取用户视频失败:', error);
    return Promise.reject(error);
  });
}

// Check subscription status
export function checkSubscriptionStatus(userId) {
  return service({
    url: `/users/${userId}/subscription_status/`,
    method: 'get'
  })
  .then(response => {
    return response;
  })
  .catch(error => {
    console.error('检查订阅状态失败:', error);
    return Promise.reject(error);
  });
}

export default service; 