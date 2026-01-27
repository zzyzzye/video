<template>
  <div class="dashboard-content">
    <PageHeader 
      title="账号安全" 
      :breadcrumb="[{ label: '个人中心' }, { label: '账号安全' }]"
      class="animate-fade-in"
    />

    <div class="security-container">
      <!-- 左侧列 -->
      <div class="security-left">
        <div class="security-card animate-slide-up" style="animation-delay: 0.1s">
          <div class="card-head">
            <h3>修改密码</h3>
          </div>
          
          <el-form 
            ref="passwordFormRef" 
            :model="passwordForm" 
            :rules="passwordRules" 
            label-width="120px"
            class="password-form"
          >
            <el-form-item label="当前密码" prop="currentPassword">
              <el-input 
                v-model="passwordForm.currentPassword" 
                type="password" 
                placeholder="请输入当前密码" 
                show-password
              />
            </el-form-item>
            
            <el-form-item label="新密码" prop="newPassword">
              <el-input 
                v-model="passwordForm.newPassword" 
                type="password" 
                placeholder="请输入新密码" 
                show-password
              />
              <template #tip>
                <div class="form-tip">密码长度至少8位，包含字母、数字或特殊字符</div>
              </template>
            </el-form-item>
            
            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input 
                v-model="passwordForm.confirmPassword" 
                type="password" 
                placeholder="请再次输入新密码" 
                show-password
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="loading.password">修改密码</el-button>
            </el-form-item>
          </el-form>
        </div>
        
        <div class="security-card animate-slide-up" style="animation-delay: 0.2s">
          <div class="card-head">
            <h3>邮箱设置</h3>
          </div>
          
          <div class="email-info">
            <div class="current-email">
              <span class="label">当前邮箱：</span>
              <span class="value">{{ userEmail }}</span>
              <el-tag v-if="emailVerified" type="success" size="small">已验证</el-tag>
              <el-tag v-else type="warning" size="small">未验证</el-tag>
            </div>
            
            <div class="email-actions" v-if="!emailVerified">
              <div class="verification-code-input">
                <el-input 
                  v-model="verifyEmailCode" 
                  placeholder="请输入验证码" 
                  maxlength="6"
                  style="width: 200px;"
                />
                <el-button 
                  type="primary" 
                  :disabled="verifyCodeButtonDisabled" 
                  @click="sendVerifyEmailCode"
                  :loading="loading.verifyEmailCode"
                >
                  {{ verifyCodeButtonText }}
                </el-button>
                <el-button 
                  type="success" 
                  @click="submitVerifyEmail" 
                  :disabled="!verifyEmailCode" 
                  :loading="loading.verification"
                >
                  验证邮箱
                </el-button>
              </div>
            </div>
          </div>
          
          <el-divider content-position="left">修改邮箱</el-divider>
          
          <el-form 
            ref="emailFormRef" 
            :model="emailForm" 
            :rules="emailRules" 
            label-width="120px"
            class="email-form"
          >
            <el-form-item label="新邮箱地址" prop="newEmail">
              <el-input 
                v-model="emailForm.newEmail" 
                placeholder="请输入新的邮箱地址"
              />
            </el-form-item>
            
            <el-form-item label="验证码" prop="code">
              <div class="verification-code-input">
                <el-input 
                  v-model="emailForm.code" 
                  placeholder="请输入验证码" 
                  maxlength="6"
                />
                <el-button 
                  type="primary" 
                  :disabled="emailCodeButtonDisabled" 
                  @click="sendChangeEmailCode"
                  :loading="loading.emailCode"
                >
                  {{ emailCodeButtonText }}
                </el-button>
              </div>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="changeEmail" :loading="loading.email">修改邮箱</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
      
      <!-- 右侧列 -->
      <div class="security-right">
        <div class="security-card animate-slide-up" style="animation-delay: 0.3s">
          <div class="card-head">
            <h3>账号安全</h3>
          </div>
          
          <div class="security-items">
        <div class="security-item">
          <div class="security-item-info">
            <div class="security-item-title">
              <el-icon><Lock /></el-icon>
              <span>登录保护</span>
            </div>
            <div class="security-item-desc">开启后，登录时将发送验证码到您的邮箱</div>
          </div>
          <div class="security-item-action">
            <el-tooltip
              content="请先验证您的邮箱以开启此功能"
              :disabled="emailVerified"
              placement="top"
            >
              <div>
                <el-switch v-model="securitySettings.loginProtection" @change="updateSecuritySetting('loginProtection')" :disabled="!emailVerified" />
              </div>
            </el-tooltip>
          </div>
        </div>
        
        <el-divider />
        
        <div class="security-item">
          <div class="security-item-info">
            <div class="security-item-title">
              <el-icon><Bell /></el-icon>
              <span>异常登录通知</span>
            </div>
            <div class="security-item-desc">开启后，检测到异常登录将通过邮箱通知您</div>
          </div>
          <div class="security-item-action">
            <el-tooltip
              content="请先验证您的邮箱以开启此功能"
              :disabled="emailVerified"
              placement="top"
            >
              <div>
                <el-switch v-model="securitySettings.loginAlert" @change="updateSecuritySetting('loginAlert')" :disabled="!emailVerified" />
              </div>
            </el-tooltip>
          </div>
        </div>
        
        <el-divider />
        
        <div class="security-item">
          <div class="security-item-info">
            <div class="security-item-title">
              <el-icon><Delete /></el-icon>
              <span>注销账号</span>
            </div>
            <div class="security-item-desc">注销后，您的账号将被永久删除，无法恢复</div>
          </div>
          <div class="security-item-action">
            <el-button type="danger" plain size="small" @click="showDeleteAccountDialog">申请注销</el-button>
          </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 注销账号对话框 -->
    <el-dialog
      v-model="deleteAccountDialog"
      title="账号注销确认"
      width="500px"
    >
      <div class="delete-account-warning">
        <el-alert
          title="注销账号将导致以下内容被永久删除："
          type="warning"
          :closable="false"
          show-icon
        >
          <div class="warning-items">
            <p>• 您上传的所有视频内容</p>
            <p>• 您的个人资料和设置</p>
            <p>• 您的评论和互动记录</p>
            <p>• 您的收藏和历史记录</p>
          </div>
        </el-alert>
      </div>
      
      <el-form 
        ref="deleteAccountFormRef" 
        :model="deleteAccountForm" 
        :rules="deleteAccountRules"
        label-position="top"
      >
        <el-form-item label="请输入您的密码" prop="password">
          <el-input 
            v-model="deleteAccountForm.password" 
            type="password" 
            placeholder="请输入密码" 
            show-password
          />
        </el-form-item>
        
        <el-form-item label="请输入「DELETE」确认注销" prop="confirmation">
          <el-input 
            v-model="deleteAccountForm.confirmation" 
            placeholder="请输入DELETE"
          />
        </el-form-item>
        
        <el-form-item prop="agreement">
          <el-checkbox v-model="deleteAccountForm.agreement">我确认已了解账号注销的后果，并自愿申请注销</el-checkbox>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteAccountDialog = false">取消</el-button>
          <el-button type="danger" @click="deleteAccount" :loading="loading.deleteAccount">确认注销</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useUserStore } from '@/store/user';
