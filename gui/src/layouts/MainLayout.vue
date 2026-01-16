<template>
  <div class="app-container">
    <!-- 側邊欄導航 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1 class="logo">
          <i class="ri-robot-line"></i>
          <span>MCP Platform</span>
        </h1>
      </div>

      <!-- 使用者資訊卡片 (Sidebar) -->
      <div v-if="currentUser" class="user-card-sidebar">
        <div class="user-avatar-large" :style="{ backgroundColor: avatarColor }">
          {{ avatarText }}
        </div>
        <div class="user-details">
          <div class="user-name-full">{{ currentUser.username }}</div>
          <div class="user-email">{{ currentUser.email }}</div>
          <div class="user-roles">
            <span v-for="role in currentUser.roles" :key="role" class="role-tag" :class="getRoleClass(role)">
              {{ typeof role === 'string' ? role : role.name }}
            </span>
          </div>
        </div>
      </div>
      
      <nav class="sidebar-nav">
        <div v-for="group in navigationGroups" :key="group.title" class="nav-group">
          <div class="nav-group-title">{{ group.title }}</div>
          <router-link
            v-for="item in group.items"
            :key="item.path"
            :to="item.path"
            class="nav-item"
            :class="{ active: isActive(item.path) }"
          >
            <i :class="item.icon"></i>
            <span>{{ item.label }}</span>
          </router-link>
        </div>
      </nav>
      
      <div class="sidebar-footer">
        <button @click="handleLogout" class="btn-logout">
          <i class="ri-logout-box-line"></i>
          <span>登出</span>
        </button>
      </div>
    </aside>

    <!-- 主要內容區 -->
    <div class="main-content">
      <!-- 頂部欄 -->
      <header class="topbar">
        <div class="topbar-left">
          <h2 class="page-title">{{ currentPageTitle }}</h2>
        </div>
        <div class="topbar-right">
          <!-- Session 計時器 (僅一般使用者顯示) -->
          <div v-if="isAuthenticated && !hasAdminRole" class="session-timer" :class="{ warning: sessionRemainingTime < 300 }">
            <i class="ri-history-line"></i>
            <span>{{ formatRemainingTime }}</span>
          </div>

          <button @click="toggleTheme" class="btn-theme" :title="isDarkMode ? '切換到亮色模式' : '切換到暗黑模式'">
            <i :class="isDarkMode ? 'ri-sun-line' : 'ri-moon-line'"></i>
          </button>
          
          <div class="user-info-topbar">
            <div class="user-avatar-small" :style="{ backgroundColor: avatarColor }">
              {{ avatarText }}
            </div>
            <span class="user-name-small">{{ currentUser?.username || '使用者' }}</span>
          </div>
        </div>
      </header>

      <!-- 頁面內容 -->
      <div class="page-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import Swal from 'sweetalert2'

export default {
  name: 'MainLayout',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const { user: currentUser, logout, hasPagePermission, isAuthenticated, sessionRemainingTime, hasRole } = useAuth()

    // 主題狀態
    const isDarkMode = ref(true)

    // 導航項目分組
    const allNavigationGroups = [
      {
        title: '核心功能',
        items: [
          { path: '/chatbot', label: '聊天機器人', icon: 'ri-message-3-line', pageCode: 'chatbot' },
          { path: '/agents', label: 'Agent 管理', icon: 'ri-robot-2-line', pageCode: 'agents' },
          { path: '/mcp', label: 'MCP 工具', icon: 'ri-tools-line', pageCode: 'mcp' },
          { path: '/linebot', label: 'LINE BOT', icon: 'ri-line-fill', pageCode: 'linebot' }
        ]
      },
      {
        title: '內容管理',
        items: [
          { path: '/prompts', label: '提示詞管理', icon: 'ri-file-text-line', pageCode: 'prompts' },
          { path: '/rag', label: '知識庫', icon: 'ri-database-2-line', pageCode: 'rag' }
        ]
      },
      {
        title: '系統設定',
        items: [
          { path: '/users', label: '使用者管理', icon: 'ri-user-settings-line', pageCode: 'users' },
          { path: '/roles', label: '角色管理', icon: 'ri-shield-user-line', pageCode: 'roles' }
        ]
      }
    ]

    // 根據權限過濾導航分組
    const navigationGroups = computed(() => {
      return allNavigationGroups.map(group => ({
        ...group,
        items: group.items.filter(item => {
          if (!item.pageCode) return true
          return hasPagePermission(item.pageCode)
        })
      })).filter(group => group.items.length > 0)
    })

    // 所有導航項目(用於標題查找)
    const allNavigationItems = allNavigationGroups.flatMap(g => g.items)

    // 當前頁面標題
    const currentPageTitle = computed(() => {
      const currentItem = allNavigationItems.find(item => item.path === route.path)
      return currentItem?.label || 'MCP Platform'
    })

    // 判斷是否為當前路由
    const isActive = (path) => {
      return route.path === path
    }

    // 主題切換
    const toggleTheme = () => {
      isDarkMode.value = !isDarkMode.value
      document.documentElement.setAttribute('data-theme', isDarkMode.value ? 'dark' : 'light')
      localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light')
    }

    // 初始化主題
    onMounted(() => {
      const savedTheme = localStorage.getItem('theme') || 'dark'
      isDarkMode.value = savedTheme === 'dark'
      document.documentElement.setAttribute('data-theme', savedTheme)
    })

    // 登出處理
    const handleLogout = async () => {
      const result = await Swal.fire({
        title: '確定要登出嗎?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: '確定登出',
        cancelButtonText: '取消'
      })

      if (result.isConfirmed) {
        await logout()
      }
    }

    // 是否有管理員權限
    const hasAdminRole = computed(() => hasRole('超級管理員'))

    // 使用者頭像文字
    const avatarText = computed(() => {
      const name = currentUser.value?.username || 'U'
      return name.charAt(0).toUpperCase()
    })

    // 使用者頭像顏色
    const avatarColor = computed(() => {
      const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981']
      const index = (currentUser.value?.username?.length || 0) % colors.length
      return colors[index]
    })

    // 取得角色樣式
    const getRoleClass = (role) => {
      const roleName = typeof role === 'string' ? role : role.name
      if (roleName === '超級管理員') return 'role-admin'
      return 'role-user'
    }

    // 格式化剩餘時間 (mm:ss)
    const formatRemainingTime = computed(() => {
      const minutes = Math.floor(sessionRemainingTime.value / 60)
      const seconds = sessionRemainingTime.value % 60
      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    })

    return {
      navigationGroups,
      currentPageTitle,
      currentUser,
      isAuthenticated,
      isDarkMode,
      isActive,
      toggleTheme,
      handleLogout,
      sessionRemainingTime,
      formatRemainingTime,
      hasAdminRole,
      avatarText,
      avatarColor,
      getRoleClass
    }
  }
}
</script>

