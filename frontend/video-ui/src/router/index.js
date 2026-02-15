import { createRouter, createWebHistory } from 'vue-router';
import { getToken } from '@/utils/auth';
import { getUserInfo } from '@/api/user';
import NProgress from 'nprogress';
import 'nprogress/nprogress.css';

NProgress.configure({ showSpinner: false });

// 路由配置
const routes = [
  {
    path: '/',
    redirect: '/home',
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/home/index.vue'),
        meta: { title: '首页', icon: 'home' }
      },
      {
        path: 'video/:id',
        name: 'VideoDetail',
        component: () => import('@/views/video/detail-refactored.vue'),
        meta: { title: '视频详情', icon: 'video-play' }
      },
      {
        path: 'search',
        name: 'Search',
        component: () => import('@/views/search/index.vue'),
        meta: { title: '搜索结果', icon: 'search' }
      },
    ]
  },
  {
    path: '/user/dashboard/create',
    name: 'UserCenterCreate',
    component: () => import('@/views/dashboard/CreateCenter.vue'),
    meta: { requiresAuth: true, title: '创作中心', icon: 'upload' }
  },
  {
    path: '/creator/editor',
    name: 'VideoEditor',
    component: () => import('@/views/creator/VideoEditor.vue'),
    meta: { requiresAuth: true, title: '视频编辑器' }
  },
  {
    path: '/creator/subtitle',
    name: 'SubtitleEditor',
    component: () => import('@/views/creator/SubtitleEditor.vue'),
    meta: { requiresAuth: true, title: '字幕编辑器' }
  },
  // 用户中心路由
  {
    path: '/user',
    component: () => import('@/layout/user/UserCenter.vue'),
    redirect: '/user/profile',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'UserCenterDashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '工作台', icon: 'data-analysis' }
      },
      {
        path: 'profile',
        name: 'UserCenterProfile',
        component: () => import('@/views/user/ProfileView.vue'),
        meta: { title: '个人资料', icon: 'user' }
      },
      {
        path: 'account',
        name: 'UserCenterAccount',
        component: () => import('@/views/user/AccountView.vue'),
        meta: { title: '账号安全', icon: 'lock' }
      },
      {
        path: 'message',
        name: 'UserCenterMessage',
        component: () => import('@/views/user/MessageView.vue'),
        meta: { title: '消息通知', icon: 'message' }
      },
      {
        path: 'settings',
        name: 'UserCenterSettings',
        component: () => import('@/views/user/SettingsView.vue'),
        meta: { title: '系统设置', icon: 'setting' }
      },
      {
        path: 'videos/uploaded',
        name: 'UploadedVideos',
        component: () => import('@/views/user/videos/UploadedVideos.vue'),
        meta: { title: '已上传视频', icon: 'video-play' }
      },
      {
        path: 'videos/edit/:id',
        name: 'EditVideo',
        component: () => import('@/views/user/videos/EditVideo.vue'),
        meta: { title: '编辑视频', icon: 'edit' }
      },
      {
        path: 'videos/collection',
        name: 'CollectionVideos',
        component: () => import('@/views/user/videos/CollectionVideos.vue'),
        meta: { title: '收藏视频', icon: 'star' }
      },
      {
        path: 'videos/history',
        name: 'HistoryVideos',
        component: () => import('@/views/user/videos/HistoryVideos.vue'),
        meta: { title: '观看历史', icon: 'time' }
      },
      {
        path: 'videos/recycle-bin',
        name: 'RecycleBin',
        component: () => import('@/views/user/RecycleBin.vue'),
        meta: { title: '回收站', icon: 'delete' }
      }
    ]
  },
  // 管理员路由
  {
    path: '/admin',
    component: () => import('@/layout/user/UserCenter.vue'),
    redirect: '/admin/videos/review',
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: 'videos/review',
        name: 'AdminReviewVideos',
        component: () => import('@/views/admin/videos/ReviewVideos.vue'),
        meta: { title: '视频审核', icon: 'document' }
      },
      {
        path: 'ai/moderation',
        name: 'AdminAIModeration',
        component: () => import('@/views/admin/ai/AIModeration.vue'),
        meta: { title: 'AI 审核', icon: 'cpu' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/users/UserManagement.vue'),
        meta: { title: '用户管理', icon: 'user' }
      },
      {
        path: 'reports',
        name: 'AdminReports',
        component: () => import('@/views/admin/ReportManagement.vue'),
        meta: { title: '举报处理', icon: 'warning' }
      },
      {
        path: 'statistics',
        name: 'AdminStatistics',
        component: () => import('@/views/admin/StatisticsView.vue'),
        meta: { title: '数据统计', icon: 'data-line' }
      }
    ]
  },
  // 超级管理员路由
  {
    path: '/superadmin',
    component: () => import('@/layout/user/UserCenter.vue'),
    redirect: '/superadmin/monitor',
    meta: { requiresAuth: true, requiresSuperAdmin: true },
    children: [
      {
        path: 'monitor',
        name: 'SuperAdminMonitor',
        component: () => import('@/views/superadmin/SystemMonitor.vue'),
        meta: { title: '系统监控', icon: 'monitor' }
      },
      {
        path: 'system',
        name: 'SuperAdminSystem',
        component: () => import('@/views/superadmin/SystemSettings.vue'),
        meta: { title: '系统配置', icon: 'setting' }
      },
      {
        path: 'admins',
        name: 'SuperAdminAdmins',
        component: () => import('@/views/superadmin/AdminManagement.vue'),
        meta: { title: '管理员管理', icon: 'user' }
      }
    ]
  },
  {
    path: '/auth',
    name: 'Auth',
    component: () => import('@/components/user/AuthForm.vue'),
    meta: { title: '登录/注册' }
  },
  {
    path: '/login',
    redirect: '/auth'
  },
  {
    path: '/register',
    redirect: '/auth?mode=register'
  },
  // 用户详情页面
  {
    path: '/user/:id',
    name: 'UserDetail',
    component: () => import('@/views/user/UserDetail.vue'),
    meta: { title: '用户详情' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: { title: '页面不存在' }
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 };
  }
});

