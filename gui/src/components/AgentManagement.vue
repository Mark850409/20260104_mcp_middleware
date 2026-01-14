<template>
  <div class="agent-wrapper">
    <!-- 左側: Agent 列表 -->
    <aside class="agents-sidebar">
      <div class="sidebar-header">
        <h2>AI Agents</h2>
        <button @click="createNewAgent" class="btn-create-agent">
          <i class="ri-add-circle-line"></i> 建立 Agent
        </button>
      </div>

      <!-- 搜尋框 -->
      <div class="search-box">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜尋 Agent..."
          class="search-input"
        />
      </div>

      <!-- Agent 卡片列表 -->
      <div class="agents-grid">
        <div
          v-for="agent in filteredAgents"
          :key="agent.id"
          :class="['agent-card', { active: selectedAgentId === agent.id }]"
          @click="selectAgent(agent.id)"
        >
          <div class="agent-avatar">
            <img v-if="agent.avatar_url" :src="agent.avatar_url" :alt="agent.name" />
            <span v-else class="avatar-placeholder">{{ agent.name.charAt(0) }}</span>
          </div>
          <div class="agent-info">
            <h3 class="agent-name">{{ agent.name }}</h3>
            <p class="agent-description">{{ agent.description || '無說明' }}</p>
            <div class="agent-meta">
              <span class="provider-badge">{{ agent.model_provider }}</span>
              <span v-if="agent.knowledge_bases && agent.knowledge_bases.length > 0" class="kb-badge">
                <i class="ri-book-2-line"></i> {{ agent.knowledge_bases.length }}
              </span>
              <span v-if="agent.mcp_tools && agent.mcp_tools.length > 0" class="tool-badge">
                <i class="ri-tools-line"></i> {{ agent.mcp_tools.length }}
              </span>
            </div>
          </div>
        </div>

        <div v-if="filteredAgents.length === 0" class="empty-state">
          {{ searchQuery ? '找不到符合的 Agent' : '尚未建立任何 Agent' }}
        </div>
      </div>
    </aside>

    <!-- 右側: Agent 編輯器 -->
    <main class="agent-editor">
      <div v-if="!selectedAgentId && !isCreating" class="welcome-screen">
        <h1><i class="ri-focus-3-line"></i> Agent 管理</h1>
        <p>選擇左側 Agent 進行編輯,或建立新的 Agent</p>
      </div>

      <div v-else class="editor-content">
        <!-- 編輯器標題 -->
        <div class="editor-header">
          <h2>{{ isCreating ? '建立新 Agent' : '編輯 Agent' }}</h2>
          <div class="header-actions">
            <button v-if="!isCreating" @click="testAgent" class="btn-test">
              <i class="ri-test-tube-line"></i> 測試
            </button>
            <button @click="saveAgent" class="btn-save" :disabled="isSaving">
              <i :class="isSaving ? 'ri-loader-4-line ri-spin' : 'ri-save-line'"></i>
              {{ isSaving ? '儲存中...' : '儲存' }}
            </button>
            <button v-if="!isCreating" @click="deleteAgent" class="btn-delete">
              <i class="ri-delete-bin-line"></i> 刪除
            </button>
          </div>
        </div>

        <!-- 基本資訊 -->
        <section class="editor-section">
          <h3 class="section-title">基本資訊</h3>
          <div class="form-group">
            <label>名稱 *</label>
            <input
              v-model="currentAgent.name"
              type="text"
              placeholder="例如: Python 專家"
              class="form-input"
              required
            />
          </div>

          <div class="form-group">
            <label>說明</label>
            <textarea
              v-model="currentAgent.description"
              placeholder="描述這個 Agent 的用途和專長..."
              class="form-textarea"
              rows="3"
            ></textarea>
          </div>

          <div class="form-group">
            <label>頭像 URL</label>
            <input
              v-model="currentAgent.avatar_url"
              type="text"
              placeholder="https://example.com/avatar.png"
              class="form-input"
            />
            <div v-if="currentAgent.avatar_url" class="avatar-preview">
              <img :src="currentAgent.avatar_url" alt="Avatar Preview" />
            </div>
          </div>
        </section>

        <!-- 模型設定 -->
        <section class="editor-section">
          <h3 class="section-title">模型設定</h3>
          <div class="form-row">
            <div class="form-group">
              <label>供應商 *</label>
              <select v-model="currentAgent.model_provider" @change="updateModelList" class="form-select">
                <option value="openai">OpenAI</option>
                <option value="google">Google</option>
                <option value="anthropic">Anthropic</option>
              </select>
            </div>

            <div class="form-group">
              <label>模型 *</label>
              <select v-model="currentAgent.model_name" class="form-select">
                <option v-for="model in availableModels" :key="model.name" :value="model.name">
                  {{ model.display_name }}
                </option>
              </select>
            </div>
          </div>
        </section>

        <!-- 系統提示詞 -->
        <section class="editor-section">
          <h3 class="section-title">系統提示詞</h3>
          <div class="form-group">
            <label>選擇提示詞</label>
            <select v-model="currentAgent.system_prompt_id" class="form-select">
              <option :value="null">無系統提示詞</option>
              <option v-for="prompt in availablePrompts" :key="prompt.id" :value="prompt.id">
                {{ prompt.name }} {{ prompt.is_default ? '(預設)' : '' }}
              </option>
            </select>
          </div>
        </section>

        <!-- 知識庫 -->
        <section class="editor-section">
          <h3 class="section-title">知識庫 (RAG)</h3>
          <div class="checkbox-group">
            <div v-if="availableKbs.length === 0" class="empty-hint">
              尚未建立任何知識庫
            </div>
            <label
              v-for="kb in availableKbs"
              :key="kb.id"
              class="checkbox-label"
            >
              <input
                type="checkbox"
                :value="kb.id"
                v-model="selectedKbIds"
              />
              <span>{{ kb.name }}</span>
              <span v-if="kb.description" class="checkbox-hint">{{ kb.description }}</span>
            </label>
          </div>
        </section>

        <!-- MCP 工具 -->
        <section class="editor-section">
          <h3 class="section-title">MCP 工具</h3>
          <div class="checkbox-group">
            <div v-if="availableMcpServers.length === 0" class="empty-hint">
              尚未設定任何 MCP Server
            </div>
            <label
              v-for="server in availableMcpServers"
              :key="server.name"
              class="checkbox-label"
            >
              <input
                type="checkbox"
                :value="server.name"
                v-model="selectedMcpTools"
              />
              <span>{{ server.name }}</span>
            </label>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import Swal from 'sweetalert2'

