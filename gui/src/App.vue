<template>
  <div id="mcp-platform">
    <!-- 側邊導航欄 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo">
          <i class="ri-rocket-2-fill"></i>
          <span v-if="!sidebarCollapsed" class="logo-text">MCP Platform</span>
        </div>
        <button 
          class="btn-collapse" 
          @click="sidebarCollapsed = !sidebarCollapsed"
          :title="sidebarCollapsed ? '展開側邊欄' : '收合側邊欄'"
        >
          <i :class="sidebarCollapsed ? 'ri-menu-unfold-line' : 'ri-menu-fold-line'"></i>
        </button>
      </div>

      <nav class="sidebar-nav">
        <!-- AI 對話系統 -->
        <div class="nav-section">
          <div v-if="!sidebarCollapsed" class="section-title">AI 對話系統</div>
          <button
            :class="['nav-item', { active: currentView === 'chatbot' }]"
            @click="currentView = 'chatbot'"
            :title="sidebarCollapsed ? 'AI Chatbot' : ''"
          >
            <i class="ri-chat-3-line"></i>
            <span v-if="!sidebarCollapsed">AI Chatbot</span>
          </button>
          <button
            :class="['nav-item', { active: currentView === 'agents' }]"
            @click="currentView = 'agents'"
            :title="sidebarCollapsed ? 'Agent 管理' : ''"
          >
            <i class="ri-robot-2-line"></i>
            <span v-if="!sidebarCollapsed">Agent 管理</span>
          </button>
        </div>

        <!-- 工具與整合 -->
        <div class="nav-section">
          <div v-if="!sidebarCollapsed" class="section-title">工具與整合</div>
          <button
            :class="['nav-item', { active: currentView === 'mcp' }]"
            @click="currentView = 'mcp'"
            :title="sidebarCollapsed ? 'MCP 工具管理' : ''"
          >
            <i class="ri-tools-line"></i>
            <span v-if="!sidebarCollapsed">MCP 工具管理</span>
          </button>
          <button
            :class="['nav-item', { active: currentView === 'linebot' }]"
            @click="currentView = 'linebot'"
            :title="sidebarCollapsed ? 'LINE BOT' : ''"
          >
            <i class="ri-line-fill"></i>
            <span v-if="!sidebarCollapsed">LINE BOT</span>
          </button>
        </div>

        <!-- 內容管理 -->
        <div class="nav-section">
          <div v-if="!sidebarCollapsed" class="section-title">內容管理</div>
          <button
            :class="['nav-item', { active: currentView === 'prompts' }]"
            @click="currentView = 'prompts'"
            :title="sidebarCollapsed ? '提示詞管理' : ''"
          >
            <i class="ri-file-text-line"></i>
            <span v-if="!sidebarCollapsed">提示詞管理</span>
          </button>
          <button
            :class="['nav-item', { active: currentView === 'rag' }]"
            @click="currentView = 'rag'"
            :title="sidebarCollapsed ? '知識庫管理' : ''"
          >
            <i class="ri-book-2-line"></i>
            <span v-if="!sidebarCollapsed">知識庫管理</span>
          </button>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="version-info" v-if="!sidebarCollapsed">
          <i class="ri-information-line"></i>
          <span>v1.0.0</span>
        </div>
      </div>
    </aside>

    <!-- 主要內容區 -->
    <div class="main-container" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <!-- 頂部欄 -->
      <header class="topbar">
        <div class="topbar-left">
          <div class="breadcrumb">
            <span class="breadcrumb-item">
              <i class="ri-home-4-line"></i>
              <span>首頁</span>
            </span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item" v-if="getCurrentViewCategory()">
              <span>{{ getCurrentViewCategory() }}</span>
            </span>
            <span class="breadcrumb-separator" v-if="getCurrentViewCategory()">/</span>
            <span class="breadcrumb-item active">
              <i :class="getCurrentViewIcon()"></i>
              <span>{{ getCurrentViewName() }}</span>
            </span>
          </div>
        </div>
        <div class="topbar-right">
          <button class="btn-icon" @click="toggleTheme" :title="theme === 'dark' ? '切換到淺色模式' : '切換到深色模式'">
            <i :class="theme === 'dark' ? 'ri-sun-line' : 'ri-moon-line'"></i>
          </button>
          <button class="btn-icon" title="通知">
            <i class="ri-notification-3-line"></i>
          </button>
          <button class="btn-icon" title="設定">
            <i class="ri-settings-3-line"></i>
          </button>
          <div class="user-avatar">
            <i class="ri-user-3-fill"></i>
          </div>
        </div>
      </header>

      <!-- 內容區 -->
      <main class="content">
        <div class="content-wrapper">
          <!-- MCP 管理頁面 -->
          <transition name="fade" mode="out-in">
            <div v-if="currentView === 'mcp'" key="mcp" class="view-container">
              <MCPManagement />
            </div>

            <!-- Chatbot 頁面 -->
            <div v-else-if="currentView === 'chatbot'" key="chatbot" class="view-container">
              <Chatbot />
            </div>

            <!-- LINE BOT 頁面 -->
            <div v-else-if="currentView === 'linebot'" key="linebot" class="view-container">
              <LineBotManagement />
            </div>

            <!-- 提示詞管理頁面 -->
            <div v-else-if="currentView === 'prompts'" key="prompts" class="view-container">
              <PromptManagement />
            </div>

            <!-- Agent 管理頁面 -->
            <div v-else-if="currentView === 'agents'" key="agents" class="view-container">
              <AgentManagement />
            </div>

            <!-- 知識庫管理頁面 -->
            <div v-else-if="currentView === 'rag'" key="rag" class="view-container">
              <KnowledgeBaseManagement />
            </div>
          </transition>
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useTheme } from './composables/useTheme'
import MCPManagement from './components/MCPManagement.vue'
import Chatbot from './components/Chatbot.vue'
import LineBotManagement from './components/LineBotManagement.vue'
import PromptManagement from './components/PromptManagement.vue'
import KnowledgeBaseManagement from './components/KnowledgeBaseManagement.vue'
import AgentManagement from './components/AgentManagement.vue'

