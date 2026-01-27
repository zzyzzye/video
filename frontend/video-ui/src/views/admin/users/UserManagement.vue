<template>
  <div class="user-management-container">
    <PageHeader
      title="用户管理"
      :breadcrumb="[{ label: '管理后台' }, { label: '用户管理' }]"
    />

    <!-- 搜索和筛选区域 -->
    <div class="filter-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input
            v-model="searchQuery"
            placeholder="搜索用户名、昵称或邮箱"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="roleFilter" placeholder="角色筛选" clearable @change="handleFilter">
            <el-option label="普通用户" value="user" />
            <el-option label="VIP用户" value="vip" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="vipStatusFilter" placeholder="VIP状态" clearable @change="handleFilter">
            <el-option label="活跃VIP" value="active" />
            <el-option label="过期VIP" value="expired" />
            <el-option label="非VIP" value="none" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="loadUsers">刷新</el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 用户列表 -->
    <div class="table-section">
      <el-table
        :data="userList"
        style="width: 100%"
        v-loading="loading"
        element-loading-text="加载中..."
      >
        <el-table-column prop="avatar" label="头像" width="80">
          <template #default="scope">
            <el-avatar :size="40" :src="scope.row.avatar">
              {{ scope.row.username.charAt(0).toUpperCase() }}
            </el-avatar>
          </template>
        </el-table-column>

        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="last_name" label="昵称" width="120" />
        <el-table-column prop="email" label="邮箱" width="200" />

        <el-table-column prop="role_display" label="角色" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.role === 'vip' ? 'success' : 'info'">
              {{ scope.row.role_display }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="vip_level_display" label="VIP等级" width="100">
          <template #default="scope">
            <el-tag
              v-if="scope.row.is_vip"
              :type="getVipTagType(scope.row.vip_status)"
            >
              {{ scope.row.vip_level_display }}
            </el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="vip_expire_time" label="VIP到期时间" width="180">
          <template #default="scope">
            <span v-if="scope.row.vip_expire_time">
              {{ formatDate(scope.row.vip_expire_time) }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
              {{ scope.row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="注册时间" width="160">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="scope">
            <el-button
              v-if="!scope.row.is_vip"
              size="small"
              type="success"
              @click="openVipDialog(scope.row)"
            >
              设置VIP
            </el-button>
            <el-button
              v-else
              size="small"
              type="warning"
              @click="cancelVip(scope.row)"
            >
              取消VIP
            </el-button>
            <el-button
              size="small"
              :type="scope.row.is_active ? 'danger' : 'success'"
              @click="toggleUserActive(scope.row)"
            >
              {{ scope.row.is_active ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-section" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 设置VIP对话框 -->
    <el-dialog
      v-model="vipDialogVisible"
      title="设置VIP"
      width="400px"
    >
      <el-form :model="vipForm" label-width="100px">
        <el-form-item label="VIP等级">
          <el-select v-model="vipForm.vip_level" placeholder="选择VIP等级">
            <el-option label="青铜VIP" :value="1" />
            <el-option label="白银VIP" :value="2" />
            <el-option label="黄金VIP" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="购买月数">
          <el-input-number
            v-model="vipForm.months"
            :min="1"
            :max="12"
            :precision="0"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="vipDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmSetVip">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import request from '@/api/user'

// 响应式数据
const loading = ref(false)
const userList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const roleFilter = ref('')
const vipStatusFilter = ref('')
const vipDialogVisible = ref(false)
const selectedUser = ref(null)
const vipForm = ref({
  vip_level: 1,
  months: 1
})

// 加载用户列表
const loadUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }

    if (searchQuery.value) {
      params.search = searchQuery.value
    }

    if (roleFilter.value) {
      params.role = roleFilter.value
    }

    if (vipStatusFilter.value) {
      params.vip_status = vipStatusFilter.value
    }

    const response = await request.get('/users/admin-users/', { params })
    console.log('API Response:', response)
    userList.value = response.results || []
    total.value = response.total || 0
  } catch (error) {
    console.error('加载用户列表失败:', error)
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  loadUsers()
}

// 筛选处理
const handleFilter = () => {
  currentPage.value = 1
  loadUsers()
}

// 分页大小改变
const handleSizeChange = (newSize) => {
  pageSize.value = newSize
  currentPage.value = 1
  loadUsers()
}

// 页码改变
const handleCurrentChange = (newPage) => {
  currentPage.value = newPage
  loadUsers()
}

// 打开VIP设置对话框
const openVipDialog = (user) => {
  selectedUser.value = user
  vipForm.value = {
    vip_level: 1,
    months: 1
  }
  vipDialogVisible.value = true
}

// 确认设置VIP
const confirmSetVip = async () => {
  if (!selectedUser.value) return

  try {
    const response = await request.post(
      `/users/admin-users/${selectedUser.value.id}/set-vip/`,
      vipForm.value
    )

    ElMessage.success(response.detail)
    vipDialogVisible.value = false
    loadUsers() // 重新加载列表
  } catch (error) {
    console.error('设置VIP失败:', error)
    ElMessage.error(error.response?.data?.detail || '设置VIP失败')
  }
}

// 取消VIP
const cancelVip = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消用户 ${user.username} 的VIP状态吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await request.post(`/users/admin-users/${user.id}/cancel-vip/`)
    ElMessage.success(response.detail)
    loadUsers() // 重新加载列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消VIP失败:', error)
      ElMessage.error(error.response?.data?.detail || '取消VIP失败')
    }
  }
}

// 切换用户激活状态
const toggleUserActive = async (user) => {
  try {
    const action = user.is_active ? '禁用' : '启用'
    await ElMessageBox.confirm(
      `确定要${action}用户 ${user.username} 的账户吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await request.post(`/users/admin-users/${user.id}/toggle-active/`)
    ElMessage.success(response.detail)
    loadUsers() // 重新加载列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换用户状态失败:', error)
      ElMessage.error(error.response?.data?.detail || '操作失败')
    }
  }
}

// 获取VIP标签类型
const getVipTagType = (vipStatus) => {
  switch (vipStatus) {
    case 'active': return 'success'
    case 'expired': return 'warning'
    default: return 'info'
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 组件挂载时加载数据
onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.user-management-container {
  padding: 20px;
}

.filter-section {
  margin-bottom: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.table-section {
  margin-bottom: 20px;
}

.pagination-section {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.text-muted {
  color: #999;
}

:deep(.el-table .el-table__cell) {
  padding: 8px 0;
}

:deep(.el-dialog .el-form-item) {
  margin-bottom: 20px;
}
</style> 