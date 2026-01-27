<template>
  <div class="settings-container">
    <PageHeader 
      title="系统设置" 
      :breadcrumb="[{ label: '个人中心' }, { label: '系统设置' }]"
    />
    
    <div class="settings-wrapper">
      <!-- 侧边导航 -->
      <div class="settings-sidebar">
        <div 
          v-for="tab in tabs" 
          :key="tab.name"
          :class="['sidebar-item', { active: activeTab === tab.name }]"
          @click="activeTab = tab.name"
        >
          <el-icon class="sidebar-icon">
            <component :is="tab.icon" />
          </el-icon>
          <span class="sidebar-label">{{ tab.label }}</span>
          <el-icon class="arrow-icon"><ArrowRight /></el-icon>
        </div>
      </div>
      
      <!-- 设置内容区 -->
      <div class="settings-main">
        <!-- 通知设置 -->
        <div v-show="activeTab === 'notifications'" class="settings-content">
          <div class="content-header">
            <h2>通知设置</h2>
            <p>管理您接收消息通知的方式</p>
          </div>
          
          <div class="settings-grid">
            <div class="setting-card">
              <div class="card-icon system">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="card-content">
                <h4>系统通知</h4>
                <p>系统更新、账号安全等重要通知</p>
              </div>
              <el-switch v-model="notificationSettings.system" @change="updateNotificationSetting('system')" />
            </div>
            
            <div class="setting-card">
              <div class="card-icon interaction">
                <el-icon><ChatDotRound /></el-icon>
              </div>
              <div class="card-content">
                <h4>视频互动通知</h4>
                <p>点赞、评论、收藏等互动提醒</p>
              </div>
              <el-switch v-model="notificationSettings.interaction" @change="updateNotificationSetting('interaction')" />
            </div>
            
            <div class="setting-card">
              <div class="card-icon message">
                <el-icon><Message /></el-icon>
              </div>
              <div class="card-content">
                <h4>私信通知</h4>
                <p>接收其他用户发送的私信</p>
              </div>
              <el-switch v-model="notificationSettings.private" @change="updateNotificationSetting('private')" />
            </div>
            
            <div class="setting-card">
              <div class="card-icon email">
                <el-icon><Promotion /></el-icon>
              </div>
              <div class="card-content">
                <h4>邮件通知</h4>
                <p>同时通过邮件接收重要通知</p>
              </div>
              <el-switch v-model="notificationSettings.email" @change="updateNotificationSetting('email')" />
            </div>
            
            <div class="setting-card">
              <div class="card-icon follow">
                <el-icon><Star /></el-icon>
              </div>
              <div class="card-content">
                <h4>关注更新通知</h4>
                <p>关注的UP主发布新视频时通知</p>
              </div>
              <el-switch v-model="notificationSettings.follow" @change="updateNotificationSetting('follow')" />
            </div>
          </div>
        </div>
        
        <!-- 隐私设置 -->
        <div v-show="activeTab === 'privacy'" class="settings-content">
          <div class="content-header">
            <h2>隐私设置</h2>
            <p>管理您的隐私偏好和数据可见性</p>
          </div>
          
          <div class="settings-grid">
            <div class="setting-card">
              <div class="card-icon privacy">
                <el-icon><User /></el-icon>
              </div>
              <div class="card-content">
                <h4>公开个人资料</h4>
                <p>允许其他用户查看您的个人资料</p>
              </div>
              <el-switch v-model="privacySettings.publicProfile" @change="updatePrivacySetting('publicProfile')" />
            </div>
            
            <div class="setting-card">
              <div class="card-icon privacy">
                <el-icon><View /></el-icon>
              </div>
              <div class="card-content">
                <h4>显示观看历史</h4>
                <p>在您的个人主页显示最近观看的视频</p>
              </div>
              <el-switch v-model="privacySettings.showHistory" @change="updatePrivacySetting('showHistory')" />
            </div>
            
            <div class="setting-card">
              <div class="card-icon privacy">
                <el-icon><ChatLineRound /></el-icon>
              </div>
              <div class="card-content">
                <h4>允许私信</h4>
                <p>允许其他用户向您发送私信</p>
              </div>
              <el-switch v-model="privacySettings.allowMessages" @change="updatePrivacySetting('allowMessages')" />
            </div>
            
            <div class="setting-card">
              <div class="card-icon privacy">
                <el-icon><Collection /></el-icon>
              </div>
              <div class="card-content">
                <h4>公开收藏夹</h4>
                <p>允许其他用户查看您的收藏视频</p>
              </div>
              <el-switch v-model="privacySettings.publicCollections" @change="updatePrivacySetting('publicCollections')" />
            </div>
            
            <div class="setting-card">
              <div class="card-icon privacy">
                <el-icon><UserFilled /></el-icon>
              </div>
              <div class="card-content">
                <h4>显示关注列表</h4>
                <p>在个人主页显示关注和粉丝列表</p>
              </div>
              <el-switch v-model="privacySettings.showFollowing" @change="updatePrivacySetting('showFollowing')" />
            </div>
          </div>
        </div>
        
        <!-- 播放设置 -->
        <div v-show="activeTab === 'playback'" class="settings-content">
          <div class="content-header">
            <h2>播放设置</h2>
            <p>自定义您的视频播放体验</p>
          </div>
          
          <div class="settings-grid">
            <div class="setting-card">
              <div class="card-icon playback">
                <el-icon><VideoCamera /></el-icon>
              </div>
              <div class="card-content">
                <h4>自动播放</h4>
                <p>浏览时自动播放视频预览</p>
              </div>
              <el-switch v-model="playbackSettings.autoplay" @change="updatePlaybackSetting('autoplay')" />
            </div>
            
            <div class="setting-card">
              <div class="card-icon playback">
                <el-icon><Picture /></el-icon>
              </div>
              <div class="card-content">
                <h4>默认清晰度</h4>
                <p>选择默认播放清晰度</p>
              </div>
              <el-select v-model="playbackSettings.quality" @change="updatePlaybackSetting('quality')" size="small" style="width: 100px;">
                <el-option label="自动" value="auto" />
                <el-option label="1080P" value="1080p" />
                <el-option label="720P" value="720p" />
                <el-option label="480P" value="480p" />
              </el-select>
            </div>
            
            <div class="setting-card">
              <div class="card-icon playback">
                <el-icon><Timer /></el-icon>
              </div>
              <div class="card-content">
                <h4>默认播放速度</h4>
                <p>设置默认播放速度</p>
              </div>
              <el-select v-model="playbackSettings.speed" @change="updatePlaybackSetting('speed')" size="small" style="width: 100px;">
                <el-option label="0.5x" value="0.5" />
                <el-option label="1.0x" value="1.0" />
                <el-option label="1.5x" value="1.5" />
                <el-option label="2.0x" value="2.0" />
              </el-select>
            </div>
            
            <div class="setting-card">
              <div class="card-icon playback">
                <el-icon><Microphone /></el-icon>
              </div>
              <div class="card-content">
                <h4>记忆音量</h4>
                <p>记住上次播放的音量设置</p>
              </div>
              <el-switch v-model="playbackSettings.rememberVolume" @change="updatePlaybackSetting('rememberVolume')" />
            </div>
            
            <div class="setting-card">
              <div class="card-icon playback">
                <el-icon><ChatLineSquare /></el-icon>
              </div>
              <div class="card-content">
                <h4>弹幕设置</h4>
                <p>默认开启弹幕显示</p>
              </div>
              <el-switch v-model="playbackSettings.danmaku" @change="updatePlaybackSetting('danmaku')" />
            </div>
            
            <div class="setting-card">
              <div class="card-icon playback">
                <el-icon><Position /></el-icon>
              </div>
              <div class="card-content">
                <h4>记忆播放进度</h4>
                <p>自动记录并恢复播放进度</p>
              </div>
              <el-switch v-model="playbackSettings.rememberProgress" @change="updatePlaybackSetting('rememberProgress')" />
            </div>
          </div>
        </div>
        
        <!-- 界面设置 -->
        <div v-show="activeTab === 'interface'" class="settings-content">
          <div class="content-header">
            <h2>界面设置</h2>
            <p>自定义界面外观和交互体验</p>
          </div>
          
          <div class="settings-grid">
            <div class="setting-card">
              <div class="card-icon interface">
                <el-icon><Moon /></el-icon>
              </div>
              <div class="card-content">
                <h4>深色模式</h4>
                <p>切换深色/浅色主题</p>
              </div>
              <el-switch v-model="interfaceSettings.darkMode" @change="updateInterfaceSetting('darkMode')" />
            </div>
            
            <div class="setting-card">
              <div class="card-icon interface">
                <el-icon><Grid /></el-icon>
              </div>
              <div class="card-content">
                <h4>首页布局</h4>
                <p>选择首页视频列表的显示方式</p>
              </div>
              <el-radio-group v-model="interfaceSettings.layout" @change="updateInterfaceSetting('layout')" size="small">
                <el-radio-button label="grid">网格</el-radio-button>
                <el-radio-button label="list">列表</el-radio-button>
              </el-radio-group>
            </div>
            
            <div class="setting-card">
              <div class="card-icon interface">
                <el-icon><Histogram /></el-icon>
              </div>
              <div class="card-content">
                <h4>每页显示数量</h4>
                <p>设置每页显示数量</p>
              </div>
              <el-select v-model="interfaceSettings.pageSize" @change="updateInterfaceSetting('pageSize')" size="small" style="width: 100px;">
                <el-option label="12个" :value="12" />
                <el-option label="24个" :value="24" />
                <el-option label="36个" :value="36" />
              </el-select>
            </div>
            
            <div class="setting-card">
              <div class="card-icon interface">
                <el-icon><Pointer /></el-icon>
              </div>
              <div class="card-content">
                <h4>悬停预览</h4>
                <p>鼠标悬停时显示视频预览</p>
              </div>
              <el-switch v-model="interfaceSettings.hoverPreview" @change="updateInterfaceSetting('hoverPreview')" />
            </div>
          </div>
        </div>
        
        <!-- 账号安全 -->
        <div v-show="activeTab === 'security'" class="settings-content">
          <div class="content-header">
            <h2>账号安全</h2>
            <p>保护您的账号安全</p>
          </div>
          
          <div class="settings-grid">
            <div class="setting-card action-card">
              <div class="card-icon security">
                <el-icon><Lock /></el-icon>
              </div>
              <div class="card-content">
                <h4>修改密码</h4>
                <p>定期修改密码以保护账号安全</p>
              </div>
              <el-button type="primary" size="small" @click="showPasswordDialog = true">
                修改
              </el-button>
            </div>
            
            <div class="setting-card action-card">
              <div class="card-icon security">
                <el-icon><Iphone /></el-icon>
              </div>
              <div class="card-content">
                <h4>绑定手机</h4>
                <p>{{ securitySettings.phone || '未绑定手机号' }}</p>
              </div>
              <el-button type="primary" size="small" @click="showPhoneDialog = true">
                {{ securitySettings.phone ? '修改' : '绑定' }}
              </el-button>
            </div>
            
            <div class="setting-card action-card">
              <div class="card-icon security">
                <el-icon><Message /></el-icon>
              </div>
              <div class="card-content">
                <h4>绑定邮箱</h4>
                <p>{{ securitySettings.email || '未绑定邮箱地址' }}</p>
              </div>
              <el-button type="primary" size="small" @click="showEmailDialog = true">
                {{ securitySettings.email ? '修改' : '绑定' }}
              </el-button>
            </div>
            
            <div class="setting-card action-card">
              <div class="card-icon security">
                <el-icon><Connection /></el-icon>
              </div>
              <div class="card-content">
                <h4>登录设备管理</h4>
                <p>查看和管理已登录的设备</p>
              </div>
              <el-button type="primary" size="small" @click="showDevicesDialog = true">
                管理
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 修改密码对话框 -->
    <el-dialog v-model="showPasswordDialog" title="修改密码" width="500px">
      <el-form :model="passwordForm" label-width="100px">
        <el-form-item label="当前密码">
          <el-input v-model="passwordForm.oldPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" @click="changePassword">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 绑定手机对话框 -->
    <el-dialog v-model="showPhoneDialog" title="绑定手机" width="500px">
      <el-form :model="phoneForm" label-width="100px">
        <el-form-item label="手机号">
          <el-input v-model="phoneForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="验证码">
          <div style="display: flex; gap: 10px;">
            <el-input v-model="phoneForm.code" placeholder="请输入验证码" />
            <el-button @click="sendPhoneCode">发送验证码</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPhoneDialog = false">取消</el-button>
        <el-button type="primary" @click="bindPhone">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 绑定邮箱对话框 -->
    <el-dialog v-model="showEmailDialog" title="绑定邮箱" width="500px">
      <el-form :model="emailForm" label-width="100px">
        <el-form-item label="邮箱地址">
          <el-input v-model="emailForm.email" placeholder="请输入邮箱地址" />
        </el-form-item>
        <el-form-item label="验证码">
          <div style="display: flex; gap: 10px;">
            <el-input v-model="emailForm.code" placeholder="请输入验证码" />
            <el-button @click="sendEmailCode">发送验证码</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEmailDialog = false">取消</el-button>
        <el-button type="primary" @click="bindEmail">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 登录设备管理对话框 -->
    <el-dialog v-model="showDevicesDialog" title="登录设备管理" width="700px">
      <el-table :data="loginDevices" style="width: 100%">
        <el-table-column prop="device" label="设备" />
        <el-table-column prop="location" label="位置" />
        <el-table-column prop="time" label="登录时间" />
        <el-table-column label="操作" width="100">
          <template #default="scope">
            <el-button 
              v-if="!scope.row.current" 
              type="danger" 
              size="small" 
              link
              @click="removeDevice(scope.row)"
            >
              移除
            </el-button>
            <el-tag v-else type="success" size="small">当前设备</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
  Bell, Lock, VideoPlay, Monitor, Key,
  Warning, ChatDotRound, Message, Promotion, Star,
  User, View, ChatLineRound, Collection, UserFilled,
  VideoCamera, Picture, Timer, Microphone, ChatLineSquare, Position,
  Moon, Grid, Histogram, Pointer,
  Iphone, Connection,
  ArrowRight
} from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import { getNotificationSettings, updateNotificationSettings } from '@/api/user';

