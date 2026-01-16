<template>
  <div class="role-management">
    <!-- 頁面標題 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <i class="ri-shield-user-line"></i>
          角色管理
        </h1>
        <p class="page-subtitle">管理系統角色與權限配置</p>
      </div>
      <div class="header-right">
        <button v-if="hasFunctionPermission('func_role_create')" class="btn-primary" @click="showCreateDialog = true">
          <i class="ri-add-line"></i>
          新增角色
        </button>
      </div>
    </div>

    <!-- 角色列表 -->
    <div class="roles-grid">
      <div v-if="loading" class="loading-state">
        <i class="ri-loader-4-line rotating"></i>
        載入中...
      </div>
      
      <div v-else-if="roles.length === 0" class="empty-state">
        <i class="ri-shield-user-line"></i>
        <p>尚無角色</p>
      </div>

      <div v-else class="role-card" v-for="role in roles" :key="role.id">
        <div class="role-header">
          <div class="role-icon">
            <i class="ri-shield-user-fill"></i>
          </div>
          <div class="role-info">
            <h3 class="role-name">{{ role.name }}</h3>
            <p class="role-description">{{ role.description }}</p>
          </div>
          <span v-if="role.is_system" class="system-badge">系統角色</span>
        </div>

        <div class="role-stats">
          <div class="stat-item">
            <i class="ri-user-line"></i>
            <span>{{ role.user_count }} 位使用者</span>
          </div>
          <div class="stat-item">
            <i class="ri-lock-line"></i>
            <span>{{ role.permission_count }} 個權限</span>
          </div>
        </div>

        <div class="role-actions">
          <button v-if="hasFunctionPermission('func_role_edit')" class="btn-action" @click="editRole(role)" :disabled="role.is_system">
            <i class="ri-edit-line"></i>
            編輯
          </button>
          <button v-if="hasFunctionPermission('func_role_permission')" class="btn-action" @click="managePermissions(role)">
            <i class="ri-lock-line"></i>
            權限設定
          </button>
          <button 
            v-if="hasFunctionPermission('func_role_delete')"
            class="btn-action danger" 
            @click="deleteRole(role)"
            :disabled="role.is_system || role.user_count > 0"
          >
            <i class="ri-delete-bin-line"></i>
            刪除
          </button>
        </div>
      </div>
    </div>

    <!-- 新增/編輯角色對話框 -->
    <div v-if="showCreateDialog || showEditDialog" class="modal-overlay" @click.self="closeDialogs">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ showCreateDialog ? '新增角色' : '編輯角色' }}</h2>
          <button class="btn-close" @click="closeDialogs">
            <i class="ri-close-line"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>角色名稱 *</label>
            <input
              v-model="formData.name"
              type="text"
              placeholder="請輸入角色名稱"
            />
          </div>
          <div class="form-group">
            <label>角色描述</label>
            <textarea
              v-model="formData.description"
              placeholder="請輸入角色描述"
              rows="3"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeDialogs">取消</button>
          <button class="btn-primary" @click="saveRole" :disabled="saving">
            {{ saving ? '儲存中...' : '儲存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 權限設定對話框 -->
    <div v-if="showPermissionDialog" class="modal-overlay" @click.self="showPermissionDialog = false">
      <div class="modal-content large">
        <div class="modal-header">
          <h2>設定角色權限</h2>
          <button class="btn-close" @click="showPermissionDialog = false">
            <i class="ri-close-line"></i>
          </button>
        </div>
        <div class="modal-body">
          <p class="dialog-subtitle">角色: {{ selectedRole?.name }}</p>
          
          <div class="permission-actions">
            <button class="btn-small" @click="selectAllPermissions">
              <i class="ri-checkbox-multiple-line"></i>
              全選
            </button>
            <button class="btn-small" @click="deselectAllPermissions">
              <i class="ri-checkbox-blank-line"></i>
              取消全選
            </button>
          </div>

          <div class="permissions-tree">
            <div class="permission-section">
              <h3 class="section-title">
                <i class="ri-pages-line"></i>
                頁面權限
              </h3>
              <div class="permission-list">
                <label
                  v-for="permission in pagePermissions"
                  :key="permission.id"
                  class="permission-item"
                >
                  <input
                    type="checkbox"
                    :value="permission.id"
                    v-model="selectedPermissionIds"
                  />
                  <div class="permission-info">
                    <span class="permission-name">{{ permission.name }}</span>
                    <span class="permission-code">{{ permission.code }}</span>
                  </div>
                </label>
              </div>
            </div>

            <div class="permission-section">
              <h3 class="section-title">
                <i class="ri-function-line"></i>
                功能權限
              </h3>
              <div class="permission-list">
                <label
                  v-for="permission in functionPermissions"
                  :key="permission.id"
                  class="permission-item"
                >
                  <input
                    type="checkbox"
                    :value="permission.id"
                    v-model="selectedPermissionIds"
                  />
                  <div class="permission-info">
                    <span class="permission-name">{{ permission.name }}</span>
                    <span class="permission-code">{{ permission.code }}</span>
                  </div>
                </label>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showPermissionDialog = false">取消</button>
          <button class="btn-primary" @click="savePermissions" :disabled="saving">
            {{ saving ? '儲存中...' : '儲存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import request from '../utils/request'
import { useAuth } from '../composables/useAuth'

export default {
  name: 'RoleManagement',
  setup() {
    const { hasFunctionPermission } = useAuth()
    const roles = ref([])
    const allPermissions = ref([])
    const loading = ref(false)
    const saving = ref(false)

    const showCreateDialog = ref(false)
    const showEditDialog = ref(false)
    const showPermissionDialog = ref(false)
    const selectedRole = ref(null)
    const formData = ref({
      name: '',
      description: ''
    })
    const selectedPermissionIds = ref([])

    // 分離頁面權限和功能權限
    const pagePermissions = computed(() => {
      return allPermissions.value.filter(p => p.type === 'page')
    })

    const functionPermissions = computed(() => {
      return allPermissions.value.filter(p => p.type === 'function')
    })

    // 載入角色列表
    const loadRoles = async () => {
      try {
        loading.value = true
        const response = await request.get('/api/roles')
        if (response.data.success) {
          roles.value = response.data.data
        }
      } catch (error) {
        console.error('載入角色列表失敗:', error)
      } finally {
        loading.value = false
      }
    }

    // 載入所有權限
    const loadPermissions = async () => {
      try {
        const response = await request.get('/api/permissions')
        if (response.data.success) {
          allPermissions.value = response.data.data
        }
      } catch (error) {
        console.error('載入權限列表失敗:', error)
      }
    }

    // 編輯角色
    const editRole = (role) => {
      selectedRole.value = role
      formData.value = {
        name: role.name,
        description: role.description
      }
      showEditDialog.value = true
    }

    // 儲存角色
    const saveRole = async () => {
      try {
        saving.value = true
        
        if (showCreateDialog.value) {
          await request.post('/api/roles', formData.value)
        } else {
          await request.put(`/api/roles/${selectedRole.value.id}`, formData.value)
        }
        
        closeDialogs()
        loadRoles()
      } catch (error) {
        alert(error.response?.data?.error || '儲存失敗')
      } finally {
        saving.value = false
      }
    }

    // 刪除角色
    const deleteRole = async (role) => {
      if (!confirm(`確定要刪除角色 "${role.name}" 嗎?`)) {
        return
      }
      
      try {
        await request.delete(`/api/roles/${role.id}`)
        loadRoles()
      } catch (error) {
        alert(error.response?.data?.error || '刪除失敗')
      }
    }

    // 管理權限
    const managePermissions = async (role) => {
      selectedRole.value = role
      
      try {
        const response = await request.get(`/api/roles/${role.id}/permissions`)
        if (response.data.success) {
          selectedPermissionIds.value = response.data.data.map(p => p.id)
        }
      } catch (error) {
        console.error('載入角色權限失敗:', error)
      }
      
      showPermissionDialog.value = true
    }

    // 儲存權限
    const savePermissions = async () => {
      try {
        saving.value = true
        await request.put(`/api/roles/${selectedRole.value.id}/permissions`, {
          permission_ids: selectedPermissionIds.value
        })
        showPermissionDialog.value = false
        loadRoles()
      } catch (error) {
        alert(error.response?.data?.error || '儲存失敗')
      } finally {
        saving.value = false
      }
    }

    // 全選權限
    const selectAllPermissions = () => {
      selectedPermissionIds.value = allPermissions.value.map(p => p.id)
    }

    // 取消全選
    const deselectAllPermissions = () => {
      selectedPermissionIds.value = []
    }

    // 關閉對話框
    const closeDialogs = () => {
      showCreateDialog.value = false
      showEditDialog.value = false
      formData.value = {
        name: '',
        description: ''
      }
      selectedRole.value = null
    }

    onMounted(() => {
      loadRoles()
      loadPermissions()
    })

    return {
      roles,
      loading,
      saving,
      showCreateDialog,
      showEditDialog,
      showPermissionDialog,
      selectedRole,
      formData,
      pagePermissions,
      functionPermissions,
      selectedPermissionIds,
      editRole,
      saveRole,
      deleteRole,
      managePermissions,
      savePermissions,
      selectAllPermissions,
      deselectAllPermissions,
      closeDialogs,
      hasFunctionPermission
    }
  }
}
</script>

<style scoped>
.role-management {
  padding: var(--spacing-6);
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-6);
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-2);
}

.page-title i {
  font-size: 2rem;
  color: var(--color-primary-500);
}

.page-subtitle {
  color: var(--color-text-secondary);
  margin: 0;
}

/* 角色網格 */
.roles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: var(--spacing-5);
}

.role-card {
  background: var(--color-background-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-5);
  transition: all var(--transition-base);
}

.role-card:hover {
  border-color: var(--color-primary-500);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.role-header {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-4);
  position: relative;
}

.role-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--color-primary-500), var(--color-primary-700));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.role-info {
  flex: 1;
  min-width: 0;
}

