<template>
  <el-dialog
    v-model="visible"
    title="举报视频"
    width="500px"
    :before-close="handleClose"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
      <el-form-item label="举报原因" prop="reason">
        <el-select v-model="form.reason" placeholder="请选择举报原因" style="width: 100%">
          <el-option label="违法违规" value="illegal" />
          <el-option label="色情低俗" value="vulgar" />
          <el-option label="血腥暴力" value="violence" />
          <el-option label="垃圾广告" value="spam" />
          <el-option label="侵权" value="copyright" />
          <el-option label="虚假误导" value="misleading" />
          <el-option label="人身攻击" value="harassment" />
          <el-option label="其他" value="other" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="详细描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          placeholder="请详细描述举报原因（选填）"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          提交举报
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import service from '@/api/user';

const props = defineProps({
  show: Boolean,
  videoId: [String, Number]
});

const emit = defineEmits(['update:show', 'success']);

const visible = ref(false);
const loading = ref(false);
const formRef = ref(null);

const form = ref({
  reason: '',
  description: ''
});

const rules = {
  reason: [
    { required: true, message: '请选择举报原因', trigger: 'change' }
  ]
};

watch(() => props.show, (val) => {
  visible.value = val;
  if (val) {
    form.value = {
      reason: '',
      description: ''
    };
  }
});

watch(visible, (val) => {
  if (!val) {
    emit('update:show', false);
  }
});

const handleClose = () => {
  visible.value = false;
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    
    loading.value = true;
    try {
      await service({
        url: `/videos/videos/${props.videoId}/report/`,
        method: 'post',
        data: {
          video: props.videoId,
          reason: form.value.reason,
          description: form.value.description
        }
      });
      
      ElMessage.success('举报成功，我们会尽快处理');
      emit('success');
      handleClose();
    } catch (error) {
      const msg = error.response?.data?.error || 
                  error.response?.data?.detail || 
                  '举报失败，请稍后重试';
      ElMessage.error(msg);
    } finally {
      loading.value = false;
    }
  });
};
</script>

<style scoped>
:deep(.el-dialog__header) {
  border-bottom: 1px solid #eee;
  padding: 16px 20px;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-dialog__footer) {
  border-top: 1px solid #eee;
  padding: 12px 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