const activeTab = ref('notifications');

// 标签页配置
const tabs = [
  { name: 'notifications', label: '通知设置', icon: Bell },
  { name: 'privacy', label: '隐私设置', icon: Lock },
  { name: 'playback', label: '播放设置', icon: VideoPlay },
  { name: 'interface', label: '界面设置', icon: Monitor },
  { name: 'security', label: '账号安全', icon: Key }
];

// 通知设置
const notificationSettings = reactive({
  system: true,
  interaction: true,
  private: true,
  email: false,
  follow: true
});

// 隐私设置
const privacySettings = reactive({
  publicProfile: true,
  showHistory: true,
  allowMessages: true,
  publicCollections: false,
  showFollowing: true
});

// 播放设置
const playbackSettings = reactive({
  autoplay: true,
  quality: 'auto',
  speed: '1.0',
  rememberVolume: true,
  danmaku: true,
  rememberProgress: true
});

// 界面设置
const interfaceSettings = reactive({
  darkMode: false,
  layout: 'grid',
  pageSize: 24,
  hoverPreview: true
});

// 安全设置
const securitySettings = reactive({
  phone: '',
  email: ''
});

// 数据管理（已删除）
// const dataSettings = reactive({
//   cacheSize: '128 MB',
//   historyCount: 156,
//   searchCount: 48,
//   autoCache: false
// });

