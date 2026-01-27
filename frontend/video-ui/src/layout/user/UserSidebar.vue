<template>
  <section id="sidebar" :class="{ 'hide': isCollapsed }">
    <a href="#" class="brand">
      <el-icon class="bx"><Avatar /></el-icon>
      <span class="text">MindPalette</span>
    </a>
    <ul class="side-menu top">
      <!-- 创作者仪表盘分组 -->
      <li class="menu-group">
        <a href="#" class="group-title" @click.prevent="toggleGroup('dashboard')" :data-title="isCollapsed ? '创作者仪表盘' : ''">
          <el-icon class="bx"><Histogram /></el-icon>
          <span class="text">创作者仪表盘</span>
          <span class="arrow" :class="{ 'expanded': expandedGroups.dashboard }">
            <el-icon><ArrowDown /></el-icon>
          </span>
        </a>
        <ul class="submenu" :class="{ 'expanded': expandedGroups.dashboard }">
          <li :class="{ active: activeMenu === '/user/dashboard' }">
            <a href="#" @click.prevent="navigateTo('/user/dashboard')" data-title="工作台">
              <el-icon class="bx"><DataLine /></el-icon>
              <span class="text">工作台</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/user/dashboard/create' }">
            <a href="#" @click.prevent="navigateTo('/user/dashboard/create')" data-title="创作中心">
              <el-icon class="bx"><VideoCamera /></el-icon>
              <span class="text">创作中心</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/creator/subtitle' }" class="vip-item">
            <a href="#" @click.prevent="navigateTo('/creator/subtitle')" data-title="智能字幕工坊">
              <span class="vip-badge">VIP</span>
              <!-- <el-icon class="bx"><EditPen /></el-icon> -->
              <span class="text">智能字幕工坊</span>
            </a>
          </li>
        </ul>
      </li>
      
      <!-- 个人中心分组 -->
      <li class="menu-group">
        <a href="#" class="group-title" @click.prevent="toggleGroup('personal')" :data-title="isCollapsed ? '个人中心' : ''">
          <el-icon class="bx"><User /></el-icon>
          <span class="text">个人中心</span>
          <span v-if="unreadMessages > 0 && !expandedGroups.personal" class="group-badge">{{ unreadMessages }}</span>
          <span class="arrow" :class="{ 'expanded': expandedGroups.personal }">
            <el-icon><ArrowDown /></el-icon>
          </span>
        </a>
        <ul class="submenu" :class="{ 'expanded': expandedGroups.personal }">
          <li :class="{ active: activeMenu === '/user/profile' }">
            <a href="#" @click.prevent="navigateTo('/user/profile')" data-title="个人资料">
              <el-icon class="bx"><Avatar /></el-icon>
              <span class="text">个人资料</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/user/account' }">
            <a href="#" @click.prevent="navigateTo('/user/account')" data-title="账号安全">
              <el-icon class="bx"><Lock /></el-icon>
              <span class="text">账号安全</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/user/message' }">
            <a href="#" @click.prevent="navigateTo('/user/message')" data-title="消息通知">
              <el-icon class="bx"><Bell /></el-icon>
              <span class="text">消息通知</span>
              <span v-if="unreadMessages > 0" class="num">{{ unreadMessages }}</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/user/settings' }">
            <a href="#" @click.prevent="navigateTo('/user/settings')" data-title="设置">
              <el-icon class="bx"><Setting /></el-icon>
              <span class="text">系统设置</span>
            </a>
          </li>
        </ul>
      </li>
      
      <!-- 视频管理分组 -->
      <li class="menu-group">
        <a href="#" class="group-title" @click.prevent="toggleGroup('videos')" :data-title="isCollapsed ? '视频管理' : ''">
          <el-icon class="bx"><FolderOpened /></el-icon>
          <span class="text">视频管理</span>
          <span class="arrow" :class="{ 'expanded': expandedGroups.videos }">
            <el-icon><ArrowDown /></el-icon>
          </span>
        </a>
        <ul class="submenu" :class="{ 'expanded': expandedGroups.videos }">
          <li :class="{ active: activeMenu === '/user/videos/uploaded' }">
            <a href="#" @click.prevent="navigateTo('/user/videos/uploaded')" data-title="已上传视频">
              <el-icon class="bx"><VideoPlay /></el-icon>
              <span class="text">已上传视频</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/user/videos/collection' }">
            <a href="#" @click.prevent="navigateTo('/user/videos/collection')" data-title="收藏视频">
              <el-icon class="bx"><Star /></el-icon>
              <span class="text">收藏视频</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/user/videos/history' }">
            <a href="#" @click.prevent="navigateTo('/user/videos/history')" data-title="观看历史">
              <el-icon class="bx"><Clock /></el-icon>
              <span class="text">观看历史</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/user/videos/recycle-bin' }">
            <a href="#" @click.prevent="navigateTo('/user/videos/recycle-bin')" data-title="回收站">
              <el-icon class="bx"><Delete /></el-icon>
              <span class="text">回收站</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/user/comments' }">
            <a href="#" @click.prevent="navigateTo('/user/comments')" data-title="我的评论">
              <el-icon class="bx"><ChatDotRound /></el-icon>
              <span class="text">我的评论</span>
            </a>
          </li>
        </ul>
      </li>
      
      <!-- 管理后台分组 (仅管理员可见) -->
      <li v-if="isAdmin" class="menu-group admin-group">
        <a href="#" class="group-title" @click.prevent="toggleGroup('admin')" :data-title="isCollapsed ? '管理后台' : ''">
          <span class="admin-badge">ADMIN</span>
          <el-icon class="bx"><Management /></el-icon>
          <span class="text">管理员后台</span>
          <span class="arrow" :class="{ 'expanded': expandedGroups.admin }">
            <el-icon><ArrowDown /></el-icon>
          </span>
        </a>
        <ul class="submenu" :class="{ 'expanded': expandedGroups.admin }">
          <li :class="{ active: activeMenu === '/admin/videos/review' }" class="admin-item">
            <a href="#" @click.prevent="navigateTo('/admin/videos/review')" data-title="视频审核">
              <el-icon class="bx"><View /></el-icon>
              <span class="text">视频审核</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/admin/ai/moderation' }" class="admin-item">
            <a href="#" @click.prevent="navigateTo('/admin/ai/moderation')" data-title="AI 审核">
              <el-icon class="bx"><Cpu /></el-icon>
              <span class="text">AI 审核</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/admin/users' }" class="admin-item">
            <a href="#" @click.prevent="navigateTo('/admin/users')" data-title="用户管理">
              <el-icon class="bx"><UserFilled /></el-icon>
              <span class="text">用户管理</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/admin/reports' }" class="admin-item">
            <a href="#" @click.prevent="navigateTo('/admin/reports')" data-title="举报处理">
              <el-icon class="bx"><Warning /></el-icon>
              <span class="text">举报处理</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/admin/statistics' }" class="admin-item">
            <a href="#" @click.prevent="navigateTo('/admin/statistics')" data-title="数据统计">
              <el-icon class="bx"><Histogram /></el-icon>
              <span class="text">数据统计</span>
            </a>
          </li>
        </ul>
      </li>
      
      <!-- 超级管理员分组 (仅超级管理员可见) -->
      <li v-if="isSuperAdmin" class="menu-group super-admin-group">
        <a href="#" class="group-title" @click.prevent="toggleGroup('superadmin')" :data-title="isCollapsed ? '超级管理员' : ''">
          <span class="super-admin-badge">SUPER</span>
          <el-icon class="bx"><Key /></el-icon>
          <span class="text">超级管理员</span>
          <span class="arrow" :class="{ 'expanded': expandedGroups.superadmin }">
            <el-icon><ArrowDown /></el-icon>
          </span>
        </a>
        <ul class="submenu" :class="{ 'expanded': expandedGroups.superadmin }">
          <li :class="{ active: activeMenu === '/superadmin/system' }" class="super-admin-item">
            <a href="#" @click.prevent="navigateTo('/superadmin/system')" data-title="系统配置">
              <el-icon class="bx"><Tools /></el-icon>
              <span class="text">系统配置</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/superadmin/admins' }" class="super-admin-item">
            <a href="#" @click.prevent="navigateTo('/superadmin/admins')" data-title="管理员管理">
              <el-icon class="bx"><Avatar /></el-icon>
              <span class="text">管理员管理</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/superadmin/permissions' }" class="super-admin-item">
            <a href="#" @click.prevent="navigateTo('/superadmin/permissions')" data-title="权限管理">
              <el-icon class="bx"><Lock /></el-icon>
              <span class="text">权限管理</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/superadmin/logs' }" class="super-admin-item">
            <a href="#" @click.prevent="navigateTo('/superadmin/logs')" data-title="系统日志">
              <el-icon class="bx"><Document /></el-icon>
              <span class="text">系统日志</span>
            </a>
          </li>
          <li :class="{ active: activeMenu === '/superadmin/database' }" class="super-admin-item">
            <a href="#" @click.prevent="navigateTo('/superadmin/database')" data-title="数据库管理">
              <el-icon class="bx"><Coin /></el-icon>
              <span class="text">数据库管理</span>
            </a>
          </li>
        </ul>
      </li>
    </ul>
    
    <div class="spacer"></div>
    
    <ul class="side-menu bottom">
      <li>
        <a href="#" class="logout" @click.prevent="logout" data-title="退出登录">
          <el-icon class="bx"><SwitchButton /></el-icon>
          <span class="text">退出登录</span>
        </a>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { computed, ref, onMounted, watch, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '@/store/user';
import { useNotificationStore } from '@/store/notification';
import { 
  User, Lock, Message, Star, Timer, 
  ChatDotRound, VideoPlay, Warning,
  Avatar, Setting, Document, Monitor, SwitchButton,
  ArrowDown, UserFilled, DataLine, Delete, Upload, Cpu,
  Histogram, FolderOpened, Clock, Bell, 
  VideoCamera, Collection, View, Management, Key, Tools, Coin, EditPen
} from '@element-plus/icons-vue';
import { useEventBus } from '@/utils/eventBus';

const props = defineProps({
  role: {
    type: String,
    default: 'user',
    validator: (value) => ['user', 'admin', 'super_admin'].includes(value)
  },
  isCollapsed: {
    type: Boolean,
    default: false
  }
});

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const notificationStore = useNotificationStore();
const eventBus = useEventBus();

const activeMenu = computed(() => route.path);
const unreadMessages = computed(() => notificationStore.unreadCount);

// 分组展开状态
const expandedGroups = ref({
  dashboard: true,
  personal: true,
  videos: true,
  admin: true,
  superadmin: true
});

const toggleGroup = (group) => {
  if (!props.isCollapsed) {
    expandedGroups.value[group] = !expandedGroups.value[group];
  }
};

// 根据当前路由自动展开对应分组
watch(() => route.path, (path) => {
  if (path.startsWith('/user/dashboard')) {
    expandedGroups.value.dashboard = true;
  } else if (path.startsWith('/user/profile') || path.startsWith('/user/account') || 
      path.startsWith('/user/message') || path.startsWith('/user/settings')) {
    expandedGroups.value.personal = true;
  } else if (path.startsWith('/user/videos') || path.startsWith('/user/comments')) {
    expandedGroups.value.videos = true;
  } else if (path.startsWith('/admin')) {
    expandedGroups.value.admin = true;
  } else if (path.startsWith('/superadmin')) {
    expandedGroups.value.superadmin = true;
  }
}, { immediate: true });

const isAdmin = computed(() => {
  const storedRole = localStorage.getItem('user_role');
  const storeRole = userStore.role;
  const effectiveRole = storedRole || storeRole;
  const result = effectiveRole === 'admin' || effectiveRole === 'superadmin';
  return result;
});

const isSuperAdmin = computed(() => {
  const storedRole = localStorage.getItem('user_role');
  const storeRole = userStore.role;
  const effectiveRole = storedRole || storeRole;
  return effectiveRole === 'superadmin';
});

onMounted(() => {
  const storedRole = localStorage.getItem('user_role');
  if (storedRole && (storedRole === 'admin' || storedRole === 'superadmin')) {
    userStore.role = storedRole;
  }
});

const navigateTo = (path) => {
  if (route.path !== path) {
    router.push(path).catch(err => {
      if (err.name !== 'NavigationDuplicated') {
        console.error(err);
      }
    });
  }
};

const logout = () => {
  notificationStore.reset();
  userStore.logout();
  router.push('/login');
};
</script>

<style scoped>
@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}

#sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 250px;
  height: 100%;
  background: #ffffff;
  z-index: 2000;
  font-family: 'Lato', sans-serif;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  scrollbar-width: none;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

#sidebar.hide {
  width: 64px;
  overflow-x: hidden;
}

#sidebar .brand {
  font-size: 22px;
  font-weight: 600;
  height: 70px;
  display: flex;
  align-items: center;
  color: #2196f3;
  position: sticky;
  top: 0;
  left: 0;
  background: #ffffff;
  z-index: 500;
  padding-left: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  text-decoration: none;
  flex-shrink: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

#sidebar.hide .brand {
  justify-content: center;
  padding-left: 0;
}

#sidebar.hide .brand .text {
  display: none;
}

#sidebar .brand .bx {
  min-width: 40px;
  display: flex;
  justify-content: center;
  font-size: 24px;
  color: #2196f3;
  margin-right: 10px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

#sidebar.hide .brand .bx {
  margin-right: 0;
}

#sidebar .side-menu {
  width: 100%;
  margin: 0;
  padding: 0px 0;
  list-style: none;
}

.spacer {
  flex-grow: 1;
}

#sidebar .side-menu.bottom {
  margin-top: auto;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

#sidebar .side-menu li {
  height: 48px;
  background: transparent;
  margin: 0px 0;
  padding: 0;
  list-style-type: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: block;
  position: relative;
}

