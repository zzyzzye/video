<template>
  <el-dialog 
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :title="title"
    width="600px"
    @close="$emit('close')"
    append-to-body
  >
    <el-form :model="config" label-width="140px">
      <el-form-item label="检测级别">
        <el-select v-model="config.threshold_level" style="width: 100%;">
          <el-option value="low" label="低风险及以上（Low+）">
            <div class="option-content">
              <span>低风险及以上（Low+）</span>
              <el-tag type="info" size="small">宽松</el-tag>
            </div>
          </el-option>
          <el-option value="medium" label="中风险及以上（Medium+）">
            <div class="option-content">
              <span>中风险及以上（Medium+）</span>
              <el-tag type="warning" size="small">推荐</el-tag>
            </div>
          </el-option>
          <el-option value="high" label="高风险（High）">
            <div class="option-content">
              <span>高风险（High）</span>
              <el-tag type="danger" size="small">严格</el-tag>
            </div>
          </el-option>
        </el-select>
        <div class="form-tip">选择用哪个累积概率来判断是否有问题。推荐使用"中风险及以上"</div>
      </el-form-item>
      
      <el-form-item label="置信度阈值">
        <el-slider 
          v-model="config.threshold" 
          :min="0" 
          :max="1" 
          :step="0.05"
          :format-tooltip="(val) => `${(val * 100).toFixed(0)}%`"
          show-input
          :input-size="'small'"
        />
        <div class="form-tip">当选定级别的概率超过此阈值时，该帧会被标记为问题帧。值越高越严格</div>
      </el-form-item>
      
      <el-form-item label="抽帧频率">
        <el-input-number 
          v-model="config.fps" 
          :min="1" 
          :max="10" 
          :step="1"
          style="width: 100%;"
        />
        <div class="form-tip">每秒抽取多少帧进行检测。值越大检测越精细，但耗时越长</div>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="$emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" :loading="loading" @click="$emit('confirm')">
          <el-icon><Cpu /></el-icon> 开始审核
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { Cpu } from '@element-plus/icons-vue';

defineProps({
  modelValue: Boolean,
  title: String,
  config: Object,
  loading: Boolean
});

defineEmits(['update:modelValue', 'close', 'confirm']);
</script>

<style scoped>
.option-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  margin-top: 4px;
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