// 对话框显示状态
const showPasswordDialog = ref(false);
const showPhoneDialog = ref(false);
const showEmailDialog = ref(false);
const showDevicesDialog = ref(false);

// 表单数据
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const phoneForm = reactive({
  phone: '',
  code: ''
});

const emailForm = reactive({
  email: '',
  code: ''
});

// 登录设备列表
const loginDevices = ref([
  { device: 'Windows 11 - Chrome', location: '北京市', time: '2026-01-21 20:30', current: true },
  { device: 'iPhone 15 Pro - Safari', location: '上海市', time: '2026-01-20 15:20', current: false },
  { device: 'MacBook Pro - Safari', location: '广州市', time: '2026-01-18 09:15', current: false }
]);

// 初始化数据
onMounted(async () => {
  await fetchNotificationSettings();
});

// 获取通知设置
const fetchNotificationSettings = async () => {
  try {
    const res = await getNotificationSettings();
    Object.assign(notificationSettings, res);
  } catch (error) {
    console.error('获取通知设置失败:', error);
  }
};

// 更新通知设置
const updateNotificationSetting = async (setting) => {
  try {
    await updateNotificationSettings(notificationSettings);
    const status = notificationSettings[setting] ? '开启' : '关闭';
    const settingNames = {
      system: '系统通知',
      interaction: '互动通知',
      private: '私信通知',
      email: '邮件通知',
      follow: '关注更新通知'
    };
    ElMessage.success(`已${status}${settingNames[setting]}`);
  } catch (error) {
    notificationSettings[setting] = !notificationSettings[setting];
    ElMessage.error('设置更新失败');
  }
};

