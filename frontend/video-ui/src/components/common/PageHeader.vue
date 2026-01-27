<template>
  <div class="page-header">
    <div class="head-title">
      <div class="left">
        <h1>{{ title }}</h1>
        <ul class="breadcrumb">
          <li v-for="(item, index) in breadcrumb" :key="index">
            <template v-if="index > 0">
              <el-icon><ArrowRight /></el-icon>
            </template>
            <a :class="{ active: index === breadcrumb.length - 1 }" :href="item.path || '#'">
              {{ item.label }}
            </a>
          </li>
        </ul>
      </div>
      <div class="right" v-if="$slots.actions">
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ArrowRight } from '@element-plus/icons-vue';

defineProps({
  title: { type: String, required: true },
  breadcrumb: { 
    type: Array, 
    default: () => [] 
    // 格式: [{ label: '个人中心', path: '/user' }, { label: '消息通知' }]
  }
});
</script>

<style scoped>
.page-header {
  margin-bottom: 20px;
}

.head-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.head-title .left h1 {
  font-size: 36px;
  font-weight: 600;
  margin: 0 0 10px 0;
  color: #342E37;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  list-style: none;
  padding: 0;
  margin: 0;
}

.breadcrumb li {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #342E37;
}

.breadcrumb a {
  color: #aaa;
  text-decoration: none;
}

.breadcrumb a.active {
  color: #3C91E6;
}
</style>
