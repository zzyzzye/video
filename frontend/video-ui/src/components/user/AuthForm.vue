<template>
  <div class="auth-container" :class="{ 'register-active': isRegisterActive, 'forgot-password-active': isForgotPasswordActive }">
    <div class="forms-container">
      <div class="signin-signup">
        <!-- 登录表单 -->
        <el-form 
          ref="loginFormRef" 
          :model="loginForm" 
          :rules="loginRules" 
          class="sign-in-form" 
          @submit.prevent="submitLoginForm"
          @keyup.enter="submitLoginForm"
        >
          <h2 class="title animate__animated" :class="{'animate__fadeIn': !isRegisterActive, 'animate__fadeOut': isRegisterActive}">登录</h2>
          <el-form-item prop="username" class="animate__animated" :class="{'animate__fadeInUp': !isRegisterActive, 'animate__fadeOutUp': isRegisterActive}" :style="{'animation-delay': '0.1s'}">
            <el-input 
              v-model="loginForm.username" 
              placeholder="用户名/邮箱" 
              
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item prop="password" class="animate__animated" :class="{'animate__fadeInUp': !isRegisterActive, 'animate__fadeOutUp': isRegisterActive}" :style="{'animation-delay': '0.2s'}">
            <el-input 
              v-model="loginForm.password" 
              type="password" 
              placeholder="密码" 
              show-password
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item class="animate__animated" :class="{'animate__fadeInUp': !isRegisterActive, 'animate__fadeOutUp': isRegisterActive}" :style="{'animation-delay': '0.3s'}">
            <el-button type="primary" round @click="submitLoginForm" :loading="loading.login">登录</el-button>
          </el-form-item>
          <div class="form-options animate__animated" :class="{'animate__fadeInUp': !isRegisterActive, 'animate__fadeOutUp': isRegisterActive}" :style="{'animation-delay': '0.4s'}">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <el-link type="primary" @click="openForgotPasswordDialog">忘记密码?</el-link>
          </div>
        </el-form>

        <!-- 注册表单 -->
        <el-form 
          ref="registerFormRef" 
          :model="registerForm" 
          :rules="registerRules" 
          class="sign-up-form" 
          @submit.prevent="submitRegisterForm"
          @keyup.enter="submitRegisterForm"
        >
          <h2 class="title animate__animated" :class="{'animate__fadeIn': isRegisterActive, 'animate__fadeOut': !isRegisterActive}">注册</h2>
          <el-form-item prop="username" class="animate__animated" :class="{'animate__fadeInUp': isRegisterActive, 'animate__fadeOutUp': !isRegisterActive}" :style="{'animation-delay': '0.1s'}">
            <el-input 
              v-model="registerForm.username" 
              placeholder="用户名"
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item prop="email" class="animate__animated" :class="{'animate__fadeInUp': isRegisterActive, 'animate__fadeOutUp': !isRegisterActive}" :style="{'animation-delay': '0.2s'}">
            <el-input 
              v-model="registerForm.email" 
              placeholder="邮箱"
            >
              <template #prefix>
                <el-icon><Message /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item prop="password" class="animate__animated" :class="{'animate__fadeInUp': isRegisterActive, 'animate__fadeOutUp': !isRegisterActive}" :style="{'animation-delay': '0.3s'}">
            <el-input 
              v-model="registerForm.password" 
              type="password" 
              placeholder="密码" 
              show-password
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item prop="confirmPassword" class="animate__animated" :class="{'animate__fadeInUp': isRegisterActive, 'animate__fadeOutUp': !isRegisterActive}" :style="{'animation-delay': '0.4s'}">
            <el-input 
              v-model="registerForm.confirmPassword" 
              type="password" 
              placeholder="确认密码" 
              show-password
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item class="animate__animated" :class="{'animate__fadeInUp': isRegisterActive, 'animate__fadeOutUp': !isRegisterActive}" :style="{'animation-delay': '0.5s'}">
            <el-button type="primary" round @click="submitRegisterForm" :loading="loading.register">注册</el-button>
          </el-form-item>
          <div class="form-options animate__animated" :class="{'animate__fadeInUp': isRegisterActive, 'animate__fadeOutUp': !isRegisterActive}" :style="{'animation-delay': '0.6s'}">
            <el-checkbox v-model="agreeTerms">我同意<el-link type="primary">服务条款</el-link>和<el-link type="primary">隐私政策</el-link></el-checkbox>
          </div>
        </el-form>

        <!-- 忘记密码表单 -->
        <el-form 
          ref="forgotPasswordFormRef" 
          :model="forgotPasswordForm" 
          :rules="forgotPasswordRules" 
          class="forgot-password-form" 
          @submit.prevent="handleForgotPassword"
          @keyup.enter="handleForgotPassword"
        >
          <h2 class="title animate__animated" :class="{'animate__fadeIn': isForgotPasswordActive, 'animate__fadeOut': !isForgotPasswordActive}">重置密码</h2>
          <el-form-item prop="contact" class="animate__animated" :class="{'animate__fadeInUp': isForgotPasswordActive, 'animate__fadeOutUp': !isForgotPasswordActive}" :style="{'animation-delay': '0.1s'}">
            <el-input 
              v-model="forgotPasswordForm.contact" 
              placeholder="邮箱/手机号"
            >
              <template #prefix>
                <el-icon><Message /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item prop="code" class="animate__animated" :class="{'animate__fadeInUp': isForgotPasswordActive, 'animate__fadeOutUp': !isForgotPasswordActive}" :style="{'animation-delay': '0.2s'}">
            <div class="verification-code-wrapper">
              <el-input 
                v-model="forgotPasswordForm.code" 
                placeholder="验证码"
                class="code-input"
              >
                <template #prefix>
                  <el-icon><Key /></el-icon>
                </template>
              </el-input>
              <el-button 
                class="send-code-btn" 
                type="primary" 
                @click="handleSendVerificationCode" 
                :disabled="isSendingCode"
              >
                {{ sendCodeButtonText }}
              </el-button>
            </div>
          </el-form-item>
          <el-form-item prop="newPassword" class="animate__animated" :class="{'animate__fadeInUp': isForgotPasswordActive, 'animate__fadeOutUp': !isForgotPasswordActive}" :style="{'animation-delay': '0.3s'}">
            <el-input 
              v-model="forgotPasswordForm.newPassword" 
              type="password" 
              placeholder="新密码" 
              show-password
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item prop="confirmNewPassword" class="animate__animated" :class="{'animate__fadeInUp': isForgotPasswordActive, 'animate__fadeOutUp': !isForgotPasswordActive}" :style="{'animation-delay': '0.4s'}">
            <el-input 
              v-model="forgotPasswordForm.confirmNewPassword" 
              type="password" 
              placeholder="确认新密码" 
              show-password
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item class="animate__animated" :class="{'animate__fadeInUp': isForgotPasswordActive, 'animate__fadeOutUp': !isForgotPasswordActive}" :style="{'animation-delay': '0.5s'}">
            <el-button type="primary" round @click="handleForgotPassword" :loading="loading.forgotPassword" class="full-width-btn">确认重置</el-button>
          </el-form-item>
          <div class="form-options animate__animated" :class="{'animate__fadeInUp': isForgotPasswordActive, 'animate__fadeOutUp': !isForgotPasswordActive}" :style="{'animation-delay': '0.6s'}">
            <div class="back-to-login-btn" @click="backToLogin">
              <el-icon><ArrowLeft /></el-icon>
              <span>返回登录</span>
            </div>
          </div>
        </el-form>
      </div>
    </div>

    <div class="panels-container">
      <!-- 左侧面板 - 登录时显示 -->
      <div class="panel left-panel">
        <div class="content">
          <h3 class="animate__animated" :class="{'animate__fadeInLeft': !isRegisterActive && !isForgotPasswordActive, 'animate__fadeOutLeft': isRegisterActive || isForgotPasswordActive}">新用户?</h3>
          <p class="animate__animated" :class="{'animate__fadeInLeft': !isRegisterActive && !isForgotPasswordActive, 'animate__fadeOutLeft': isRegisterActive || isForgotPasswordActive}" :style="{'animation-delay': '0.1s'}">欢迎加入我们的视频社区，立即注册开始分享精彩内容！</p>
          <el-button class="btn-transparent animate__animated" :class="{'animate__fadeInLeft': !isRegisterActive && !isForgotPasswordActive, 'animate__fadeOutLeft': isRegisterActive || isForgotPasswordActive}" :style="{'animation-delay': '0.2s'}" @click="toggleForm">
            注册
            <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
        </div>
        <div class="panel-illustration animate__animated" :class="{'animate__fadeInLeft': !isRegisterActive && !isForgotPasswordActive, 'animate__fadeOutLeft': isRegisterActive || isForgotPasswordActive}" :style="{'animation-delay': '0.3s','margin-left':'10%'}">
          <el-icon :size="100"><VideoPlay /></el-icon>
        </div>
      </div>

      <!-- 右侧面板 - 注册时显示 -->
      <div class="panel right-panel">
        <div class="content">
          <h3 class="animate__animated" :class="{'animate__fadeInRight': isRegisterActive && !isForgotPasswordActive, 'animate__fadeOutRight': !isRegisterActive || isForgotPasswordActive}">已有账号?</h3>
          <p class="animate__animated" :class="{'animate__fadeInRight': isRegisterActive && !isForgotPasswordActive, 'animate__fadeOutRight': !isRegisterActive || isForgotPasswordActive}" :style="{'animation-delay': '0.1s'}">登录您的账号，继续探索精彩视频世界！</p>
          <el-button class="btn-transparent animate__animated" :class="{'animate__fadeInRight': isRegisterActive && !isForgotPasswordActive, 'animate__fadeOutRight': !isRegisterActive || isForgotPasswordActive}" :style="{'animation-delay': '0.2s'}" @click="toggleForm">
            登录
            <el-icon class="el-icon--right"><ArrowLeft /></el-icon>
          </el-button>
        </div>
        <div class="panel-illustration animate__animated" :class="{'animate__fadeInRight': isRegisterActive && !isForgotPasswordActive, 'animate__fadeOutRight': !isRegisterActive || isForgotPasswordActive}" :style="{'animation-delay': '0.3s'}">
          <el-icon :size="100"><Film /></el-icon>
        </div>
      </div>

      <!-- 底部面板 - 忘记密码时显示 -->
      <div class="panel bottom-panel">
        <div class="content">
          <h3 class="animate__animated" :class="{'animate__fadeInUp': isForgotPasswordActive, 'animate__fadeOutDown': !isForgotPasswordActive}">找回密码</h3>
          <p class="animate__animated" :class="{'animate__fadeInUp': isForgotPasswordActive, 'animate__fadeOutDown': !isForgotPasswordActive}" :style="{'animation-delay': '0.1s'}">通过邮箱或手机号验证，快速重置您的密码</p>
        </div>
        <div class="panel-illustration animate__animated" :class="{'animate__fadeInUp': isForgotPasswordActive, 'animate__fadeOutDown': !isForgotPasswordActive}" :style="{'animation-delay': '0.2s'}">
          <el-icon :size="100"><Lock /></el-icon>
        </div>
      </div>
    </div>
    
    <!-- 背景动画元素 -->
    <div class="circles">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { login, register, getUserInfo, sendVerificationCode, changePasswordWithCode } from '@/api/user';
