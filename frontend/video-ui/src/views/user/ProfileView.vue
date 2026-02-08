<template>
  <div class="dashboard-content">
    <PageHeader 
      title="个人资料" 
      :breadcrumb="[{ label: '个人中心' }, { label: '个人资料' }]"
      class="animate-slide-up"
    >
      <template #actions>
        <a href="#" class="btn-save" @click.prevent="saveUserProfile">
          <el-icon><Check /></el-icon>
          <span class="text">保存更改</span>
        </a>
      </template>
    </PageHeader>

    <div class="profile-container">
      <!-- 头像卡片 -->
      <div class="avatar-card animate-slide-up">
        <div class="card-header">
          <div class="header-icon">
            <el-icon><Avatar /></el-icon>
          </div>
          <h3>头像设置</h3>
        </div>
        <div class="avatar-content">
          <div class="avatar-wrapper">
            <el-avatar :size="140" :src="userData.avatar || defaultAvatar" class="main-avatar"></el-avatar>
            <div class="avatar-overlay">
              <el-icon class="upload-icon"><Upload /></el-icon>
              <span class="upload-text">点击上传</span>
            </div>
          </div>
          <div class="avatar-info">
            <h4>{{ userData.username || '未设置用户名' }}</h4>
            <p class="user-role">{{ userData.email || '未设置邮箱' }}</p>
            <el-upload
              class="avatar-uploader"
              :http-request="uploadAvatar"
              :show-file-list="false"
              accept="image/*"
              :before-upload="beforeAvatarUpload"
            >
              <el-button type="primary" class="upload-btn" round>
                <el-icon><Upload /></el-icon>
                <span>更换头像</span>
              </el-button>
            </el-upload>
            <p class="upload-tip">支持 JPG、PNG 格式，大小不超过 2MB</p>
          </div>
        </div>
      </div>

      <!-- 基本信息卡片 -->
      <div class="info-card animate-slide-up" style="animation-delay: 0.1s">
        <div class="card-header">
          <div class="header-icon">
            <el-icon><User /></el-icon>
          </div>
          <h3>基本信息</h3>
        </div>
        <div class="info-content">
          <el-form :model="userData" label-position="top" class="profile-form">
            <div class="form-grid">
              <el-form-item label="用户名" class="form-item">
                <el-input 
                  v-model="userData.username" 
                  placeholder="请输入用户名"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><User /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item label="昵称" class="form-item">
                <el-input 
                  v-model="userData.last_name" 
                  placeholder="请输入昵称"
                >
                  <template #prefix>
                    <el-icon class="input-icon"><User /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
            </div>

            <el-form-item label="邮箱地址" class="form-item">
              <el-input 
                v-model="userData.email" 
                placeholder="请输入邮箱地址"
              >
                <template #prefix>
                  <el-icon class="input-icon"><Message /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            
            <div class="form-grid">
              <el-form-item label="性别" class="form-item">
                <el-select 
                  v-model="userData.gender" 
                  placeholder="请选择性别"
                >
                  <el-option label="男" value="male">
                    <span class="option-content">
                      <el-icon><Male /></el-icon>
                      <span>男</span>
                    </span>
                  </el-option>
                  <el-option label="女" value="female">
                    <span class="option-content">
                      <el-icon><Female /></el-icon>
                      <span>女</span>
                    </span>
                  </el-option>
                  <el-option label="保密" value="other">
                    <span class="option-content">
                      <el-icon><Hide /></el-icon>
                      <span>保密</span>
                    </span>
                  </el-option>
                </el-select>
              </el-form-item>
              
              <el-form-item label="生日" class="form-item">
                <el-date-picker
                  v-model="userData.birthday"
                  type="date"
                  placeholder="请选择生日"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                ></el-date-picker>
              </el-form-item>
            </div>
            
            <el-form-item label="个人网站" class="form-item">
              <el-input 
                v-model="userData.website" 
                placeholder="https://example.com"
              >
                <template #prefix>
                  <el-icon class="input-icon"><Link /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            
            <el-form-item label="个人简介" class="form-item">
              <el-input
                v-model="userData.bio"
                type="textarea"
                :rows="4"
                placeholder="介绍一下你自己吧..."
                maxlength="200"
                show-word-limit
              ></el-input>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useUserStore } from '@/store/user';
