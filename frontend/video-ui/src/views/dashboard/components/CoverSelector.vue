<template>
  <div class="cover-selection">
    <div class="cover-options">
      <!-- 智能推荐封面（前3个） -->
      <div 
        v-for="(cover, index) in covers.slice(0, 3)" 
        :key="index"
        class="cover-option"
        :class="{ active: selectedIndex === index }"
        @click="selectCover(index)"
      >
        <img v-if="cover" :src="cover" alt="封面" />
        <div v-else class="cover-placeholder">
          <el-icon><Picture /></el-icon>
          <div class="cover-label">{{ placeholderLabels[index] }}</div>
        </div>
      </div>
      
      <!-- 自定义上传封面 -->
      <div 
        class="cover-option upload-cover"
        :class="{ active: selectedIndex === 3 }"
        @click="triggerUpload"
      >
        <img v-if="covers[3]" :src="covers[3]" alt="自定义封面" />
        <div v-else class="cover-upload-btn">
          <el-icon><Upload /></el-icon>
          <div class="cover-label">自定义封面</div>
        </div>
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          style="display: none"
          @change="handleFileChange"
        />
      </div>
    </div>
    <div class="cover-tip">
      好封面=收藏多|更多人观看作品 
      <a href="#" class="cover-example">优质封面示例</a>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Picture, Upload } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const props = defineProps({
  covers: {
    type: Array,
    default: () => [null, null, null, null]
  },
  selectedIndex: {
    type: Number,
    default: 0
  }
});

const emit = defineEmits(['update:selectedIndex', 'update:covers', 'select', 'upload']);

const fileInput = ref(null);
const placeholderLabels = ['横封面4:3', '竖封面3:4', '默认封面'];

const selectCover = (index) => {
  emit('update:selectedIndex', index);
  emit('select', index);
};

const triggerUpload = () => {
  fileInput.value?.click();
};

const handleFileChange = (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件');
    return;
  }
  
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过5MB');
    return;
  }
  
  const reader = new FileReader();
  reader.onload = (e) => {
    const newCovers = [...props.covers];
    newCovers[3] = e.target.result;
    emit('update:covers', newCovers);
    emit('update:selectedIndex', 3);
    emit('upload', e.target.result);
    ElMessage.success('封面上传成功');
  };
  reader.readAsDataURL(file);
  
  event.target.value = '';
};
</script>

<style scoped>
.cover-selection {
  width: 100%;
}

.cover-options {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 8px;
}

.cover-option {
  position: relative;
  aspect-ratio: 16/9;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid #e5e7eb;
  transition: all 0.3s;
  background: #000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.cover-option:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.cover-option.active {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.cover-option img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 2;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 32px;
  background: #000;
}

.cover-placeholder .cover-label,
.cover-upload-btn .cover-label {
  color: white;
  font-size: 11px;
  font-weight: 500;
  text-align: center;
}

.upload-cover {
  background: #000;
}

.cover-upload-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 32px;
  width: 100%;
  height: 100%;
}

.cover-upload-btn:hover {
  color: #3b82f6;
}

.cover-tip {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.5;
}

.cover-example {
  color: #3b82f6;
  text-decoration: none;
  margin-left: 8px;
}

.cover-example:hover {
  text-decoration: underline;
}

@media screen and (max-width: 768px) {
  .cover-options {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