import { setToken, setRefreshToken, removeToken } from '@/utils/auth';
import { ElMessage } from 'element-plus';
import { User, Lock, Message, VideoPlay, Film, ArrowRight, ArrowLeft, Key } from '@element-plus/icons-vue';
import { useUserStore } from '@/store/user';
import 'animate.css';

const router = useRouter();
const route = useRoute();
const isRegisterActive = ref(false);
const isForgotPasswordActive = ref(false);
const loginFormRef = ref(null);
const registerFormRef = ref(null);
const forgotPasswordFormRef = ref(null);
const rememberMe = ref(false);
const agreeTerms = ref(false);
const userStore = useUserStore();

// 忘记密码相关
const isSendingCode = ref(false);
const sendCodeButtonText = ref('发送验证码');
let countdownTimer = null;

// 加载状态
const loading = reactive({
  login: false,
  register: false,
  forgotPassword: false
});

// 忘记密码表单
const forgotPasswordForm = reactive({
  contact: '',
  code: '',
  newPassword: '',
  confirmNewPassword: ''
});

// 忘记密码表单验证规则
const forgotPasswordRules = {
  contact: [
    { required: true, message: '请输入您的邮箱或手机号', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能小于8个字符', trigger: 'blur' }
  ],
  confirmNewPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== forgotPasswordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ]
};