export default {
  name: 'App',
  components: {
    MCPManagement,
    Chatbot,
    LineBotManagement,
    PromptManagement,
    KnowledgeBaseManagement,
    AgentManagement
  },
  setup() {
    const currentView = ref('chatbot')
    const sidebarCollapsed = ref(false)
    
    // 主題管理
    const { theme, initTheme, toggleTheme } = useTheme()
    
    // 初始化主題
    onMounted(() => {
      initTheme()
    })

    const viewConfig = {
      chatbot: { name: 'AI Chatbot', icon: 'ri-chat-3-line', category: 'AI 對話系統' },
      agents: { name: 'Agent 管理', icon: 'ri-robot-2-line', category: 'AI 對話系統' },
      mcp: { name: 'MCP 工具管理', icon: 'ri-tools-line', category: '工具與整合' },
      linebot: { name: 'LINE BOT', icon: 'ri-line-fill', category: '工具與整合' },
      prompts: { name: '提示詞管理', icon: 'ri-file-text-line', category: '內容管理' },
      rag: { name: '知識庫管理', icon: 'ri-book-2-line', category: '內容管理' }
    }

    const getCurrentViewName = () => {
      return viewConfig[currentView.value]?.name || ''
    }

    const getCurrentViewIcon = () => {
      return viewConfig[currentView.value]?.icon || 'ri-home-line'
    }

    const getCurrentViewCategory = () => {
      return viewConfig[currentView.value]?.category || ''
    }

    return {
      currentView,
      sidebarCollapsed,
      getCurrentViewName,
      getCurrentViewIcon,
      getCurrentViewCategory,
      theme,
      toggleTheme
    }
  }
}
</script>

<style scoped>
/* ============================================
   主容器佈局
   ============================================ */
#mcp-platform {
  display: flex;
  min-height: 100vh;
  background: var(--color-background);
}

/* ============================================
   側邊導航欄
   ============================================ */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--color-background-secondary);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-base);
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

/* 側邊欄頭部 */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-5) var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
  min-height: var(--topbar-height);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.logo i {
  font-size: 1.75rem;
  color: var(--color-primary-500);
}

.logo-text {
  color: var(--color-primary-500);
  white-space: nowrap;
}

.btn-collapse {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-base);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-collapse:hover {
  background: var(--color-slate-700);
  color: var(--color-text-primary);
}

