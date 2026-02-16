<template>
  <div class="permission-management">
    <PageHeader 
      title="权限管理" 
      :breadcrumb="[
        { label: '超级管理员', path: '/superadmin/monitor' },
        { label: '权限管理' }
      ]"
    >
      <template #actions>
        <el-button type="primary" @click="showRoleDialog(null)">
          <el-icon><Plus /></el-icon>
          创建角色
        </el-button>
      </template>
    </PageHeader>

    <div class="content-wrapper">
      <el-tabs v-model="activeTab" class="tabs-container">
        <!-- 角色管理 -->
        <el-tab-pane label="角色管理" name="roles">
          <el-table 
            v-loading="loading"
            :data="roleList" 
            style="width: 100%"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="name" label="角色名称" min-width="200" />
            <el-table-column label="权限数量" width="120" align="center">
              <template #default="{ row }">
                <el-tag type="info">{{ row.permissions.length }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="user_count" label="用户数量" width="120" align="center">
              <template #default="{ row }">
                <el-tag type="success">{{ row.user_count }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="300" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="showRoleDialog(row)">
                  编辑
                </el-button>
                <el-button type="info" size="small" @click="viewRoleUsers(row)">
                  查看用户
                </el-button>
                <el-popconfirm
                  title="确定要删除此角色吗？"
                  @confirm="deleteRole(row.id)"
                >
                  <template #reference>
                    <el-button type="danger" size="small">
                      删除
                    </el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 权限列表 -->
        <el-tab-pane label="权限列表" name="permissions">
          <div class="permissions-container">
            <el-collapse v-model="activePermissions">
              <el-collapse-item 
                v-for="(perms, app) in permissionsByApp" 
                :key="app"
                :name="app"
              >
                <template #title>
                  <div class="collapse-title">
                    <span class="app-name">{{ getAppName(app) }}</span>
                    <el-tag type="info" size="small">{{ perms.length }} 个权限</el-tag>
                  </div>
                </template>
                
                <el-table :data="perms" style="width: 100%">
                  <el-table-column prop="id" label="ID" width="80" />
                  <el-table-column prop="name" label="权限名称" min-width="200" />
                  <el-table-column prop="codename" label="权限代码" min-width="200" />
                  <el-table-column label="模型" width="150">
                    <template #default="{ row }">
                      {{ row.content_type.model }}
                    </template>
                  </el-table-column>
                </el-table>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-tab-pane>

        <!-- 用户权限 -->
        <el-tab-pane label="用户权限" name="user-permissions">
          <div class="user-search">
            <el-input
              v-model="userSearch"
              placeholder="输入用户 ID 查询"
              style="width: 300px;"
              @keyup.enter="loadUserPermissions"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="loadUserPermissions">
              查询
            </el-button>
          </div>

          <div v-if="currentUser" class="user-permissions-detail">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="用户 ID">{{ currentUser.id }}</el-descriptions-item>
              <el-descriptions-item label="用户名">{{ currentUser.username }}</el-descriptions-item>
              <el-descriptions-item label="邮箱" :span="2">{{ currentUser.email }}</el-descriptions-item>
            </el-descriptions>

            <div class="section">
              <div class="section-header">
                <h3>所属角色</h3>
                <el-button type="primary" size="small" @click="showAssignGroupDialog">
                  分配角色
                </el-button>
              </div>
              <el-tag 
                v-for="group in userPermissions.groups" 
                :key="group.id"
                type="success"
                closable
                @close="removeUserGroup(group.id)"
                style="margin-right: 10px; margin-bottom: 10px;"
              >
                {{ group.name }} ({{ group.permissions.length }} 个权限)
              </el-tag>
              <el-empty v-if="!userPermissions.groups || userPermissions.groups.length === 0" 
                description="未分配角色" 
                :image-size="80" 
              />
            </div>

            <div class="section">
              <div class="section-header">
                <h3>直接权限</h3>
                <el-button type="primary" size="small" @click="showAssignPermissionDialog">
                  分配权限
                </el-button>
              </div>
              <el-tag 
                v-for="perm in userPermissions.direct_permissions" 
                :key="perm.id"
                type="info"
                style="margin-right: 10px; margin-bottom: 10px;"
              >
                {{ perm.name }}
              </el-tag>
              <el-empty v-if="!userPermissions.direct_permissions || userPermissions.direct_permissions.length === 0" 
                description="未分配直接权限" 
                :image-size="80" 
              />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 角色编辑对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="isEditRole ? '编辑角色' : '创建角色'"
      width="700px"
      @close="resetRoleForm"
    >
      <el-form :model="roleForm" label-width="100px">
        <el-form-item label="角色名称">
          <el-input v-model="roleForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        
        <el-form-item label="权限">
          <el-transfer
            v-model="roleForm.permissions"
            :data="allPermissionsForTransfer"
            :titles="['可用权限', '已选权限']"
            filterable
            filter-placeholder="搜索权限"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRole" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 角色用户列表对话框 -->
    <el-dialog
      v-model="roleUsersDialogVisible"
      title="角色用户列表"
      width="600px"
    >
      <el-table :data="roleUsers" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="150" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 分配角色对话框 -->
    <el-dialog
      v-model="assignGroupDialogVisible"
      title="分配角色"
      width="500px"
    >
      <el-checkbox-group v-model="selectedGroups">
        <el-checkbox 
          v-for="role in roleList" 
          :key="role.id" 
          :label="role.id"
          style="display: block; margin-bottom: 10px;"
        >
          {{ role.name }}
        </el-checkbox>
      </el-checkbox-group>

      <template #footer>
        <el-button @click="assignGroupDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="assignGroups" :loading="assigning">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 分配权限对话框 -->
    <el-dialog
      v-model="assignPermissionDialogVisible"
      title="分配权限"
      width="700px"
    >
      <el-transfer
        v-model="selectedPermissions"
        :data="allPermissionsForTransfer"
        :titles="['可用权限', '已选权限']"
        filterable
        filter-placeholder="搜索权限"
      />

      <template #footer>
        <el-button @click="assignPermissionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="assignPermissions" :loading="assigning">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Plus, Search } from '@element-plus/icons-vue';
import PageHeader from '@/components/common/PageHeader.vue';
import service from '@/api/user';

const loading = ref(false);
const saving = ref(false);
const assigning = ref(false);
const activeTab = ref('roles');
const activePermissions = ref([]);

const roleList = ref([]);
const permissionsByApp = ref({});
const userSearch = ref('');
const currentUser = ref(null);
const userPermissions = ref({
  groups: [],
  direct_permissions: [],
  all_permissions: []
});

const roleDialogVisible = ref(false);
const isEditRole = ref(false);
const roleForm = ref({
  id: null,
  name: '',
  permissions: []
});

const roleUsersDialogVisible = ref(false);
const roleUsers = ref([]);

const assignGroupDialogVisible = ref(false);
const selectedGroups = ref([]);

const assignPermissionDialogVisible = ref(false);
const selectedPermissions = ref([]);

const allPermissionsForTransfer = computed(() => {
  const result = [];
  for (const app in permissionsByApp.value) {
    for (const perm of permissionsByApp.value[app]) {
      result.push({
        key: perm.id,
        label: `${perm.name} (${perm.codename})`,
        disabled: false
      });
    }
  }
  return result;
});

const loadRoles = async () => {
  loading.value = true;
  try {
    const response = await service({
      url: '/users/roles/',
      method: 'get'
    });
    roleList.value = response.roles || [];
  } catch (error) {
    console.error('加载角色列表失败:', error);
    ElMessage.error('加载角色列表失败');
  } finally {
    loading.value = false;
  }
};

const loadPermissions = async () => {
  try {
    const response = await service({
      url: '/users/permissions/',
      method: 'get'
    });
    permissionsByApp.value = response.permissions || {};
  } catch (error) {
    console.error('加载权限列表失败:', error);
    ElMessage.error('加载权限列表失败');
  }
};

const loadUserPermissions = async () => {
  if (!userSearch.value) {
    ElMessage.warning('请输入用户 ID');
    return;
  }

  try {
    const response = await service({
      url: '/users/user-permissions/user_permissions/',
      method: 'get',
      params: { user_id: userSearch.value }
    });
    
    currentUser.value = response.user;
    userPermissions.value = response;
  } catch (error) {
    console.error('加载用户权限失败:', error);
    ElMessage.error(error.response?.data?.error || '加载用户权限失败');
  }
};

const showRoleDialog = (role) => {
  if (role) {
    isEditRole.value = true;
    roleForm.value = {
      id: role.id,
      name: role.name,
      permissions: role.permissions.map(p => p.id)
    };
  } else {
    isEditRole.value = false;
    roleForm.value = {
      id: null,
      name: '',
      permissions: []
    };
  }
  roleDialogVisible.value = true;
};

const saveRole = async () => {
  if (!roleForm.value.name) {
    ElMessage.warning('请输入角色名称');
    return;
  }

  saving.value = true;
  try {
    if (isEditRole.value) {
      await service({
        url: `/users/roles/${roleForm.value.id}/`,
        method: 'put',
        data: {
          name: roleForm.value.name,
          permissions: roleForm.value.permissions
        }
      });
      ElMessage.success('角色更新成功');
    } else {
      await service({
        url: '/users/roles/',
        method: 'post',
        data: {
          name: roleForm.value.name,
          permissions: roleForm.value.permissions
        }
      });
      ElMessage.success('角色创建成功');
    }
    
    roleDialogVisible.value = false;
    loadRoles();
  } catch (error) {
    console.error('保存角色失败:', error);
    ElMessage.error(error.response?.data?.error || '保存角色失败');
  } finally {
    saving.value = false;
  }
};

const deleteRole = async (roleId) => {
  try {
    await service({
      url: `/users/roles/${roleId}/`,
      method: 'delete'
    });
    ElMessage.success('角色删除成功');
    loadRoles();
  } catch (error) {
    console.error('删除角色失败:', error);
    ElMessage.error(error.response?.data?.error || '删除角色失败');
  }
};

const viewRoleUsers = async (role) => {
  try {
    const response = await service({
      url: `/users/roles/${role.id}/users/`,
      method: 'get'
    });
    roleUsers.value = response.users || [];
    roleUsersDialogVisible.value = true;
  } catch (error) {
    console.error('加载角色用户失败:', error);
    ElMessage.error('加载角色用户失败');
  }
};

const showAssignGroupDialog = () => {
  selectedGroups.value = userPermissions.value.groups.map(g => g.id);
  assignGroupDialogVisible.value = true;
};

const assignGroups = async () => {
  assigning.value = true;
  try {
    await service({
      url: '/users/user-permissions/assign_groups/',
      method: 'post',
      data: {
        user_id: currentUser.value.id,
        groups: selectedGroups.value
      }
    });
    ElMessage.success('角色分配成功');
    assignGroupDialogVisible.value = false;
    loadUserPermissions();
  } catch (error) {
    console.error('分配角色失败:', error);
    ElMessage.error('分配角色失败');
  } finally {
    assigning.value = false;
  }
};

const removeUserGroup = async (groupId) => {
  const newGroups = userPermissions.value.groups
    .filter(g => g.id !== groupId)
    .map(g => g.id);
  
  try {
    await service({
      url: '/users/user-permissions/assign_groups/',
      method: 'post',
      data: {
        user_id: currentUser.value.id,
        groups: newGroups
      }
    });
    ElMessage.success('角色移除成功');
    loadUserPermissions();
  } catch (error) {
    console.error('移除角色失败:', error);
    ElMessage.error('移除角色失败');
  }
};

const showAssignPermissionDialog = () => {
  selectedPermissions.value = userPermissions.value.direct_permissions.map(p => p.id);
  assignPermissionDialogVisible.value = true;
};

const assignPermissions = async () => {
  assigning.value = true;
  try {
    await service({
      url: '/users/user-permissions/assign_permissions/',
      method: 'post',
      data: {
        user_id: currentUser.value.id,
        permissions: selectedPermissions.value
      }
    });
    ElMessage.success('权限分配成功');
    assignPermissionDialogVisible.value = false;
    loadUserPermissions();
  } catch (error) {
    console.error('分配权限失败:', error);
    ElMessage.error('分配权限失败');
  } finally {
    assigning.value = false;
  }
};

const resetRoleForm = () => {
  roleForm.value = {
    id: null,
    name: '',
    permissions: []
  };
};

const getAppName = (app) => {
  const appNames = {
    'users': '用户管理',
    'videos': '视频管理',
    'ai_service': 'AI 服务',
    'authentication': '认证',
    'core': '核心',
    'admin': '管理后台',
    'auth': '权限',
    'contenttypes': '内容类型',
    'sessions': '会话'
  };
  return appNames[app] || app;
};

onMounted(() => {
  loadRoles();
  loadPermissions();
});
</script>

<style scoped>
.permission-management {
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

.tabs-container {
  margin-top: 0;
}

.permissions-container {
  padding: 10px 0;
}

.collapse-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 20px;
}

.app-name {
  font-weight: 600;
  font-size: 15px;
}

.user-search {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.user-permissions-detail {
  margin-top: 20px;
}

.section {
  margin-top: 30px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}
</style>