#sidebar.hide .side-menu li {
  position: relative;
}

#sidebar .side-menu li a {
  width: 100%;
  height: 100%;
  background: transparent;
  color: #333;
  display: flex;
  align-items: center;
  font-weight: 400;
  white-space: nowrap;
  overflow-x: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0 20px;
  border-left: 3px solid transparent;
  position: relative;
}

#sidebar .side-menu li a::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 0;
  background: linear-gradient(90deg, rgba(33, 150, 243, 0.1) 0%, transparent 100%);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: -1;
}

#sidebar.hide .side-menu li a {
  padding: 0;
  justify-content: center;
}

#sidebar.hide .side-menu li a .text,
#sidebar.hide .side-menu li a .num {
  display: none;
}

#sidebar.hide .side-menu li a:hover::after {
  content: attr(data-title);
  position: absolute;
  left: 60px;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  z-index: 100;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

#sidebar .side-menu li a:hover {
  color: #2196f3;
  background-color: rgba(33, 150, 243, 0.06);
}

#sidebar .side-menu li a:hover::before {
  width: 100%;
}

#sidebar .side-menu li.active > a {
  color: #2196f3;
  background-color: rgba(33, 150, 243, 0.08);
  border-left: 3px solid #2196f3;
  font-weight: 500;
}