// 打开忘记密码表单
const openForgotPasswordDialog = () => {
  isForgotPasswordActive.value = true;
  isRegisterActive.value = false;
};

// 返回登录
const backToLogin = () => {
  isForgotPasswordActive.value = false;
  if (forgotPasswordFormRef.value) {
    forgotPasswordFormRef.value.resetFields();
  }
  clearInterval(countdownTimer);
  sendCodeButtonText.value = '发送验证码';
  isSendingCode.value = false;
};

// 发送验证码
const handleSendVerificationCode = async () => {
  if (!forgotPasswordForm.contact) {
    ElMessage.warning('请输入邮箱或手机号');
    return;
  }

  isSendingCode.value = true;
  sendCodeButtonText.value = '发送中...';

  try {
    await sendVerificationCode({ contact: forgotPasswordForm.contact, usage: 'reset_password' });
    ElMessage.success('验证码已发送，请注意查收');

    let countdown = 60;
    sendCodeButtonText.value = `${countdown}秒后重试`;
    countdownTimer = setInterval(() => {
      countdown--;
      if (countdown > 0) {
        sendCodeButtonText.value = `${countdown}秒后重试`;
      } else {
        clearInterval(countdownTimer);
        sendCodeButtonText.value = '发送验证码';
        isSendingCode.value = false;
      }
    }, 1000);

  } catch (error) {
    ElMessage.error('验证码发送失败，请稍后再试');
    sendCodeButtonText.value = '发送验证码';
    isSendingCode.value = false;
  }
};

