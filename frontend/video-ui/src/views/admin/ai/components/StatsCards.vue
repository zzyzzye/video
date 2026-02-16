<template>
  <div class="stats-cards">
    <div class="stat-card">
      <div class="stat-icon pending">
        <el-icon><Clock /></el-icon>
      </div>
      <div class="stat-info">
        <div class="stat-value">{{ stats?.pending || 0 }}</div>
        <div class="stat-label">待审核</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon processing">
        <el-icon><Loading /></el-icon>
      </div>
      <div class="stat-info">
        <div class="stat-value">{{ stats?.processing || 0 }}</div>
        <div class="stat-label">审核中</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon safe">
        <el-icon><CircleCheck /></el-icon>
      </div>
      <div class="stat-info">
        <div class="stat-value">{{ stats?.safe || 0 }}</div>
        <div class="stat-label">安全内容</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon unsafe">
        <el-icon><CircleClose /></el-icon>
      </div>
      <div class="stat-info">
        <div class="stat-value">{{ (stats?.unsafe || 0) + (stats?.uncertain || 0) }}</div>
        <div class="stat-label">风险内容</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Clock, Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue';

defineProps({
  stats: {
    type: Object,
    required: true,
    default: () => ({
      pending: 0,
      processing: 0,
      safe: 0,
      unsafe: 0
    })
  }
});
</script>

<style scoped>
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.stat-icon.pending {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.stat-icon.processing {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
}

.stat-icon.safe {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: #fff;
}

.stat-icon.unsafe {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: #fff;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #18191c;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #9499a0;
}
</style>