#sidebar.hide .side-menu li.active > a {
  border-left: none;
  border-right: 3px solid #2196f3;
}

#sidebar .side-menu li a .bx {
  min-width: 25px;
  display: flex;
  align-items: center;
  font-size: 20px;
  margin-right: 10px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

#sidebar .side-menu li a:hover .bx {
  transform: scale(1.1);
  color: #2196f3;
}

#sidebar.hide .side-menu li a .bx {
  min-width: unset;
  margin: 0;
  font-size: 22px;
}

#sidebar .side-menu li a .num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  border-radius: 10px;
  margin-left: 10px;
  padding: 0 6px;
  box-shadow: 0 2px 8px rgba(244, 67, 54, 0.4);
  animation: pulse 2s ease-in-out infinite;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

#sidebar .side-menu li a:hover .num {
  transform: scale(1.1);
  box-shadow: 0 3px 12px rgba(244, 67, 54, 0.5);
}

#sidebar.hide .side-menu li a .num {
  position: absolute;
  top: 5px;
  right: 10px;
  height: 16px;
  min-width: 16px;
  font-size: 10px;
  padding: 0 4px;
}

#sidebar .side-menu li a.logout {
  color: var(--red, #DB504A);
}

#sidebar .side-menu li a.logout:hover {
  background-color: rgba(219, 80, 74, 0.06);
}

#sidebar .side-menu li a.logout:hover .bx {
  transform: scale(1.15);
}

#sidebar .side-menu li a.logout .bx {
  color: var(--red, #DB504A);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 分组菜单样式 */
#sidebar .side-menu li.menu-group {
  height: auto;
  display: block;
  position: relative;
}

#sidebar .menu-group .group-title {
  width: 100%;
  height: 48px;
  background: transparent;
  color: #333;
  display: flex;
  align-items: center;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0 40px 0 20px;
  border-left: 3px solid transparent;
  position: relative;
  cursor: pointer;
  text-decoration: none;
  box-sizing: border-box;
}

#sidebar .menu-group .group-title:hover {
  color: #2196f3;
  background-color: rgba(33, 150, 243, 0.06);
}

#sidebar .menu-group .group-title .bx {
  min-width: 25px;
  display: flex;
  align-items: center;
  font-size: 20px;
  margin-right: 10px;
}

#sidebar .menu-group .group-title .arrow {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), color 0.3s;
  color: #999;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

#sidebar .menu-group .group-title .arrow.expanded {
  transform: translateY(-50%) rotate(180deg);
  color: #2196f3;
}

#sidebar .menu-group .group-title .arrow .el-icon {
  font-size: 14px;
}