// 处理忘记密码
const handleForgotPassword = () => {
  forgotPasswordFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.forgotPassword = true;
      try {
        await changePasswordWithCode({
          contact: forgotPasswordForm.contact,
          code: forgotPasswordForm.code,
          new_password: forgotPasswordForm.newPassword
        });
        ElMessage.success('密码重置成功，请使用新密码登录');
        backToLogin();
      } catch (error) {
        ElMessage.error('密码重置失败，请稍后再试');
      } finally {
        loading.forgotPassword = false;
      }
    }
  });
};

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
});

// 注册表单数据
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
});

// 登录表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' }
  ]
};

// 注册表单验证规则
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名长度不能小于3个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
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
          
          // 常见密码检查（简单示例）
          const commonPasswords = ['password', '12345678', 'qwerty123', '11111111', '88888888'];
          if (commonPasswords.includes(value.toLowerCase())) {
            callback(new Error('请使用不常见的密码'));
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
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ]
};

// 根据URL参数设置初始模式
const initFormMode = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const mode = urlParams.get('mode');
  isRegisterActive.value = mode === 'register';
};

// 监听路由变化
// watch(
//   () => route.query.mode,
//   (newMode) => {
//     isRegisterActive.value = newMode === 'register';
//   }
// );

// 切换表单
const toggleForm = () => {
  // 如果在忘记密码页面，先返回登录
  if (isForgotPasswordActive.value) {
    backToLogin();
    return;
  }
  
  // 切换状态
  isRegisterActive.value = !isRegisterActive.value;
  
  // 更新URL，但不触发路由导航
  const newUrl = isRegisterActive.value 
    ? `${window.location.pathname}?mode=register` 
    : window.location.pathname;
  window.history.replaceState({}, '', newUrl);
};

// 提交登录表单
const submitLoginForm = () => {
  loginFormRef.value.validate((valid) => {
    if (valid) {
      handleLogin();
    }
  });
};

// 提交注册表单
const submitRegisterForm = () => {
  registerFormRef.value.validate((valid) => {
    if (valid) {
      if (!agreeTerms.value) {
        ElMessage.warning('请同意服务条款和隐私政策');
        return;
      }
      handleRegister();
    }
  });
};

// 处理登录
const handleLogin = async () => {
  try {
    loading.login = true;
    const response = await login({
      username: loginForm.username,
      password: loginForm.password
    });
    
    if (!response || !response.access) {
      ElMessage.error('登录响应缺少访问令牌');
      console.error('Missing access token in response:', response);
      return;
    }
    
    // 存储token
    setToken(response.access);
    // 存储刷新令牌
    if (response.refresh) {
      setRefreshToken(response.refresh);
    }
    
    if (rememberMe.value) {
      localStorage.setItem('remember_username', loginForm.username);
    } else {
      localStorage.removeItem('remember_username');
    }
    
    // 获取用户信息
    try {
      const userInfo = await getUserInfo();
      
      // 确保用户ID存在
      if (!userInfo || !userInfo.id) {
        console.error('User info missing ID:', userInfo);
        ElMessage.error('获取用户信息失败，请重新登录');
        return;
      }
      
      // 设置用户信息到store
      userStore.loginAction(userInfo);
      
      // 直接将完整用户信息存储到localStorage
      localStorage.setItem('user_role', userInfo.role || 'user');
      
      ElMessage.success('登录成功');
      
      // 如果有重定向URL，则跳转到该URL，否则跳转到首页
      const urlParams = new URLSearchParams(window.location.search);
      const redirectUrl = urlParams.get('redirect') || '/';
      router.push(redirectUrl);
    } catch (error) {
      console.error('Failed to get user info:', error);
      ElMessage.error('获取用户信息失败，请重新登录');
      // 登录失败，清除token
      removeToken();
    }
  } catch (error) {
    console.error('Login error:', error);
    
    if (error.response && error.response.data) {
      if (error.response.data.detail) {
        ElMessage.error(error.response.data.detail);
      } else if (typeof error.response.data === 'object') {
        // 处理可能的字段错误
        const errorMessages = [];
        for (const key in error.response.data) {
          if (Array.isArray(error.response.data[key])) {
            errorMessages.push(...error.response.data[key]);
          } else {
            errorMessages.push(error.response.data[key]);
          }
        }
        
        if (errorMessages.length > 0) {
          ElMessage({
            message: errorMessages.join('<br>'),
            type: 'error',
            dangerouslyUseHTMLString: true,
            duration: 5000,
            showClose: true
          });
        } else {
          ElMessage.error('登录失败，请检查用户名和密码');
        }
      } else {
        ElMessage.error('登录失败，请检查用户名和密码');
      }
    } else {
      ElMessage.error('登录失败，请稍后再试');
    }
  } finally {
    loading.login = false;
  }
};

