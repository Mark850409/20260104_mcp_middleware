<template>
  <div class="chatbot-wrapper">
    <!-- 側邊欄 - 對話列表 -->
    <aside class="conversations-sidebar">
      <div class="sidebar-header">
        <h2>對話列表</h2>
        <div class="header-actions">
          <button v-if="hasFunctionPermission('func_chat_create')" @click="createNewConversation" class="btn-new">
            <i class="ri-add-circle-line"></i> 新對話
          </button>
          <button v-if="hasFunctionPermission('func_chat_delete')" @click="clearAllConversations" class="btn-clear">
            <i class="ri-delete-bin-6-line"></i> 清空
          </button>
        </div>
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
              <i :class="message.role === 'user' ? 'ri-user-3-line' : 'ri-robot-line'"></i>
            </div>
            <div class="message-content">
              <!-- MCP 工具調用顯示 (先顯示) -->
              <div v-if="message.tool_calls && message.tool_calls.length > 0" class="tool-calls">
                <div v-for="(call, idx) in message.tool_calls" :key="idx" class="tool-call-item">
                  <div class="tool-call-header" @click="toggleToolCall(call)">
                    <span class="tool-icon"><i class="ri-flashlight-line"></i></span>
                    <span class="tool-name">{{ call.function.name }}</span>
                    <span class="tool-badge">工具調用</span>
                    <span class="toggle-icon" :class="{ rotated: !call.collapsed }">
                      <i class="ri-arrow-down-s-line"></i>
                    </span>
                  </div>
                  
                  <div class="tool-call-body-wrapper" :class="{ expanded: !call.collapsed }">
                    <div class="tool-call-body-inner">
                      <div class="tool-call-body">
                        <!-- Request -->
                        <div class="tool-section">
                          <div class="section-header">
                            <span class="section-icon"><i class="ri-upload-2-line"></i></span>
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
                            <span class="section-icon"><i class="ri-download-2-line"></i></span>
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
                </div>
              </div>

              <!-- 答案內容 (後顯示) -->
              <div v-if="message.content" class="message-text markdown-body" v-html="renderMarkdown(message.content)"></div>
              
              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </div>
          
          <div v-if="isLoading" class="message assistant">
            <div class="message-avatar"><i class="ri-robot-line"></i></div>
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
                <i :class="selectedMcpServers.length > 0 ? 'ri-tools-fill' : 'ri-add-line'"></i>
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
                    <span class="check-icon">
                      <i :class="selectedMcpServers.includes(server.name) ? 'ri-checkbox-fill' : 'ri-checkbox-blank-line'"></i>
                    </span>
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
                  <span class="arrow-icon"><i class="ri-arrow-down-s-line"></i></span>
                </button>
                
                <!-- 模型選單 Popup -->
                <div v-if="showModelMenu" class="popover-menu model-menu-right">
                   <div class="popover-header">
                    <span class="popover-title">模型設定</span>
                    <button class="btn-close-popover" @click="showModelMenu = false">✕</button>
                  </div>
                  <div class="popover-content p-2">
                    <div class="form-group">
                      <label>使用 Agent</label>
                      <select v-model="selectedAgentId" @change="onAgentChange" class="popup-select">
                        <option :value="null">無 (自訂模式)</option>
                        <option v-for="agent in availableAgents" :key="agent.id" :value="agent.id">
                          {{ agent.name }}
                        </option>
                      </select>
                      <div v-if="selectedAgentId" class="agent-hint">
                        🤖 使用 Agent 時,模型和工具由 Agent 管理
                      </div>
                    </div>
                    <div class="form-group">
                      <label>供應商</label>
                      <select v-model="selectedProvider" @change="updateModelList" class="popup-select" :disabled="!!selectedAgentId">
                        <option value="openai">OpenAI</option>
                        <option value="google">Google</option>
                        <option value="anthropic">Anthropic</option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label>模型</label>
                      <select v-model="selectedModel" class="popup-select" :disabled="!!selectedAgentId">
                        <option v-for="model in availableModels" :key="model.name" :value="model.name">
                          {{ model.display_name }}
                        </option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label>系統提示詞</label>
                      <select v-model="selectedPromptId" class="popup-select" :disabled="!!selectedAgentId">
                        <option :value="null">無系統提示詞</option>
                        <option v-for="prompt in availablePrompts" :key="prompt.id" :value="prompt.id">
                          {{ prompt.name }} {{ prompt.is_default ? '(預設)' : '' }}
                        </option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label>知識庫 (RAG)</label>
                      <select v-model="selectedKbId" class="popup-select" :disabled="!!selectedAgentId">
                        <option :value="null">不使用知識庫</option>
                        <option v-for="kb in availableKbs" :key="kb.id" :value="kb.id">
                          {{ kb.name }}
                        </option>
                      </select>
                    </div>
                  </div>
                </div>
                <!-- Backdrop for closing -->
                <div v-if="showModelMenu" class="popover-backdrop" @click="showModelMenu = false"></div>
              </div>

              <button
                v-if="hasFunctionPermission('func_chat_create')"
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
import request from '../utils/request'
import Swal from 'sweetalert2'
import { marked } from 'marked'
import { useAuth } from '../composables/useAuth'