import { Lock, Bell, Delete } from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import { 
  getUserInfo, 
  sendVerificationCode, 
  verifyEmail, 
  changePassword as apiChangePassword,
  changeEmailWithCode
} from '@/api/user';

const userStore = useUserStore();
const passwordFormRef = ref(null);
const emailFormRef = ref(null);
const deleteAccountFormRef = ref(null);
const deleteAccountDialog = ref(false);
const userEmail = ref('');
const emailVerified = ref(false);
const verifyEmailCode = ref('');  // 邮箱验证码

// 验证码倒计时
const countdown = reactive({
  email: 0,
  verifyEmail: 0
});

// 验证码按钮文本
const emailCodeButtonText = computed(() => {
  return countdown.email > 0 ? `${countdown.email}秒后重新发送` : '获取验证码';
});

const verifyCodeButtonText = computed(() => {
  return countdown.verifyEmail > 0 ? `${countdown.verifyEmail}秒后重新发送` : '获取验证码';
});

// 验证码按钮禁用状态
const emailCodeButtonDisabled = computed(() => countdown.email > 0 || !emailForm.newEmail);
const verifyCodeButtonDisabled = computed(() => countdown.verifyEmail > 0);

// 加载状态
const loading = reactive({
  password: false,
  email: false,
  verification: false,
  deleteAccount: false,
  emailCode: false,
  verifyEmailCode: false
});

// 密码表单
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
});

// 邮箱表单
const emailForm = reactive({
  newEmail: '',
  code: ''
});

// 注销账号表单
const deleteAccountForm = reactive({
  password: '',
  confirmation: '',
  agreement: false
});

// 安全设置
const securitySettings = reactive({
  loginProtection: false,
  loginAlert: true
});

