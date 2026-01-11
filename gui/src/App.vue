<template>
  <div id="mcp-platform">
    <!-- 導航列 -->
    <nav class="navbar">
      <div class="nav-brand">
        <h1>🚀 MCP Platform</h1>
      </div>
      <div class="nav-tabs">
        <button
          :class="['nav-tab', { active: currentView === 'mcp' }]"
          @click="currentView = 'mcp'"
        >
          🛠️ MCP 管理
        </button>
        <button
          :class="['nav-tab', { active: currentView === 'chatbot' }]"
          @click="currentView = 'chatbot'"
        >
          💬 AI Chatbot
        </button>
        <button
          :class="['nav-tab', { active: currentView === 'linebot' }]"
          @click="currentView = 'linebot'"
        >
          📱 LINE BOT
        </button>
        <button
          :class="['nav-tab', { active: currentView === 'prompts' }]"
          @click="currentView = 'prompts'"
        >
          📝 提示詞管理
        </button>
      </div>
    </nav>

    <!-- 內容區 -->
    <div class="content">
      <!-- MCP 管理頁面 -->
      <div v-if="currentView === 'mcp'" class="view-container">
        <MCPManagement />
      </div>

      <!-- Chatbot 頁面 -->
      <div v-if="currentView === 'chatbot'" class="view-container">
        <Chatbot />
      </div>

      <!-- LINE BOT 頁面 -->
      <div v-if="currentView === 'linebot'" class="view-container">
        <LineBotManagement />
      </div>

      <!-- 提示詞管理頁面 -->
      <div v-if="currentView === 'prompts'" class="view-container">
        <PromptManagement />
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import MCPManagement from './components/MCPManagement.vue'
import Chatbot from './components/Chatbot.vue'
import LineBotManagement from './components/LineBotManagement.vue'
import PromptManagement from './components/PromptManagement.vue'

export default {
  name: 'App',
  components: {
    MCPManagement,
    Chatbot,
    LineBotManagement,
    PromptManagement
  },
  setup() {
    const currentView = ref('mcp')

    return {
      currentView
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#mcp-platform {
  min-height: 100vh;
  background: #f8fafc;
  font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #1e293b;
}

.navbar {
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  padding: 1rem 2rem;
  gap: 2rem;
}

.nav-brand h1 {
  font-size: 1.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.02em;
}

.nav-tabs {
  display: flex;
  gap: 0.5rem;
}

.nav-tab {
  padding: 0.75rem 1.5rem;
  border: none;
  background: transparent;
  color: #666;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.nav-tab:hover {
  background: #f0f0f0;
}

.nav-tab.active {
  background: #667eea;
  color: white;
}

.content {
  height: calc(100vh - 80px);
}

.view-container {
  height: 100%;
}
</style>
