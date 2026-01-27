<template>
  <div class="dashboard-content">
    <PageHeader 
      title="个人资料" 
      :breadcrumb="[{ label: '个人中心' }, { label: '个人资料' }]"
      class="animate-fade-in"
    >
      <template #actions>
        <a href="#" class="btn-save" @click.prevent="saveUserProfile">
          <el-icon><Check /></el-icon>
          <span class="text">保存更改</span>
        </a>
      </template>
    </PageHeader>

    <div class="table-data">
      <div class="order animate-slide-up" style="animation-delay: 0.1s">
        <div class="head">
          <h3>个人信息</h3>
        </div>
        <div class="profile-content">
          <div class="avatar-section">
            <div class="avatar-container">
              <div class="avatar-wrapper">
                <el-avatar :size="120" :src="userData.avatar || defaultAvatar"></el-avatar>
                <div class="avatar-overlay">
                  <el-icon><Upload /></el-icon>
                </div>
              </div>
              <div class="avatar-upload">
                <el-upload
                  class="avatar-uploader"
                  :http-request="uploadAvatar"
                  :show-file-list="false"
                  accept="image/*"
                  :before-upload="beforeAvatarUpload"
                >
                  <el-button type="primary" class="upload-btn">
                    <el-icon><Upload /></el-icon>
                    <span>更换头像</span>
                  </el-button>
                </el-upload>
              </div>
            </div>
          </div>
          <div class="info-section">
            <el-form :model="userData" label-position="top">
              <el-form-item label="用户名">
                <el-input v-model="userData.username" placeholder="请输入用户名">
                  <template #prefix>
                    <el-icon><User /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item label="昵称">
                <el-input v-model="userData.last_name" placeholder="请输入昵称">
                  <template #prefix>
                    <el-icon><User /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item label="邮箱">
                <el-input v-model="userData.email" placeholder="请输入邮箱">
                  <template #prefix>
                    <el-icon><Message /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <!-- 性别和生日并排 -->
              <div class="form-row">
                <el-form-item label="性别" class="form-col">
                  <el-select v-model="userData.gender" placeholder="请选择性别">
                    <el-option label="男" value="male"></el-option>
                    <el-option label="女" value="female"></el-option>
                    <el-option label="保密" value="other"></el-option>
                  </el-select>
                </el-form-item>
                
                <el-form-item label="生日" class="form-col">
                  <el-date-picker
                    v-model="userData.birthday"
                    type="date"
                    placeholder="请选择生日"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                  ></el-date-picker>
                </el-form-item>
              </div>
              
              <el-form-item label="个人网站">
                <el-input v-model="userData.website" placeholder="请输入个人网站">
                  <template #prefix>
                    <el-icon><Link /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item label="个人简介">
                <el-input
                  v-model="userData.bio"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入个人简介"
                ></el-input>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useUserStore } from '@/store/user';
import { getUserInfo, updateUserProfile, uploadAvatar as apiUploadAvatar } from '@/api/user';
import { 
  Check, Upload, User, Message, Link
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
  padding: 32px;
  box-sizing: border-box;
  overflow-x: hidden;
  background: #f0f2f5;
  position: relative;
}

/* 动画定义 */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 应用动画 */
.animate-fade-in {
  animation: fadeIn 0.6s ease-out;
}

.animate-slide-up {
  animation: slideUp 0.6s ease-out both;
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

/* 头部标题 */
.head-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  grid-gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 32px;
  padding: 0 8px;
}

.head-title .left h1 {
  font-size: 42px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #1a202c;
  letter-spacing: -0.5px;
}

.head-title .left .breadcrumb {
  display: flex;
  align-items: center;
  grid-gap: 12px;
  list-style: none;
  padding: 0;
  margin: 0;
}

.head-title .left .breadcrumb li {
  color: #4a5568;
  font-size: 14px;
}

.head-title .left .breadcrumb li a {
  color: #718096;
  pointer-events: none;
  text-decoration: none;
  transition: color 0.3s;
}

.head-title .left .breadcrumb li a.active {
  color: #3b82f6;
  pointer-events: unset;
  font-weight: 500;
}

.head-title .btn-save {
  height: 44px;
  padding: 0 24px;
  border-radius: 8px;
  background: #3b82f6;
  color: #ffffff;
  display: flex;
  justify-content: center;
  align-items: center;
  grid-gap: 8px;
  font-weight: 600;
  font-size: 15px;
  text-decoration: none;
  flex-shrink: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
}