.role-name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-2);
}

.role-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.system-badge {
  position: absolute;
  top: 0;
  right: 0;
  padding: 4px 12px;
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
  border-radius: var(--radius-base);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.role-stats {
  display: flex;
  gap: var(--spacing-4);
  padding: var(--spacing-3) 0;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--spacing-4);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.stat-item i {
  font-size: 1.1rem;
  color: var(--color-primary-500);
}

.role-actions {
  display: flex;
  gap: var(--spacing-2);
}

.btn-action {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--color-surface-hover);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-action:hover:not(:disabled) {
  background: var(--color-primary-600);
  border-color: var(--color-primary-600);
  color: white;
}

.btn-action.danger:hover:not(:disabled) {
  background: #dc2626;
  border-color: #dc2626;
  color: white;
}

.btn-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 權限設定 */
.permission-actions {
  display: flex;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
}

.btn-small {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--color-surface-hover);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  font-size: var(--font-size-sm);
  cursor: pointer;
}

.btn-small:hover {
  background: var(--color-primary-600);
  border-color: var(--color-primary-600);
  color: white;
}

.permissions-tree {
  max-height: 500px;
  overflow-y: auto;
}

.permission-section {
  margin-bottom: var(--spacing-5);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-3);
  padding-bottom: var(--spacing-2);
  border-bottom: 2px solid var(--color-border);
}