// 更新隐私设置
const updatePrivacySetting = (setting) => {
  const status = privacySettings[setting] ? '开启' : '关闭';
  const settingNames = {
    publicProfile: '公开个人资料',
    showHistory: '显示观看历史',
    allowMessages: '允许私信',
    publicCollections: '公开收藏夹',
    showFollowing: '显示关注列表'
  };
  ElMessage.success(`已${status}${settingNames[setting]}`);
};

// 更新播放设置
const updatePlaybackSetting = (setting) => {
  const settingNames = {
    autoplay: '自动播放',
    quality: '默认清晰度',
    speed: '播放速度',
    rememberVolume: '记忆音量',
    danmaku: '弹幕显示',
    rememberProgress: '记忆播放进度'
  };
  
  if (setting === 'quality' || setting === 'speed') {
    ElMessage.success(`已设置${settingNames[setting]}为 ${playbackSettings[setting]}`);
  } else {
    const status = playbackSettings[setting] ? '开启' : '关闭';
    ElMessage.success(`已${status}${settingNames[setting]}`);
  }
};

// 更新界面设置
const updateInterfaceSetting = (setting) => {
  const settingNames = {
    darkMode: '深色模式',
    layout: '首页布局',
    pageSize: '每页显示数量',
    hoverPreview: '悬停预览'
  };
  
  if (setting === 'layout') {
    const layoutText = interfaceSettings.layout === 'grid' ? '网格' : '列表';
    ElMessage.success(`已切换到${layoutText}布局`);
  } else if (setting === 'pageSize') {
    ElMessage.success(`已设置每页显示 ${interfaceSettings.pageSize} 个视频`);
  } else {
    const status = interfaceSettings[setting] ? '开启' : '关闭';
    ElMessage.success(`已${status}${settingNames[setting]}`);
  }
};