// 处理注册
const handleRegister = async () => {
  try {
    loading.register = true;
    await register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
      password2: registerForm.confirmPassword
    });
    
    ElMessage.success('注册成功，请登录');
    isRegisterActive.value = false; // 切换到登录表单
    // 自动填充登录表单
    loginForm.username = registerForm.username;
  } catch (error) {
    console.error('Register error:', error);
    // 处理后端返回的错误信息
    if (error.response && error.response.data) {
      const errorData = error.response.data;
      
      // 处理password2字段错误
      if (errorData.password2) {
        const password2Error = Array.isArray(errorData.password2) ? 
          errorData.password2.join('<br>') : errorData.password2;
        ElMessage({
          message: password2Error,
          type: 'error',
          dangerouslyUseHTMLString: true,
          duration: 5000,
          showClose: true
        });
      }
      // 处理密码验证错误
      else if (errorData.password) {
        if (Array.isArray(errorData.password)) {
          // 使用更友好的错误展示
          ElMessage({
            message: errorData.password.join('<br>'),
            type: 'error',
            dangerouslyUseHTMLString: true,
            duration: 5000,
            showClose: true
          });
        } else {
          ElMessage.error(errorData.password);
        }
      } 
      // 处理用户名错误
      else if (errorData.username) {
        const usernameError = Array.isArray(errorData.username) ? 
          errorData.username.join('<br>') : errorData.username;
        ElMessage({
          message: usernameError,
          type: 'error',
          dangerouslyUseHTMLString: true,
          duration: 5000,
          showClose: true
        });
      }
      // 处理邮箱错误
      else if (errorData.email) {
        const emailError = Array.isArray(errorData.email) ? 
          errorData.email.join('<br>') : errorData.email;
        ElMessage({
          message: emailError,
          type: 'error',
          dangerouslyUseHTMLString: true,
          duration: 5000,
          showClose: true
        });
      }
      // 处理其他错误
      else if (errorData.detail) {
        ElMessage.error(errorData.detail);
      }
      // 处理未知错误
      else {
        ElMessage.error('注册失败，请检查输入信息');
      }
    } else {
      ElMessage.error('注册失败，请检查网络连接');
    }
  } finally {
    loading.register = false;
  }
};

// 初始化时检查是否有保存的用户名
const initSavedUsername = () => {
  const savedUsername = localStorage.getItem('remember_username');
  if (savedUsername) {
    loginForm.username = savedUsername;
    rememberMe.value = true;
  }
};

// 组件挂载时执行
onMounted(() => {
  initFormMode();
  initSavedUsername();
});
</script>

<style scoped>
@import 'animate.css';

.auth-container {
  position: relative;
  width: 100%;
  min-height: 100vh;
  background-color: var(--el-bg-color);
  overflow: hidden;
}

.forms-container {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
}

.signin-signup {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  left: 75%;
  width: 50%;
  transition: all 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  display: grid;
  grid-template-columns: 1fr;
  z-index: 5;
}

.el-form {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 0 5rem;
  transition: all 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  overflow: hidden;
  grid-column: 1 / 2;
  grid-row: 1 / 2;
  width: 100%;
  max-width: 450px;
  margin: 0 auto;
}

.sign-up-form {
  opacity: 0;
  z-index: 1;
  transform: translateX(100%);
  transition: all 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  left: 0;
}

.sign-in-form {
  z-index: 2;
  transform: translateX(0);
  transition: all 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  left: 0;
}

.forgot-password-form {
  opacity: 0;
  z-index: 1;
  transform: translateY(100%);
  transition: all 1.2s cubic-bezier(0.19, 1, 0.22, 1);
}

.title {
  font-size: 2.5rem;
  color: var(--el-text-color-primary);
  margin-bottom: 30px;
  text-align: center;
  font-weight: 600;
}

.el-form-item {
  width: 100%;
  margin-bottom: 25px;
}

.el-form-item :deep(.el-input__wrapper) {
  padding: 0 15px;
  height: 50px;
  border-radius: 25px;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  cursor: text;
}

.el-form-item :deep(.el-input__wrapper:hover) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.el-form-item :deep(.el-input__inner) {
  font-size: 16px;
  cursor: text;
}

.el-form-item :deep(.el-input__prefix) {
  cursor: text;
}