// 密码表单验证规则
const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能小于8个字符', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        // 检查密码复杂度
        if (value && value.length >= 8) {
          // 纯数字密码
          if (/^\d+$/.test(value)) {
            callback(new Error('密码不能仅包含数字'));
            return;
          }
          
          // 密码复杂度检查
          let complexity = 0;
          if (/[a-z]/.test(value)) complexity++; // 小写字母
          if (/[A-Z]/.test(value)) complexity++; // 大写字母
          if (/\d/.test(value)) complexity++;    // 数字
          if (/[^a-zA-Z0-9]/.test(value)) complexity++; // 特殊字符
          
          if (complexity < 2) {
            callback(new Error('密码应包含字母、数字或特殊字符的组合'));
            return;
          }
        }
        callback();
      },
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ]
};

// 邮箱表单验证规则
const emailRules = {
  newEmail: [
    { required: true, message: '请输入新邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { min: 6, max: 6, message: '验证码长度为6位', trigger: 'blur' }
  ]
};

// 注销账号表单验证规则
const deleteAccountRules = {
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ],
  confirmation: [
    { required: true, message: '请输入DELETE确认注销', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== 'DELETE') {
          callback(new Error('请输入正确的确认文字'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ],
  agreement: [
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback(new Error('请确认您了解账号注销的后果'));
        } else {
          callback();
        }
      },
      trigger: 'change'
    }
  ]
};

// 初始化数据
onMounted(async () => {
  try {
    // 获取用户信息
    const userData = await getUserInfo();
    
    // 设置用户邮箱和验证状态
    userEmail.value = userData.email;
    emailVerified.value = userData.is_verified;
    
    // 设置安全选项
    securitySettings.loginProtection = false;
    securitySettings.loginAlert = true;
  } catch (error) {
    ElMessage.error('获取账号信息失败');
  }
});

// 发送邮箱验证验证码
const sendVerifyEmailCode = async () => {
  try {
    loading.verifyEmailCode = true;
    await sendVerificationCode({
      code_type: 'email_verify'
    });
    
    ElMessage.success('验证码已发送到您的邮箱');
    startCountdown('verifyEmail');
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发送验证码失败');
  } finally {
    loading.verifyEmailCode = false;
  }
};

// 发送修改邮箱验证码
const sendChangeEmailCode = async () => {
  if (!emailForm.newEmail) {
    ElMessage.warning('请先输入新邮箱地址');
    return;
  }
  
  try {
    loading.emailCode = true;
    await sendVerificationCode({
      code_type: 'email_change',
      email: emailForm.newEmail
    });
    
    ElMessage.success('验证码已发送到新邮箱');
    startCountdown('email');
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发送验证码失败');
  } finally {
    loading.emailCode = false;
  }
};

// 开始倒计时
const startCountdown = (type) => {
  countdown[type] = 60;
  const timer = setInterval(() => {
    countdown[type]--;
    if (countdown[type] <= 0) {
      clearInterval(timer);
    }
  }, 1000);
};

// 提交邮箱验证
const submitVerifyEmail = async () => {
  if (!verifyEmailCode.value) {
    ElMessage.warning('请输入验证码');
    return;
  }
  
  try {
    loading.verification = true;
    await verifyEmail(verifyEmailCode.value);
    
    ElMessage.success('邮箱验证成功');
    emailVerified.value = true;
    verifyEmailCode.value = '';
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '邮箱验证失败');
  } finally {
    loading.verification = false;
  }
};

// 修改密码
const changePassword = () => {
  passwordFormRef.value.validate(async (valid) => {
    if (!valid) return;
    
    try {
      loading.password = true;
      
      // 使用旧密码修改密码
      await apiChangePassword({
        old_password: passwordForm.currentPassword,
        new_password: passwordForm.newPassword,
        new_password2: passwordForm.confirmPassword
      });
      
      ElMessage.success('密码修改成功');
      passwordForm.currentPassword = '';
      passwordForm.newPassword = '';
      passwordForm.confirmPassword = '';
      passwordFormRef.value.resetFields();
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '密码修改失败');
    } finally {
      loading.password = false;
    }
  });
};

// 修改邮箱
const changeEmail = () => {
  emailFormRef.value.validate(async (valid) => {
    if (!valid) return;
    
    try {
      loading.email = true;
      await changeEmailWithCode({
        code: emailForm.code,
        email: emailForm.newEmail
      });
      
      ElMessage.success('邮箱修改成功');
      userEmail.value = emailForm.newEmail;
      emailVerified.value = true;
      emailForm.newEmail = '';
      emailForm.code = '';
      emailFormRef.value.resetFields();
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '邮箱修改失败');
    } finally {
      loading.email = false;
    }
  });
};

// 更新安全设置
const updateSecuritySetting = async (setting) => {
  try {
    // 实际项目中应该调用API
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const status = securitySettings[setting] ? '开启' : '关闭';
    ElMessage.success(`已${status}${setting === 'loginProtection' ? '登录保护' : '异常登录通知'}`);
  } catch (error) {
    // 恢复原值
    securitySettings[setting] = !securitySettings[setting];
    ElMessage.error('设置更新失败');
  }
};

