<template>
  <footer class="app-footer">
    <div class="footer-content">
      <div class="footer-main">
        <div class="footer-logo">
          <div class="logo-placeholder">MP</div>
          <span>MindPalette</span>
        </div>
        
        <div class="footer-links">
          <div class="links-column">
            <h4>产品</h4>
            <ul>
              <li><a href="#">视频播放器</a></li>
              <li><a href="#">创作工具</a></li>
              <li><a href="#">企业版</a></li>
              <li><a href="#">定价</a></li>
            </ul>
          </div>
          
          <div class="links-column">
            <h4>资源</h4>
            <ul>
              <li><a href="#">下载应用</a></li>
              <li><a href="#">博客</a></li>
              <li><a href="#">开发者</a></li>
              <li><a href="#">帮助中心</a></li>
            </ul>
          </div>
          
          <div class="links-column">
            <h4>公司</h4>
            <ul>
              <li><a href="#">关于我们</a></li>
              <li><a href="#">招贤纳士</a></li>
              <li><a href="#">联系我们</a></li>
            </ul>
          </div>
          
          <div class="links-column">
            <h4>政策</h4>
            <ul>
              <li><a href="#">服务条款</a></li>
              <li><a href="#">隐私政策</a></li>
              <li><a href="#">社区准则</a></li>
              <li><a href="#">Cookie 政策</a></li>
            </ul>
          </div>
        </div>
      </div>
      
      <div class="footer-bottom">
        <div class="copyright">
          © {{ currentYear }} MindPalette. All rights reserved.
        </div>
        
        <div class="social-links">
          <a href="#" aria-label="微信" class="social-link">
            <el-icon><ChatDotRound /></el-icon>
          </a>
          <a href="#" aria-label="微博" class="social-link">
            <el-icon><Share /></el-icon>
          </a>
          <a href="#" aria-label="GitHub" class="social-link">
            <el-icon><Platform /></el-icon>
          </a>
        </div>
        
        <div class="language-selector">
          <el-dropdown trigger="click">
            <span class="language-text">
              <el-icon><Location /></el-icon>
              简体中文
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>简体中文</el-dropdown-item>
                <el-dropdown-item>繁體中文</el-dropdown-item>
                <el-dropdown-item>English</el-dropdown-item>
                <el-dropdown-item>日本語</el-dropdown-item>
                <el-dropdown-item>한국어</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue';
import { ChatDotRound, Share, Platform, Location } from '@element-plus/icons-vue';

const currentYear = computed(() => new Date().getFullYear());
</script>

<style scoped>
.app-footer {
  background-color: var(--bg-color); /* 使用主题变量 */
  color: var(--text-color); /* 使用主题变量 */
  padding: 48px 0 24px;
  width: 100%;
  box-sizing: border-box;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.footer-main {
  display: flex;
  flex-wrap: wrap;
  gap: 40px;
  margin-bottom: 48px;
}

.footer-logo {
  display: flex;
  align-items: center;
  margin-right: 40px;
}

.logo-placeholder {
  width: 32px;
  height: 32px;
  background-color: var(--accent-color); /* 使用主题变量 */
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  border-radius: 4px;
  margin-right: 8px;
}

.footer-logo span {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color); /* 使用主题变量 */
}

.footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 40px;
  flex: 1;
}

.links-column h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 16px;
  color: var(--text-color); /* 使用主题变量 */
}

.links-column ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.links-column li {
  margin-bottom: 8px;
}

.links-column a {
  color: var(--text-color-tertiary); /* 使用主题变量 */
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.links-column a:hover {
  color: var(--accent-color); /* 使用主题变量 */
}

.footer-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 24px;
  border-top: 1px solid var(--border-color); /* 使用主题变量 */
  flex-wrap: wrap;
  gap: 16px;
}

.copyright {
  color: var(--text-color-tertiary); /* 使用主题变量 */
  font-size: 13px;
}

.social-links {
  display: flex;
  gap: 16px;
}

.social-link {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: var(--bg-color-tertiary); /* 使用主题变量 */
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-color); /* 使用主题变量 */
  transition: background-color 0.2s;
}

.social-link:hover {
  background-color: var(--accent-color); /* 使用主题变量 */
}

.language-selector {
  display: flex;
  align-items: center;
}

.language-text {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-color-tertiary); /* 使用主题变量 */
  cursor: pointer;
  font-size: 14px;
}

.language-text:hover {
  color: var(--accent-color); /* 使用主题变量 */
}

:deep(.el-dropdown-menu) {
  background-color: var(--dropdown-bg); /* 使用主题变量 */
  border: none;
}

:deep(.el-dropdown-menu__item) {
  color: var(--text-color); /* 使用主题变量 */
}

:deep(.el-dropdown-menu__item:hover) {
  background-color: var(--dropdown-hover); /* 使用主题变量 */
}

@media (max-width: 1200px) {
  .app-footer {
    margin-left: 0;
  }
}

@media (max-width: 992px) {
  .app-footer {
    margin-left: 0;
  }
}

@media (max-width: 768px) {
  .app-footer {
    padding: 32px 0 16px;
    margin-left: 0;
  }
  
  .footer-content {
    padding: 0 16px;
  }
  
  .footer-main {
    flex-direction: column;
    gap: 32px;
  }
  
  .footer-logo {
    margin-right: 0;
  }
  
  .footer-links {
    gap: 24px;
  }
  
  .footer-bottom {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 576px) {
  .footer-links {
    flex-direction: column;
    gap: 24px;
  }
}
</style> 