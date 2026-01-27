<template>
  <div class="app-container">
    <header-component />
    <div class="main-content">
      <main class="page-content">
        <router-view />
      </main>
    </div>
    <footer-component />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import HeaderComponent from './components/Header.vue';
import FooterComponent from './components/Footer.vue';

const route = useRoute();
const isMobile = ref(false);

// 检测屏幕宽度变化
const checkScreenSize = () => {
  isMobile.value = window.innerWidth <= 768;
};

onMounted(() => {
  checkScreenSize();
  window.addEventListener('resize', checkScreenSize);
});

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize);
});
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  width: 100%;
  max-width: 100%;
  background-color: var(--bg-color);
  color: var(--text-color);
  overflow-x: hidden;
  box-sizing: border-box;
}

.main-content {
  display: flex;
  flex: 1;
  width: 100%;
  max-width: 100%;
  margin-top: 56px; /* Header height */
  overflow-x: hidden;
  box-sizing: border-box;
}

.page-content {
  flex: 1;
  padding: 16px 24px;
  overflow-y: auto;
  overflow-x: hidden;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  background-color: var(--bg-color);
  min-height: calc(100vh - 56px); /* Full height minus header */
}

@media (max-width: 768px) {
  .page-content {
    padding: 12px 16px;
  }
}

@media (max-width: 480px) {
  .page-content {
    padding: 8px 12px;
  }
}
</style> 