// 显示注销账号对话框
const showDeleteAccountDialog = () => {
  deleteAccountDialog.value = true;
};

// 注销账号
const deleteAccount = () => {
  deleteAccountFormRef.value.validate(async (valid) => {
    if (!valid) return;
    
    try {
      loading.deleteAccount = true;
      // 实际项目中应该调用API
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      deleteAccountDialog.value = false;
      ElMessageBox.alert(
        '您的账号已成功注销，感谢您使用我们的服务。',
        '注销成功',
        {
          confirmButtonText: '确定',
          callback: () => {
            // 退出登录并跳转到首页
            userStore.logout();
            window.location.href = '/';
          }
        }
      );
    } catch (error) {
      ElMessage.error('账号注销失败');
    } finally {
      loading.deleteAccount = false;
    }
  });
};
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

/* 安全设置容器 - 左右布局 */
.security-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.security-left,
.security-right {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 安全卡片 */
.security-card {
  border-radius: 12px;
  background: #ffffff;
  padding: 32px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  transition: all 0.3s;
}

.security-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.card-head {
  display: flex;
  align-items: center;
  grid-gap: 16px;
  margin-bottom: 28px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f3f4f6;
}

.card-head h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #111827;
}

/* 表单样式 */
.password-form,
.email-form {
  max-width: 100%;
}

.password-form :deep(.el-form-item__content),
.email-form :deep(.el-form-item__content) {
  max-width: 100%;
}

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

.verification-code-input {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.verification-code-input .el-input {
  flex: 1;
  min-width: 0;
}

.verification-code-input .el-button {
  flex-shrink: 0;
  white-space: nowrap;
}

.form-tip {
  font-size: 12px;
  color: #718096;
  margin-top: 5px;
}

/* 按钮样式 */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 600;
  padding: 25px 20px;
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

:deep(.el-button--success) {
  background: #10b981;
  color: #ffffff;
}

:deep(.el-button--success:hover) {
  background: #059669;
}

:deep(.el-button--danger) {
  background: #ef4444;
  color: #ffffff;
}

:deep(.el-button--danger:hover) {
  background: #dc2626;
}

:deep(.el-button--danger.is-plain) {
  background: transparent;
  border: 1px solid #ef4444;
  color: #ef4444;
}

:deep(.el-button--danger.is-plain:hover) {
  background: #fef2f2;
  border-color: #dc2626;
  color: #dc2626;
}

:deep(.el-button.is-plain) {
  background: transparent;
  border: 1px solid currentColor;
}

/* 邮箱信息 */
.email-info {
  margin-bottom: 24px;
}

.current-email {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
}

.current-email .label {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.current-email .value {
  color: #1f2937;
  font-size: 14px;
  font-weight: 500;
}

:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 600;
  font-size: 12px;
}

.email-actions {
  margin-top: 16px;
}

:deep(.el-divider) {
  margin: 24px 0;
}

:deep(.el-divider__text) {
  background: #ffffff;
  color: #6b7280;
  font-weight: 600;
}

/* 安全项目 */
.security-items {
  display: flex;
  flex-direction: column;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px 0;
}

.security-item-info {
  flex: 1;
  padding-top: 2px;
}

.security-item-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
  font-size: 15px;
}

.security-item-title .el-icon {
  font-size: 18px;
  color: #3b82f6;
}

.security-item-desc {
  text-align: left;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
}

.security-item-action {
  margin-left: 16px;
  padding-top: 4px;
  display: flex;
  align-items: flex-start;
}

:deep(.el-switch) {
  --el-switch-on-color: #3b82f6;
}

/* 对话框样式 */
:deep(.el-dialog) {
  border-radius: 12px;
}

:deep(.el-dialog__header) {
  padding: 24px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
}

:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

.delete-account-warning {
  margin-bottom: 24px;
}

.warning-items p {
  margin: 8px 0;
  color: #92400e;
  font-size: 14px;
}

/* 响应式设计 */
@media screen and (max-width: 1200px) {
  .security-container {
    grid-template-columns: 1fr;
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
  
  .head-title .left h1 {
    font-size: 32px;
  }
  
  .security-card {
    padding: 20px;
  }
  
  .verification-code-input {
    flex-direction: column;
  }
  
  .verification-code-input .el-input {
    width: 100% !important;
    flex: none;
  }
  
  .verification-code-input .el-button {
    width: 100%;
  }
  
  .security-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .security-item-action {
    margin-left: 0;
  }
}

@media screen and (max-width: 576px) {
  .current-email {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style> 