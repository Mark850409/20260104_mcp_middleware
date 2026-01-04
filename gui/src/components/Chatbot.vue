<template>
  <div class="chatbot-container">
    <!-- 側邊欄 - 對話列表 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>💬 對話列表</h2>
        <button @click="createNewConversation" class="btn-new">
          ➕ 新對話
        </button>
        <button @click="clearAllConversations" class="btn-clear">
          🗑️ 清空全部
        </button>
      </div>
      
      <div class="conversations-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          :class="['conversation-item', { active: currentConversationId === conv.id }]"
          @click="selectConversation(conv.id)"
        >
          <div class="conv-title">{{ conv.title }}</div>
          <div class="conv-meta">
            <span class="provider-badge">{{ conv.model_provider }}</span>
            <span v-if="conv.mcp_enabled" class="mcp-badge">🔧 MCP</span>
          </div>
        </div>
        
        <div v-if="conversations.length === 0" class="empty-state">
          尚無對話記錄
        </div>
      </div>
    </aside>

    <!-- 主要聊天區 -->
    <main class="chat-main">
      <!-- 頂部工具列 -->
      <div class="chat-header">
        <div class="header-left">
          <div class="selector-group">
            <span class="selector-label">供應商</span>
            <select v-model="selectedProvider" @change="updateModelList" class="modern-select">
              <option value="openai">OpenAI</option>
              <option value="google">Google</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </div>
          
          <div class="selector-group">
            <span class="selector-label">模型</span>
            <select v-model="selectedModel" class="modern-select">
              <option v-for="model in availableModels" :key="model.name" :value="model.name">
                {{ model.display_name }}
              </option>
            </select>
          </div>
        </div>
        
        <div class="header-right">
          <div class="mcp-chips-container">
            <span class="selector-label">MCP 工具 (可多選)</span>
            <div class="mcp-chips">
              <div 
                v-for="server in availableMcpServers" 
                :key="server.name"
                :class="['mcp-chip', { active: selectedMcpServers.includes(server.name) }]"
                @click="toggleMcpServer(server.name)"
              >
                <span class="chip-icon">{{ selectedMcpServers.includes(server.name) ? '✅' : '⚙️' }}</span>
                {{ server.name }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 訊息區 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="!currentConversationId" class="welcome-screen">
          <h1>🤖 AI Chatbot</h1>
          <p>選擇左側對話或建立新對話開始聊天</p>
        </div>
        
        <div v-else class="messages-list">
          <div
            v-for="message in currentMessages"
            :key="message.id"
            :class="['message', message.role]"
          >
            <div class="message-avatar">
              {{ message.role === 'user' ? '👤' : '🤖' }}
            </div>
            <div class="message-content">
              <!-- MCP 工具調用顯示 (先顯示) -->
              <div v-if="message.tool_calls && message.tool_calls.length > 0" class="tool-calls">
                <div v-for="(call, idx) in message.tool_calls" :key="idx" class="tool-call-item">
                  <div class="tool-call-details">
                    <div class="tool-call-summary">
                      <span class="tool-icon">⚡</span>
                      <span class="tool-name">{{ call.function.name }}</span>
                    </div>
                    
                    <div class="tool-call-content">
                      <!-- Request -->
                      <div class="tool-section">
                        <div class="section-label">Request</div>
                        <pre class="code-block">{{ formatJSON(call.function.arguments) }}</pre>
                      </div>
                      
                      <!-- Response -->
                      <div v-if="call.result" class="tool-section">
                        <div class="section-label">Response</div>
                        <pre class="code-block">{{ formatJSON(call.result) }}</pre>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 答案內容 (後顯示) -->
              <div v-if="message.content" class="message-text">{{ message.content }}</div>
              
              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </div>
          
          <div v-if="isLoading" class="message assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 輸入區 -->
      <div class="input-wrapper">
        <div class="input-container">
          <textarea
            v-model="userInput"
            @keydown.enter.exact.prevent="sendMessage"
            placeholder="輸入訊息... (Enter 發送, Shift+Enter 換行)"
            :disabled="!currentConversationId || isLoading"
            rows="1"
            ref="inputArea"
            @input="adjustTextareaHeight"
          ></textarea>
          <button
            @click="sendMessage"
            :disabled="!currentConversationId || !userInput.trim() || isLoading"
            class="btn-send-modern"
            :title="isLoading ? '發送中' : '發送訊息'"
          >
            <svg v-if="!isLoading" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div v-else class="btn-loader"></div>
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import axios from 'axios'

export default {
  name: 'Chatbot',
  setup() {
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'
    
    // 狀態
    const conversations = ref([])
    const currentConversationId = ref(null)
    const currentMessages = ref([])
    const userInput = ref('')
    const isLoading = ref(false)
    const isLoadingConfig = ref(false)
    
    // 模型設定
    const selectedProvider = ref('openai')
    const selectedModel = ref('gpt-4o')
    const mcpEnabled = ref(false)
    const allModels = ref({})
    const messagesContainer = ref(null)
    
    // 計算屬性
    const availableModels = computed(() => {
      return allModels.value[selectedProvider.value] || []
    })
    
    // MCP Servers
    const availableMcpServers = ref([])
    const selectedMcpServers = ref([])
    
    // 方法
    const loadConversations = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/chat/conversations`)
        if (response.data.success) {
          conversations.value = response.data.conversations
        }
      } catch (error) {
        console.error('載入對話列表失敗:', error)
      }
    }
    
    const loadModels = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/chat/models`)
        if (response.data.success) {
          allModels.value = response.data.models
        }
      } catch (error) {
        console.error('載入模型列表失敗:', error)
      }
    }
    
    const loadMcpServers = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/mcp/servers`)
        if (response.data.success) {
          availableMcpServers.value = response.data.data
        }
      } catch (error) {
        console.error('載入 MCP servers 失敗:', error)
      }
    }
    
    const clearAllConversations = async () => {
      if (!confirm('確定要清空所有對話紀錄嗎?此操作無法復原!')) {
        return
      }
      
      try {
        const response = await axios.delete(`${API_URL}/api/chat/conversations/clear-all`)
        if (response.data.success) {
          conversations.value = []
          currentConversationId.value = null
          currentMessages.value = []
          alert(response.data.message)
        }
      } catch (error) {
        console.error('清空對話失敗:', error)
        alert('清空對話失敗: ' + error.message)
      }
    }
    
    const createNewConversation = async () => {
      try {
        const response = await axios.post(`${API_URL}/api/chat/conversations`, {
          title: `新對話 ${new Date().toLocaleString()}`,
          model_provider: selectedProvider.value,
          model_name: selectedModel.value,
          mcp_enabled: selectedMcpServers.value.length > 0,
          mcp_servers: selectedMcpServers.value
        })
        
        if (response.data.success) {
          await loadConversations()
          selectConversation(response.data.conversation_id)
        }
      } catch (error) {
        console.error('建立對話失敗:', error)
        alert('建立對話失敗: ' + error.message)
      }
    }
    
    const selectConversation = async (conversationId) => {
      try {
        isLoadingConfig.value = true // 標記正在載入配置,避免觸發 watch
        const response = await axios.get(`${API_URL}/api/chat/conversations/${conversationId}`)
        if (response.data.success) {
          currentConversationId.value = conversationId
          const conv = response.data.conversation
          currentMessages.value = conv.messages || []
          
          // 更新模型設定
          selectedProvider.value = conv.model_provider
          selectedModel.value = conv.model_name
          selectedMcpServers.value = conv.mcp_servers || []
          
          // 滾動到底部
          await nextTick()
          scrollToBottom()
        }
      } catch (error) {
        console.error('載入對話失敗:', error)
      } finally {
        // 使用 setTimeout 確保在 Vue 的 nextTick 之後才解除標記
        // 這能確保 watch 不會因為 selectConversation 的賦值而被觸發
        setTimeout(() => {
          isLoadingConfig.value = false
        }, 100)
      }
    }
    
    const sendMessage = async () => {
      if (!userInput.value.trim() || isLoading.value) return
      
      const message = userInput.value.trim()
      userInput.value = ''
      isLoading.value = true
      
      // 立即顯示使用者訊息
      currentMessages.value.push({
        role: 'user',
        content: message,
        created_at: new Date().toISOString()
      })
      
      await nextTick()
      scrollToBottom()
      
      try {
        const response = await axios.post(
          `${API_URL}/api/chat/conversations/${currentConversationId.value}/messages`,
          { content: message }
        )
        
        if (response.data.success) {
          currentMessages.value.push(response.data.message)
          await nextTick()
          scrollToBottom()
        }
      } catch (error) {
        console.error('發送訊息失敗:', error)
        alert('發送訊息失敗: ' + error.response?.data?.error || error.message)
      } finally {
        isLoading.value = false
      }
    }
    
    const updateConversationConfig = async () => {
      // 只有在選中了對話,且不是正在載入配置時才執行
      if (!currentConversationId.value || isLoadingConfig.value) return
      
      console.log("[Chatbot] 自動同步配置到後端...")
      try {
        await axios.patch(`${API_URL}/api/chat/conversations/${currentConversationId.value}`, {
          model_provider: selectedProvider.value,
          model_name: selectedModel.value,
          mcp_servers: selectedMcpServers.value
        })
        
        // 更新本地對話列表中的資料
        const conv = conversations.value.find(c => c.id === currentConversationId.value)
        if (conv) {
          conv.model_provider = selectedProvider.value
          conv.model_name = selectedModel.value
          conv.mcp_servers = selectedMcpServers.value
          conv.mcp_enabled = selectedMcpServers.value.length > 0
        }
      } catch (error) {
        console.error('更新對話配置失敗:', error)
      }
    }
    
    // 監看模型與 MCP 工具變更,自動同步
    watch([selectedProvider, selectedModel, selectedMcpServers], () => {
      updateConversationConfig()
    }, { deep: true })
    
    const updateModelList = () => {
      // 當供應商改變時,選擇第一個可用模型
      const models = availableModels.value
      if (models.length > 0) {
        selectedModel.value = models[0].name
      }
    }
    
    const toggleMcpServer = (serverId) => {
      const index = selectedMcpServers.value.indexOf(serverId)
      if (index === -1) {
        selectedMcpServers.value = [...selectedMcpServers.value, serverId]
      } else {
        selectedMcpServers.value = selectedMcpServers.value.filter(id => id !== serverId)
      }
    }
    
    const inputArea = ref(null)
    const adjustTextareaHeight = () => {
      const el = inputArea.value
      if (!el) return
      el.style.height = 'auto'
      el.style.height = (el.scrollHeight) + 'px'
    }
    
    const scrollToBottom = () => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }
    
    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
    }
    
    const formatJSON = (data) => {
      try {
        if (typeof data === 'string') {
          // 嘗試解析 JSON 字串
          const parsed = JSON.parse(data)
          return JSON.stringify(parsed, null, 2)
        }
        return JSON.stringify(data, null, 2)
      } catch (e) {
        // 如果不是 JSON,直接返回
        return String(data)
      }
    }
    
    // 初始化
    onMounted(async () => {
      await loadModels()
      await loadMcpServers()
      await loadConversations()
    })
    
    return {
      conversations,
      currentConversationId,
      currentMessages,
      userInput,
      isLoading,
      selectedProvider,
      selectedModel,
      availableModels,
      availableMcpServers,
      selectedMcpServers,
      messagesContainer,
      createNewConversation,
      selectConversation,
      sendMessage,
      updateModelList,
      clearAllConversations,
      formatTime,
      formatJSON,
      toggleMcpServer,
      adjustTextareaHeight,
      inputArea
    }
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

.chatbot-container {
  display: flex;
  height: 100vh;
  background: #f8fafc;
  font-family: 'Outfit', sans-serif;
  color: #1e293b;
  overflow: hidden;
}

/* 側邊欄 */
.sidebar {
  width: 320px;
  background: white;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.02);
  z-index: 10;
}

.sidebar-header {
  padding: 2rem 1.5rem;
}

.sidebar-header h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.4rem;
  font-weight: 700;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-new {
  width: 100%;
  padding: 0.8rem;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.btn-new:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(99, 102, 241, 0.4);
}

.btn-clear {
  width: 100%;
  padding: 0.8rem;
  margin-top: 0.75rem;
  background: white;
  color: #ef4444;
  border: 1.5px solid #fee2e2;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-clear:hover {
  background: #fef2f2;
  border-color: #fca5a5;
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem;
}

.conversations-list::-webkit-scrollbar {
  width: 5px;
}

.conversations-list::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}

.conversation-item {
  padding: 1.25rem;
  margin-bottom: 0.75rem;
  background: white;
  border: 1px solid #f1f5f9;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.conversation-item:hover {
  border-color: #cbd5e1;
  background: #f8fafc;
}

.conversation-item.active {
  background: #f1f5ff;
  border-color: #6366f1;
}

.conv-title {
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: #1e293b;
  font-size: 0.95rem;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.conv-meta {
  display: flex;
  gap: 0.5rem;
}

.provider-badge, .mcp-badge {
  padding: 0.25rem 0.6rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.provider-badge {
  background: #f1f5f9;
  color: #64748b;
}

.mcp-badge {
  background: #ecfdf5;
  color: #10b981;
}

/* 主聊天區 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  position: relative;
}

.chat-header {
  padding: 1rem 2rem;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 5;
  height: 80px; /* 固定高度避免晃動 */
}

.header-left {
  display: flex;
  gap: 2rem;
  flex-shrink: 0;
}

.selector-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.selector-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.modern-select {
  padding: 0.5rem 2rem 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: white;
  font-size: 0.9rem;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  outline: none;
  transition: all 0.2s;
}

.modern-select:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.header-right {
  display: flex;
  align-items: center;
  max-width: 50%; /* 限制寬度避免推擠 */
  overflow: hidden;
}

.mcp-chips-container {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  align-items: flex-end;
  width: 100%;
}

.mcp-chips {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto; /* 超過時可水平捲動 */
  padding-bottom: 4px;
  width: 100%;
  justify-content: flex-end;
}

.mcp-chips::-webkit-scrollbar {
  height: 3px;
}

.mcp-chip {
  padding: 0.4rem 0.8rem;
  border-radius: 10px;
  background: #f1f5f9;
  color: #64748b;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  border: 1.5px solid transparent;
  white-space: nowrap;
  flex-shrink: 0;
}

.mcp-chip:hover {
  background: #e2e8f0;
  color: #475569;
}

.mcp-chip.active {
  background: #eef2ff;
  color: #6366f1;
  border-color: #c7d2fe;
}

/* 訊息區 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 15% 2rem 15%;
  background: white;
}

@media (max-width: 1200px) {
  .messages-container { padding: 2rem 5%; }
}

.welcome-screen {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #94a3b8;
}

.welcome-screen h1 {
  font-size: 3.5rem;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.message {
  display: flex;
  gap: 1.25rem;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  background: #f1f5f9;
  flex-shrink: 0;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

.message-content {
  max-width: 85%;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.message-text {
  padding: 1.25rem;
  border-radius: 20px;
  background: #f8fafc;
  color: #334155;
  line-height: 1.6;
  font-size: 1rem;
  box-shadow: 0 2px 5px rgba(0,0,0,0.02);
  width: fit-content;
}

.message.user .message-text {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
  border-bottom-right-radius: 4px;
  box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.2);
  margin-left: auto;
}

.message.assistant .message-text {
  border-bottom-left-radius: 4px;
}

/* 工具調用樣式 */
.tool-calls {
  width: 100%;
  max-width: 800px;
}

.tool-call-item {
  margin-bottom: 0.75rem;
}

.tool-call-details {
  background: #1e293b;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.tool-call-summary {
  padding: 0.8rem 1.25rem;
  background: #334155;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #cbd5e1;
  font-weight: 600;
  font-size: 0.9rem;
  border-bottom: 1px solid #1e293b;
}

.tool-call-content { padding: 1rem; }
.section-label { color: #64748b; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; margin-bottom: 0.5rem; }
.code-block { background: #0f172a; color: #38bdf8; padding: 1.25rem; border-radius: 8px; font-family: 'Fira Code', monospace; font-size: 0.85rem; }

/* 輸入區 */
.input-wrapper {
  padding: 1.5rem 15%;
  background: linear-gradient(to bottom, rgba(255,255,255,0) 0%, white 100%);
  position: relative;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  background: white;
  padding: 0.75rem 1rem;
  border-radius: 24px;
  border: 2px solid #f1f5f9;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
}

.input-container:focus-within {
  border-color: #6366f1;
  box-shadow: 0 15px 35px -5px rgba(99, 102, 241, 0.1);
}

.input-container textarea {
  flex: 1;
  border: none;
  background: transparent;
  padding: 0.5rem;
  font-size: 1rem;
  max-height: 200px;
  resize: none;
  font-family: inherit;
  outline: none;
  line-height: 1.5;
}

.btn-send-modern {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background: #6366f1;
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.btn-send-modern:hover {
  background: #4f46e5;
  transform: scale(1.05);
}

.btn-send-modern:disabled {
  background: #e2e8f0;
  color: #94a3b8;
  cursor: not-allowed;
  transform: none;
}

.btn-send-modern svg { width: 20px; height: 20px; }

.btn-loader {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.message-time { font-size: 0.7rem; color: #94a3b8; margin-top: 0.5rem; font-weight: 500; }
.typing-indicator span { background: #cbd5e1; }
.empty-state { text-align: center; padding: 2rem; color: #94a3b8; font-style: italic; }
</style>