<style>
/* 主題變數 (全域生效) */
:root,
:root[data-theme="dark"] {
  --color-bg-primary: #0f172a;
  --color-bg-secondary: #1e293b;
  --color-bg-tertiary: #334155;
  --color-bg-hover: rgba(148, 163, 184, 0.1);
  --color-bg-active: rgba(59, 130, 246, 0.1);
  --color-text-primary: #f1f5f9;
  --color-text-secondary: #94a3b8;
  --color-text-tertiary: #64748b;
  --color-border: #334155;
  --color-primary: #3b82f6;
  --color-primary-rgb: 59, 130, 246;
  --color-danger: #ef4444;
}

:root[data-theme="light"] {
  --color-bg-primary: #f8fafc;
  --color-bg-secondary: #ffffff;
  --color-bg-tertiary: #f1f5f9;
  --color-bg-hover: rgba(15, 23, 42, 0.05);
  --color-bg-active: rgba(59, 130, 246, 0.1);
  --color-text-primary: #0f172a;
  --color-text-secondary: #475569;
  --color-text-tertiary: #94a3b8;
  --color-border: #e2e8f0;
  --color-primary: #3b82f6;
  --color-primary-rgb: 59, 130, 246;
  --color-danger: #ef4444;
}
</style>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
}

/* 側邊欄 */
.sidebar {
  width: 260px;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 20px 20px 10px 20px;
  border-bottom: none;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.logo i {
  font-size: 28px;
  color: var(--color-primary);
}

.sidebar-nav {
  flex: 1;
  padding: 20px 0;
  overflow-y: auto;
}

.nav-group {
  margin-bottom: 24px;
}

.nav-group:last-child {
  margin-bottom: 0;
}

.nav-group-title {
  padding: 8px 20px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.nav-item.active {
  background: var(--color-bg-active);
  color: var(--color-primary);
  border-left-color: var(--color-primary);
}

.nav-item i {
  font-size: 20px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid var(--color-border);
}

.btn-logout {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 20px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-logout:hover {
  background: var(--color-danger);
  border-color: var(--color-danger);
  color: white;
}

.btn-logout i {
  font-size: 20px;
}

/* 主要內容區 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 頂部欄 */
.topbar {
  height: 64px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-theme {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-bg-tertiary);
  border: none;
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-theme:hover {
  background: var(--color-bg-hover);
  color: var(--color-primary);
}

.btn-theme i {
  font-size: 20px;
}

.user-info-topbar i,
.user-info-topbar span {
  font-size: 18px;
}

.user-info-topbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 14px;
  background: var(--color-bg-tertiary);
  border-radius: 20px;
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.user-avatar-small {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.user-name-small {
  font-size: 14px;
  font-weight: 500;
}

/* Sidebar 使用者卡片 */
.user-card-sidebar {
  padding: 10px 20px 24px 20px;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
  background: linear-gradient(to bottom, transparent, rgba(var(--color-primary-rgb), 0.05));
}

.user-avatar-large {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 2px solid var(--color-bg-secondary);
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.user-name-full {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.user-email {
  font-size: 12px;
  color: var(--color-text-tertiary);
  word-break: break-all;
}

.user-roles {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
  margin-top: 8px;
}

.role-tag {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.role-admin {
  background: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.role-user {
  background: rgba(148, 163, 184, 0.15);
  color: #94a3b8;
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.session-timer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--color-bg-tertiary);
  border-radius: 8px;
  color: var(--color-text-secondary);
  font-family: monospace;
  font-size: 14px;
}

.session-timer.warning {
  color: var(--color-danger);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.6; }
  100% { opacity: 1; }
}

/* 頁面內容 */
.page-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.btn-logout {
  width: 100%;
  padding: 12px;
  background: transparent;
  border: 1px solid var(--color-border);
  color: #ef4444;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
  margin-top: auto;
}

.btn-logout:hover {
  background-color: #ef4444 !important;
  color: white !important;
  border-color: #ef4444 !important;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}

/* 滾動條樣式 */
.sidebar-nav::-webkit-scrollbar,
.page-content::-webkit-scrollbar {
  width: 6px;
}

.sidebar-nav::-webkit-scrollbar-track,
.page-content::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-nav::-webkit-scrollbar-thumb,
.page-content::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

.sidebar-nav::-webkit-scrollbar-thumb:hover,
.page-content::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-secondary);
}
</style>