.el-form-item :deep(.el-button) {
  width: 100%;
  height: 50px;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 600;
  margin-top: 10px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.el-form-item :deep(.el-button:hover) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

/* 确保按钮整个区域可点击 */
.full-width-btn {
  display: block !important;
  width: 100% !important;
}

.full-width-btn :deep(span) {
  width: 100%;
  display: block;
}

/* 返回登录按钮样式 */
.back-to-login-btn {
  cursor: pointer !important;
  padding: 8px 16px;
  transition: all 0.3s ease;
  color: var(--el-color-primary);
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
  user-select: none;
}

.back-to-login-btn:hover {
  transform: translateX(-3px);
  opacity: 0.8;
}

.back-to-login-btn .el-icon {
  font-size: 16px;
}

.back-to-login-btn span {
  cursor: pointer;
}

.form-options {
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-top: 15px;
  font-size: 14px;
}

.panels-container {
  position: absolute;
  height: 100%;
  width: 100%;
  top: 0;
  left: 0;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
}

.auth-container:before {
  content: "";
  position: absolute;
  height: 2400px;
  width: 2400px;
  top: -10%;
  right: 48%;
  transform: translateY(-50%);
  background-image: linear-gradient(-45deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
  transition: transform 1.2s cubic-bezier(0.19, 1, 0.22, 1), right 1.2s cubic-bezier(0.19, 1, 0.22, 1), top 1.2s cubic-bezier(0.19, 1, 0.22, 1), left 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  border-radius: 50%;
  z-index: 6;
  box-shadow: 0 0 50px rgba(0, 0, 0, 0.2);
  will-change: transform, right, top, left;
}

.auth-container.register-active:before {
  transform: translate(100%, -50%);
  right: 52%;
}

.auth-container.forgot-password-active:before {
  transform: translateY(-50%);
  top: 90%;
  bottom: auto;
  right: 48%;
  left: auto;
}

/* 背景动画圆形 */
.circles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 1;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(-45deg, var(--el-color-primary-light-5) 0%, var(--el-color-primary-light-7) 100%);
  opacity: 0.3;
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -50px;
  left: -50px;
  animation: float 15s infinite alternate ease-in-out;
}

.circle-2 {
  width: 300px;
  height: 300px;
  top: -50px;
  right: -50px;
  animation: float 12s infinite alternate-reverse ease-in-out;
}

@keyframes float {
  0% {
    transform: translate(0, 0) rotate(0deg);
  }
  100% {
    transform: translate(50px, 50px) rotate(10deg);
  }
}

.panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  z-index: 6;
  position: relative;
  height: 100%;
}

.left-panel {
  pointer-events: all;
  padding: 3rem 17% 2rem 12%;
  align-items: flex-start;
  text-align: left;
}

.right-panel {
  pointer-events: none;
  padding: 3rem 12% 2rem 17%;
  align-items: flex-end;
  text-align: right;
}

.right-panel .content {
  margin-left: auto;
  margin-right: 0;
}

.panel .content {
  color: #fff;
  transition: transform 1.2s cubic-bezier(0.19, 1, 0.22, 1), opacity 0.6s ease;
  transition-delay: 0.2s;
  position: relative;
  z-index: 7;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  margin-bottom: 2rem;
}

.left-panel .content {
  margin-right: auto;
}

.right-panel .panel-illustration {
  margin-left: auto;
  margin-right: 10%;
}

.panel h3 {
  font-weight: 600;
  line-height: 1;
  font-size: 1.8rem;
  margin-bottom: 10px;
}

.panel p {
  font-size: 1rem;
  padding: 0.7rem 0;
  margin-bottom: 20px;
}

.panel-illustration {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
  transition: transform 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  transition-delay: 0.2s;
  margin: 2rem 0;
  position: relative;
  z-index: 7;
}

.panel-illustration .el-icon {
  filter: drop-shadow(0 5px 15px rgba(0, 0, 0, 0.25));
  opacity: 0.9;
  font-size: 100px;
  transition: all 0.3s ease;
}

.panel-illustration:hover .el-icon {
  transform: scale(1.1);
  filter: drop-shadow(0 8px 20px rgba(0, 0, 0, 0.3));
}

.left-panel .panel-illustration {
  margin-left: auto;
  margin-right: 10%;
}

.right-panel .panel-illustration {
  /* margin-left: 10%; */
  margin-right: auto;
}