export default {
  name: 'AgentManagement',
  setup() {
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

    // 狀態
    const agents = ref([])
    const selectedAgentId = ref(null)
    const isCreating = ref(false)
    const isSaving = ref(false)
    const searchQuery = ref('')

    // 當前編輯的 Agent
    const currentAgent = ref({
      name: '',
      description: '',
      avatar_url: '',
      model_provider: 'openai',
      model_name: 'gpt-4o',
      system_prompt_id: null,
      is_active: true
    })

    // 選中的知識庫和工具
    const selectedKbIds = ref([])
    const selectedMcpTools = ref([])

    // 可用選項
    const allModels = ref({})
    const availablePrompts = ref([])
    const availableKbs = ref([])
    const availableMcpServers = ref([])

    // 計算屬性
    const filteredAgents = computed(() => {
      if (!searchQuery.value) return agents.value
      const query = searchQuery.value.toLowerCase()
      return agents.value.filter(agent =>
        agent.name.toLowerCase().includes(query) ||
        (agent.description && agent.description.toLowerCase().includes(query))
      )
    })

    const availableModels = computed(() => {
      return allModels.value[currentAgent.value.model_provider] || []
    })

    // 方法
    const loadAgents = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/agents`)
        if (response.data.success) {
          agents.value = response.data.agents
        }
      } catch (error) {
        console.error('載入 Agent 列表失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '載入失敗',
          text: error.message,
          toast: true,
          position: 'top-end',
          showConfirmButton: false,
          timer: 3000
        })
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

    const loadPrompts = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/prompts`)
        if (response.data.success) {
          availablePrompts.value = response.data.prompts
        }
      } catch (error) {
        console.error('載入提示詞失敗:', error)
      }
    }

    const loadKbs = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/rag/kb`)
        if (response.data.success) {
          availableKbs.value = response.data.data
        }
      } catch (error) {
        console.error('載入知識庫失敗:', error)
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

    const createNewAgent = () => {
      isCreating.value = true
      selectedAgentId.value = null
      currentAgent.value = {
        name: '',
        description: '',
        avatar_url: '',
        model_provider: 'openai',
        model_name: 'gpt-4o',
        system_prompt_id: null,
        is_active: true
      }
      selectedKbIds.value = []
      selectedMcpTools.value = []
    }

    const selectAgent = async (agentId) => {
      try {
        const response = await axios.get(`${API_URL}/api/agents/${agentId}`)
        if (response.data.success) {
          const agent = response.data.agent
          selectedAgentId.value = agentId
          isCreating.value = false

          currentAgent.value = {
            name: agent.name,
            description: agent.description || '',
            avatar_url: agent.avatar_url || '',
            model_provider: agent.model_provider,
            model_name: agent.model_name,
            system_prompt_id: agent.system_prompt_id,
            is_active: agent.is_active
          }

          selectedKbIds.value = agent.knowledge_bases.map(kb => kb.id)
          selectedMcpTools.value = agent.mcp_tools.map(tool => tool.mcp_server_name)
        }
      } catch (error) {
        console.error('載入 Agent 失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '載入失敗',
          text: error.message
        })
      }
    }

    const saveAgent = async () => {
      // 驗證
      if (!currentAgent.value.name) {
        Swal.fire({
          icon: 'warning',
          title: '請填寫 Agent 名稱'
        })
        return
      }

      isSaving.value = true

      try {
        const payload = {
          ...currentAgent.value,
          knowledge_bases: selectedKbIds.value,
          mcp_tools: selectedMcpTools.value
        }

        let response
        if (isCreating.value) {
          // 建立新 Agent
          response = await axios.post(`${API_URL}/api/agents`, payload)
        } else {
          // 更新現有 Agent
          response = await axios.put(`${API_URL}/api/agents/${selectedAgentId.value}`, payload)
        }

        if (response.data.success) {
          Swal.fire({
            icon: 'success',
            title: isCreating.value ? 'Agent 建立成功' : 'Agent 更新成功',
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 2000
          })

          // 重新載入列表
          await loadAgents()

          // 如果是建立,選中新建立的 Agent
          if (isCreating.value) {
            selectAgent(response.data.agent_id)
          }
        }
      } catch (error) {
        console.error('儲存 Agent 失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '儲存失敗',
          text: error.response?.data?.error || error.message
        })
      } finally {
        isSaving.value = false
      }
    }

    const deleteAgent = async () => {
      const result = await Swal.fire({
        title: '確定要刪除嗎?',
        text: '刪除後將無法復原!',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: '確定刪除',
        cancelButtonText: '取消'
      })

      if (!result.isConfirmed) return

      try {
        const response = await axios.delete(`${API_URL}/api/agents/${selectedAgentId.value}`)

        if (response.data.success) {
          Swal.fire({
            icon: 'success',
            title: 'Agent 已刪除',
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 2000
          })

          // 重新載入列表
          await loadAgents()

          // 清空選擇
          selectedAgentId.value = null
          isCreating.value = false
        }
      } catch (error) {
        console.error('刪除 Agent 失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '刪除失敗',
          text: error.response?.data?.error || error.message
        })
      }
    }

    const testAgent = async () => {
      // 直接建立對話並導航到 Chatbot
      const result = await Swal.fire({
        title: '測試 Agent',
        text: '即將開啟新對話視窗測試此 Agent',
        icon: 'info',
        showCancelButton: true,
        confirmButtonText: '開始測試',
        cancelButtonText: '取消'
      })
      
      if (result.isConfirmed) {
        try {
          // 使用 Agent 建立新對話
          const response = await axios.post(`${API_URL}/api/chat/conversations`, {
            title: `測試 ${currentAgent.value.name} - ${new Date().toLocaleString()}`,
            agent_id: selectedAgentId.value
          })
          
          if (response.data.success) {
            // 儲存對話 ID 到 localStorage
            localStorage.setItem('test_conversation_id', response.data.conversation_id)
            
            // 導航到 Chatbot (重新載入頁面到根路徑)
            window.location.href = '/'
          }
        } catch (error) {
          console.error('建立測試對話失敗:', error)
          Swal.fire({
            icon: 'error',
            title: '建立對話失敗',
            text: error.response?.data?.error || error.message
          })
        }
      }
    }

    const updateModelList = () => {
      const models = availableModels.value
      if (models.length > 0) {
        currentAgent.value.model_name = models[0].name
      }
    }

    // 初始化
    onMounted(() => {
      loadAgents()
      loadModels()
      loadPrompts()
      loadKbs()
      loadMcpServers()
    })

    return {
      agents,
      selectedAgentId,
      isCreating,
      isSaving,
      searchQuery,
      currentAgent,
      selectedKbIds,
      selectedMcpTools,
      filteredAgents,
      availableModels,
      availablePrompts,
      availableKbs,
      availableMcpServers,
      createNewAgent,
      selectAgent,
      saveAgent,
      deleteAgent,
      testAgent,
      updateModelList
    }
  }
}
</script>

<style scoped>
.agent-wrapper {
  display: flex;
  height: calc(100vh - var(--topbar-height));
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: var(--color-text-primary, #e0e0e0);
}

/* 左側邊欄 */
.agents-sidebar {
  width: 350px;
  background: var(--color-background-secondary);
  backdrop-filter: blur(10px);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.sidebar-header h2 {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.btn-create-agent {
  width: 100%;
  padding: 0.85rem 1.25rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-create-agent:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.search-box {
  padding: 1rem 1.5rem;
}

.search-input {
  width: 100%;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: var(--color-text-primary, #e0e0e0);
  font-size: 0.9rem;
}

.search-input::placeholder {
  color: var(--color-text-tertiary);
}

.agents-grid {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.5rem;
}

.agent-card {
  background: var(--color-background-secondary);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  gap: 1rem;
}

.agent-card:hover {
  background: var(--color-surface);
  transform: translateX(4px);
}

.agent-card.active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  border-color: #667eea;
}

.agent-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.agent-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
}

.agent-info {
  flex: 1;
  min-width: 0;
}

.agent-name {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
}

.agent-description {
  margin: 0 0 0.5rem 0;
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.provider-badge,
.kb-badge,
.tool-badge {
  padding: 0.25rem 0.5rem;
  background: var(--color-surface);
  border-radius: 4px;
  font-size: 0.75rem;
}

/* 右側編輯器 */
.agent-editor {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.welcome-screen h1 {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-screen p {
  font-size: 1.1rem;
  color: var(--color-text-secondary);
}

.editor-content {
  max-width: 800px;
  margin: 0 auto;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.editor-header h2 {
  margin: 0;
  font-size: 1.8rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-actions {
  display: flex;
  gap: 1.25rem;
}

.btn-test,
.btn-save,
.btn-delete {
  padding: 0.75rem 1.75rem;
  border: none;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-base);
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
}

.btn-test {
  background: var(--color-background-secondary);
  color: var(--color-primary-600);
  border: 1.5px solid var(--color-primary-600);
}

.btn-test:hover {
  background: var(--color-primary-50);
  border-color: var(--color-primary-700);
  color: var(--color-primary-700);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.btn-save {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-save:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  filter: brightness(1.1);
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-delete {
  background: #fee2e2;
  color: #ef4444;
  border: 1.5px solid #fecaca;
}

.btn-delete:hover {
  background: #fef2f2;
  border-color: #dc2626;
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.editor-section {
  background: var(--color-background-secondary);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.section-title {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  color: var(--color-text-primary, #e0e0e0);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.form-input,
.form-textarea,
.form-select {
  width: 100%;
  padding: 0.85rem 1rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  color: var(--color-text-primary);
  font-size: 1rem;
  transition: all var(--transition-base) ease;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: var(--color-primary-500);
  background: var(--color-surface);
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.avatar-preview {
  margin-top: 0.5rem;
}

.avatar-preview img {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--color-border);
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  cursor: pointer;
  transition: all var(--transition-base) ease;
}

.checkbox-label:hover {
  background: var(--color-background-secondary);
}

.checkbox-label input[type="checkbox"] {
  margin-top: 0.2rem;
  cursor: pointer;
}

.checkbox-hint {
  display: block;
  font-size: 0.85rem;
  color: var(--color-text-tertiary);
  margin-top: 0.25rem;
}

.empty-hint,
.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--color-text-tertiary);
  font-size: 0.95rem;
}

/* 滾動條樣式 */
.agents-grid::-webkit-scrollbar,
.agent-editor::-webkit-scrollbar {
  width: 8px;
}

.agents-grid::-webkit-scrollbar-track,
.agent-editor::-webkit-scrollbar-track {
  background: var(--color-background-secondary);
}

.agents-grid::-webkit-scrollbar-thumb,
.agent-editor::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 4px;
}

.agents-grid::-webkit-scrollbar-thumb:hover,
.agent-editor::-webkit-scrollbar-thumb:hover {
  background: var(--color-border-hover);
}

/* ============================================
   淺色主題覆蓋樣式
   ============================================ */
[data-theme="light"] .agent-wrapper {
  background: var(--color-background);
  color: var(--color-text-primary);
}

[data-theme="light"] .agents-sidebar {
  background: var(--color-slate-50);
  border-right-color: var(--color-border);
}

[data-theme="light"] .sidebar-header {
  border-bottom-color: var(--color-border);
}

[data-theme="light"] .search-input {
  background: var(--color-background);
  border-color: var(--color-border);
  color: var(--color-text-primary);
}

[data-theme="light"] .search-input::placeholder {
  color: var(--color-text-tertiary);
}

[data-theme="light"] .agent-card {
  background: var(--color-surface);
  border-color: var(--color-border);
}

[data-theme="light"] .agent-card:hover {
  background: var(--color-slate-50);
}

[data-theme="light"] .agent-card.active {
  background: var(--color-primary-50);
  border-color: var(--color-primary-300);
}

[data-theme="light"] .agent-name,
[data-theme="light"] .section-title {
  color: var(--color-text-primary);
}

[data-theme="light"] .agent-description {
  color: var(--color-text-secondary);
}

[data-theme="light"] .editor-section {
  background: var(--color-surface);
  border-color: var(--color-border);
}

[data-theme="light"] .form-input,
[data-theme="light"] .form-textarea,
[data-theme="light"] .form-select {
  background: var(--color-background);
  border-color: var(--color-border);
  color: var(--color-text-primary);
}

[data-theme="light"] .form-group label {
  color: var(--color-text-secondary);
}

[data-theme="light"] .form-input:focus,
[data-theme="light"] .form-textarea:focus,
[data-theme="light"] .form-select:focus {
  border-color: var(--color-primary-500);
  background: var(--color-background);
}

[data-theme="light"] .checkbox-label {
  background: var(--color-slate-50);
  border-color: var(--color-border);
}

[data-theme="light"] .checkbox-label:hover {
  background: var(--color-slate-100);
}

[data-theme="light"] .welcome-screen p {
  color: var(--color-text-secondary);
}

</style>
