<template>
  <div class="user-management">
    <!-- 頁面標題 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <i class="ri-user-line"></i>
          使用者管理
        </h1>
        <p class="page-subtitle">管理系統使用者帳號與權限</p>
      </div>
      <div class="header-right">
        <button v-if="hasFunctionPermission('func_user_create')" class="btn-primary" @click="showCreateDialog = true">
          <i class="ri-user-add-line"></i>
          新增使用者
        </button>
      </div>
    </div>

    <!-- 搜尋與篩選 -->
    <div class="filter-section">
      <div class="search-box">
        <i class="ri-search-line"></i>
        <input
          v-model="filters.search"
          type="text"
          placeholder="搜尋使用者名稱或 Email..."
          @input="handleSearch"
        />
      </div>
      <select v-model="filters.status" @change="loadUsers" class="filter-select">
        <option value="">所有狀態</option>
        <option value="active">啟用</option>
        <option value="inactive">停用</option>
        <option value="locked">鎖定</option>
      </select>
    </div>

    <!-- 使用者列表 -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>使用者名稱</th>
            <th>Email</th>
            <th>角色</th>
            <th>狀態</th>
            <th>最後登入</th>
            <th>建立時間</th>
            <th v-if="canPerformActions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td :colspan="canPerformActions ? 7 : 6" class="loading-cell">
              <i class="ri-loader-4-line rotating"></i>
              載入中...
            </td>
          </tr>
          <tr v-else-if="users.length === 0">
            <td :colspan="canPerformActions ? 7 : 6" class="empty-cell">
              <i class="ri-user-line"></i>
              沒有找到使用者
            </td>
          </tr>
          <tr v-else v-for="user in users" :key="user.id">
            <td>
              <div class="user-info">
                <div class="user-avatar">
                  {{ user.username.charAt(0).toUpperCase() }}
                </div>
                <span class="user-name">{{ user.username }}</span>
              </div>
            </td>
            <td>{{ user.email }}</td>
            <td>
              <div class="roles-tags">
                <span v-for="role in user.roles" :key="role" class="role-tag">
                  {{ role }}
                </span>
              </div>
            </td>
            <td>
              <span :class="['status-badge', `status-${user.status}`]">
                {{ getStatusText(user.status) }}
              </span>
            </td>
            <td>{{ formatDate(user.last_login_at) }}</td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td v-if="canPerformActions">
              <div class="action-buttons">
                <button
                  v-if="hasFunctionPermission('func_user_edit')"
                  class="btn-icon"
                  title="編輯"
                  @click="editUser(user)"
                >
                  <i class="ri-edit-line"></i>
                </button>
                <button
                  v-if="hasFunctionPermission('func_user_role')"
                  class="btn-icon"
                  title="設定角色"
                  @click="showRolesDialog(user)"
                >
                  <i class="ri-shield-user-line"></i>
                </button>
                <button
                  v-if="hasFunctionPermission('func_user_delete')"
                  class="btn-icon danger"
                  title="刪除"
                  @click="deleteUser(user)"
                >
                  <i class="ri-delete-bin-line"></i>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分頁 -->
    <div v-if="pagination.total > 0" class="pagination">
      <button
        class="btn-page"
        :disabled="pagination.page === 1"
        @click="changePage(pagination.page - 1)"
      >
        <i class="ri-arrow-left-s-line"></i>
        上一頁
      </button>
      <span class="page-info">
        第 {{ pagination.page }} / {{ pagination.total_pages }} 頁
        (共 {{ pagination.total }} 筆)
      </span>
      <button
        class="btn-page"
        :disabled="pagination.page === pagination.total_pages"
        @click="changePage(pagination.page + 1)"
      >
        下一頁
        <i class="ri-arrow-right-s-line"></i>
      </button>
    </div>

    <!-- 新增/編輯使用者對話框 -->
    <div v-if="showCreateDialog || showEditDialog" class="modal-overlay" @click.self="closeDialogs">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ showCreateDialog ? '新增使用者' : '編輯使用者' }}</h2>
          <button class="btn-close" @click="closeDialogs">
            <i class="ri-close-line"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>使用者名稱</label>
            <input
              v-model="formData.username"
              type="text"
              placeholder="請輸入使用者名稱"
              :disabled="showEditDialog"
            />
          </div>
          <div class="form-group">
            <label>Email</label>
            <input
              v-model="formData.email"
              type="email"
              placeholder="請輸入 Email"
            />
          </div>
          <div v-if="showCreateDialog" class="form-group">
            <label>密碼</label>
            <input
              v-model="formData.password"
              type="password"
              placeholder="至少 8 個字元"
            />
          </div>
          <div v-if="showEditDialog" class="form-group">
            <label>狀態</label>
            <select v-model="formData.status">
              <option value="active">啟用</option>
              <option value="inactive">停用</option>
              <option value="locked">鎖定</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeDialogs">取消</button>
          <button class="btn-primary" @click="saveUser" :disabled="saving">
            {{ saving ? '儲存中...' : '儲存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 角色設定對話框 -->
    <div v-if="showRoleDialog" class="modal-overlay" @click.self="showRoleDialog = false">
      <div class="modal-content">
        <div class="modal-header">
          <h2>設定使用者角色</h2>
          <button class="btn-close" @click="showRoleDialog = false">
            <i class="ri-close-line"></i>
          </button>
        </div>
        <div class="modal-body">
          <p class="dialog-subtitle">使用者: {{ selectedUser?.username }}</p>
          <div class="roles-list">
            <label
              v-for="role in availableRoles"
              :key="role.id"
              class="role-checkbox"
            >
              <input
                type="checkbox"
                :value="role.id"
                v-model="selectedRoleIds"
              />
              <div class="role-info">
                <span class="role-name">{{ role.name }}</span>
                <span class="role-desc">{{ role.description }}</span>
              </div>
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showRoleDialog = false">取消</button>
          <button class="btn-primary" @click="saveUserRoles" :disabled="saving">
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
  name: 'UserManagement',
  setup() {
    const { hasFunctionPermission } = useAuth()
    const users = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const filters = ref({
      search: '',
      status: ''
    })
    const pagination = ref({
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0
    })

    const showCreateDialog = ref(false)
    const showEditDialog = ref(false)
    const showRoleDialog = ref(false)
    const selectedUser = ref(null)
    const formData = ref({
      username: '',
      email: '',
      password: '',
      status: 'active'
    })

    const availableRoles = ref([])
    const selectedRoleIds = ref([])

    const canPerformActions = computed(() => {
      return hasFunctionPermission('func_user_edit') ||
             hasFunctionPermission('func_user_role') ||
             hasFunctionPermission('func_user_delete')
    })

    // 載入使用者列表
    const loadUsers = async () => {
      try {
        loading.value = true
        const params = {
          page: pagination.value.page,
          page_size: pagination.value.page_size,
          search: filters.value.search,
          status: filters.value.status
        }

        const response = await request.get('/api/users', { params })
        
        if (response.data.success) {
          users.value = response.data.data.users
          pagination.value = response.data.data.pagination
        }
      } catch (error) {
        console.error('載入使用者列表失敗:', error)
      } finally {
        loading.value = false
      }
    }

    // 載入角色列表
    const loadRoles = async () => {
      try {
        const response = await request.get('/api/roles')
        if (response.data.success) {
          availableRoles.value = response.data.data
        }
      } catch (error) {
        console.error('載入角色列表失敗:', error)
      }
    }

    // 搜尋處理
    let searchTimeout
    const handleSearch = () => {
      clearTimeout(searchTimeout)
      searchTimeout = setTimeout(() => {
        pagination.value.page = 1
        loadUsers()
      }, 500)
    }

    // 換頁
    const changePage = (page) => {
      pagination.value.page = page
      loadUsers()
    }

    // 編輯使用者
    const editUser = (user) => {
      selectedUser.value = user
      formData.value = {
        username: user.username,
        email: user.email,
        status: user.status
      }
      showEditDialog.value = true
    }

    // 儲存使用者
    const saveUser = async () => {
      try {
        saving.value = true
        
        if (showCreateDialog.value) {
          // 新增使用者
          await request.post('/api/users', formData.value)
        } else {
          // 更新使用者
          await request.put(`/api/users/${selectedUser.value.id}`, {
            email: formData.value.email,
            status: formData.value.status
          })
        }
        
        closeDialogs()
        loadUsers()
      } catch (error) {
        alert(error.response?.data?.error || '儲存失敗')
      } finally {
        saving.value = false
      }
    }

    // 刪除使用者
    const deleteUser = async (user) => {
      if (!confirm(`確定要刪除使用者 "${user.username}" 嗎?`)) {
        return
      }
      
      try {
        await request.delete(`/api/users/${user.id}`)
        loadUsers()
      } catch (error) {
        alert(error.response?.data?.error || '刪除失敗')
      }
    }

    // 顯示角色設定對話框
    const showRolesDialog = async (user) => {
      selectedUser.value = user
      
      // 取得使用者詳細資料
      try {
        const response = await request.get(`/api/users/${user.id}`)
        if (response.data.success) {
          selectedRoleIds.value = response.data.data.roles.map(r => r.id)
        }
      } catch (error) {
        console.error('取得使用者資料失敗:', error)
      }
      
      showRoleDialog.value = true
    }

    // 儲存使用者角色
    const saveUserRoles = async () => {
      try {
        saving.value = true
        await request.put(`/api/users/${selectedUser.value.id}/roles`, {
          role_ids: selectedRoleIds.value
        })
        showRoleDialog.value = false
        loadUsers()
      } catch (error) {
        alert(error.response?.data?.error || '儲存失敗')
      } finally {
        saving.value = false
      }
    }

    // 關閉對話框
    const closeDialogs = () => {
      showCreateDialog.value = false
      showEditDialog.value = false
      formData.value = {
        username: '',
        email: '',
        password: '',
        status: 'active'
      }
      selectedUser.value = null
    }

    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return date.toLocaleString('zh-TW')
    }

    // 取得狀態文字
    const getStatusText = (status) => {
      const statusMap = {
        active: '啟用',
        inactive: '停用',
        locked: '鎖定'
      }
      return statusMap[status] || status
    }

    onMounted(() => {
      loadUsers()
      loadRoles()
    })

    return {
      users,
      loading,
      saving,
      filters,
      pagination,
      showCreateDialog,
      showEditDialog,
      showRoleDialog,
      selectedUser,
      formData,
      availableRoles,
      selectedRoleIds,
      loadUsers,
      handleSearch,
      changePage,
      editUser,
      saveUser,
      deleteUser,
      showRolesDialog,
      saveUserRoles,
      closeDialogs,
      formatDate,
      getStatusText,
      hasFunctionPermission,
      canPerformActions
    }
  }
}
</script>

