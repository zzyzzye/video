<template>
  <div class="stats-grid">
    <div 
      v-for="(item, index) in statsItems" 
      :key="item.key"
      :class="['stat-card', item.className]"
      class="animate-slide-up" 
      :style="{ animationDelay: `${(index + 1) * 0.1}s` }"
    >
      <div class="stat-icon">
        <el-icon><component :is="item.icon" /></el-icon>
      </div>
      <div class="stat-content">
        <div class="stat-value">{{ formatNumber(stats[item.key]) }}</div>
        <div class="stat-label">{{ item.label }}</div>
      </div>
      <div class="stat-bg-icon">
        <el-icon><component :is="item.icon" /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { VideoCamera, Star, User, View } from '@element-plus/icons-vue';

defineProps({
  stats: {
    type: Object,
    required: true,
    default: () => ({
      videoCount: 0,
      likeCount: 0,
      followerCount: 0,
      viewCount: 0
    })
  }
});

const statsItems = [
  { key: 'videoCount', label: '作品数量', icon: VideoCamera, className: 'video' },
  { key: 'likeCount', label: '获赞数量', icon: Star, className: 'like' },
  { key: 'followerCount', label: '粉丝数量', icon: User, className: 'follower' },
  { key: 'viewCount', label: '总播放量', icon: View, className: 'view' }
];

// 格式化数字
const formatNumber = (num) => {
  if (!num && num !== 0) return '0';
  if (num >= 100000000) {
    return (num / 100000000).toFixed(1) + '亿';
  } else if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k';
  }
  return num.toString();
};
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  position: relative;
  padding: 28px;
  background: #fff;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 20px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  border: 1px solid #e8e8e8;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: #d0d0d0;
}

/* 图标容器 - 不同颜色 */
.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s;
}

.stat-card.video .stat-icon {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
}

.stat-card.like .stat-icon {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
}

.stat-card.follower .stat-icon {
  background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%);
}

.stat-card.view .stat-icon {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
}

.stat-card:hover .stat-icon {
  transform: scale(1.05);
}

.stat-icon .el-icon {
  font-size: 32px;
}

.stat-card.video .stat-icon .el-icon {
  color: #4f46e5;
}

.stat-card.like .stat-icon .el-icon {
  color: #f59e0b;
}

.stat-card.follower .stat-icon .el-icon {
  color: #7c3aed;
}

.stat-card.view .stat-icon .el-icon {
  color: #10b981;
}

/* 内容区域 */
.stat-content {
  flex: 1;
  z-index: 1;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

/* 背景装饰图标 */
.stat-bg-icon {
  position: absolute;
  right: -15px;
  bottom: -15px;
  opacity: 0.03;
  z-index: 0;
}

.stat-bg-icon .el-icon {
  font-size: 100px;
  color: #000;
}

/* 动画 */
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

.animate-slide-up {
  animation: slideUp 0.6s ease-out both;
}

/* 响应式 */
@media screen and (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media screen and (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .stat-card {
    padding: 20px;
  }
  
  .stat-icon {
    width: 56px;
    height: 56px;
  }
  
  .stat-icon .el-icon {
    font-size: 28px;
  }
  
  .stat-value {
    font-size: 28px;
  }
  
  .stat-label {
    font-size: 13px;
  }
}

@media screen and (max-width: 576px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
