<template>
  <div>
    <div class="line-bot-management">
      <!-- 標題區 -->
      <header class="page-header">
        <h2>📱 LINE BOT 管理</h2>
        <p class="subtitle">設定與管理 LINE Messaging API 整合</p>
      </header>

      <!-- 主要內容區 -->
      <div class="container">
        <!-- 使用說明 -->
        <div class="card info-card">
          <h3>📖 設定說明</h3>
          <ol class="instructions">
            <li>前往 <a href="https://developers.line.biz/" target="_blank">LINE Developers Console</a> 建立 Messaging API Channel</li>
            <li>取得 <strong>Channel Access Token</strong> 和 <strong>Channel Secret</strong></li>
            <li>在此頁面新增 LINE BOT 設定,填入上述資訊</li>
            <li>複製產生的 <strong>Webhook URL</strong></li>
            <li>回到 LINE Developers Console,在 Messaging API 設定中貼上 Webhook URL</li>
            <li>啟用 Webhook 並關閉自動回覆訊息</li>
            <li>開始使用您的 LINE BOT!</li>
          </ol>
        </div>

        <div class="card">
          <div class="card-header">
            <h3>🤖 LINE BOT 設定</h3>
            <button @click="showAddDialog = true" class="btn btn-primary">
              ➕ 新增 LINE BOT
            </button>
          </div>

          <div v-if="loading" class="loading">載入中...</div>
          <div v-else-if="configs.length === 0" class="empty-state">
            <div class="empty-icon">🤖</div>
            <p>尚未設定任何 LINE BOT</p>
            <p class="empty-hint">點擊上方按鈕開始設定您的第一個 LINE BOT</p>
          </div>
          <div v-else class="configs-list">
            <div v-for="config in configs" :key="config.id" class="config-card">
              <div class="config-header">
                <div class="config-title">
                  <h4>{{ config.bot_name }}</h4>
                  <span :class="['status-badge', config.is_active ? 'active' : 'inactive']">
                    {{ config.is_active ? '✓ 啟用中' : '⊗ 已停用' }}
                  </span>
                </div>
                <label class="switch">
                  <input 
                    type="checkbox" 
                    :checked="config.is_active" 
                    @change="toggleConfig(config.id, $event.target.checked)"
                  />
                  <span class="slider"></span>
                </label>
              </div>

              <div class="config-info">
                <div class="info-row">
                  <span class="label">Webhook URL:</span>
                  <div class="webhook-url">
                    <code>{{ config.webhook_url }}</code>
                    <button @click="copyWebhookUrl(config.webhook_url)" class="btn-copy" title="複製">
                      📋
                    </button>
                  </div>
                </div>
                <div class="info-row">
                  <span class="label">MCP 工具:</span>
                  <div class="mcp-servers">
                    <template v-if="getValidServers(config.selected_mcp_servers).length === 0">
                      <span class="no-tools">未選擇工具</span>
                    </template>
                    <template v-else>
                      <span class="tool-badge" v-for="server in getValidServers(config.selected_mcp_servers)" :key="server">
                        {{ server }}
                      </span>
                    </template>
                  </div>
                </div>
                <div class="info-row">
                  <span class="label">系統提示詞:</span>
                  <div class="prompt-info">
                    <span v-if="config.system_prompt_id" class="prompt-badge">
                      {{ getPromptName(config.system_prompt_id) }}
                    </span>
                    <span v-else class="no-tools">無系統提示詞</span>
                  </div>
                </div>
                <div class="info-row">
                  <span class="label">知識庫 (RAG):</span>
                  <div class="kb-info">
                    <span v-if="config.kb_id" class="kb-badge">
                      {{ getKbName(config.kb_id) }}
                    </span>
                    <span v-else class="no-tools">未選擇知識庫</span>
                  </div>
                </div>
                <div class="info-row">
                  <span class="label">建立時間:</span>
                  <span>{{ formatDate(config.created_at) }}</span>
                </div>
              </div>

              <div class="config-actions">
                <button @click="editConfig(config)" class="btn btn-sm btn-secondary">
                  ✏️ 編輯
                </button>
                <button @click="deleteConfig(config.id)" class="btn btn-sm btn-danger">
                  🗑️ 刪除
                </button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- 新增/編輯對話框 -->
    <div v-if="showAddDialog || editingConfig" class="modal-overlay" @click.self="closeDialog">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingConfig ? '編輯 LINE BOT' : '新增 LINE BOT' }}</h3>
          <button @click="closeDialog" class="btn-close">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>BOT 名稱 *</label>
            <input 
              v-model="configForm.bot_name" 
              class="form-input" 
              placeholder="例如: 客服機器人"
            />
          </div>

          <div class="form-group">
            <label>選擇 MCP 工具</label>
            <div class="mcp-tools-grid">
              <div v-if="availableServers.length === 0" class="no-servers">
                <div class="no-servers-icon">🔧</div>
                <p>尚無可用的 MCP Server</p>
                <p class="hint">請先在 MCP 管理頁面添加 Server</p>
              </div>
              <label 
                v-else 
                v-for="server in availableServers" 
                :key="server.name" 
                class="tool-card"
                :class="{ 'selected': configForm.selected_mcp_servers.includes(server.name) }"
              >
                <input 
                  type="checkbox" 
                  :value="server.name"
                  v-model="configForm.selected_mcp_servers"
                  class="tool-checkbox"
                />
                <div class="tool-card-content">
                  <div class="tool-icon">🛠️</div>
                  <div class="tool-info">
                    <div class="tool-name">{{ server.name }}</div>
                    <div class="tool-desc">{{ server.description || '無描述' }}</div>
                  </div>
                  <div class="tool-check">
                    <svg v-if="configForm.selected_mcp_servers.includes(server.name)" width="20" height="20" viewBox="0 0 20 20" fill="none">
                      <circle cx="10" cy="10" r="10" fill="#06C755"/>
                      <path d="M6 10L9 13L14 7" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <svg v-else width="20" height="20" viewBox="0 0 20 20" fill="none">
                      <circle cx="10" cy="10" r="9" stroke="#ddd" stroke-width="2"/>
                    </svg>
                  </div>
                </div>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label>選擇系統提示詞</label>
            <select v-model="configForm.system_prompt_id" class="form-input">
              <option :value="null">無系統提示詞</option>
              <option v-for="prompt in availablePrompts" :key="prompt.id" :value="prompt.id">
                {{ prompt.name }} {{ prompt.is_default ? '(預設)' : '' }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>選擇知識庫 (RAG)</label>
            <select v-model="configForm.kb_id" class="form-input">
              <option :value="null">不使用知識庫</option>
              <option v-for="kb in availableKbs" :key="kb.id" :value="kb.id">
                {{ kb.name }}
              </option>
            </select>
          </div>

        </div>
        <div class="modal-footer">
          <button @click="closeDialog" class="btn btn-secondary">取消</button>
          <button @click="saveConfig" class="btn btn-primary">儲存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import Swal from 'sweetalert2'

export default {
  name: 'LineBotManagement',
  setup() {
    // API Base URL
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

    // 狀態
    const configs = ref([])
    const loading = ref(false)
    const showAddDialog = ref(false)
    const editingConfig = ref(null)
    const availableServers = ref([])
    const availableKbs = ref([])
    const availablePrompts = ref([])
    const configForm = ref({
      bot_name: '',
      selected_mcp_servers: [],
      is_active: true,
      system_prompt_id: null,
      kb_id: null
    })

    // 載入設定列表
    const loadConfigs = async () => {
      loading.value = true
      try {
        const response = await axios.get(`${API_URL}/api/line/configs`)
        if (response.data.success) {
          configs.value = response.data.data
        }
      } catch (error) {
        console.error('載入 LINE BOT 設定失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '載入失敗',
          text: '載入 LINE BOT 設定失敗: ' + error.message
        })
      } finally {
        loading.value = false
      }
    }

    // 載入可用的 MCP Servers
    const loadAvailableServers = async () => {
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
          
          availableServers.value = servers.filter(s => s.enabled)
        }
      } catch (error) {
        console.error('載入 MCP Servers 失敗:', error)
      }
    }

    // 載入可用的知識庫
    const loadAvailableKbs = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/rag/kb`)
        if (response.data.success) {
          availableKbs.value = response.data.data
        }
      } catch (error) {
        console.error('載入知識庫失敗:', error)
      }
    }

    // 載入可用的系統提示詞
    const loadAvailablePrompts = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/prompts`)
        if (response.data.success) {
          availablePrompts.value = response.data.prompts
        }
      } catch (error) {
        console.error('載入系統提示詞失敗:', error)
      }
    }

    // 切換啟用狀態
    const toggleConfig = async (configId, isActive) => {
      const loadingTimer = setTimeout(() => {
        Swal.fire({
          title: '狀態更新中...',
          text: '正在更新 LINE BOT 狀態，請稍後...',
          allowOutsideClick: false,
          didOpen: () => Swal.showLoading()
        })
      }, 3000)

      try {
        const response = await axios.post(`${API_URL}/api/line/configs/${configId}/toggle`)
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()

        if (response.data.success) {
          await loadConfigs()
          if (isActive) {
            Swal.fire({
              icon: 'success',
              title: '已啟用',
              text: 'LINE BOT 已啟用!',
              timer: 1500,
              showConfirmButton: false
            })
          }
        } else {
          Swal.fire({
            icon: 'error',
            title: '切換失敗',
            text: response.data.error || '未知錯誤'
          })
          await loadConfigs()
        }
      } catch (error) {
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()
        console.error('切換狀態失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '切換失敗',
          text: error.message
        })
        await loadConfigs()
      }
    }

    // 編輯設定
    const editConfig = (config) => {
      editingConfig.value = config
      configForm.value = {
        bot_name: config.bot_name,
        selected_mcp_servers: config.selected_mcp_servers || [],
        is_active: config.is_active,
        system_prompt_id: config.system_prompt_id,
        kb_id: config.kb_id
      }
      loadAvailableServers()
    }

    // 刪除設定
    const deleteConfig = async (configId) => {
      const result = await Swal.fire({
        title: '確定要刪除嗎?',
        text: '確定要刪除此 LINE BOT 設定嗎?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: '確定刪除',
        cancelButtonText: '取消'
      })
      
      if (!result.isConfirmed) return

      try {
        const response = await axios.delete(`${API_URL}/api/line/configs/${configId}`)
        if (response.data.success) {
          await loadConfigs()
        }
      } catch (error) {
        console.error('刪除設定失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '刪除失敗',
          text: error.message
        })
      }
    }

    // 關閉對話框
    const closeDialog = () => {
      showAddDialog.value = false
      editingConfig.value = null
      configForm.value = {
        bot_name: '',
        selected_mcp_servers: [],
        is_active: true,
        system_prompt_id: null,
        kb_id: null
      }
    }

    // 儲存設定
    const saveConfig = async () => {
      // 驗證
      if (!configForm.value.bot_name) {
        Swal.fire({
          icon: 'warning',
          title: '欄位未填',
          text: '請輸入 BOT 名稱'
        })
        return
      }

      const loadingTimer = setTimeout(() => {
        Swal.fire({
          title: '正在儲存...',
          text: '正在更新 LINE BOT 設定，請稍後...',
          allowOutsideClick: false,
          didOpen: () => Swal.showLoading()
        })
      }, 3000)

      if (editingConfig.value) {
        // 更新
        try {
          const updateData = {
            bot_name: configForm.value.bot_name,
            selected_mcp_servers: configForm.value.selected_mcp_servers,
            is_active: configForm.value.is_active,
            system_prompt_id: configForm.value.system_prompt_id,
            kb_id: configForm.value.kb_id
          }

          const response = await axios.put(
            `${API_URL}/api/line/configs/${editingConfig.value.id}`,
            updateData
          )
          clearTimeout(loadingTimer)
          if (Swal.isVisible()) Swal.close()

          if (response.data.success) {
            await loadConfigs()
            closeDialog()
          }
        } catch (error) {
          clearTimeout(loadingTimer)
          if (Swal.isVisible()) Swal.close()
          console.error('更新設定失敗:', error)
          Swal.fire({
            icon: 'error',
            title: '更新失敗',
            text: error.message
          })
        }
      } else {
        // 新增
        try {
          const response = await axios.post(`${API_URL}/api/line/configs`, configForm.value)
          clearTimeout(loadingTimer)
          if (Swal.isVisible()) Swal.close()

          if (response.data.success) {
            await loadConfigs()
            closeDialog()
            Swal.fire({
              icon: 'success',
              title: '建立成功',
              html: `LINE BOT 設定已建立!<br><br>Webhook URL: <code style="font-size: 0.8em; background: #eee; padding: 5px;">${response.data.data.webhook_url}</code>`,
              confirmButtonText: '太棒了'
            })
          }
        } catch (error) {
          clearTimeout(loadingTimer)
          if (Swal.isVisible()) Swal.close()
          console.error('建立設定失敗:', error)
          Swal.fire({
            icon: 'error',
            title: '建立失敗',
            text: error.message
          })
        }
      }
    }

    // 複製 Webhook URL
    const copyWebhookUrl = (url) => {
      navigator.clipboard.writeText(url).then(() => {
        Swal.fire({
          icon: 'success',
          title: '複製成功',
          text: 'Webhook URL 已複製到剪貼簿!',
          timer: 1500,
          showConfirmButton: false,
          toast: true,
          position: 'top-end'
        })
      }).catch(err => {
        console.error('複製失敗:', err)
        Swal.fire({
          icon: 'error',
          title: '複製失敗',
          text: '請手動複製'
        })
      })
    }

    // 格式化日期
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleString('zh-TW')
    }

    // 顯示過濾後的可用 Servers
    const getValidServers = (selectedServers) => {
      if (!selectedServers || !Array.isArray(selectedServers)) return []
      const availableNames = availableServers.value.map(s => s.name)
      return selectedServers.filter(name => availableNames.includes(name))
    }

    const getKbName = (kbId) => {
      const kb = availableKbs.value.find(k => k.id === kbId)
      return kb ? kb.name : `未知知識庫 (${kbId})`
    }

    const getPromptName = (promptId) => {
      const prompt = availablePrompts.value.find(p => p.id === promptId)
      return prompt ? prompt.name : `未知提示詞 (${promptId})`
    }

    // 初始化
    onMounted(async () => {
      await loadConfigs()
      await loadAvailableServers()
      await loadAvailableKbs()
      await loadAvailablePrompts()
    })

    return {
      configs,
      loading,
      showAddDialog,
      editingConfig,
      configForm,
      availableServers,
      loadConfigs,
      toggleConfig,
      editConfig,
      deleteConfig,
      closeDialog,
      saveConfig,
      copyWebhookUrl,
      formatDate,
      getValidServers,
      availableKbs,
      getKbName,
      availablePrompts,
      getPromptName
    }
  }
}
</script>