.btn-transparent {
  margin: 0;
  background: transparent;
  border: 2px solid #fff;
  color: #fff;
  font-weight: 600;
  padding: 10px 20px;
  border-radius: 30px;
  font-size: 16px;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.btn-transparent:hover {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  border-color: #fff;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.15);
}

.btn-transparent:active {
  transform: translateY(0);
}

.right-panel .panel-illustration,
.right-panel .content {
  transform: translateX(800px);
}

/* 动画 */
.auth-container.register-active .signin-signup {
  left: 25%;
}

.auth-container.register-active .sign-up-form {
  opacity: 1;
  z-index: 2;
  transform: translateX(0);
}

.auth-container.register-active .sign-in-form {
  opacity: 0;
  z-index: 1;
  transform: translateX(-100%);
}

.auth-container.register-active .right-panel .panel-illustration,
.auth-container.register-active .right-panel .content {
  transform: translateX(0);
}

.auth-container.register-active .left-panel .panel-illustration,
.auth-container.register-active .left-panel .content {
  transform: translateX(-800px);
}

.auth-container.register-active .right-panel {
  pointer-events: all;
}

.auth-container.register-active .left-panel {
  pointer-events: none;
}

/* 忘记密码激活状态 */
.auth-container.forgot-password-active .signin-signup {
  top: 50%;
  left: 70%;
}

.auth-container.forgot-password-active .sign-in-form {
  opacity: 0;
  z-index: 1;
  transform: translateY(-100%);
}

.auth-container.forgot-password-active .forgot-password-form {
  opacity: 1;
  z-index: 2;
  transform: translateY(0);
}

.auth-container.forgot-password-active .left-panel,
.auth-container.forgot-password-active .right-panel {
  pointer-events: none;
}

.auth-container.forgot-password-active .left-panel .panel-illustration,
.auth-container.forgot-password-active .left-panel .content,
.auth-container.forgot-password-active .right-panel .panel-illustration,
.auth-container.forgot-password-active .right-panel .content {
  opacity: 0;
  transform: scale(0.8);
}

.auth-container.forgot-password-active .bottom-panel {
  pointer-events: all;
}

.auth-container.forgot-password-active .bottom-panel .panel-illustration,
.auth-container.forgot-password-active .bottom-panel .content {
  transform: translateY(0);
}

/* 底部面板样式 */
.bottom-panel {
  position: absolute;
  bottom: 20%;
  left: 5%;
  width: 35%;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  z-index: 6;
  pointer-events: none;
  text-align: left;
  padding: 2rem;
}

.bottom-panel .content {
  color: #fff;
  transition: transform 1.2s cubic-bezier(0.19, 1, 0.22, 1), opacity 0.6s ease;
  transition-delay: 0.2s;
  position: relative;
  z-index: 7;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  margin-bottom: 2rem;
}

.bottom-panel .panel-illustration,
.bottom-panel .content {
  transform: translateY(800px);
}

.bottom-panel .panel-illustration {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  color: white;
  transition: transform 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  transition-delay: 0.2s;
  position: relative;
  z-index: 7;
}

.bottom-panel .panel-illustration .el-icon {
  filter: drop-shadow(0 8px 20px rgba(0, 0, 0, 0.4));
  opacity: 1;
  font-size: 80px;
  transition: all 0.3s ease;
}

.bottom-panel .panel-illustration:hover .el-icon {
  transform: scale(1.1) rotate(5deg);
  filter: drop-shadow(0 12px 25px rgba(0, 0, 0, 0.5));
}

/* 验证码输入框样式 */
.verification-code-wrapper {
  width: 100%;
  display: flex;
  gap: 10px;
  align-items: center;
}

.verification-code-wrapper .code-input {
  flex: 1;
}

.verification-code-wrapper .send-code-btn {
  height: 50px;
  border-radius: 25px;
  padding: 0 25px;
  font-weight: 600;
  white-space: nowrap;
  transition: all 0.3s ease;
}

.verification-code-wrapper .send-code-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.verification-code-wrapper .send-code-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 870px) {
  .auth-container {
    min-height: 800px;
    height: 100vh;
  }
  
  .signin-signup {
    width: 100%;
    top: 95%;
    transform: translate(-50%, -100%);
    transition: 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  }
  
  .signin-signup,
  .auth-container.register-active .signin-signup {
    left: 50%;
  }
  
  .sign-up-form {
    transform: translateY(100%);
    transition: all 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  }
  
  .sign-in-form {
    transform: translateY(0);
    transition: all 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  }
  
  .auth-container.register-active .sign-up-form {
    transform: translateY(0);
  }
  
  .auth-container.register-active .sign-in-form {
    transform: translateY(-100%);
  }
  
  .panels-container {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr 2fr 1fr;
  }
  
  .panel {
    flex-direction: row;
    justify-content: space-around;
    align-items: center;
    padding: 2.5rem 8%;
    grid-column: 1 / 2;
    text-align: center;
  }
  
  .left-panel, .right-panel {
    align-items: center;
    text-align: center;
  }
  
  .left-panel .content, 
  .right-panel .content {
    padding-right: 0;
    text-align: center;
  }
  
  .right-panel .btn-transparent,
  .left-panel .btn-transparent {
    margin: 0 auto;
  }
  
  .right-panel {
    grid-row: 3 / 4;
  }
  
  .left-panel {
    grid-row: 1 / 2;
  }
  
  .panel-illustration {
    transition: transform 1.2s cubic-bezier(0.19, 1, 0.22, 1);
    transition-delay: 0.2s;
  }
  
  .panel .content {
    padding-right: 15%;
    transition: transform 1.2s cubic-bezier(0.19, 1, 0.22, 1);
    transition-delay: 0.2s;
  }
  
  .panel h3 {
    font-size: 1.2rem;
  }
  
  .panel p {
    font-size: 0.7rem;
    padding: 0.5rem 0;
  }
  
  .auth-container:before {
    width: 2000px;
    height: 2000px;
    top: initial;
    bottom: 72%;
    right: initial;
    left: 50%;
    transform: translateX(-50%);
    transition: 1.2s cubic-bezier(0.19, 1, 0.22, 1);
    will-change: transform, bottom;
  }
  
  .auth-container.register-active:before {
    bottom: 28%;
    transform: translateX(-50%) translateY(100%);
    transition: 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  }
  
  .auth-container.forgot-password-active:before {
    bottom: 8%;
    transform: translateX(-50%) translateY(-120%);
    transition: 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  }
  
  .auth-container.forgot-password-active .signin-signup {
    top: 50%;
    transform: translate(-50%, -50%);
  }
  
  .auth-container.forgot-password-active .bottom-panel .panel-illustration,
  .auth-container.forgot-password-active .bottom-panel .content {
    transform: translateX(0);
  }
  
  .auth-container.forgot-password-active .left-panel .panel-illustration,
  .auth-container.forgot-password-active .left-panel .content,
  .auth-container.forgot-password-active .right-panel .panel-illustration,
  .auth-container.forgot-password-active .right-panel .content {
    opacity: 0;
    transform: scale(0.8);
  }
  
  .bottom-panel {
    bottom: 10%;
    width: 90%;
  }
  
  .bottom-panel::before {
    width: 400px;
    height: 400px;
  }
  
  .verification-code-wrapper {
    flex-direction: column;
    gap: 15px;
  }
  
  .verification-code-wrapper .send-code-btn {
    width: 100%;
  }
  
  .auth-container.register-active .left-panel .panel-illustration,
  .auth-container.register-active .left-panel .content {
    transform: translateY(-300px);
  }
  
  .auth-container.register-active .right-panel .panel-illustration,
  .auth-container.register-active .right-panel .content {
    transform: translateY(0px);
  }
  
  .right-panel .panel-illustration,
  .right-panel .content {
    transform: translateY(300px);
  }
  
  .auth-container.register-active .signin-signup {
    top: 5%;
    transform: translate(-50%, 0);
  }
  
  .circle-1 {
    width: 400px;
    height: 400px;
    bottom: -100px;
    left: -100px;
  }
  
  .circle-2 {
    width: 300px;
    height: 300px;
    top: -50px;
    right: -50px;
  }
}

