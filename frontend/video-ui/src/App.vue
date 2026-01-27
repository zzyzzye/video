<script setup>
import { onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

// 监听路由变化，强制刷新组件
const handleRouteChange = (to, from) => {
  // 可以在这里添加额外的处理逻辑
};

onMounted(() => {
  router.beforeEach(handleRouteChange);
});

onUnmounted(() => {
  // 清理路由监听器
  const removeListener = router.beforeEach(() => {});
  removeListener();
});
</script>

<template>
  <router-view v-slot="{ Component }">
    <component :is="Component" :key="$route.fullPath" />
  </router-view>
</template>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: var(--bg-color);
  color: var(--text-color);
  overflow-x: hidden;
  width: 100%;
  max-width: 100%;
}

#app {
  /* text-align: left; */
  height: 100vh;
  overflow-x: hidden;
  width: 100%;
  max-width: 100%;
}
</style>