// 配置 marked
marked.setOptions({
  breaks: true, // 支援換行
  gfm: true, // 啟用 GitHub Flavored Markdown
  headerIds: false,
  mangle: false
})

export default {
  name: 'Chatbot',
  setup() {
    const { hasFunctionPermission } = useAuth()
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
    const selectedPromptId = ref(null)
    const mcpEnabled = ref(false)
    const allModels = ref({})
    const availablePrompts = ref([])
    const availableKbs = ref([])
    const selectedKbId = ref(null)
    const messagesContainer = ref(null)
    
    // 計算屬性
    const availableModels = computed(() => {
      return allModels.value[selectedProvider.value] || []
    })
    
    // MCP Servers
    const availableMcpServers = ref([])
    const selectedMcpServers = ref([])
    
    // Agents
    const availableAgents = ref([])
    const selectedAgentId = ref(null)
    
    // 方法
    const loadConversations = async () => {
      try {
        const response = await request.get('/api/chat/conversations')
        if (response.data.success) {
          conversations.value = response.data.conversations
        }
      } catch (error) {
        console.error('載入對話列表失敗:', error)
      }
    }
    
    const loadModels = async () => {
      try {
        const response = await request.get('/api/chat/models')
        if (response.data.success) {
          allModels.value = response.data.models
        }
      } catch (error) {
        console.error('載入模型列表失敗:', error)
      }
    }
    
    const loadMcpServers = async () => {
      try {
        const response = await request.get('/api/mcp/servers')
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

    const loadPrompts = async () => {
      try {
        const response = await request.get('/api/prompts')
        if (response.data.success) {
          availablePrompts.value = response.data.prompts
          // 如果沒有選中且有預設，則選中預設
          if (!selectedPromptId.value) {
            const defaultPrompt = availablePrompts.value.find(p => p.is_default)
            if (defaultPrompt) {
              selectedPromptId.value = defaultPrompt.id
            }
          }
        }
      } catch (error) {
        console.error('載入提示詞失敗:', error)
      }
    }

    const loadKbs = async () => {
      try {
        const response = await request.get('/api/rag/kb')
        if (response.data.success) {
          availableKbs.value = response.data.data
        }
      } catch (error) {
        console.error('載入知識庫失敗:', error)
      }
    }
    
    const loadAgents = async () => {
      try {
        const response = await request.get('/api/agents')
        if (response.data.success) {
          availableAgents.value = response.data.agents
        }
      } catch (error) {
        console.error('載入 Agents 失敗:', error)
      }
    }
    
    const onAgentChange = async () => {
      if (selectedAgentId.value) {
        // 載入 Agent 配置
        try {
          const response = await request.get(`/api/agents/${selectedAgentId.value}`)
          if (response.data.success) {
            const agent = response.data.agent
            
            // 套用 Agent 配置
            selectedProvider.value = agent.model_provider
            selectedModel.value = agent.model_name
            selectedPromptId.value = agent.system_prompt_id
            
            // 載入知識庫 (取第一個)
            if (agent.knowledge_bases && agent.knowledge_bases.length > 0) {
              selectedKbId.value = agent.knowledge_bases[0].id
            } else {
              selectedKbId.value = null
            }
            
            // 載入 MCP 工具
            if (agent.mcp_tools && agent.mcp_tools.length > 0) {
              selectedMcpServers.value = agent.mcp_tools.map(tool => tool.mcp_server_name)
            } else {
              selectedMcpServers.value = []
            }
            
            console.log(`[Agent] 已套用 Agent "${agent.name}" 的配置`)
          }
        } catch (error) {
          console.error('載入 Agent 配置失敗:', error)
          Swal.fire({
            icon: 'error',
            title: '載入 Agent 失敗',
            text: error.message
          })
        }
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

      try {
        const response = await request.delete('/api/chat/conversations/clear-all')

        if (response.data.success) {
          conversations.value = []
          currentConversationId.value = null
          currentMessages.value = []
          Swal.fire({
            icon: 'success',
            title: '已清空',
            text: response.data.message,
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 2000
          })
        }
      } catch (error) {
        console.error('清空對話失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '清空失敗',
          text: error.message,
          toast: true,
          position: 'top-end',
          showConfirmButton: false,
          timer: 3000
        })
      }
    }
    
    const createNewConversation = async () => {
      try {
        const payload = {
          title: `新對話 ${new Date().toLocaleString()}`,
          agent_id: selectedAgentId.value
        }
        
        // 如果沒有使用 Agent,使用自訂配置
        if (!selectedAgentId.value) {
          payload.model_provider = selectedProvider.value
          payload.model_name = selectedModel.value
          payload.mcp_enabled = selectedMcpServers.value.length > 0
          payload.mcp_servers = selectedMcpServers.value
          payload.system_prompt_id = selectedPromptId.value
          payload.kb_id = selectedKbId.value
        }
        
        const response = await request.post('/api/chat/conversations', payload)
        
        if (response.data.success) {
          await loadConversations()
          selectConversation(response.data.conversation_id)
        }
      } catch (error) {
        console.error('建立對話失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '建立對話失敗',
          text: error.message,
          toast: true,
          position: 'top-end',
          showConfirmButton: false,
          timer: 3000
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
        const response = await request.get(`/api/chat/conversations/${conversationId}`)
        if (response.data.success) {
          currentConversationId.value = conversationId
          const conv = response.data.conversation
          // 初始化工具調用折疊狀態
          if (conv.messages) {
            conv.messages.forEach(msg => {
              if (msg.tool_calls) {
                msg.tool_calls.forEach(call => {
                  call.collapsed = true
                })
              }
            })
          }
          currentMessages.value = conv.messages || []
          currentConversationSource.value = conv.source
          
          // 更新模型設定
          selectedProvider.value = conv.model_provider
          selectedModel.value = conv.model_name
          selectedMcpServers.value = conv.mcp_servers || []
          selectedPromptId.value = conv.system_prompt_id || null
          selectedKbId.value = conv.kb_id || null
          selectedAgentId.value = conv.agent_id || null
          
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
        const response = await request.get(`/api/chat/conversations/${currentConversationId.value}`)
        if (response.data.success) {
          const conv = response.data.conversation
          const newMessages = conv.messages || []
          
          // 為新訊息初始化工具折疊狀態
          newMessages.forEach(msg => {
            if (msg.tool_calls) {
              msg.tool_calls.forEach(call => {
                // 如果已經存在且狀態被手動改變過，保持狀態，否則預設折疊
                // 這裡簡化處理，因為是替換整個陣列，我們嘗試保留舊狀態比較複雜
                // 但如果是增量更新，新訊息預設折疊是合理的
                call.collapsed = true
              })
            }
          })
          
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
          response = await request.post(
            `/api/line/conversations/${currentConversationId.value}/send`,
            { content: message }
          )
          
          if (response.data.success) {
            console.log('[LINE] 訊息已發送到 LINE,等待自動刷新...')
            // 立即刷新一次
            await refreshMessages()
          }
        } else {
          // Web 對話:正常處理
          response = await request.post(
            `/api/chat/conversations/${currentConversationId.value}/messages`,
            { content: message }
          )
          
          if (response.data.success) {
            currentMessages.value.push(response.data.message)
            await nextTick()
            scrollToBottom()
          }
        }
      } catch (error) {
        console.error('發送訊息失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '發送失敗',
          text: (error.response?.data?.error || error.message),
          toast: true,
          position: 'top-end',
          showConfirmButton: false,
          timer: 3000
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
        await request.patch(`/api/chat/conversations/${currentConversationId.value}`, {
          model_provider: selectedProvider.value,
          model_name: selectedModel.value,
          mcp_servers: selectedMcpServers.value,
          system_prompt_id: selectedPromptId.value,
          kb_id: selectedKbId.value
        })
        
        // 更新本地對話列表中的資料
        const conv = conversations.value.find(c => c.id === currentConversationId.value)
        if (conv) {
          conv.model_provider = selectedProvider.value
          conv.model_name = selectedModel.value
          conv.mcp_servers = selectedMcpServers.value
          conv.mcp_enabled = selectedMcpServers.value.length > 0
          conv.system_prompt_id = selectedPromptId.value
        }
      } catch (error) {
        console.error('更新對話配置失敗:', error)
      }
    }
    
    // 監看模型與 MCP 工具、提示詞、知識庫變更,自動同步
    watch([selectedProvider, selectedModel, selectedMcpServers, selectedPromptId, selectedKbId], () => {
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
    
    const toggleToolCall = (call) => {
      call.collapsed = !call.collapsed
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

    const renderMarkdown = (content) => {
      if (!content) return ''
      try {
        let processedContent = content
        
        // 如果已經有程式碼標記,直接渲染
        if (content.includes('```')) {
          return marked.parse(content)
        }
        
        // 檢測程式碼片段並自動包裹
        // 匹配常見的程式碼模式
        const codeBlockRegex = /((?:^|\n)(?:def |class |import |from |print\(|console\.log|function |const |let |var |public |private |#include|package |<?php)[\s\S]*?)(?=\n\n|\n[^\s]|$)/g
        
        // 簡單的行內程式碼檢測
        const inlineCodeRegex = /\b(print\([^)]+\)|console\.log\([^)]+\)|def \w+|class \w+|function \w+)\b/g
        
        // 檢查是否包含程式碼
        if (codeBlockRegex.test(content) || inlineCodeRegex.test(content)) {
          // 重置 regex
          codeBlockRegex.lastIndex = 0
          inlineCodeRegex.lastIndex = 0
          
          // 嘗試智能分割內容
          const lines = content.split('\n')
          const result = []
          let i = 0
          
          while (i < lines.length) {
            const line = lines[i]
            
            // 檢查是否是程式碼行
            const isCodeStart = /^(def |class |import |from |print\(|console\.log|function |const |let |var |public |private |#include|package |<?php)/.test(line.trim())
            
            if (isCodeStart) {
              // 收集程式碼區塊
              const codeLines = []
              let lang = 'python' // 預設語言
              
              // 根據關鍵字判斷語言
              if (/^(console\.log|function |const |let |var )/.test(line.trim())) {
                lang = 'javascript'
              } else if (/^(public |private |class \w+\s*{)/.test(line.trim())) {
                lang = 'java'
              } else if (/^(#include|using namespace)/.test(line.trim())) {
                lang = 'cpp'
              } else if (/^(<?php)/.test(line.trim())) {
                lang = 'php'
              }
              
              codeLines.push(line)
              i++
              
              // 繼續收集程式碼行
              while (i < lines.length) {
                const nextLine = lines[i]
                // 如果是空行或縮排行,繼續
                if (nextLine.trim() === '' || /^(\s{2,}|\t)/.test(nextLine)) {
                  codeLines.push(nextLine)
                  i++
                } else if (/^(def |class |import |from |print\(|return |if |else|for |while |try |except )/.test(nextLine.trim())) {
                  // 繼續程式碼
                  codeLines.push(nextLine)
                  i++
                } else {
                  // 結束程式碼區塊
                  break
                }
              }
              
              // 添加程式碼區塊
              result.push('```' + lang)
              result.push(...codeLines)
              result.push('```')
            } else {
              // 普通文字行
              result.push(line)
              i++
            }
          }
          
          processedContent = result.join('\n')
        }
        
        return marked.parse(processedContent)
      } catch (e) {
        console.error('Markdown 渲染失敗:', e)
        return content.replace(/\n/g, '<br>')
      }
    }

    
    // 初始化
    onMounted(async () => {
      await loadModels()
      await loadMcpServers()
      await loadPrompts()
      await loadKbs()
      await loadAgents()
      await loadConversations()
      
      // 檢查是否有測試對話需要開啟
      const testConversationId = localStorage.getItem('test_conversation_id')
      if (testConversationId) {
        localStorage.removeItem('test_conversation_id')
        selectConversation(parseInt(testConversationId))
      }
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
      hasFunctionPermission,
      parseToolArguments,
      parseToolResult,
      formatKey,
      renderMarkdown,
      toggleMcpServer,
      adjustTextareaHeight,
      inputArea,
      showMcpMenu,
      showModelMenu,
      currentConversationSource,
      validSelectedMcpServers,
      availablePrompts,
      selectedPromptId,
      availableKbs,
      selectedKbId,
      availableAgents,
      selectedAgentId,
      onAgentChange,
      toggleToolCall
    }
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* 根容器樣式 */
.chatbot-wrapper {
  display: flex;
  height: calc(100vh - var(--topbar-height));
  font-family: 'Outfit', sans-serif;
  overflow: hidden;
  position: relative;
}

/* 側邊欄 - 對話列表 */
.conversations-sidebar {
  width: 320px;
  background: var(--color-background-secondary);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 10px rgba(0, 0, 0, 0.02);
  z-index: 10;
  flex-shrink: 0;
  position: relative;
}

.sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 200px;
  background: linear-gradient(180deg, rgba(102, 126, 234, 0.1) 0%, transparent 100%);
  pointer-events: none;
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.sidebar-header h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-new {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 16px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 
    0 4px 15px rgba(102, 126, 234, 0.4),
    0 1px 3px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.btn-new::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.btn-new:hover::before {
  left: 100%;
}

.btn-new:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 
    0 8px 25px rgba(102, 126, 234, 0.5),
    0 4px 10px rgba(0, 0, 0, 0.15);
}

.btn-new:active {
  transform: translateY(-1px) scale(0.98);
}

.btn-clear {
  width: 100%;
  padding: 1rem;
  margin-top: 0.75rem;
  background: var(--color-background-secondary);
  color: var(--color-red-600);
  border: 1.5px solid var(--color-red-100);
  border-radius: 16px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all var(--transition-base);
  backdrop-filter: blur(10px);
}

.btn-clear:hover {
  background: var(--color-red-50);
  border-color: var(--color-red-600);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem;
}

.conversations-list::-webkit-scrollbar {
  width: 6px;
}

.conversations-list::-webkit-scrollbar-track {
  background: transparent;
}

.conversations-list::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}

.conversations-list::-webkit-scrollbar-thumb:hover {
  background: #cbd5e1;
}

.conversation-item {
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
  background: var(--color-surface);
  backdrop-filter: blur(10px);
  border: 1px solid var(--color-border);
  border-radius: 18px;
  cursor: pointer;
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.conversation-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 18px;
  padding: 2px;
  background: linear-gradient(135deg, transparent, transparent);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.3s;
}

.conversation-item:hover {
  background: var(--color-surface-hover);
  transform: translateX(5px);
  box-shadow: var(--shadow-md);
}

.conversation-item:hover::before {
  opacity: 1;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.conversation-item.active {
  background: var(--color-surface);
  border-color: var(--color-primary-500);
  box-shadow: var(--shadow-md);
}

.conversation-item.active::before {
  opacity: 1;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.conv-title {
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: var(--color-text-primary);
  font-size: 1rem;
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
  padding: 0.3rem 0.75rem;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: all 0.3s;
}

.provider-badge {
  background: var(--color-primary-50);
  color: var(--color-primary-600);
  border: 1px solid var(--color-primary-200);
}

.mcp-badge {
  background: var(--color-green-50);
  color: var(--color-green-600);
  border: 1px solid var(--color-green-200);
}

/* 主聊天區 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-background);
  position: relative;
  overflow: hidden;
  box-shadow: inset 4px 0 10px rgba(0, 0, 0, 0.02);
}

.chat-header {
  padding: 0 2rem;
  background: var(--color-background);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 5;
  height: 70px; 
  flex-shrink: 0;
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
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-surface);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary);
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
  padding: 0.5rem 1rem;
  border-radius: 10px;
  background: var(--color-background);
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-base) ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid var(--color-border);
  white-space: nowrap;
  flex-shrink: 0;
}

.mcp-chip:hover {
  border-color: #94a3b8;
  color: #475569;
  background: #f8fafc;
}

.mcp-chip.active {
  background: var(--color-primary-100);
  color: var(--color-primary-700);
  border-color: var(--color-primary-300);
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
  background: transparent;
  scroll-behavior: smooth;
  min-height: 0;
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
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
  letter-spacing: -0.02em;
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
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  background: var(--color-background-secondary);
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.message-content {
  max-width: 85%;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.message-text {
  padding: 1.5rem;
  border-radius: 20px;
  background: var(--color-background-secondary);
  color: var(--color-text-primary);
  line-height: 1.6;
  font-size: 1.05rem;
  box-shadow: var(--shadow-sm);
  width: fit-content;
  border: 1px solid var(--color-border);
}

.message.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
  margin-left: auto;
  position: relative;
  overflow: hidden;
}

.message.user .message-text::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.15) 0%, transparent 70%);
  pointer-events: none;
}

.message.assistant .message-text {
  border-bottom-left-radius: 4px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.message.assistant .message-text:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--color-primary-300);
}

/* 工具調用樣式 */
/* 工具調用顯示 - 易讀格式 */
.tool-calls {
  width: 100%;
  max-width: 800px;
}

.tool-call-item {
  margin-bottom: 1rem;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
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
  cursor: pointer;
  transition: all 0.2s;
}

.tool-call-header:hover {
  opacity: 0.95;
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

.toggle-icon {
  margin-left: auto;
  transition: transform 0.3s;
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}

/* 工具折疊動畫 */
.tool-call-body-wrapper {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.3s ease-out;
}

.tool-call-body-wrapper.expanded {
  grid-template-rows: 1fr;
}

.tool-call-body-inner {
  overflow: hidden;
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
  border-bottom: 2px solid var(--color-border);
}

.section-icon {
  font-size: 1.25rem;
}

.section-title {
  font-weight: 700;
  color: var(--color-text-primary);
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
  background: var(--color-surface);
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.param-key, .result-key {
  font-weight: 600;
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  min-width: 100px;
  flex-shrink: 0;
}

.param-value, .result-value {
  color: var(--color-text-primary);
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
  background: linear-gradient(to bottom, transparent 0%, var(--color-background) 100%);
  position: relative;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  background: var(--color-background);
  padding: 0.75rem 1rem;
  border-radius: 24px;
  border: 2px solid var(--color-border);
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
  background: var(--color-primary-600);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-base);
  flex-shrink: 0;
}

.btn-send-modern:hover:not(:disabled) {
  background: var(--color-primary-700);
  transform: translateY(-2px) scale(1.05);
  box-shadow: var(--shadow-md);
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
  background: transparent; 
  position: relative;
  z-index: 20; /* 確保 Popover 在最上層 */
}

.input-integrated-container {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 0.75rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.input-integrated-container:focus-within {
  border-color: var(--color-primary-500);
  background: var(--color-background);
  box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.1);
}

.input-top-row {
  display: flex;
  align-items: flex-start;
  gap: 1.25rem;
}

.accordion-wrapper {
  position: relative;
}

.btn-plus {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
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
  color: var(--color-text-primary);
  caret-color: var(--color-primary-500);
  min-height: 40px;
}

.main-textarea::placeholder {
  color: var(--color-text-tertiary);
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
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
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
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-background-secondary);
}

.popover-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-text-primary);
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
  color: var(--color-text-primary);
  font-size: 0.9rem;
}

.menu-item:hover {
  background: var(--color-surface-hover);
}

.menu-item.active {
  background: var(--color-primary-100);
  color: var(--color-primary-600);
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
  color: var(--color-text-secondary);
  margin-bottom: 0.3rem;
}

.popover-content .popup-select,
.popover-content select.popup-select {
  width: 100%;
  padding: 0.5rem;
  background-color: var(--color-background-secondary) !important;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  outline: none;
  font-size: 0.9rem;
  color: var(--color-text-primary) !important;
}

.popover-content .popup-select option,
.popover-content select.popup-select option {
  background-color: var(--color-surface) !important;
  color: var(--color-text-primary) !important;
  padding: 0.5rem;
}

.popover-content .popup-select:focus,
.popover-content select.popup-select:focus {
  border-color: #6366f1;
  background-color: #ffffff !important;
}

.popover-content .popup-select:disabled,
.popover-content select.popup-select:disabled {
  background-color: var(--color-slate-100) !important;
  color: var(--color-text-tertiary) !important;
  cursor: not-allowed;
  opacity: 0.8;
}

.agent-hint {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: var(--color-primary-50);
  border-left: 3px solid var(--color-primary-500);
  border-radius: 4px;
  font-size: 0.75rem;
  color: var(--color-primary-700);
  font-weight: 500;
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

/* Markdown 樣式 */
.markdown-body {
  line-height: 1.6;
  color: var(--color-text-primary);
}

.markdown-body p {
  margin: 0.75rem 0;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin: 1.25rem 0 0.75rem 0;
  font-weight: 600;
  line-height: 1.3;
  color: var(--color-text-primary);
}

.markdown-body h1 { font-size: 1.75rem; border-bottom: 2px solid var(--color-border); padding-bottom: 0.5rem; }
.markdown-body h2 { font-size: 1.5rem; border-bottom: 1px solid var(--color-border); padding-bottom: 0.4rem; }
.markdown-body h3 { font-size: 1.25rem; }
.markdown-body h4 { font-size: 1.1rem; }
.markdown-body h5 { font-size: 1rem; }
.markdown-body h6 { font-size: 0.9rem; color: var(--color-text-secondary); }

.markdown-body ul,
.markdown-body ol {
  margin: 1rem 0;
  padding-left: 2.5rem;
}

.markdown-body li {
  margin: 0.8rem 0;
  line-height: 1.8;
  padding-left: 0.5rem;
}

/* 巢狀列表 */
.markdown-body li > ul,
.markdown-body li > ol {
  margin: 0.6rem 0;
  padding-left: 2rem;
}

/* 第一層列表 */
.markdown-body > ul > li,
.markdown-body > ol > li {
  margin: 1rem 0;
  font-weight: 500;
}

/* 第二層列表(子項目) */
.markdown-body li ul li,
.markdown-body li ol li {
  margin: 0.5rem 0;
  font-size: 0.95em;
  font-weight: 400;
  padding-left: 0.3rem;
}

/* 第三層列表 */
.markdown-body li li ul li,
.markdown-body li li ol li {
  margin: 0.3rem 0;
  font-size: 0.9em;
}

.markdown-body ul li {
  list-style-type: disc;
}

.markdown-body ol li {
  list-style-type: decimal;
}

/* 巢狀列表的樣式 */
.markdown-body ul ul li {
  list-style-type: circle;
}

.markdown-body ul ul ul li {
  list-style-type: square;
}

.markdown-body ol ol li {
  list-style-type: lower-alpha;
}

.markdown-body ol ol ol li {
  list-style-type: lower-roman;
}

/* 確保列表項目之間有足夠的空間 */
.markdown-body li + li {
  margin-top: 0.8rem;
}

.markdown-body li ul li + li,
.markdown-body li ol li + li {
  margin-top: 0.5rem;
}

.markdown-body code {
  background: #f1f5f9;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  color: #e11d48;
}

.markdown-body pre {
  background: #1e293b;
  color: #e2e8f0;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1rem 0;
}

.markdown-body pre code {
  background: transparent;
  padding: 0;
  color: #e2e8f0;
  font-size: 0.875rem;
}

.markdown-body blockquote {
  border-left: 4px solid #cbd5e1;
  padding-left: 1rem;
  margin: 1rem 0;
  color: #64748b;
  font-style: italic;
}

.markdown-body a {
  color: #3b82f6;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s;
}

.markdown-body a:hover {
  border-bottom-color: #3b82f6;
}

.markdown-body table {
  border-collapse: collapse;
  width: 100%;
  margin: 1rem 0;
}

.markdown-body table th,
.markdown-body table td {
  border: 1px solid #e2e8f0;
  padding: 0.5rem 0.75rem;
  text-align: left;
}

.markdown-body table th {
  background: #f8fafc;
  font-weight: 600;
}

.markdown-body hr {
  border: none;
  border-top: 2px solid #e2e8f0;
  margin: 1.5rem 0;
}

.markdown-body strong {
  font-weight: 600;
  color: var(--color-text-primary);
}

.markdown-body em {
  font-style: italic;
}

/* 載入動畫 */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.5rem 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(1) {
  animation-delay: 0s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.7;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

/* ============================================
   淺色主題覆蓋樣式
   ============================================ */
[data-theme="light"] .chatbot-wrapper {
  /* 對話列表 */
  .conversations-sidebar {
    background: var(--color-background-secondary);
    border-right-color: var(--color-border);

    .sidebar-header {
      border-bottom-color: var(--color-border);
      h2 { color: var(--color-text-primary); }
    }
  }

  .conversation-item {
    background: var(--color-surface);
    border-color: var(--color-border);
    color: var(--color-text-primary);
  }

  .conversation-item:hover {
    background: var(--color-surface-hover);
  }

  .conversation-item.active {
    background: var(--color-primary-100);
    border-color: var(--color-primary-300);
    color: var(--color-primary-700);
  }

  /* 訊息區 */
  .messages-container {
    background: var(--color-background);
  }

  .message {
    color: var(--color-text-primary);
  }

  .message.user .message-text {
    background: var(--color-primary-100);
    color: var(--color-primary-900);
    border-color: var(--color-primary-200);
  }

  .message.assistant .message-text {
    background: var(--color-surface);
    color: var(--color-text-primary);
    border-color: var(--color-border);
  }

  /* 程式碼區塊 */
  pre {
    background: var(--color-slate-100) !important;
    border-color: var(--color-border);
  }

  code {
    background: var(--color-slate-100);
    color: var(--color-slate-900);
  }

  /* 工具調用 */
  .tool-call {
    background: var(--color-blue-50);
    border-color: var(--color-blue-200);
    color: var(--color-blue-900);
  }

  .tool-result {
    background: var(--color-green-50);
    border-color: var(--color-green-200);
    color: var(--color-green-900);
  }

  /* 輸入區 */
  .input-integrated-container {
    background: var(--color-surface);
    border-color: var(--color-border);
  }

  .main-textarea {
    background: transparent;
    color: var(--color-text-primary);
  }

  .main-textarea::placeholder {
    color: var(--color-text-tertiary);
  }

  /* 按鈕 */
  .btn-plus {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
    border-color: var(--color-border);
  }

  .btn-plus:hover {
    background: var(--color-primary-100);
    color: var(--color-primary-700);
    border-color: var(--color-primary-300);
  }

  .btn-model-trigger {
    background: var(--color-surface);
    color: var(--color-text-primary);
    border-color: var(--color-border);
  }

  .btn-model-trigger:hover {
    background: var(--color-surface-hover);
    border-color: var(--color-border-hover);
  }

  /* 彈出選單 */
  .popover-menu {
    background: var(--color-surface);
    border-color: var(--color-border);
    box-shadow: var(--shadow-xl);
  }

  .popover-header {
    border-bottom-color: var(--color-border);
  }

  .popover-title {
    color: var(--color-text-primary);
  }

  .menu-item {
    color: var(--color-text-primary);
  }

  .menu-item:hover {
    background: var(--color-surface-hover);
  }

  .menu-item.active {
    background: var(--color-primary-100);
    color: var(--color-primary-700);
  }

  /* Mini chips */
  .mini-chip {
    background: var(--color-primary-100);
    color: var(--color-primary-700);
    border-color: var(--color-primary-200);
  }

  /* 時間戳記 */
  .message-time {
    color: var(--color-text-tertiary);
  }

  /* JSON 顯示 */
  .json-key {
    color: var(--color-blue-700);
  }

  .json-string {
    color: var(--color-green-700);
  }

  .json-number {
    color: var(--color-orange-700);
  }

  .json-boolean {
    color: var(--color-purple-700);
  }

  /* 清空按鈕與其它 */
  .btn-clear {
    background: var(--color-surface);
    border-color: var(--color-border);
    color: #ef4444;
  }

  .btn-clear:hover {
    background: #fff1f2;
    border-color: #fecaca;
  }

  .welcome-screen {
    color: var(--color-text-tertiary);
  }
}
</style>
