import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import pinia from './store';
import { useUserStore } from './store/user';
import { useNotificationStore } from './store/notification';
import ElementPlus from 'element-plus';
import zhCn from 'element-plus/dist/locale/zh-cn.mjs';
import 'element-plus/dist/index.css';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
import './style.css';
import './styles/theme.css';
import 'animate.css';

const app = createApp(App);

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

app.use(pinia)
   .use(router)
   .use(ElementPlus, { size: 'default', locale: zhCn })
   .mount('#app');

const userStore = useUserStore();

if (userStore.isLoggedIn) {
  const notificationStore = useNotificationStore();
  notificationStore.init();
}
