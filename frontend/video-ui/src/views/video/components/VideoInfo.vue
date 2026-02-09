<template>
  <div class="video-info-overlay" :class="{ 'hidden': isCleanMode }">
    <div class="creator-row">
      <router-link :to="`/user/${videoData.creatorId}`" class="creator-name">
        @{{ videoData.creatorName }}
      </router-link>
      <span class="publish-time">· {{ videoData.publishTime }}</span>
    </div>
    
    <h1 class="video-title">{{ videoData.title }}</h1>
    
    <div class="video-description" :class="{ 'expanded': descriptionExpanded }">
      <span class="desc-text" ref="descTextRef">{{ videoData.description }}</span>
      <span 
        class="expand-btn" 
        v-if="showExpandBtn && !descriptionExpanded" 
        @click="descriptionExpanded = true"
      >...展开</span>
      <span 
        class="collapse-btn" 
        v-if="descriptionExpanded" 
        @click="descriptionExpanded = false"
      > 收起</span>
    </div>
    
    <div class="video-tags">
      <span class="tag" v-if="videoData.category">
        #{{ typeof videoData.category === 'object' ? videoData.category.name : videoData.category }}
      </span>
      <span class="tag" v-for="tag in videoData.tags?.slice(0, 3)" :key="tag.id || tag">
        #{{ typeof tag === 'object' ? tag.name : tag }}
      </span>
    </div>
    
    <div class="ai-actions">
      <router-link 
        v-if="videoData.collection" 
        :to="`/collection/${videoData.collection.id}`" 
        class="ai-btn collection-btn"
      >
        <svg viewBox="0 0 1024 1024" width="16" height="16">
          <path fill="currentColor" d="M880 112H144c-17.7 0-32 14.3-32 32v736c0 17.7 14.3 32 32 32h736c17.7 0 32-14.3 32-32V144c0-17.7-14.3-32-32-32zM368 744c0 4.4-3.6 8-8 8h-80c-4.4 0-8-3.6-8-8V280c0-4.4 3.6-8 8-8h80c4.4 0 8 3.6 8 8v464zm192-280c0 4.4-3.6 8-8 8h-80c-4.4 0-8-3.6-8-8V280c0-4.4 3.6-8 8-8h80c4.4 0 8 3.6 8 8v184zm192 72c0 4.4-3.6 8-8 8h-80c-4.4 0-8-3.6-8-8V280c0-4.4 3.6-8 8-8h80c4.4 0 8 3.6 8 8v256z"/>
        </svg>
        <span>{{ videoData.collection.name }}</span>
        <span class="collection-index">{{ videoData.collectionIndex }}/{{ videoData.collection.count }}</span>
      </router-link>
      
      <button class="ai-btn" @click="$emit('ai-summarize')">
        <svg viewBox="0 0 1024 1024" width="16" height="16">
          <path fill="currentColor" d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z"/>
          <path fill="currentColor" d="M464 336a48 48 0 1 0 96 0 48 48 0 1 0-96 0zm72 112h-48c-4.4 0-8 3.6-8 8v272c0 4.4 3.6 8 8 8h48c4.4 0 8-3.6 8-8V456c0-4.4-3.6-8-8-8z"/>
        </svg>
        <span>AI总结</span>
      </button>
      
      <button v-if="isPaused" class="ai-btn" @click="$emit('ai-recognize')">
        <svg viewBox="0 0 1024 1024" width="16" height="16">
          <path fill="currentColor" d="M942.2 486.2C847.4 286.5 704.1 186 512 186c-192.2 0-335.4 100.5-430.2 300.3a60.3 60.3 0 0 0 0 51.5C176.6 737.5 319.9 838 512 838c192.2 0 335.4-100.5 430.2-300.3 7.7-16.2 7.7-35 0-51.5zM512 766c-161.3 0-279.4-81.8-362.7-254C232.6 339.8 350.7 258 512 258c161.3 0 279.4 81.8 362.7 254C791.5 684.2 673.4 766 512 766zm-4-430c-97.2 0-176 78.8-176 176s78.8 176 176 176 176-78.8 176-176-78.8-176-176-176zm0 288c-61.9 0-112-50.1-112-112s50.1-112 112-112 112 50.1 112 112-50.1 112-112 112z"/>
        </svg>
        <span>识别画面</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue';

const props = defineProps({
  videoData: { type: Object, required: true },
  isPaused: Boolean,
  isCleanMode: Boolean
});

defineEmits(['ai-summarize', 'ai-recognize']);

const descriptionExpanded = ref(false);
const showExpandBtn = ref(false);
const descTextRef = ref(null);

// 检查描述文字是否溢出
const checkDescOverflow = async () => {
  await nextTick();
  if (descTextRef.value) {
    const el = descTextRef.value;
    showExpandBtn.value = el.scrollHeight > el.clientHeight || 
                          (props.videoData.description?.length > 60);
  }
};

watch(() => props.videoData.description, checkDescOverflow, { immediate: true });
</script>

<style scoped>
.video-info-overlay {
  position: absolute;
  left: 20px;
  bottom: 60px;
  max-width: 30%;
  z-index: 100;
  transition: opacity 0.3s, transform 0.3s;
  text-align: left;
}

.video-info-overlay.hidden {
  opacity: 0;
  transform: translateY(20px);
  pointer-events: none;
}

.creator-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.creator-name {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  text-decoration: none;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5);
}

.creator-name:hover {
  color: #FB7299;
}

.publish-time {
  color: rgba(255,255,255,0.7);
  font-size: 13px;
}

.video-title {
  font-size: 15px;
  font-weight: 500;
  color: #fff;
  margin: 0 0 8px 0;
  line-height: 1.5;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5);
  text-align: left;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.video-description {
  font-size: 13px;
  color: rgba(255,255,255,0.8);
  line-height: 1.5;
  margin-bottom: 8px;
  text-align: left;
}

.video-description:not(.expanded) .desc-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.video-description.expanded .desc-text {
  display: inline;
}

.desc-text {
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}

.expand-btn,
.collapse-btn {
  color: #fff;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}

.collapse-btn {
  color: rgba(255,255,255,0.7);
}

.video-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  padding: 4px 10px;
  background: rgba(255,255,255,0.15);
  border-radius: 4px;
  color: #fff;
  font-size: 12px;
  backdrop-filter: blur(4px);
  cursor: pointer;
  transition: background 0.2s;
}

.tag:hover {
  background: rgba(251,114,153,0.5);
}

.ai-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.ai-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(8px);
  border: none;
  border-radius: 20px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
}

.ai-btn:hover {
  background: rgba(0, 161, 214, 0.6);
}

.ai-btn svg {
  flex-shrink: 0;
}

.collection-index {
  opacity: 0.7;
  font-size: 12px;
}
</style>