// 路由守卫
router.beforeEach(async (to, from, next) => {
  NProgress.start();
  
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - MindPalette` : 'MindPalette';
  
  // 检查是否需要登录权限
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin);
  const requiresSuperAdmin = to.matched.some(record => record.meta.requiresSuperAdmin);
  
  if (requiresAuth || requiresAdmin || requiresSuperAdmin) {
    const hasToken = getToken();
    
    if (hasToken) {
      // 如果需要超级管理员权限
      if (requiresSuperAdmin) {
        try {
          const userInfo = await getUserInfo();
          
          if (userInfo && userInfo.role) {
            localStorage.setItem('user_role', userInfo.role);
          }
          
          const storedRole = localStorage.getItem('user_role');
          const isSuperAdmin = storedRole === 'superadmin';
          
          if (isSuperAdmin) {
            next();
          } else {
            next('/user/dashboard');
          }
        } catch (error) {
          console.error('Failed to check super admin status:', error);
          next('/user/dashboard');
        }
      }
      // 如果需要管理员权限，则检查用户角色
      else if (requiresAdmin) {
        try {
          // 尝试获取最新的用户信息
          const userInfo = await getUserInfo();
          
          // 存储角色到localStorage
          if (userInfo && userInfo.role) {
            localStorage.setItem('user_role', userInfo.role);
          }
          
          const storedRole = localStorage.getItem('user_role');
          const isAdmin = storedRole === 'admin' || storedRole === 'superadmin';
          
          if (isAdmin) {
            next();
          } else {
            next('/user/dashboard'); // 普通用户重定向到用户仪表盘
          }
        } catch (error) {
          console.error('Failed to check admin status:', error);
          // 出错时，假设不是管理员
          next('/user/dashboard');
        }
      } else {
        next();
      }
    } else {
      next({
        path: '/auth',
        query: { redirect: to.fullPath }
      });
    }
  } else {
    next();
  }
});

router.afterEach(() => {
  NProgress.done();
});

export default router; 
