<template>
  <el-dialog 
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="AI 审核详情" 
    width="900px" 
    destroy-on-close
    @close="$emit('close')"
    append-to-body
  >
    <div v-if="detail" class="detail-content">
      <div class="detail-section" v-if="detail.video">
        <h3>视频信息</h3>
        <div class="video-detail">
          <el-image 
            :src="detail.video.thumbnail || '/placeholder.jpg'" 
            fit="cover" 
            style="width: 200px; height: 112px; border-radius: 8px;"
          >
            <template #error>
              <div class="image-error">
                <el-icon><Picture /></el-icon>
              </div>
            </template>
          </el-image>
          <div class="video-detail-info">
            <h4>{{ detail.video.title || '未知标题' }}</h4>
            <p>上传者: {{ detail.video.user?.username || '未知' }}</p>
            <p>上传时间: {{ detail.video.created_at ? formatDateTime(detail.video.created_at) : '未知' }}</p>
          </div>
        </div>
      </div>
      
      <div class="detail-section" v-else>
        <h3>视频信息</h3>
        <el-alert type="warning" :closable="false">
          视频信息加载失败
        </el-alert>
      </div>

      <el-divider />

      <div class="detail-section">
        <h3>审核结果</h3>
        <div class="result-summary">
          <div class="result-item">
            <span class="label">审核状态:</span>
            <el-tag :type="getStatusType(detail.status)">
              {{ getStatusText(detail.status) }}
            </el-tag>
          </div>
          <div class="result-item">
            <span class="label">审核结果:</span>
            <el-tag :type="getResultType(detail.result)">
              {{ getResultText(detail.result) }}
            </el-tag>
          </div>
          <div class="result-item">
            <span class="label">置信度:</span>
            <span class="value">{{ (detail.confidence * 100).toFixed(2) }}%</span>
          </div>
        </div>
      </div>

      <el-divider />

      <div class="detail-section">
        <h3>风险评分</h3>
        <div class="risk-detail">
          <div class="risk-item" v-for="risk in riskItems" :key="risk.name">
            <div class="risk-header">
              <span class="risk-name">{{ risk.label }}</span>
              <span class="risk-score" :class="getScoreLevel(risk.value)">
                {{ (risk.value * 100).toFixed(1) }}
              </span>
            </div>
            <el-progress 
              :percentage="risk.value * 100" 
              :color="getScoreColor(risk.value)"
            />
          </div>
        </div>
      </div>

      <el-divider v-if="detail.flagged_frames?.length > 0" />

      <div class="detail-section" v-if="detail.flagged_frames?.length > 0">
        <h3>问题帧 ({{ detail.flagged_frames.length }})</h3>
        <div class="flagged-frames">
          <div 
            v-for="(frame, index) in detail.flagged_frames" 
            :key="index" 
            class="frame-item"
          >
            <div class="frame-thumb-container" v-if="frame.image_url">
              <el-image 
                :src="frame.image_url" 
                fit="cover" 
                class="frame-thumb"
                :preview-src-list="[frame.image_url]"
              />
            </div>
            <div class="frame-info">
              <div class="frame-time">{{ formatTime(frame.timestamp) }}</div>
              <div class="frame-reason">{{ frame.reason || '检测到风险内容' }}</div>
              <div class="frame-scores" v-if="frame.scores">
                <el-tag size="small" type="danger" v-if="frame.scores.high > 0.5">高风险</el-tag>
                <el-tag size="small" type="warning" v-else-if="frame.scores.medium > 0.5">中风险</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>

      <el-divider />

      <div class="detail-actions" v-if="detail.status === 'completed'">
        <el-button type="primary" @click="$emit('submit-review')">提交人工审核</el-button>
        <el-button type="warning" @click="$emit('re-moderate')">重新 AI 审核</el-button>
        <el-button type="danger" @click="$emit('revoke-review')">撤销审核结果</el-button>
      </div>

      <el-divider v-if="detail.error_message" />

      <div class="detail-section" v-if="detail.error_message">
        <h3>错误信息</h3>
        <el-alert type="error" :closable="false">
          {{ detail.error_message }}
        </el-alert>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue';
import { Picture } from '@element-plus/icons-vue';

const props = defineProps({
  modelValue: Boolean,
  detail: Object,
  getStatusType: Function,
  getStatusText: Function,
  getResultType: Function,
  getResultText: Function,
  getScoreColor: Function,
  getScoreLevel: Function,
  formatDateTime: Function,
  formatTime: Function
});

defineEmits(['update:modelValue', 'close', 'submit-review', 'revoke-review', 're-moderate']);

const riskItems = computed(() => [
  { label: '低风险及以上 (Low+)', name: 'low', value: props.detail?.low_score || 0 },
  { label: '中风险及以上 (Medium+)', name: 'medium', value: props.detail?.medium_score || 0 },
  { label: '高风险 (High)', name: 'high', value: props.detail?.high_score || 0 }
]);
</script>

<style scoped>
.detail-content { padding: 10px; }
.detail-section { margin-bottom: 20px; }
.detail-section h3 { font-size: 16px; font-weight: 600; color: #18191c; margin: 0 0 16px 0; }
.video-detail { display: flex; gap: 16px; }
.video-detail-info h4 { font-size: 16px; font-weight: 500; margin: 0 0 12px 0; }
.video-detail-info p { font-size: 14px; color: #61666d; margin: 6px 0; }
.result-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.result-item { display: flex; flex-direction: column; gap: 8px; }
.result-item .label { font-size: 13px; color: #9499a0; }
.result-item .value { font-size: 18px; font-weight: 600; color: #18191c; }
.risk-detail { display: flex; flex-direction: column; gap: 16px; }
.risk-item { display: flex; flex-direction: column; gap: 8px; }
.risk-header { display: flex; justify-content: space-between; align-items: center; }
.risk-name { font-size: 14px; color: #61666d; }
.risk-score { font-size: 18px; font-weight: 600; }
.risk-score.low { color: #67c23a; }
.risk-score.medium { color: #e6a23c; }
.risk-score.high { color: #f56c6c; }
.flagged-frames { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.frame-item { display: flex; gap: 12px; padding: 12px; background: #f6f7f8; border-radius: 6px; border-left: 3px solid #f56c6c; }
.frame-thumb-container { width: 100px; height: 56px; flex-shrink: 0; }
.frame-thumb { width: 100%; height: 100%; border-radius: 4px; }
.frame-info { flex: 1; min-width: 0; }
.frame-time { font-size: 14px; font-weight: 600; color: #18191c; margin-bottom: 4px; }
.frame-reason { font-size: 12px; color: #61666d; margin-bottom: 4px; line-height: 1.4; }
.frame-scores { display: flex; gap: 4px; }
.detail-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 20px; }
.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #f5f5f5;
  color: #ccc;
  font-size: 32px;
}
</style>