<style scoped>
.line-bot-management {
  height: 100%;
  overflow-y: auto;
  background: linear-gradient(135deg, #06C755 0%, #00B900 100%);
}

.page-header {
  background: rgba(255, 255, 255, 0.95);
  padding: 2rem;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.page-header h2 {
  font-size: 2rem;
  color: #06C755;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  font-size: 1rem;
}

.container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1rem 2rem 1rem;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.card-header h3 {
  color: #06C755;
  font-size: 1.3rem;
  margin: 0;
}

.loading, .empty-state {
  text-align: center;
  padding: 3rem;
  color: #999;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-hint {
  font-size: 0.9rem;
  color: #aaa;
  margin-top: 0.5rem;
}

/* 設定列表 */
.configs-list {
  display: grid;
  gap: 1.5rem;
}

.config-card {
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  transition: all 0.3s;
}

.config-card:hover {
  border-color: #06C755;
  box-shadow: 0 4px 12px rgba(6, 199, 85, 0.2);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.config-title {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.config-title h4 {
  color: #333;
  margin: 0;
  font-size: 1.2rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-badge.active {
  background: #d4edda;
  color: #155724;
}

.status-badge.inactive {
  background: #f8d7da;
  color: #721c24;
}

.config-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.info-row {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.info-row .label {
  font-weight: 600;
  color: #666;
  min-width: 120px;
}

.webhook-url {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.webhook-url code {
  background: #f5f5f5;
  padding: 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  flex: 1;
  overflow-x: auto;
}

.btn-copy {
  background: #06C755;
  color: white;
  border: none;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-copy:hover {
  background: #00B900;
}

.mcp-servers {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tool-badge {
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
}

.prompt-badge {
  background: #f3e5f5;
  color: #7b1fa2;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
}

.kb-badge {
  background: #fff3e0;
  color: #e65100;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
}

.no-tools {
  color: #999;
  font-style: italic;
}

.config-actions {
  display: flex;
  gap: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid #f0f0f0;
}

/* 開關 */
.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #06C755;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

/* 按鈕 */
.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #06C755;
  color: white;
}

.btn-primary:hover {
  background: #00B900;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
}

/* 說明卡片 */
.info-card h3 {
  color: #06C755;
  margin-bottom: 1rem;
}

.instructions {
  padding-left: 1.5rem;
  line-height: 1.8;
}

.instructions li {
  margin-bottom: 0.5rem;
}

.instructions a {
  color: #06C755;
  text-decoration: none;
  font-weight: 600;
}

.instructions a:hover {
  text-decoration: underline;
}

/* 對話框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 2px solid #f1f5f9;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
  transition: color 0.2s;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1.5rem;
  border-top: 2px solid #f0f0f0;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #334155;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s;
  background: white;
  color: #1e293b;
}

.form-input:focus {
  outline: none;
  border-color: #06C755;
}


/* MCP 工具選擇器 - 卡片式設計 */
.mcp-tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
  max-height: 400px;
  overflow-y: auto;
  padding: 0.5rem;
}

.tool-card {
  position: relative;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
  display: block;
}

.tool-card:hover {
  border-color: #06C755;
  box-shadow: 0 4px 12px rgba(6, 199, 85, 0.15);
  transform: translateY(-2px);
}

.tool-card.selected {
  border-color: #06C755;
  background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
  box-shadow: 0 4px 12px rgba(6, 199, 85, 0.2);
}

.tool-checkbox {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.tool-card-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.tool-icon {
  font-size: 2rem;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0fdf4 0%, #e8f5e9 100%);
  border-radius: 12px;
}

.tool-info {
  flex: 1;
  min-width: 0;
}

.tool-name {
  font-weight: 600;
  color: #333;
  font-size: 1rem;
  margin-bottom: 0.25rem;
}

.tool-desc {
  color: #666;
  font-size: 0.85rem;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.tool-check {
  flex-shrink: 0;
}

.no-servers {
  grid-column: 1 / -1;
  text-align: center;
  padding: 3rem 1rem;
  color: #999;
}

.no-servers-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-servers p {
  margin: 0.5rem 0;
}

.no-servers .hint {
  font-size: 0.85rem;
  color: #aaa;
}

</style>