.head-title .btn-save:hover {
  background: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.head-title .btn-save:active {
  transform: translateY(0);
}

/* 表格数据 */
.table-data {
  display: flex;
  flex-wrap: wrap;
  grid-gap: 20px;
  margin-bottom: 32px;
  width: 100%;
}

.table-data > div {
  border-radius: 12px;
  background: #ffffff;
  padding: 32px;
  overflow-x: auto;
  border: 1px solid #e5e7eb;
  transition: all 0.3s;
}

.table-data > div:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.table-data .head {
  display: flex;
  align-items: center;
  grid-gap: 16px;
  margin-bottom: 28px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f3f4f6;
}

.table-data .head h3 {
  margin-right: auto;
  font-size: 20px;
  font-weight: 700;
  color: #111827;
}

.table-data .order {
  flex-grow: 1;
  flex-basis: 500px;
}

/* 个人资料卡片 */
.profile-content {
  display: flex;
  flex-wrap: wrap;
  gap: 32px;
}

.avatar-section {
  flex: 0 0 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.avatar-wrapper {
  position: relative;
  cursor: pointer;
  transition: transform 0.3s;
}

.avatar-wrapper:hover {
  transform: scale(1.05);
}

.avatar-wrapper .el-avatar {
  width: 120px;
  height: 120px;
  border: 4px solid #e5e7eb;
  transition: border-color 0.3s;
}

.avatar-wrapper:hover .el-avatar {
  border-color: #3b82f6;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(59, 130, 246, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
  color: white;
  font-size: 32px;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.avatar-upload {
  margin-top: 8px;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.info-section {
  flex: 1;
  min-width: 300px;
}

.info-section .el-form {
  max-width: 100%;
}

.info-section .el-form-item {
  margin-bottom: 24px;
  max-width: 100%;
}

/* 表单行布局 - 两列 */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.form-row .form-col {
  margin-bottom: 0;
}

.form-row .el-select,
.form-row .el-date-picker {
  width: 100%;
}

/* 表单样式 */
:deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
  margin-bottom: 8px;
}

:deep(.el-input__wrapper) {
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  transition: all 0.2s;
  background: #ffffff;
  box-shadow: none;
}

:deep(.el-input__wrapper:hover) {
  border-color: #9ca3af;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

:deep(.el-textarea__inner) {
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  transition: all 0.2s;
  background: #ffffff;
  line-height: 1.6;
  box-shadow: none;
}

:deep(.el-textarea__inner:hover) {
  border-color: #9ca3af;
}

:deep(.el-textarea__inner:focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

:deep(.el-select .el-input__wrapper) {
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  box-shadow: none;
}

:deep(.el-select .el-input__wrapper:hover) {
  border-color: #9ca3af;
}

:deep(.el-select .el-input__wrapper.is-focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

:deep(.el-date-editor) {
  width: 100%;
}

/* 按钮样式 */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 600;
  padding: 12px 24px;
  border: none;
  font-size: 14px;
  transition: all 0.2s;
}

:deep(.el-button:hover) {
  transform: translateY(-1px);
}

:deep(.el-button:active) {
  transform: translateY(0);
}

:deep(.el-button--primary) {
  background: #3b82f6;
  color: #ffffff;
}

:deep(.el-button--primary:hover) {
  background: #2563eb;
}

/* 响应式设计 */
@media screen and (max-width: 1200px) {
  .profile-content {
    flex-direction: column;
  }
  
  .avatar-section {
    width: 100%;
    margin-bottom: 20px;
  }
  
  .info-section {
    width: 100%;
  }
}

@media screen and (max-width: 768px) {
  .dashboard-content {
    padding: 16px;
  }
  
  .head-title {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .head-title .btn-save {
    margin-top: 16px;
    align-self: flex-start;
  }
  
  .form-row {
    grid-template-columns: 1fr;
    gap: 0;
  }
  
  .form-row .form-col {
    margin-bottom: 24px;
  }
  
  .info-section .el-form-item {
    margin-bottom: 20px;
  }
  
  .table-data > div {
    padding: 20px;
  }
}

@media screen and (max-width: 576px) {
  .head-title .left h1 {
    font-size: 32px;
  }
  
  .profile-content {
    gap: 20px;
  }
}
</style> 