<style scoped>
.user-management {
  padding: var(--spacing-6);
  max-width: 1400px;
  margin: 0 auto;
}

/* 頁面標題 */
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

/* 篩選區域 */
.filter-section {
  display: flex;
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-6);
}

.search-box {
  flex: 1;
  position: relative;
}

.search-box i {
  position: absolute;
  left: var(--spacing-4);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-tertiary);
  font-size: 1.25rem;
}

.search-box input {
  width: 100%;
  padding: var(--spacing-3) var(--spacing-4) var(--spacing-3) 45px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  transition: all var(--transition-base);
}

.search-box input:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.filter-select {
  padding: var(--spacing-3) var(--spacing-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  min-width: 150px;
  cursor: pointer;
}

/* 表格 */
.table-container {
  background: var(--color-background-secondary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: var(--color-bg-tertiary);
}

.data-table th {
  padding: var(--spacing-4);
  text-align: left;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.data-table td {
  padding: var(--spacing-4);
  border-top: 1px solid var(--color-border);
  color: var(--color-text-secondary);
}

.data-table tbody tr:hover {
  background: var(--color-surface-hover);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  background: var(--color-primary-600);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-lg);
}

.user-name {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.roles-tags {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.role-tag {
  padding: 4px 12px;
  background: var(--color-primary-100);
  color: var(--color-primary-700);
  border-radius: var(--radius-base);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.status-badge {
  padding: 4px 12px;
  border-radius: var(--radius-base);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.status-active {
  background: #d1fae5;
  color: #065f46;
}

.status-inactive {
  background: #fee;
  color: #991b1b;
}

.status-locked {
  background: #fef3c7;
  color: #92400e;
}

.action-buttons {
  display: flex;
  gap: var(--spacing-2);
}

.btn-icon {
  padding: var(--spacing-2);
  background: transparent;
  border: none;
  border-radius: var(--radius-base);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-icon:hover {
  background: var(--color-surface-hover);
  color: var(--color-primary-500);
}

.btn-icon.danger:hover {
  background: #fee;
  color: #dc2626;
}

/* 分頁 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-4);
  margin-top: var(--spacing-6);
}

.btn-page {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--color-background-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-page:hover:not(:disabled) {
  background: var(--color-surface-hover);
  border-color: var(--color-primary-500);
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

/* 按鈕 */
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

.btn-primary:hover {
  background: var(--color-primary-700);
  box-shadow: var(--shadow-md);
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
}

.btn-close:hover {
  background: var(--color-surface-hover);
}

.modal-body {
  padding: var(--spacing-5);
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
.form-group select {
  width: 100%;
  padding: var(--spacing-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
}

.modal-footer {
  display: flex;
  gap: var(--spacing-3);
  justify-content: flex-end;
  padding: var(--spacing-5);
  border-top: 1px solid var(--color-border);
}

.roles-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.role-checkbox {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  cursor: pointer;
  transition: all var(--transition-base);
}

.role-checkbox:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-primary-500);
}

.role-checkbox input {
  margin-top: 2px;
}

.role-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.role-name {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.role-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: var(--spacing-8) !important;
  color: var(--color-text-tertiary);
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
