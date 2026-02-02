<template>
  <div class="subtitle-list-container">
    <!-- 顶部工具栏 -->
    <div class="subtitle-toolbar">
      <div class="toolbar-left">
        <span class="label">显示</span>
        <div class="tab-btn active">双字幕</div>
        <div class="tab-btn">主字幕</div>
        <div class="tab-btn">副字幕</div>
        <button class="swap-btn" @click="handleSwapSubtitles" title="交换主副字幕">
          <el-icon><Sort /></el-icon>
        </button>
      </div>
      <div class="toolbar-right">
        <span class="label">翻译:</span>
        <el-select v-model="translateLang" size="small" class="lang-select">
          <el-option label="中文" value="zh" />
          <el-option label="英语" value="en" />
          <el-option label="日语" value="ja" />
        </el-select>
        <el-button type="danger" size="small" class="start-btn">开始</el-button>
      </div>
    </div>

    <!-- 字幕列表区域 -->
    <div class="subtitle-list-wrapper">
      <!-- 字幕内容列表 -->
      <div class="subtitle-content-list">
        <div v-if="!subtitles || subtitles.length === 0" class="subtitle-empty">
          <div class="empty-title">暂无字幕</div>
          <div class="empty-desc">请先导入字幕文件，或在视频中添加字幕后再编辑</div>
        </div>
        <div
          v-for="(subtitle, index) in subtitles"
          :key="index"
          class="subtitle-item"
          :class="{ active: currentSubtitleIndex === index }"
          @click="$emit('select-subtitle', index)"
        >
          <!-- 最左侧：操作按钮 -->
          <div class="item-actions">
            <el-icon @click.stop="handleDelete(index)" title="删除"><Delete /></el-icon>
            <el-icon @click.stop="handleMerge(index)" title="合并"><Bottom /></el-icon>
            <el-icon @click.stop="handleAdd(index)" title="插入"><Plus /></el-icon>
          </div>

          <!-- 中间：时间信息区 -->
          <div class="item-time">
            <div class="time-row">
              <el-icon class="time-icon"><Top /></el-icon>
              <div class="time-value">{{ formatTime(subtitle.startTime) }}</div>
            </div>
            <div class="time-row">
              <el-icon class="time-icon"><Bottom /></el-icon>
              <div class="time-value">{{ formatTime(subtitle.endTime) }}</div>
            </div>
            <div class="time-row">
              <el-icon class="time-icon"><Timer /></el-icon>
              <div class="duration-value">{{ (subtitle.endTime - subtitle.startTime).toFixed(1) }}</div>
            </div>
            <div class="time-row">
              <span class="index-icon">#</span>
              <div class="item-index">{{ index }}</div>
            </div>
          </div>

          <!-- 右侧：字幕内容区 -->
          <div class="item-content">
            <div
              class="text-primary"
              contenteditable="true"
              spellcheck="false"
              @click.stop
              @mousedown.stop
              @input="updateSubtitleText(subtitle, 'text', $event)"
            >{{ subtitle.text }}</div>
            <div
              class="text-secondary"
              contenteditable="true"
              spellcheck="false"
              @click.stop
              @mousedown.stop
              @input="updateSubtitleText(subtitle, 'translation', $event)"
            >{{ subtitle.translation }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { Delete, Bottom, Plus, Top, Timer, Sort } from '@element-plus/icons-vue'

const props = defineProps({
  subtitles: {
    type: Array,
    default: () => []
  },
  currentSubtitleIndex: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits([
  'select-subtitle',
  'add-subtitle',
  'merge-subtitle',
  'delete-subtitle',
  'swap-subtitles'
])

const translateLang = ref('zh')

const updateSubtitleText = (subtitle, field, event) => {
  if (!subtitle || !field) return
  const value = event?.target?.innerText ?? ''
  subtitle[field] = value.replace(/\r\n/g, '\n')
}

// 监听当前字幕索引变化，自动滚动到顶部
watch(() => props.currentSubtitleIndex, (newIndex) => {
  nextTick(() => {
    const listContainer = document.querySelector('.subtitle-content-list')
    const subtitleItems = document.querySelectorAll('.subtitle-item')
    
    if (listContainer && subtitleItems.length > 0 && newIndex >= 0 && newIndex < subtitleItems.length) {
      const activeItem = subtitleItems[newIndex]
      // 每个字幕项高度是 90px，计算滚动位置让激活项显示在顶部
      const scrollTop = newIndex * 90
      listContainer.scrollTo({
        top: scrollTop,
        behavior: 'smooth' // 平滑滚动
      })
    }
  })
})

const formatTime = (seconds) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 1000)
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`
}

const handleAdd = (index) => {
  emit('add-subtitle', index)
}

const handleMerge = (index) => {
  emit('merge-subtitle', index)
}

const handleDelete = (index) => {
  emit('delete-subtitle', index)
}

const handleSwapSubtitles = () => {
  emit('swap-subtitles')
}
</script>

<style scoped lang="scss">
.subtitle-list-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1a1a1a;
}

.subtitle-toolbar {
  height: 30px;
  background: #1a1a1a;
  border-bottom: 1px solid #2a2a2a;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;

  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 0;

    .label {
      color: #999;
      font-size: 14px;
      margin-right: 12px;
    }

    .tab-btn {
      padding: 3px 12px;
      background: #2a2a2a;
      border: none;
      cursor: pointer;
      font-size: 14px;
      color: #999;
      transition: all 0.2s;
      user-select: none;
      position: relative;

      &:first-of-type {
        border-radius: 6px 0 0 6px;
      }

      &:nth-of-type(3) {
        border-radius: 0 6px 6px 0;
      }

      &:hover {
        background: #3a3a3a;
        color: #fff;
      }

      &.active {
        background: #c72626;
        color: #fff;
      }

      & + .tab-btn {
        border-left: 1px solid #1a1a1a;
      }
    }

    .swap-btn {
      margin-left: 12px;
      padding: 3px 12px;
      background: #2a2a2a;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      color: #999;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      justify-content: center;

      .el-icon {
        font-size: 18px;
      }

      &:hover {
        background: #3a3a3a;
        color: #fff;
      }

      &:active {
        transform: scale(0.95);
      }
    }
  }

  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 12px;

    .label {
      color: #999;
      font-size: 13px;
    }

    .lang-select {
      width: 140px;
    }

    .start-btn {
      background: #c72626;
      border-color: #c72626;
      color: #fff;
      padding: 8px 24px;
      font-weight: 500;

      &:hover {
        background: #d73636;
        border-color: #d73636;
      }
    }
  }
}

.subtitle-list-wrapper {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.subtitle-content-list {
  flex: 1;
  height: 100%;
  overflow-y: auto;
  background: #000;

  .subtitle-empty {
    padding: 24px 16px;
    color: #999;

    .empty-title {
      font-size: 14px;
      color: #fff;
      margin-bottom: 8px;
    }

    .empty-desc {
      font-size: 13px;
      color: #999;
      line-height: 1.6;
    }
  }

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: #0a0a0a;
  }

  &::-webkit-scrollbar-thumb {
    background: #3a3a3a;
    border-radius: 4px;

    &:hover {
      background: #4a4a4a;
    }
  }

  .subtitle-item {
    display: flex;
    border-bottom: 1px solid #1a1a2a;
    height: 90px;
    cursor: pointer;
    transition: all 0.2s;
    background: #000;

    &:hover {
      background: #0a0a0a;
    }

    &.active {
      .item-actions {
        background: rgba(86, 42, 178, 1);
      }

      .item-time {
        background: rgba(86, 42, 178, 1);
      }

      .item-content {
        background: rgba(86, 42, 178, 0.6);
      }
    }

    .item-actions {
      width: 35px;
      background: #1a1a1a;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 2px;
      padding: 4px 0;
      flex-shrink: 0;
      transition: all 0.2s;

      .el-icon {
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-size: 16px;
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.2s;

        &:hover {
          background: rgba(255, 255, 255, 0.25);
          transform: scale(1.05);
        }

        &:active {
          transform: scale(0.95);
        }
      }
    }

    .item-time {
      max-width: 110px;
      background: #1a1a1a;
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding: 6px 12px;
      gap: 2px;
      flex-shrink: 0;
      border-left: 0.1px solid #2a2a2a;
      transition: all 0.2s;

      .time-row {
        display: flex;
        align-items: center;
        gap: 8px;
        line-height: 1.4;
        font-size: 14px;
        color: white;

        .time-icon {
          width: 16px;
          height: 16px;
          flex-shrink: 0;
        }

        .index-icon {
          width: 16px;
          height: 16px;
          font-weight: 700;
          flex-shrink: 0;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .time-value {
          letter-spacing: 0.3px;
        }
      }
    }

    .item-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      background: #1a1a1a;
      transition: all 0.2s;

      .text-primary[contenteditable='true'],
      .text-secondary[contenteditable='true'] {
        outline: none;
        cursor: text;
      }

      .text-primary {
        flex: 1;
        height: 45px;
        color: #fff;
        font-size: 14px;
        line-height: 1.4;
        padding: 6px 12px;
        display: flex;
        align-items: center;
        border-top: 1px solid #2a2a3a;
      }

      .text-secondary {
        flex: 1;
        height: 45px;
        color: #888;
        font-size: 12px;
        line-height: 1.4;
        padding: 6px 12px;
        display: flex;
        align-items: center;
        border-top: 1px solid #2a2a3a;

      }
    }
  }
}

// Element Plus 样式覆盖
:deep(.el-input__wrapper) {
  background: #1a1a1a;
  border-color: #3a3a3a;
  box-shadow: none;

  &:hover {
    border-color: #4a4a4a;
  }
}

:deep(.el-input__inner) {
  color: #fff;
}

:deep(.el-select) {
  .el-input__wrapper {
    background: #1a1a1a;
    border-color: #3a3a3a;
  }
}
</style>