import { getUserInfo, updateUserProfile, uploadAvatar as apiUploadAvatar } from '@/api/user';
import { 
  Check, Upload, User, Message, Link, Avatar, Male, Female, Hide
} from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';

const userStore = useUserStore();
const defaultAvatar = new URL('@/assets/default-avatar.png', import.meta.url).href;

// 用户数据
const userData = reactive({
  username: '',
  last_name: '', // 使用last_name替代nickname
  email: '',
  bio: '',
  avatar: '',
  gender: 'other',
  birthday: '',
  website: ''
});

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const data = await getUserInfo();
    
    // 确保所有字段都存在
    userData.username = data.username || '';
    userData.last_name = data.last_name || ''; // 使用last_name
    userData.email = data.email || '';
    userData.bio = data.bio || '';
    userData.avatar = data.avatar || '';
    userData.gender = data.gender || 'other';
    userData.birthday = data.birthday || '';
    userData.website = data.website || '';
  } catch (error) {
    console.error('获取用户信息失败:', error);
    ElMessage.error('获取用户信息失败，请刷新页面重试');
  }
};

// 保存用户信息
const saveUserProfile = async () => {
  try {
    // 只发送有值的字段
    const updateData = {};
    
    if (userData.username) updateData.username = userData.username;
    if (userData.last_name) updateData.last_name = userData.last_name;
    if (userData.email) updateData.email = userData.email;
    if (userData.bio) updateData.bio = userData.bio;
    if (userData.gender) updateData.gender = userData.gender;
    if (userData.birthday) updateData.birthday = userData.birthday;
    if (userData.website) updateData.website = userData.website;
    
    await updateUserProfile(updateData);
    ElMessage.success('个人信息更新成功');
  } catch (error) {
    console.error('更新个人信息失败:', error);
    if (error.response && error.response.data) {
      // 显示具体的错误信息
      const errors = error.response.data;
      const errorMessages = [];
      for (const key in errors) {
        if (Array.isArray(errors[key])) {
          errorMessages.push(...errors[key]);
        } else {
          errorMessages.push(errors[key]);
        }
      }
      ElMessage.error(errorMessages.join('; ') || '更新个人信息失败，请重试');
    } else {
      ElMessage.error('更新个人信息失败，请重试');
    }
  }
};

// 头像上传前验证
const beforeAvatarUpload = (file) => {
  const isImage = file.type.startsWith('image/');
  const isLt2M = file.size / 1024 / 1024 < 2;

  if (!isImage) {
    ElMessage.error('头像必须是图片格式!');
    return false;
  }
  if (!isLt2M) {
    ElMessage.error('头像大小不能超过 2MB!');
    return false;
  }
  return true;
};

// 上传头像
const uploadAvatar = async (options) => {
  try {
    const response = await apiUploadAvatar(options.file);
    
    if (response && response.avatar_url) {
      userData.avatar = response.avatar_url;
      userStore.setAvatar(response.avatar_url);
      ElMessage.success('头像上传成功');
    } else {
      ElMessage.error('头像上传返回格式错误');
    }
  } catch (error) {
    console.error('头像上传失败:', error);
    ElMessage.error('头像上传失败，请重试');
  }
};

onMounted(() => {
  fetchUserInfo();
});
</script>

<style scoped>
/* 仪表盘内容容器 */
.dashboard-content {
  width: 100%;
  min-height: 100%;
  padding: 24px;
  box-sizing: border-box;
  overflow-x: hidden;
  background: #f5f7fa;
  position: relative;
}

/* 动画定义 */
@keyframes subtleSlideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-slide-up {
  animation: subtleSlideUp 0.4s ease-out both;
}

/* 个人资料容器 */
.profile-container {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
  position: relative;
  z-index: 1;
}

/* 卡片通用样式 */
.avatar-card,
.info-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  overflow: hidden;
}

.avatar-card:hover,
.info-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

/* 卡片头部 */
.card-header {
  padding: 18px 24px;
  background: #f8f9fa;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  width: 36px;
  height: 36px;
  background: #e5e7eb;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  font-size: 18px;
}