#sidebar .menu-group .group-title:hover .arrow {
  color: #2196f3;
}

#sidebar .menu-group .group-title .arrow.expanded {
  transform: rotate(180deg);
  color: #2196f3;
}

#sidebar .menu-group .group-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
  color: #fff;
  font-size: 11px;
  font-weight: 500;
  border-radius: 9px;
  margin-left: 8px;
  padding: 0 5px;
  box-shadow: 0 2px 6px rgba(244, 67, 54, 0.3);
}

#sidebar .submenu {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0;
  margin: 0;
  list-style: none;
  background: transparent;
  display: block;
  position: relative;
}

#sidebar .submenu.expanded {
  max-height: 500px;
}

#sidebar .submenu li {
  height: 42px;
  display: block;
  position: relative;
}

#sidebar .submenu li a {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  padding-left: 45px;
  font-size: 14px;
  color: #333;
  text-decoration: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-left: 3px solid transparent;
}

#sidebar .submenu li a:hover {
  color: #2196f3;
  background-color: rgba(33, 150, 243, 0.06);
}

#sidebar .submenu li.active a {
  color: #2196f3;
  background-color: rgba(33, 150, 243, 0.08);
  border-left: 3px solid #2196f3;
}

#sidebar .submenu li a .bx {
  min-width: 25px;
  display: flex;
  align-items: center;
  font-size: 16px;
  margin-right: 10px;
}

#sidebar .submenu li a .num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  border-radius: 10px;
  margin-left: 10px;
  padding: 0 6px;
  box-shadow: 0 2px 8px rgba(244, 67, 54, 0.4);
}

/* 折叠状态下的分组样式 */
#sidebar.hide .menu-group .group-title {
  padding: 0;
  justify-content: center;
}

#sidebar.hide .menu-group .group-title .text,
#sidebar.hide .menu-group .group-title .arrow,
#sidebar.hide .menu-group .group-title .group-badge {
  display: none;
}

#sidebar.hide .menu-group .group-title .bx {
  margin-right: 0;
}

#sidebar.hide .menu-group .group-title:hover::after {
  content: attr(data-title);
  position: absolute;
  left: 60px;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  z-index: 100;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

#sidebar.hide .submenu {
  max-height: 0 !important;
}

#sidebar.hide .submenu li a {
  padding-left: 0;
  justify-content: center;
}

/* VIP 菜单项样式 */
#sidebar .submenu li.vip-item {
  position: relative;
}

#sidebar .submenu li.vip-item a {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #333;
  font-weight: 600;
  position: relative;
  overflow: hidden;
}

#sidebar .submenu li.vip-item a::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.5s;
}

#sidebar .submenu li.vip-item a:hover::before {
  left: 100%;
}

#sidebar .submenu li.vip-item a:hover {
  background: linear-gradient(135deg, #ffed4e 0%, #ffd700 100%);
  color: #000;
  box-shadow: 0 4px 12px rgba(255, 215, 0, 0.4);
}

#sidebar .submenu li.vip-item.active a {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #000;
  border-left: 3px solid #ff9800;
  box-shadow: 0 4px 12px rgba(255, 215, 0, 0.5);
}

#sidebar .submenu li.vip-item a .vip-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 18px;
  background: linear-gradient(135deg, #ff9800 0%, #ff5722 100%);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  border-radius: 9px;
  margin-right: 8px;
  padding: 0 6px;
  box-shadow: 0 2px 6px rgba(255, 152, 0, 0.4);
  letter-spacing: 0.5px;
  animation: pulse 2s ease-in-out infinite;
}

#sidebar .submenu li.vip-item a .bx {
  color: #ff9800;
}

#sidebar .submenu li.vip-item a:hover .bx {
  color: #ff5722;
  transform: scale(1.15) rotate(5deg);
}

#sidebar .submenu li.vip-item.active a .bx {
  color: #ff5722;
}

/* 折叠状态下的 VIP 样式 */
#sidebar.hide .submenu li.vip-item a {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
}

#sidebar.hide .submenu li.vip-item a .vip-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 24px;
  height: 14px;
  font-size: 8px;
  padding: 0 4px;
}

#sidebar.hide .submenu li.vip-item a:hover::after {
  content: attr(data-title);
  position: absolute;
  left: 60px;
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #000;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  z-index: 100;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(255, 215, 0, 0.4);
  font-weight: 600;
}

/* 管理员分组样式 */
#sidebar .menu-group.admin-group .group-title {
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(239, 68, 68, 0.1) 100%);
  border-left: 3px solid #dc2626;
}

