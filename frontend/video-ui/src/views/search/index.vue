<template>
  <div class="search-container">
    <h1>搜索结果: {{ searchQuery }}</h1>
    <div v-if="loading" class="loading">
      <el-skeleton :rows="5" animated />
    </div>
    <div v-else-if="results.length > 0" class="search-results">
      <p>找到 {{ results.length }} 个结果</p>
      <div class="result-list">
        <!-- 搜索结果将在这里显示 -->
        <div v-for="result in results" :key="result.id" class="result-item">
          {{ result.title }}
        </div>
      </div>
    </div>
    <div v-else class="no-results">
      <p>未找到相关结果</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const searchQuery = ref('');
const loading = ref(true);
const results = ref([]);

// 模拟搜索结果
const mockResults = [
  { id: 1, title: '视频 1' },
  { id: 2, title: '视频 2' },
  { id: 3, title: '视频 3' }
];

const performSearch = (query) => {
  loading.value = true;
  searchQuery.value = query;
  
  // 模拟API请求延迟
  setTimeout(() => {
    results.value = mockResults;
    loading.value = false;
  }, 1000);
};

// 监听路由参数变化
watch(() => route.query.q, (newQuery) => {
  if (newQuery) {
    performSearch(newQuery);
  }
});

onMounted(() => {
  if (route.query.q) {
    performSearch(route.query.q);
  } else {
    loading.value = false;
  }
});
</script>

<style scoped>
.search-container {
  padding: 20px;
}

.loading {
  margin-top: 20px;
}

.search-results {
  margin-top: 20px;
}

.result-list {
  margin-top: 10px;
}

.result-item {
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.no-results {
  margin-top: 20px;
  text-align: center;
  color: #909399;
}
</style> 