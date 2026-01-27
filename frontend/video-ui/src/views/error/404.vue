<template>
  <div class="not-found">
    <div class="not-found-content">
      <h1>404</h1>
      <h2>页面不存在</h2>
      <p>抱歉，您访问的页面不存在或已被删除。</p>
      <el-button type="primary" @click="goHome">返回首页</el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

const goHome = () => {
  router.push('/');
};
</script>

<style scoped>
.not-found {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
  text-align: center;
}

.not-found-content {
  max-width: 500px;
}

h1 {
  font-size: 120px;
  margin: 0;
  color: #409eff;
}

h2 {
  font-size: 30px;
  margin-top: 0;
}

p {
  font-size: 18px;
  color: #606266;
  margin-bottom: 30px;
}
</style> 