// 修改密码
const changePassword = () => {
  if (!passwordForm.oldPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
    ElMessage.warning('请填写完整信息');
    return;
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.error('两次输入的密码不一致');
    return;
  }
  ElMessage.success('密码修改成功');
  showPasswordDialog.value = false;
  Object.assign(passwordForm, { oldPassword: '', newPassword: '', confirmPassword: '' });
};

// 发送手机验证码
const sendPhoneCode = () => {
  if (!phoneForm.phone) {
    ElMessage.warning('请输入手机号');
    return;
  }
  ElMessage.success('验证码已发送');
};

// 绑定手机
const bindPhone = () => {
  if (!phoneForm.phone || !phoneForm.code) {
    ElMessage.warning('请填写完整信息');
    return;
  }
  securitySettings.phone = phoneForm.phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2');
  ElMessage.success('手机绑定成功');
  showPhoneDialog.value = false;
  Object.assign(phoneForm, { phone: '', code: '' });
};

// 发送邮箱验证码
const sendEmailCode = () => {
  if (!emailForm.email) {
    ElMessage.warning('请输入邮箱地址');
    return;
  }
  ElMessage.success('验证码已发送');
};

// 绑定邮箱
const bindEmail = () => {
  if (!emailForm.email || !emailForm.code) {
    ElMessage.warning('请填写完整信息');
    return;
  }
  securitySettings.email = emailForm.email.replace(/(.{3}).*(@.*)/, '$1****$2');
  ElMessage.success('邮箱绑定成功');
  showEmailDialog.value = false;
  Object.assign(emailForm, { email: '', code: '' });
};