#sidebar .menu-group.admin-group .group-title:hover {
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.15) 0%, rgba(239, 68, 68, 0.15) 100%);
}

#sidebar .menu-group.admin-group .group-title .bx {
  color: #dc2626;
}

#sidebar .menu-group.admin-group .group-title .admin-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  height: 18px;
  background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  border-radius: 9px;
  margin-right: 8px;
  padding: 0 6px;
  box-shadow: 0 2px 6px rgba(220, 38, 38, 0.4);
  letter-spacing: 0.5px;
}

/* 管理员菜单项样式 */
#sidebar .submenu li.admin-item a {
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.05) 0%, rgba(239, 68, 68, 0.05) 100%);
  border-left: 3px solid transparent;
}

#sidebar .submenu li.admin-item a:hover {
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.12) 0%, rgba(239, 68, 68, 0.12) 100%);
  color: #dc2626;
  border-left: 3px solid #dc2626;
}

#sidebar .submenu li.admin-item.active a {
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.15) 0%, rgba(239, 68, 68, 0.15) 100%);
  color: #dc2626;
  border-left: 3px solid #dc2626;
  font-weight: 600;
}

#sidebar .submenu li.admin-item a .bx {
  color: #dc2626;
}

#sidebar .submenu li.admin-item a:hover .bx {
  color: #b91c1c;
  transform: scale(1.15);
}

#sidebar .submenu li.admin-item.active a .bx {
  color: #b91c1c;
}

/* 折叠状态下的管理员样式 */
#sidebar.hide .menu-group.admin-group .group-title {
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(239, 68, 68, 0.1) 100%);
  border-left: none;
  border-right: 3px solid #dc2626;
}

#sidebar.hide .menu-group.admin-group .group-title .admin-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 36px;
  height: 14px;
  font-size: 8px;
  padding: 0 4px;
}

#sidebar.hide .submenu li.admin-item a {
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.05) 0%, rgba(239, 68, 68, 0.05) 100%);
}

#sidebar.hide .submenu li.admin-item a:hover::after {
  content: attr(data-title);
  position: absolute;
  left: 60px;
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.95) 0%, rgba(239, 68, 68, 0.95) 100%);
  color: #fff;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  z-index: 100;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.4);
  font-weight: 600;
}

/* 超级管理员分组样式 */
#sidebar .menu-group.super-admin-group .group-title {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
  border-left: 3px solid #8b5cf6;
}

#sidebar .menu-group.super-admin-group .group-title:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%);
}

#sidebar .menu-group.super-admin-group .group-title .bx {
  color: #8b5cf6;
}

#sidebar .menu-group.super-admin-group .group-title .super-admin-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  height: 18px;
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  border-radius: 9px;
  margin-right: 8px;
  padding: 0 6px;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.5);
  letter-spacing: 0.5px;
  animation: pulse 2s ease-in-out infinite;
}

/* 超级管理员菜单项样式 */
#sidebar .submenu li.super-admin-item a {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(168, 85, 247, 0.08) 100%);
  border-left: 3px solid transparent;
}

#sidebar .submenu li.super-admin-item a:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
  color: #8b5cf6;
  border-left: 3px solid #8b5cf6;
}

#sidebar .submenu li.super-admin-item.active a {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%);
  color: #8b5cf6;
  border-left: 3px solid #8b5cf6;
  font-weight: 600;
}

#sidebar .submenu li.super-admin-item a .bx {
  color: #8b5cf6;
}

#sidebar .submenu li.super-admin-item a:hover .bx {
  color: #7c3aed;
  transform: scale(1.15) rotate(-5deg);
}

#sidebar .submenu li.super-admin-item.active a .bx {
  color: #7c3aed;
}

/* 折叠状态下的超级管理员样式 */
#sidebar.hide .menu-group.super-admin-group .group-title {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
  border-left: none;
  border-right: 3px solid #8b5cf6;
}

#sidebar.hide .menu-group.super-admin-group .group-title .super-admin-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 40px;
  height: 14px;
  font-size: 8px;
  padding: 0 4px;
}

#sidebar.hide .submenu li.super-admin-item a {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(168, 85, 247, 0.08) 100%);
}

#sidebar.hide .submenu li.super-admin-item a:hover::after {
  content: attr(data-title);
  position: absolute;
  left: 60px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.95) 0%, rgba(168, 85, 247, 0.95) 100%);
  color: #fff;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  z-index: 100;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.5);
  font-weight: 600;
}
</style>
