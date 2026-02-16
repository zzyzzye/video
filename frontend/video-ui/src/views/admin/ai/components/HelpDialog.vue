<template>
  <el-dialog 
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="AI 审核参数说明" 
    width="800px"
    append-to-body
  >
    <div class="help-content">
      <el-alert type="success" :closable="false" style="margin-bottom: 20px;">
        <template #title>
          <div style="font-size: 15px; line-height: 1.8;">
            <strong>核心概念</strong><br/>
            AI 模型会对视频的每一帧图片进行分类，输出风险等级的概率值。
          </div>
        </template>
      </el-alert>

      <h3 style="margin-top: 24px;">风险等级说明</h3>
      <div class="help-section">
        <div class="help-item">
          <h4>Neutral（正常内容）</h4>
          <p>图片是安全、正常内容的概率。</p>
        </div>
        <div class="help-item">
          <h4>Medium+（中风险及以上）</h4>
          <p>包含：明显暴露、裸露、性暗示等内容。</p>
        </div>
        <div class="help-item">
          <h4>High（高风险）</h4>
          <p>包含：色情、露骨、明确违规内容。</p>
        </div>
      </div>
    </div>
    <template #footer>
      <el-button type="primary" @click="$emit('update:modelValue', false)">我知道了</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
defineProps({
  modelValue: Boolean
});
defineEmits(['update:modelValue']);
</script>

<style scoped>
.help-content { padding: 10px; }
.help-item { margin-bottom: 16px; padding: 12px; background: #f8f9fa; border-radius: 4px; }
.help-item h4 { margin: 0 0 8px 0; }
.help-item p { margin: 0; font-size: 14px; color: #606266; }
</style>