.card-header h3 {
  color: #374151;
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

/* 头像卡片 */
.avatar-card {
  height: fit-content;
}

.avatar-content {
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}

.avatar-wrapper {
  position: relative;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.avatar-wrapper:hover {
  transform: scale(1.05);
}

.main-avatar {
  width: 120px;
  height: 120px;
  border: 4px solid #f3f4f6;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.avatar-wrapper:hover .main-avatar {
  border-color: #667eea;
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.25);
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
  color: white;
  gap: 8px;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.upload-icon {
  font-size: 32px;
}

.upload-text {
  font-size: 13px;
  font-weight: 500;
}

.avatar-info {
  text-align: center;
  width: 100%;
}

.avatar-info h4 {
  font-size: 18px;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 6px 0;
}

.user-role {
  font-size: 13px;
  color: #718096;
  margin: 0 0 16px 0;
}

.upload-btn {
  width: 100%;
  height: 40px;
  font-size: 14px;
  font-weight: 600;
  background: #3b82f6;
  border: none;
  transition: all 0.3s ease;
}

.upload-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.35);
}

.upload-tip {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 10px;
  line-height: 1.4;
}

/* 信息卡片 */
.info-content {
  padding: 20px;
}

.profile-form {
  max-width: 100%;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-item {
  margin-bottom: 16px;
}

/* 表单样式增强 */
:deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
  font-size: 13px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

:deep(.el-input__wrapper) {
  padding: 8px 12px;
  border-radius: 8px;
  border: 2px solid #e5e7eb;
  transition: all 0.3s;
  background: #f9fafb;
  box-shadow: none;
}

:deep(.el-input__wrapper:hover) {
  border-color: #d1d5db;
  background: #ffffff;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.input-icon {
  color: #9ca3af;
  font-size: 16px;
}

:deep(.el-textarea__inner) {
  padding: 8px 12px;
  border-radius: 8px;
  border: 2px solid #e5e7eb;
  transition: all 0.3s;
  background: #f9fafb;
  line-height: 1.6;
  box-shadow: none;
  font-family: inherit;
}

:deep(.el-textarea__inner:hover) {
  border-color: #d1d5db;
  background: #ffffff;
}

:deep(.el-textarea__inner:focus) {
  border-color: #667eea;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-select .el-input__wrapper) {
  padding: 8px 12px;
  border-radius: 8px;
  border: 2px solid #e5e7eb;
  background: #f9fafb;
  box-shadow: none;
}

:deep(.el-select .el-input__wrapper:hover) {
  border-color: #d1d5db;
  background: #ffffff;
}

:deep(.el-select .el-input__wrapper.is-focus) {
  border-color: #667eea;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.option-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.el-date-editor) {
  width: 100%;
}

:deep(.el-date-editor .el-input__wrapper) {
  padding: 8px 12px;
  border-radius: 8px;
  border: 2px solid #e5e7eb;
  background: #f9fafb;
}

/* 保存按钮样式 */
.btn-save {
  height: 40px;
  padding: 0 24px;
  border-radius: 8px;
  background: #3b82f6;
  color: #ffffff;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  text-decoration: none;
  flex-shrink: 0;
  transition: all 0.3s ease;
  border: none;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25);
}

.btn-save:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.35);
}

.btn-save:active {
  transform: translateY(0);
}

/* 响应式设计 */
@media screen and (max-width: 1200px) {
  .profile-container {
    grid-template-columns: 1fr;
  }
  
  .avatar-card {
    max-width: 100%;
  }
}

@media screen and (max-width: 768px) {
  .dashboard-content {
    padding: 12px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }
  
  .card-header {
    padding: 16px 20px;
  }
  
  .avatar-content,
  .info-content {
    padding: 20px 16px;
  }
  
  .main-avatar {
    width: 100px;
    height: 100px;
  }
}

@media screen and (max-width: 576px) {
  .dashboard-content {
    padding: 10px;
  }
  
  .profile-container {
    gap: 16px;
  }
  
  .card-header h3 {
    font-size: 15px;
  }
  
  .header-icon {
    width: 32px;
    height: 32px;
    font-size: 16px;
  }
}

/* 滚动条样式 */
.dashboard-content::-webkit-scrollbar {
  width: 8px;
}

.dashboard-content::-webkit-scrollbar-track {
  background: transparent;
}

.dashboard-content::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.dashboard-content::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}
</style> 