@media (max-width: 570px) {
  .el-form {
    padding: 0 1.5rem;
  }
  
  .panel-illustration {
    display: none;
  }
  
  .panel .content {
    padding: 0.5rem 1rem;
  }
  
  .auth-container {
    padding: 1.5rem;
  }
  
  .auth-container:before {
    width: 1800px;
    height: 1800px;
    bottom: 72%;
    left: 50%;
    transform: translateX(-50%);
    transition: 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  }
  
  .auth-container.register-active:before {
    transform: translateX(-50%) translateY(100%);
    bottom: 20%;
    transition: 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  }
  
  .auth-container.forgot-password-active:before {
    top: 0;
    bottom: auto;
    left: 50%;
    transform: translateX(-50%) translateY(-50%);
    transition: 1.2s cubic-bezier(0.19, 1, 0.22, 1);
  }
  
  .auth-container.forgot-password-active .signin-signup {
    left: 50%;
  }
  
  .form-options {
    flex-direction: column;
    align-items: center;
    gap: 10px;
  }
  
  .circle-1, .circle-2 {
    opacity: 0.2;
  }
  
  .bottom-panel {
    bottom: 5%;
    width: 95%;
  }
  
  .bottom-panel::before {
    width: 350px;
    height: 350px;
  }
  
  .bottom-panel .panel-illustration .el-icon {
    font-size: 60px;
  }
  
  .verification-code-wrapper .send-code-btn {
    padding: 0 20px;
    font-size: 14px;
  }
}

/* 添加动画持续时间自定义 */
.animate__animated {
  --animate-duration: 0.6s;
}

/* 修复图标和输入框之间的间距 */
.el-form-item :deep(.el-input__prefix) {
  margin-right: 5px;
}

.el-form-item :deep(.el-input__prefix-inner) {
  display: flex;
  align-items: center;
}

.el-form-item :deep(.el-input__prefix .el-icon) {
  margin-right: 0;
  font-size: 18px;
}

.right-panel .btn-transparent {
  margin-left: auto;
}
</style> 