.btn-collapse i {
  font-size: 1.25rem;
}

/* 側邊欄導航 */
.sidebar-nav {
  flex: 1;
  padding: var(--spacing-4);
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-section {
  margin-bottom: var(--spacing-6);
}

.section-title {
  padding: var(--spacing-2) var(--spacing-3);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--spacing-2);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  width: 100%;
  padding: var(--spacing-3) var(--spacing-4);
  margin-bottom: var(--spacing-1);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-base);
  cursor: pointer;
  transition: all var(--transition-base);
  text-align: left;
  white-space: nowrap;
}

.nav-item i {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.nav-item:hover {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
}

.nav-item.active {
  background: var(--color-primary-600);
  color: white;
  box-shadow: var(--shadow-md);
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: var(--spacing-3);
}

.sidebar.collapsed .nav-item span {
  display: none;
}

/* 側邊欄底部 */
.sidebar-footer {
  padding: var(--spacing-4);
  border-top: 1px solid var(--color-border);
}

.version-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  background: var(--color-slate-900);
  border-radius: var(--radius-base);
}

/* ============================================
   主要內容區
   ============================================ */
.main-container {
  flex: 1;
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  transition: margin-left var(--transition-base);
  min-height: 100vh;
}

.main-container.sidebar-collapsed {
  margin-left: var(--sidebar-collapsed-width);
}

/* 頂部欄 */
.topbar {
  position: sticky;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--topbar-height);
  padding: 0 var(--spacing-6);
  background: var(--color-background-secondary);
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(8px);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.breadcrumb-item i {
  font-size: 1.1rem;
}

.breadcrumb-item.active {
  color: var(--color-text-primary);
  font-weight: var(--font-weight-semibold);
}

.breadcrumb-item.active i {
  color: var(--color-primary-500);
}

.breadcrumb-separator {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
  margin: 0 var(--spacing-1);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-base);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-icon:hover {
  background: var(--color-slate-700);
  color: var(--color-text-primary);
}

.btn-icon i {
  font-size: 1.25rem;
}

.user-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-primary-600);
  border-radius: var(--radius-full);
  color: white;
  font-size: 1.25rem;
  cursor: pointer;
  transition: all var(--transition-base);
}

.user-avatar:hover {
  background: var(--color-primary-700);
  transform: scale(1.05);
  box-shadow: var(--shadow-lg);
}

/* 內容區 */
.content {
  flex: 1;
  padding: var(--spacing-6);
}

.content-wrapper {
  max-width: var(--content-max-width);
  margin: 0 auto;
}

.view-container {
  width: 100%;
  height: 100%;
  overflow-y: auto;
}

/* ============================================
   響應式設計
   ============================================ */
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
  }

  .sidebar.collapsed {
    transform: translateX(0);
    width: var(--sidebar-collapsed-width);
  }

  .main-container {
    margin-left: 0;
  }

  .main-container.sidebar-collapsed {
    margin-left: var(--sidebar-collapsed-width);
  }

  .topbar {
    padding: 0 var(--spacing-4);
  }

  .content {
    padding: var(--spacing-4);
  }
}
</style>

<style>
/* ============================================
   淺色主題全局覆蓋樣式 (非 Scoped)
   ============================================ */
[data-theme="light"] .sidebar {
  background: #ffffff;
}

[data-theme="light"] .sidebar-header {
  border-bottom-color: var(--color-border);
}

[data-theme="light"] .btn-collapse:hover {
  background: var(--color-slate-100);
  color: var(--color-primary-600);
}

[data-theme="light"] .nav-item {
  color: var(--color-slate-600);
}

[data-theme="light"] .nav-item:hover {
  background: var(--color-slate-100);
  color: var(--color-primary-600);
}

[data-theme="light"] .nav-item.active {
  background: var(--color-primary-50);
  color: var(--color-primary-600);
}

[data-theme="light"] .version-info {
  background: var(--color-slate-100);
  color: var(--color-slate-500);
}

[data-theme="light"] .topbar {
  background: #ffffff;
}

[data-theme="light"] .btn-icon:hover {
  background: var(--color-slate-100);
  color: var(--color-primary-600);
}
</style>
