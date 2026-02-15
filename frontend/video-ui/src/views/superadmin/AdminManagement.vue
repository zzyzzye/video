<template>
  <div class="admin-management">
    <PageHeader 
      title="管理员管理" 
      :breadcrumb="[
        { label: '超级管理员', path: '/superadmin/monitor' },
        { label: '管理员管理' }
      ]"
    >
      <template #actions>
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加管理员
        </el-button>
      </template>
    </PageHeader>

    <div class="content-wrapper">
      <!-- 搜索和筛选 -->
      <div class="filter-section">
        <el-input
          v-model="searchQuery"
          placeholder="搜索用户名、邮箱"
          style="width: 300px;"
          clearable
          @clear="loadAdmins"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select v-model="roleFilter" placeholder="角色筛选" style="width: 150px;" @change="loadAdmins">
          <el-option label="全部" value="" />
          <el-option label="管理员" value="admin" />
          <el-option label="超级管理员" value="superadmin" />
        </el-select>

        <el-button type="primary" @click="loadAdmins">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>

      <!-- 管理员列表 -->
      <el-table 
        v-loading="loading"
        :data="adminList" 
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
      >
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column label="用户信息" min-width="200">
          <template #default="{ row }">
            <div class="user-info">
              <el-avatar :size="40" :src="row.avatar" />
              <div class="user-details">
                <div class="username">{{ row.username }}</div>
                <div class="email">{{ row.email }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="角色" width="150" align="center">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="last_login" label="最后登录" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.last_login) }}
          </template>
        </el-table-column>

        <el-table-column prop="date_joined" label="加入时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.date_joined) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              @click="editAdmin(row)"
              :disabled="row.role === 'superadmin' && !isSuperAdmin"
            >
              编辑
            </el-button>
            
            <el-button 
              :type="row.is_active ? 'warning' : 'success'" 
              size="small" 
              @click="toggleStatus(row)"
              :disabled="row.role === 'superadmin' && !isSuperAdmin"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            
            <el-popconfirm
              title="确定要删除此管理员吗？"
              @confirm="deleteAdmin(row)"
              :disabled="row.role === 'superadmin'"
            >
              <template #reference>
                <el-button 
                  type="danger" 
                  size="small"
                  :disabled="row.role === 'superadmin'"
                >
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadAdmins"
          @current-change="loadAdmins"
        />
      </div>
    </div>

    <!-- 添加/编辑管理员对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑管理员' : '添加管理员'"
      width="500px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username" v-if="!isEdit">
          <el-input v-model="formData.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="请输入邮箱" />
        </el-form-item>

        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input 
            v-model="formData.password" 
            type="password" 
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" placeholder="请选择角色" style="width: 100%;">
            <el-option label="管理员" value="admin" />
            <el-option label="超级管理员" value="superadmin" v-if="isSuperAdmin" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Search } from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import service from '@/api/user';
import { useUserStore } from '@/store/user';

const userStore = useUserStore();
const isSuperAdmin = computed(() => userStore.role === 'superadmin');

const loading = ref(false);
const submitting = ref(false);
const searchQuery = ref('');
const roleFilter = ref('');
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);
const adminList = ref([]);

const dialogVisible = ref(false);
const isEdit = ref(false);
const formRef = ref(null);
const formData = ref({
  username: '',
  email: '',
  password: '',
  role: 'admin',
  is_active: true
});

const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 30, message: '用户名长度在 3 到 30 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
};

const loadAdmins = async () => {
  loading.value = true;
  try {
    const response = await service({
      url: '/users/admins/',
      method: 'get',
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        search: searchQuery.value,
        role: roleFilter.value
      }
    });
    
    adminList.value = response.results || [];
    total.value = response.count || 0;
  } catch (error) {
    console.error('加载管理员列表失败:', error);
    ElMessage.error('加载管理员列表失败');
  } finally {
    loading.value = false;
  }
};

const showAddDialog = () => {
  isEdit.value = false;
  dialogVisible.value = true;
};

const editAdmin = (row) => {
  isEdit.value = true;
  formData.value = {
    id: row.id,
    username: row.username,
    email: row.email,
    role: row.role,
    is_active: row.is_active
  };
  dialogVisible.value = true;
};

const submitForm = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    
    submitting.value = true;
    try {
      if (isEdit.value) {
        await service({
          url: `/users/admins/${formData.value.id}/`,
          method: 'put',
          data: {
            email: formData.value.email,
            role: formData.value.role,
            is_active: formData.value.is_active
          }
        });
        ElMessage.success('更新管理员成功');
      } else {
        await service({
          url: '/users/admins/',
          method: 'post',
          data: formData.value
        });
        ElMessage.success('添加管理员成功');
      }
      
      dialogVisible.value = false;
      loadAdmins();
    } catch (error) {
      console.error('操作失败:', error);
      ElMessage.error(error.response?.data?.detail || '操作失败');
    } finally {
      submitting.value = false;
    }
  });
};

const toggleStatus = async (row) => {
  try {
    await service({
      url: `/users/admins/${row.id}/toggle-status/`,
      method: 'post'
    });
    
    ElMessage.success(`${row.is_active ? '禁用' : '启用'}成功`);
    loadAdmins();
  } catch (error) {
    console.error('操作失败:', error);
    ElMessage.error('操作失败');
  }
};

const deleteAdmin = async (row) => {
  try {
    await service({
      url: `/users/admins/${row.id}/`,
      method: 'delete'
    });
    
    ElMessage.success('删除成功');
    loadAdmins();
  } catch (error) {
    console.error('删除失败:', error);
    ElMessage.error('删除失败');
  }
};

const resetForm = () => {
  formData.value = {
    username: '',
    email: '',
    password: '',
    role: 'admin',
    is_active: true
  };
  formRef.value?.resetFields();
};

const getRoleType = (role) => {
  const types = {
    'superadmin': 'danger',
    'admin': 'warning',
    'user': 'info'
  };
  return types[role] || 'info';
};

const getRoleLabel = (role) => {
  const labels = {
    'superadmin': '超级管理员',
    'admin': '管理员',
    'user': '普通用户'
  };
  return labels[role] || role;
};

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

onMounted(() => {
  loadAdmins();
});
</script>

<style scoped>
.admin-management {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 70px);
}

.content-wrapper {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.filter-section {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.username {
  font-weight: 600;
  color: #303133;
}

.email {
  font-size: 12px;
  color: #909399;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