.permission-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-2);
}

.permission-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  cursor: pointer;
  transition: all var(--transition-base);
}

.permission-item:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-primary-500);
}

.permission-item input {
  margin-top: 2px;
  cursor: pointer;
}

.permission-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.permission-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.permission-code {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  font-family: monospace;
}

/* 對話框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-4);
}

.modal-content {
  background: var(--color-background-secondary);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-content.large {
  max-width: 900px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-5);
  border-bottom: 1px solid var(--color-border);
}

.modal-header h2 {
  margin: 0;
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.btn-close {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: var(--spacing-2);
  border-radius: var(--radius-base);
  font-size: 1.5rem;
}

.btn-close:hover {
  background: var(--color-surface-hover);
}

.modal-body {
  padding: var(--spacing-5);
}

.dialog-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-4);
}

.form-group {
  margin-bottom: var(--spacing-4);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-2);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: var(--spacing-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  font-family: inherit;
}

.form-group textarea {
  resize: vertical;
}

.modal-footer {
  display: flex;
  gap: var(--spacing-3);
  justify-content: flex-end;
  padding: var(--spacing-5);
  border-top: 1px solid var(--color-border);
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-5);
  background: var(--color-primary-600);
  color: white;
  border: none;
  border-radius: var(--radius-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-700);
  box-shadow: var(--shadow-md);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: var(--spacing-3) var(--spacing-5);
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-secondary:hover {
  background: var(--color-bg-hover);
}

.loading-state,
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: var(--spacing-8);
  color: var(--color-text-tertiary);
}

.empty-state i {
  font-size: 4rem;
  margin-bottom: var(--spacing-4);
  opacity: 0.5;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