// 移除设备
const removeDevice = (device) => {
  ElMessageBox.confirm(`确定要移除设备"${device.device}"吗？`, '移除设备', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    const index = loginDevices.value.indexOf(device);
    if (index > -1) {
      loginDevices.value.splice(index, 1);
    }
    ElMessage.success('设备已移除');
  }).catch(() => {});
};
</script>

<style scoped>
.settings-container {
  padding: 20px;
  min-height: 100%;
  background: #f5f5f5;
}

.settings-wrapper {
  display: flex;
  gap: 20px;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  min-height: 600px;
}

/* 侧边导航 */
.settings-sidebar {
  width: 220px;
  background: #fafafa;
  border-right: 1px solid #e8e8e8;
  padding: 20px 0;
  flex-shrink: 0;
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 24px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.sidebar-item:hover {
  background: #f0f0f0;
}

.sidebar-item.active {
  background: linear-gradient(90deg, #e6f7ff 0%, transparent 100%);
  color: #1890ff;
  font-weight: 500;
}

.sidebar-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #1890ff;
}

.sidebar-icon {
  font-size: 20px;
}

.sidebar-label {
  flex: 1;
  font-size: 15px;
}

.arrow-icon {
  font-size: 14px;
  opacity: 0;
  transition: opacity 0.3s;
}

.sidebar-item.active .arrow-icon {
  opacity: 1;
}

/* 主内容区 */
.settings-main {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
}

.settings-content {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.content-header {
  margin-bottom: 30px;
}

.content-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.content-header p {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

/* 设置网格 */
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 16px;
}

/* 设置卡片 */
.setting-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  transition: all 0.3s;
  min-height: 88px;
}

.setting-card:hover {
  border-color: #1890ff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.1);
  transform: translateY(-2px);
}

/* 确保控件不会被压缩 */
.setting-card .el-switch,
.setting-card .el-select,
.setting-card .el-radio-group,
.setting-card .el-button {
  flex-shrink: 0;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 24px;
}

.card-icon.system {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.card-icon.interaction {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
}

.card-icon.message {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: #fff;
}

.card-icon.email {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: #fff;
}

.card-icon.follow {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: #fff;
}

.card-icon.privacy {
  background: linear-gradient(135deg, #30cfd0 0%, #330867 100%);
  color: #fff;
}

.card-icon.playback {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  color: #333;
}

.card-icon.interface {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  color: #333;
}

.card-icon.security {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  color: #333;
}

.card-icon.data {
  background: linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%);
  color: #333;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-content h4 {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 6px 0;
}

.card-content p {
  font-size: 13px;
  color: #909399;
  margin: 0;
  line-height: 1.5;
  word-wrap: break-word;
}

.action-card {
  cursor: default;
}

/* 响应式 */
@media screen and (max-width: 1200px) {
  .settings-grid {
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  }
}

@media screen and (max-width: 968px) {
  .settings-wrapper {
    flex-direction: column;
  }
  
  .settings-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e8e8e8;
    padding: 10px 0;
    display: flex;
    overflow-x: auto;
  }
  
  .sidebar-item {
    flex-direction: column;
    gap: 4px;
    padding: 10px 16px;
    white-space: nowrap;
  }
  
  .sidebar-item.active::before {
    left: 0;
    right: 0;
    top: auto;
    bottom: 0;
    width: auto;
    height: 3px;
  }
  
  .arrow-icon {
    display: none;
  }
  
  .sidebar-label {
    font-size: 13px;
  }
  
  .settings-main {
    padding: 20px;
  }
}

@media screen and (max-width: 768px) {
  .settings-container {
    padding: 12px;
  }
  
  .settings-grid {
    grid-template-columns: 1fr;
  }
  
  .content-header h2 {
    font-size: 20px;
  }
}
</style>
