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
      <!-- 頂部工具列已移除 -->

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
                  <div class="tool-call-header">
                    <span class="tool-icon">⚡</span>
                    <span class="tool-name">{{ call.function.name }}</span>
                    <span class="tool-badge">工具調用</span>
                  </div>
                  
                  <div class="tool-call-body">
                    <!-- Request -->
                    <div class="tool-section">
                      <div class="section-header">
                        <span class="section-icon">📤</span>
                        <span class="section-title">請求參數</span>
                      </div>
                      <div class="section-content">
                        <div v-for="(value, key) in parseToolArguments(call.function.arguments)" :key="key" class="param-item">
                          <span class="param-key">{{ key }}</span>
                          <span class="param-value">{{ value }}</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- Response -->
                    <div v-if="call.result" class="tool-section">
                      <div class="section-header">
                        <span class="section-icon">📥</span>
                        <span class="section-title">回應結果</span>
                      </div>
                      <div class="section-content">
                        <div v-for="(value, key) in parseToolResult(call.result)" :key="key" class="result-item">
                          <span class="result-key">{{ formatKey(key) }}</span>
                          <span class="result-value">{{ value }}</span>
                        </div>
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

      <!-- 輸入區 (整合版) -->
      <div class="input-wrapper">
        <div class="input-integrated-container">
          <!-- 上排: + 按鈕 與 輸入框 -->
          <div class="input-top-row">
            <div class="accordion-wrapper">
              <button 
                class="btn-plus" 
                @click="showMcpMenu = !showMcpMenu"
                :title="selectedMcpServers.length > 0 ? `已選 ${selectedMcpServers.length} 個工具` : '新增工具'"
                :class="{ 'has-selection': selectedMcpServers.length > 0 }"
              >
                <span>➕</span>
              </button>
              
              <!-- MCP 選單 Popup -->
              <div v-if="showMcpMenu" class="popover-menu mcp-menu-left">
                <div class="popover-header">
                  <span class="popover-title">MCP 工具</span>
                  <button class="btn-close-popover" @click="showMcpMenu = false">✕</button>
                </div>
                <div class="popover-content">
                  <div v-if="availableMcpServers.length === 0" class="empty-popover">無可用工具</div>
                  <div 
                    v-else
                    v-for="server in availableMcpServers" 
                    :key="server.name"
                    class="menu-item"
                    :class="{ active: selectedMcpServers.includes(server.name) }"
                    @click="toggleMcpServer(server.name)"
                  >
                    <span class="check-icon">{{ selectedMcpServers.includes(server.name) ? '☑️' : '⬜' }}</span>
                    <span class="menu-label">{{ server.name }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Backdrop for closing -->
              <div v-if="showMcpMenu" class="popover-backdrop" @click="showMcpMenu = false"></div>
            </div>

            <textarea
              v-model="userInput"
              @keydown.enter.exact.prevent="sendMessage"
              :placeholder="currentConversationId ? '輸入訊息... (Enter 發送, Shift+Enter 換行)' : '請先選擇左側對話或建立新對話'"
              :disabled="!currentConversationId || isLoading"
              rows="1"
              ref="inputArea"
              @input="adjustTextareaHeight"
              class="main-textarea"
            ></textarea>
          </div>
          
          <!-- 下排: 工具標籤 與 右側動作 -->
          <div class="input-bottom-row">
            <div class="active-tools-display">
              <span v-if="validSelectedMcpServers.length > 0" class="mini-label">已啟用:</span>
              <span 
                v-for="server in validSelectedMcpServers" 
                :key="server" 
                class="mini-chip"
                @click="toggleMcpServer(server)"
              >
                {{ server }} ✕
              </span>
            </div>
            
            <div class="right-actions">
              <!-- 模型選擇器觸發 -->
              <div class="model-selector-wrapper">
                <button 
                  class="btn-model-trigger" 
                  @click="showModelMenu = !showModelMenu"
                >
                  <span class="provider-dot" :class="selectedProvider"></span>
                  {{ selectedModel }}
                  <span class="arrow-icon">▼</span>
                </button>
                
                <!-- 模型選單 Popup -->
                <div v-if="showModelMenu" class="popover-menu model-menu-right">
                   <div class="popover-header">
                    <span class="popover-title">模型設定</span>
                    <button class="btn-close-popover" @click="showModelMenu = false">✕</button>
                  </div>
                  <div class="popover-content p-2">
                    <div class="form-group">
                      <label>供應商</label>
                      <select v-model="selectedProvider" @change="updateModelList" class="popup-select">
                        <option value="openai">OpenAI</option>
                        <option value="google">Google</option>
                        <option value="anthropic">Anthropic</option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label>模型</label>
                      <select v-model="selectedModel" class="popup-select">
                        <option v-for="model in availableModels" :key="model.name" :value="model.name">
                          {{ model.display_name }}
                        </option>
                      </select>
                    </div>
                  </div>
                </div>
                <!-- Backdrop for closing -->
                <div v-if="showModelMenu" class="popover-backdrop" @click="showModelMenu = false"></div>
              </div>

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
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import axios from 'axios'
import Swal from 'sweetalert2'

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
    const autoRefreshInterval = ref(null)
    const currentConversationSource = ref(null)
    
    // UI 狀態
    const showMcpMenu = ref(false)
    const showModelMenu = ref(false)
    
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
          const result = response.data.data
          let servers = []
          
          if (result.mcpServers) {
            servers = Object.entries(result.mcpServers).map(([name, config]) => ({
              name,
              ...config
            }))
          } else if (Array.isArray(result)) {
            servers = result
          } else if (typeof result === 'object') {
            servers = Object.entries(result).map(([name, config]) => ({
              name,
              ...config
            }))
          }
          
          availableMcpServers.value = servers
        }
      } catch (error) {
        console.error('載入 MCP servers 失敗:', error)
      }
    }
    
    const clearAllConversations = async () => {
      const result = await Swal.fire({
        title: '確定要清空嗎?',
        text: '確定要清空所有對話紀錄嗎? 此操作無法復原!',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: '確定清空',
        cancelButtonText: '取消'
      })
      
      if (!result.isConfirmed) return
      
      const loadingTimer = setTimeout(() => {
        Swal.fire({
          title: '正在清空...',
          text: '正在刪除所有對話紀錄，請稍後...',
          allowOutsideClick: false,
          didOpen: () => Swal.showLoading()
        })
      }, 3000)

      try {
        const response = await axios.delete(`${API_URL}/api/chat/conversations/clear-all`)
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()

        if (response.data.success) {
          conversations.value = []
          currentConversationId.value = null
          currentMessages.value = []
          Swal.fire({
            icon: 'success',
            title: '已清空',
            text: response.data.message,
            timer: 1500,
            showConfirmButton: false
          })
        }
      } catch (error) {
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()
        console.error('清空對話失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '清空失敗',
          text: error.message
        })
      }
    }
    
    const createNewConversation = async () => {
      const loadingTimer = setTimeout(() => {
        Swal.fire({
          title: '正在建立對話...',
          text: '正在初始化聊天環境，請稍後...',
          allowOutsideClick: false,
          didOpen: () => Swal.showLoading()
        })
      }, 3000)

      try {
        const response = await axios.post(`${API_URL}/api/chat/conversations`, {
          title: `新對話 ${new Date().toLocaleString()}`,
          model_provider: selectedProvider.value,
          model_name: selectedModel.value,
          mcp_enabled: selectedMcpServers.value.length > 0,
          mcp_servers: selectedMcpServers.value
        })
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()
        
        if (response.data.success) {
          await loadConversations()
          selectConversation(response.data.conversation_id)
        }
      } catch (error) {
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()
        console.error('建立對話失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '建立對話失敗',
          text: error.message
        })
      }
    }
    
    const selectConversation = async (conversationId) => {
      try {
        // 清除舊的自動刷新
        if (autoRefreshInterval.value) {
          clearInterval(autoRefreshInterval.value)
          autoRefreshInterval.value = null
        }
        
        isLoadingConfig.value = true // 標記正在載入配置,避免觸發 watch
        const response = await axios.get(`${API_URL}/api/chat/conversations/${conversationId}`)
        if (response.data.success) {
          currentConversationId.value = conversationId
          const conv = response.data.conversation
          currentMessages.value = conv.messages || []
          currentConversationSource.value = conv.source
          
          // 更新模型設定
          selectedProvider.value = conv.model_provider
          selectedModel.value = conv.model_name
          selectedMcpServers.value = conv.mcp_servers || []
          
          // 如果是 LINE 對話,啟動自動刷新
          if (conv.source === 'line') {
            console.log('[LINE] 啟動自動刷新,每 5 秒更新一次')
            autoRefreshInterval.value = setInterval(async () => {
              await refreshMessages()
            }, 5000)
          }
          
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
    
    const refreshMessages = async () => {
      if (!currentConversationId.value) return
      
      try {
        console.log('[LINE] 執行自動刷新...')
        const response = await axios.get(`${API_URL}/api/chat/conversations/${currentConversationId.value}`)
        if (response.data.success) {
          const conv = response.data.conversation
          const newMessages = conv.messages || []
          
          console.log(`[LINE] 當前訊息數: ${currentMessages.value.length}, 新訊息數: ${newMessages.length}`)
          
          // 比較訊息數量或最後一則訊息的時間戳
          const shouldUpdate = 
            newMessages.length !== currentMessages.value.length ||
            (newMessages.length > 0 && currentMessages.value.length > 0 &&
             newMessages[newMessages.length - 1].created_at !== currentMessages.value[currentMessages.value.length - 1].created_at)
          
          if (shouldUpdate) {
            console.log('[LINE] 檢測到新訊息,更新中...')
            currentMessages.value = newMessages
            await nextTick()
            scrollToBottom()
          } else {
            console.log('[LINE] 無新訊息')
          }
        }
      } catch (error) {
        console.error('刷新訊息失敗:', error)
      }
    }
    
    // 工具過濾
    const validSelectedMcpServers = computed(() => {
      const availableNames = availableMcpServers.value.map(s => s.name)
      return selectedMcpServers.value.filter(name => availableNames.includes(name))
    })

    const sendMessage = async () => {
      if (!userInput.value.trim() || isLoading.value) return
      
      const message = userInput.value.trim()
      userInput.value = ''
      isLoading.value = true
      
      const loadingTimer = setTimeout(() => {
        Swal.fire({
          title: '正在等待回應...',
          text: 'AI 正在處理您的請求，請稍後...',
          allowOutsideClick: false,
          didOpen: () => Swal.showLoading()
        })
      }, 3000)

      // 立即顯示使用者訊息
      currentMessages.value.push({
        role: 'user',
        content: message,
        created_at: new Date().toISOString()
      })
      
      await nextTick()
      scrollToBottom()
      
      try {
        let response
        
        // 根據對話來源選擇不同的 API
        if (currentConversationSource.value === 'line') {
          // LINE 對話:發送到 LINE
          console.log('[LINE] 發送訊息到 LINE')
          response = await axios.post(
            `${API_URL}/api/line/conversations/${currentConversationId.value}/send`,
            { content: message }
          )
          
          if (response.data.success) {
            console.log('[LINE] 訊息已發送到 LINE,等待自動刷新...')
            // 立即刷新一次
            await refreshMessages()
          }
        } else {
          // Web 對話:正常處理
          response = await axios.post(
            `${API_URL}/api/chat/conversations/${currentConversationId.value}/messages`,
            { content: message }
          )
          
          if (response.data.success) {
            currentMessages.value.push(response.data.message)
            await nextTick()
            scrollToBottom()
          }
        }
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()
      } catch (error) {
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()
        console.error('發送訊息失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '發送失敗',
          text: (error.response?.data?.error || error.message)
        })
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
    
    const parseToolArguments = (args) => {
      try {
        if (typeof args === 'string') {
          return JSON.parse(args)
        }
        return args
      } catch (e) {
        return { error: '無法解析參數' }
      }
    }
    
    const parseToolResult = (result) => {
      try {
        if (typeof result === 'string') {
          return JSON.parse(result)
        }
        return result
      } catch (e) {
        return { result: String(result) }
      }
    }
    
    const formatKey = (key) => {
      // 將 snake_case 或 camelCase 轉換成可讀的格式
      const formatted = key
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .trim()
      return formatted.charAt(0).toUpperCase() + formatted.slice(1)
    }

    
    // 初始化
    onMounted(async () => {
      await loadModels()
      await loadMcpServers()
      await loadConversations()
    })
    
    // 清理
    onUnmounted(() => {
      if (autoRefreshInterval.value) {
        clearInterval(autoRefreshInterval.value)
        autoRefreshInterval.value = null
      }
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
      parseToolArguments,
      parseToolResult,
      formatKey,
      toggleMcpServer,
      adjustTextareaHeight,
      inputArea,
      showMcpMenu,
      showModelMenu,
      currentConversationSource,
      validSelectedMcpServers
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
/* 主聊天區 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  position: relative;
  overflow: hidden; /* 關鍵修正: 防止主區域撐開導致父容器截斷 */
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
  height: 80px; 
  flex-shrink: 0; /* 防止 Header 被壓縮 */
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

/* 美化後的 MCP Chip 樣式 - 簡約版 */
.mcp-chip {
  padding: 0.4rem 0.8rem;
  border-radius: 8px;
  background: white;
  color: #64748b;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid #e2e8f0;
  white-space: nowrap;
  flex-shrink: 0;
}

.mcp-chip:hover {
  border-color: #94a3b8;
  color: #475569;
  background: #f8fafc;
}

.mcp-chip.active {
  background: #eff6ff; /* 淺藍色背景 */
  color: #4f46e5;      /* 靛藍色文字 */
  border-color: #6366f1;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.1);
}

.mcp-chip.active:hover {
  background: #e0e7ff;
}

.mcp-chip.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f1f5f9;
  border-color: #e2e8f0;
  box-shadow: none;
}

.mcp-chip.disabled:hover {
  transform: none;
  border-color: #e2e8f0;
}

.modern-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f8fafc;
}

/* 訊息區 - 修正為正確的 Class 名稱 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 15% 2rem 15%;
  background: white;
  scroll-behavior: smooth;
  min-height: 0; /* 關鍵修正: 允許 Flex 子元素收縮產生捲動 */
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
/* 工具調用顯示 - 易讀格式 */
.tool-calls {
  width: 100%;
  max-width: 800px;
}

.tool-call-item {
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.tool-call-header {
  padding: 1rem 1.25rem;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: white;
}

.tool-call-header .tool-icon {
  font-size: 1.5rem;
}

.tool-call-header .tool-name {
  font-weight: 700;
  font-size: 1.1rem;
  flex: 1;
}

.tool-badge {
  padding: 0.25rem 0.75rem;
  background: rgba(255,255,255,0.2);
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.tool-call-body {
  padding: 1.25rem;
}

.tool-section {
  margin-bottom: 1.25rem;
}

.tool-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e2e8f0;
}

.section-icon {
  font-size: 1.25rem;
}

.section-title {
  font-weight: 700;
  color: #334155;
  font-size: 0.95rem;
}

.section-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.param-item, .result-item {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #f1f5f9;
}

.param-key, .result-key {
  font-weight: 600;
  color: #64748b;
  font-size: 0.85rem;
  min-width: 100px;
  flex-shrink: 0;
}

.param-value, .result-value {
  color: #1e293b;
  font-size: 0.95rem;
  word-break: break-word;
  flex: 1;
}

.result-value {
  font-weight: 500;
}


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

/* 輸入區新樣式 */
.input-wrapper {
  padding: 1.5rem 15%;
  background: white; /* 不需要漸層了，因為沒有頂部遮擋 */
  position: relative;
  z-index: 20; /* 確保 Popover 在最上層 */
}

.input-integrated-container {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 0.75rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.input-integrated-container:focus-within {
  border-color: #6366f1;
  background: white;
  box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.1);
}

.input-top-row {
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
}

.accordion-wrapper {
  position: relative;
}

.btn-plus {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid #e2e8f0;
  background: white;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  transition: all 0.2s;
  padding: 0;
  flex-shrink: 0;
  margin-top: 2px; /* align with textarea text */
}

.btn-plus:hover {
  background: #f1f5f9;
  color: #334155;
  border-color: #cbd5e1;
}

.btn-plus.has-selection {
  background: #eff6ff;
  color: #6366f1;
  border-color: #c7d2fe;
}

.btn-plus:disabled,
.btn-plus:disabled:hover {
  background: #f1f5f9;
  color: #cbd5e1;
  border-color: #e2e8f0;
  cursor: not-allowed;
}

.tool-count {
  font-size: 0.8rem;
  font-weight: 700;
}

.main-textarea {
  flex: 1;
  border: none;
  background: transparent;
  padding: 0.5rem 0;
  font-size: 1rem;
  max-height: 200px;
  resize: none;
  outline: none;
  line-height: 1.5;
  color: #1e293b;
  min-height: 40px;
}

.input-bottom-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.2rem;
}

.active-tools-display {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.mini-label {
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 600;
}

.mini-chip {
  font-size: 0.75rem;
  padding: 0.1rem 0.5rem;
  background: #eff6ff;
  color: #4f46e5;
  border-radius: 4px;
  cursor: pointer;
}

.mini-chip:hover {
  background: #e0e7ff;
  text-decoration: line-through; 
}

.right-actions {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-left: auto;
}

.model-selector-wrapper {
  position: relative;
}

.btn-model-trigger {
  background: transparent;
  border: none;
  color: #64748b;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.8rem;
  border-radius: 8px;
  transition: all 0.2s;
}

.btn-model-trigger:hover {
  background: #f1f5f9;
  color: #334155;
}

.provider-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e1;
}

.provider-dot.openai { background: #10a37f; }
.provider-dot.google { background: #4285f4; }
.provider-dot.anthropic { background: #da7756; }

.arrow-icon {
  font-size: 0.6rem;
  opacity: 0.5;
}

.btn-send-modern {
  width: 40px;
  height: 40px;
  border-radius: 12px;
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

.btn-send-modern svg { width: 18px; height: 18px; }

/* Popover Styles */
.popover-menu {
  position: absolute;
  bottom: 100%; /* pop up above */
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(0,0,0,0.05);
  margin-bottom: 0.8rem;
  min-width: 220px;
  z-index: 100;
  overflow: hidden;
  animation: popIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.mcp-menu-left {
  left: 0;
}

.model-menu-right {
  right: 0;
}

.popover-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 99;
  cursor: default;
}

.popover-header {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8fafc;
}

.popover-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
}

.btn-close-popover {
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
}

.popover-content {
  max-height: 300px;
  overflow-y: auto;
  padding: 0.5rem;
}

.menu-item {
  padding: 0.6rem 0.8rem;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  transition: all 0.2s;
  color: #334155;
  font-size: 0.9rem;
}

.menu-item:hover {
  background: #f1f5f9;
}

.menu-item.active {
  background: #eff6ff;
  color: #4f46e5;
  font-weight: 500;
}

.empty-popover {
  padding: 1rem;
  text-align: center;
  color: #94a3b8;
  font-style: italic;
  font-size: 0.9rem;
}

.p-2 { padding: 0.75rem; }

.form-group {
  margin-bottom: 0.8rem;
}

.form-group:last-child { margin-bottom: 0; }

.form-group label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 0.3rem;
}

.popup-select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  outline: none;
  font-size: 0.9rem;
  color: #1e293b;
}

.popup-select:focus {
  border-color: #6366f1;
}

@keyframes popIn {
  from { opacity: 0; transform: translateY(10px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

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
