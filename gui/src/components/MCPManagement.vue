<template>
  <div class="mcp-management">
    <!-- 標題區 -->
    <header class="page-header">
      <h2><i class="ri-settings-3-line"></i> MCP 工具管理</h2>
      <p class="subtitle">管理與操作 Model Context Protocol 工具</p>
      
      <div class="header-actions" style="display: flex; gap: 10px; justify-content: center; margin-top: 15px;">
        <button @click="exportConfig" class="btn" style="background-color: #4b5563; color: white;">
          <i class="ri-download-2-line"></i> 匯出配置
        </button>
        <button @click="triggerImport" class="btn" style="background-color: #2563eb; color: white;">
          <i class="ri-upload-2-line"></i> 匯入配置
        </button>
        <input 
          type="file" 
          ref="fileInput" 
          style="display: none;"
          accept=".json" 
          @change="handleImportFile" 
        />
      </div>
    </header>

    <!-- Tab 切換 -->
    <div class="tabs-container">
      <div class="tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          :class="['tab', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          <i :class="tab.icon"></i> {{ tab.label }}
        </button>
      </div>
    </div>

    <!-- 主要內容區 -->
    <div class="container">
      <!-- Tab 1: MCP Servers 管理 -->
      <div v-if="activeTab === 'servers'" class="tab-content">
        <div class="card">
          <div class="card-header">
            <h3><i class="ri-server-line"></i> MCP Servers</h3>
            <button @click="showAddServerDialog = true" class="btn btn-primary">
              <i class="ri-add-line"></i> 新增 Server
            </button>
          </div>

          <div v-if="loadingServers" class="loading">載入中...</div>
          <div v-else-if="servers.length === 0" class="empty-state">
            尚未配置任何 MCP Server
          </div>
          <div v-else class="servers-grid">
            <div v-for="server in servers" :key="server.name" class="server-card">
              <div class="server-header">
                <div>
                  <h4>{{ server.name }}</h4>
                  <p class="server-description">{{ server.description || '無描述' }}</p>
                </div>
                <label class="switch">
                  <input 
                    type="checkbox" 
                    :checked="server.enabled" 
                    @change="toggleServer(server.name, $event.target.checked)"
                  />
                  <span class="slider"></span>
                </label>
              </div>

              <div class="server-info">
                <!-- HTTP/SSE Server -->
                <template v-if="server.url">
                    <div class="info-row">
                        <span class="label">URL:</span>
                        <code class="url-text">{{ server.url }}</code>
                    </div>
                </template>
                
                <!-- Local/Node Server -->
                <template v-else>
                    <div class="info-row">
                        <span class="label">Command:</span>
                        <code>{{ server.command }}</code>
                    </div>
                    <div class="info-row">
                        <span class="label">Args:</span>
                        <code>{{ server.args ? server.args.join(' ') : '' }}</code>
                    </div>
                </template>

                <!-- Env / Headers -->
                <div v-if="server.env && Object.keys(server.env).length > 0" class="info-row">
                  <span class="label">Env:</span>
                  <code>{{ Object.keys(server.env).length }} 個變數</code>
                </div>
                <div v-if="server.headers && Object.keys(server.headers).length > 0" class="info-row">
                  <span class="label">Headers:</span>
                  <code>{{ Object.keys(server.headers).length }} 個變數</code>
                </div>
              </div>

              <div class="server-actions">
                <button @click="editServer(server)" class="btn btn-sm btn-secondary">
                  <i class="ri-edit-line"></i> 編輯
                </button>
                <button 
                  @click="testServer(server.name)" 
                  :disabled="testingServers[server.name]" 
                  class="btn btn-sm btn-info"
                >
                  <i :class="testingServers[server.name] ? 'ri-loader-4-line ri-spin' : 'ri-search-line'"></i>
                  {{ testingServers[server.name] ? '測試中...' : '測試' }}
                </button>
                <button @click="deleteServer(server.name)" class="btn btn-sm btn-danger">
                  <i class="ri-delete-bin-line"></i> 刪除
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab 2: Tools 管理 -->
      <div v-if="activeTab === 'tools'" class="tab-content">
        <div class="card">
          <div class="card-header">
            <h3><i class="ri-tools-line"></i> MCP Tools</h3>
            <select v-model="selectedServerForTools" class="form-select">
              <option value="">-- 選擇 Server --</option>
              <option v-for="server in enabledServers" :key="server.name" :value="server.name">
                {{ server.name }}
              </option>
            </select>
          </div>

          <div v-if="loadingTools" class="loading">載入中...</div>
          <div v-else-if="!selectedServerForTools" class="empty-state">
            請先選擇一個 Server
          </div>
          <div v-else-if="tools.length === 0" class="empty-state">
            此 Server 沒有可用的工具
          </div>
          <div v-else class="tools-list">
            <div v-for="tool in tools" :key="tool.name" class="tool-item">
              <div class="tool-header">
                <h4>{{ tool.name }}</h4>
                <button @click="quickTestTool(tool)" class="btn btn-sm btn-success">
                  <i class="ri-flashlight-line"></i> 快速測試
                </button>
              </div>
              <p class="tool-description">{{ tool.description }}</p>
              <details class="tool-schema">
                <summary>參數 Schema</summary>
                <pre>{{ JSON.stringify(tool.inputSchema, null, 2) }}</pre>
              </details>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab 3: Playground 操作區 -->
      <div v-if="activeTab === 'playground'" class="tab-content">
        <div class="playground-layout">
          <div class="playground-main card">
            <h3>⚡ Tool Playground</h3>

            <!-- Server 選擇 -->
            <div class="form-group">
              <label>選擇 Server:</label>
              <select v-model="playgroundServer" class="form-select" @change="onServerChange">
                <option value="">-- 請選擇 Server --</option>
                <option v-for="server in enabledServers" :key="server.name" :value="server.name">
                  {{ server.name }}
                </option>
              </select>
            </div>

            <!-- Tool 選擇 -->
            <div class="form-group">
              <label>選擇 Tool:</label>
              <select v-model="playgroundTool" class="form-select" @change="onToolChange">
                <option value="">-- 請選擇工具 --</option>
                <option v-for="tool in playgroundTools" :key="tool.name" :value="tool.name">
                  {{ tool.name }}
                </option>
              </select>
            </div>

            <!-- 動態參數輸入 -->
            <div v-if="playgroundTool && selectedToolSchema" class="form-group">
              <label>參數輸入:</label>
              <div v-for="(prop, key) in selectedToolSchema.properties" :key="key" class="param-input">
                <label class="param-label">
                  {{ key }}
                  <span v-if="selectedToolSchema.required?.includes(key)" class="required">*</span>
                </label>
                <input
                  v-model="playgroundArguments[key]"
                  :type="prop.type === 'number' || prop.type === 'integer' ? 'number' : 'text'"
                  :placeholder="prop.description || key"
                  class="form-input"
                />
              </div>
            </div>

            <!-- 執行按鈕 -->
            <div class="form-group">
              <button
                @click="executePlayground"
                :disabled="!playgroundTool || executing"
                class="btn btn-execute"
              >
                <i :class="executing ? 'ri-loader-4-line ri-spin' : 'ri-rocket-line'"></i>
                {{ executing ? '執行中...' : '執行 Tool' }}
              </button>
            </div>

            <!-- 結果顯示 -->
            <div v-if="playgroundResult" class="result-section">
              <h4>執行結果:</h4>
              <div :class="['result-box', playgroundResult.success ? 'success' : 'error']">
                <pre>{{ JSON.stringify(playgroundResult, null, 2) }}</pre>
              </div>
            </div>
          </div>

          <!-- 執行歷史 -->
          <div class="playground-sidebar card">
            <h4><i class="ri-history-line"></i> 執行歷史</h4>
            <div v-if="executionHistory.length === 0" class="empty-state-small">
              尚無執行記錄
            </div>
            <div v-else class="history-list">
              <div 
                v-for="(item, index) in executionHistory" 
                :key="index"
                class="history-item"
                @click="loadHistoryItem(item)"
              >
                <div class="history-header">
                  <span class="history-tool">{{ item.tool }}</span>
                  <span :class="['history-status', item.success ? 'success' : 'error']">
                    {{ item.success ? '✓' : '✗' }}
                  </span>
                </div>
                <div class="history-time">{{ formatTime(item.time) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

    <!-- 新增/編輯 Server 對話框 -->
    <div v-if="showAddServerDialog || editingServer" class="modal-overlay" @click.self="closeServerDialog">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingServer ? '編輯 Server' : '新增 Server' }}</h3>
          <button @click="closeServerDialog" class="btn-close">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Server 名稱 *</label>
            <input 
              v-model="serverForm.name" 
              :disabled="!!editingServer"
              class="form-input" 
              placeholder="例如: weather, github"
            />
          </div>
          <div class="form-group">
            <label>描述</label>
            <input 
              v-model="serverForm.description" 
              class="form-input" 
              placeholder="Server 的功能描述"
            />
          </div>
          
          <!-- 工具來源選擇器 -->
          <div class="form-group">
            <label>工具來源 *</label>
            <select v-model="serverForm.source" class="form-select" @change="onSourceChange">
              <option value="local">本地工具 (自己開發)</option>
              <option value="npm">線上工具 (npm 套件)</option>
            </select>
          </div>
          
          <!-- 工具配置 (Command & Args) -->
          <div class="form-group">
              <label>Command *</label>
              <select v-model="serverForm.command" class="form-select">
                <option value="python">python</option>
                <option value="uvx">uvx</option>
                <option value="npx">npx</option>
                <option value="http">http (SSE)</option>
              </select>
            </div>
            
            <!-- HTTP URL 配置 -->
            <div v-if="serverForm.command === 'http'" class="form-group">
                <label>Server URL *</label>
                <input 
                    v-model="serverForm.url" 
                    class="form-input" 
                    placeholder="https://example.com/sse"
                />
            </div>

            <!-- 本地/NPX 工具參數 -->
            <div v-else class="form-group">
              <label>Args *</label>
              <div class="args-input">
                <div v-for="(arg, index) in serverForm.args" :key="index" class="arg-row">
                  <input v-model="serverForm.args[index]" class="form-input" placeholder="檔案路徑或參數" />
                  <button @click="removeArg(index)" class="btn btn-sm btn-danger">✕</button>
                </div>
                <button @click="addArg" class="btn btn-sm btn-secondary"><i class="ri-add-line"></i> 新增參數</button>
              </div>
            </div>
          
          <!-- 環境變數 / Headers -->
          <div class="form-group">
            <label>{{ serverForm.command === 'http' ? 'Headers' : 'Environment Variables' }}</label>
            <div class="env-input">
              <div v-for="(value, key) in serverForm.env" :key="key" class="env-row">
                <input :value="key" @input="updateEnvKey($event, key)" class="form-input" placeholder="KEY" />
                <input v-model="serverForm.env[key]" class="form-input" placeholder="VALUE" />
                <button @click="removeEnv(key)" class="btn btn-sm btn-danger">✕</button>
              </div>
              <button @click="addEnv" class="btn btn-sm btn-secondary"><i class="ri-add-line"></i> 新增環境變數</button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeServerDialog" class="btn btn-secondary">取消</button>
          <button @click="saveServer" :disabled="savingServer" class="btn btn-primary">
            {{ savingServer ? '儲存中...' : '儲存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import request from '../utils/request'
import Swal from 'sweetalert2'

// API 基礎 URL
const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

export default {
  name: 'MCPManagement',
  setup() {
    // API 基礎 URL 已定義在外部

    // Tab 管理
    const tabs = [
      { id: 'servers', label: 'Servers', icon: 'ri-server-line' },
      { id: 'tools', label: 'Tools', icon: 'ri-tools-line' },
      { id: 'playground', label: 'Playground', icon: 'ri-flashlight-line' }
    ]
    const activeTab = ref('servers')

    // Servers 管理
    const servers = ref([])
    const loadingServers = ref(false)
    const showAddServerDialog = ref(false)
    const editingServer = ref(null)
    const savingServer = ref(false)
    const testingServers = reactive({})
    const serverForm = ref({
      name: '',
      description: '',
      source: 'local',  // 預設為本地工具
      command: 'python',
      args: [''],
      url: '',
      env: {},
      enabled: true
    })
    
    // 檔案匯入
    const fileInput = ref(null)

    // Tools 管理
    const selectedServerForTools = ref('')
    const tools = ref([])
    const loadingTools = ref(false)

    // Playground
    const playgroundServer = ref('')
    const playgroundTool = ref('')
    const playgroundTools = ref([])
    const playgroundArguments = ref({})
    const playgroundResult = ref(null)
    const executing = ref(false)
    const executionHistory = ref([])

    // 計算屬性
    const enabledServers = computed(() => {
      return servers.value.filter(s => s.enabled)
    })

    const selectedToolSchema = computed(() => {
      if (!playgroundTool.value) return null
      const tool = playgroundTools.value.find(t => t.name === playgroundTool.value)
      return tool?.inputSchema || null
    })

    // Servers 管理方法
    const loadServers = async () => {
      loadingServers.value = true
      try {
        const response = await request.get('/api/mcp/servers')
        if (response.data.success) {
          const result = response.data.data
          // 如果回傳的是物件格式 (新的 config_manager 結構)
          if (result.mcpServers) {
            servers.value = Object.entries(result.mcpServers).map(([name, config]) => ({
              name,
              ...config
            }))
          } 
          // 如果回傳的是陣列 (舊的結構或是已經處理過的)
          else if (Array.isArray(result)) {
            servers.value = result
          }
          // 直接回傳字典但沒有 mcpServers key (可能直接是 server map)
          else if (typeof result === 'object') {
            servers.value = Object.entries(result).map(([name, config]) => ({
              name,
              ...config
            }))
          }
        }
      } catch (error) {
        console.error('載入 Servers 失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '載入失敗',
          text: '載入 Servers 失敗: ' + error.message
        })
      } finally {
        loadingServers.value = false
      }
    }

    const toggleServer = async (serverName, enabled) => {
      const loadingTimer = setTimeout(() => {
        Swal.fire({
          title: '狀態切換中...',
          text: '正在更新伺服器狀態，請稍後...',
          allowOutsideClick: false,
          didOpen: () => Swal.showLoading()
        })
      }, 3000)

      try {
        const response = await request.post(
          `/api/mcp/servers/${serverName}/toggle`, 
          { enabled },
          { headers: { 'Content-Type': 'application/json' } }
        )
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()

        if (response.data.success) {
          await loadServers()
        } else {
          Swal.fire({
            icon: 'error',
            title: '切換失敗',
            text: response.data.error || '未知錯誤'
          })
          await loadServers() // 恢復原狀態
        }
      } catch (error) {
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()
        console.error('切換 Server 狀態失敗:', error)
        const errorMsg = error.response?.data?.error || error.message
        Swal.fire({
          icon: 'error',
          title: '切換失敗',
          text: errorMsg
        })
        await loadServers() // 恢復原狀態
      }
    }

    const editServer = (server) => {
      editingServer.value = server
      
      // 判斷是否為線上工具 (command === 'npx')
      const isNpmTool = server.command === 'npx'
      const packageName = isNpmTool && server.args && server.args.length >= 2 
        ? server.args[1]  // args: ['-y', 'package-name']
        : ''
      
      serverForm.value = {
        name: server.name,
        description: server.description || '',
        source: isNpmTool ? 'npm' : 'local',
        command: isNpmTool ? 'npx' : (server.command || (server.url ? 'http' : 'python')),
        args: server.args ? [...server.args] : [''],
        url: server.url || '',
        env: { ...(server.env || server.headers || {}) },
        enabled: server.enabled
      }
    }

    const testServer = async (serverName) => {
      testingServers[serverName] = true
      const loadingTimer = setTimeout(() => {
        Swal.fire({
          title: '連線測試中...',
          text: `正在與 Server ${serverName} 建立連線，請稍後...`,
          allowOutsideClick: false,
          didOpen: () => Swal.showLoading()
        })
      }, 3000)

      try {
        const response = await request.post(
          `/api/mcp/servers/${serverName}/test`,
          {},
          { headers: { 'Content-Type': 'application/json' } }
        )
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()

        if (response.data.success) {
          Swal.fire({
            icon: 'success',
            title: '測試成功',
            text: `Server ${serverName} 連結正常!\n${response.data.message || ''}`
          })
        } else {
          Swal.fire({
            icon: 'error',
            title: '測試失敗',
            text: response.data.error || '未知錯誤'
          })
        }
      } catch (error) {
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()
        const errorMsg = error.response?.data?.error || error.message
        Swal.fire({
          icon: 'error',
          title: '測試異常',
          text: errorMsg
        })
      } finally {
        testingServers[serverName] = false
      }
    }

    const deleteServer = async (serverName) => {
      const result = await Swal.fire({
        title: '確定要刪除嗎?',
        text: `確定要刪除 Server "${serverName}" 嗎?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: '確定刪除',
        cancelButtonText: '取消'
      })
      
      if (!result.isConfirmed) return
      
      try {
        const response = await request.delete(`/api/mcp/servers/${serverName}`)
        if (response.data.success) {
          await loadServers()
        }
      } catch (error) {
        console.error('刪除 Server 失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '刪除失敗',
          text: error.message
        })
      }
    }

    const closeServerDialog = () => {
      showAddServerDialog.value = false
      editingServer.value = null
      serverForm.value = {
        name: '',
        description: '',
        source: 'local',
        command: 'python',
        args: [''],
        package: '',
        env: {},
        enabled: true
      }
    }

    const saveServer = async () => {
      savingServer.value = true
      const loadingTimer = setTimeout(() => {
        Swal.fire({
          title: '正在儲存...',
          text: '正在更新伺服器配置，請稍後...',
          allowOutsideClick: false,
          didOpen: () => Swal.showLoading()
        })
      }, 3000)

      try {
        // 建立配置物件
        const config = {
          source: serverForm.value.source,
          description: serverForm.value.description,
          enabled: serverForm.value.enabled,
        }
        
        // 根據來源類型新增對應欄位
        if (serverForm.value.command === 'http') {
            config.type = 'sse'
            config.url = serverForm.value.url
            config.headers = serverForm.value.env
        } else {
            config.command = serverForm.value.command
            config.args = serverForm.value.args.filter(a => a.trim())
            config.env = serverForm.value.env

            if (serverForm.value.command === 'node' || serverForm.value.command === 'npx') {
                config.type = 'nodejs'
            } else if (serverForm.value.command === 'python' || serverForm.value.command === 'uvx') {
                config.type = 'python'
            }
        }
        
        if (editingServer.value) {
          // 更新
          const response = await request.put(
            `/api/mcp/servers/${serverForm.value.name}`,
            config
          )
          clearTimeout(loadingTimer)
          if (Swal.isVisible()) Swal.close()

          if (response.data.success) {
            if (response.data.warning) {
              Swal.fire({
                icon: 'warning',
                title: '更新成功 (有警告)',
                text: response.data.warning
              })
            }
            await loadServers()
            closeServerDialog()
          }
        } else {
          // 新增
          const response = await request.post('/api/mcp/servers', {
            name: serverForm.value.name,
            config: config
          })
          clearTimeout(loadingTimer)
          if (Swal.isVisible()) Swal.close()

          if (response.data.success) {
            if (response.data.warning) {
              Swal.fire({
                icon: 'warning',
                title: '儲存成功 (有警告)',
                text: response.data.warning
              })
            }
            await loadServers()
            closeServerDialog()
          }
        }
      } catch (error) {
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()
        console.error('儲存 Server 失敗:', error)
        
        // 即使失敗也嘗試重整列表,因為可能是「部分成功」(例如資料庫存入但後續初始化報錯)
        await loadServers()
        
        Swal.fire({
          icon: 'error',
          title: '儲存失敗',
          text: error.response?.data?.error || error.message
        })
      } finally {
        savingServer.value = false
      }
    }

    // 匯出配置
    const exportConfig = () => {
      window.open('/api/mcp/export', '_blank')
    }
    
    // 觸發匯入
    const triggerImport = () => {
      fileInput.value.click()
    }
    
    const handleImportFile = async (event) => {
      const file = event.target.files[0]
      if (!file) return
      
      try {
        const reader = new FileReader()
        reader.onload = async (e) => {
          let loadingTimer
          try {
            const configData = JSON.parse(e.target.result)
            
            // 詢問使用者是否覆寫
            const confirmResult = await Swal.fire({
              title: '是否覆寫?',
              text: '是否覆寫現有同名的 Server 配置?',
              icon: 'question',
              showCancelButton: true,
              confirmButtonText: '是, 覆寫',
              cancelButtonText: '否, 略過同名項目'
            })
            
            const overwrite = confirmResult.isConfirmed
            
            loadingTimer = setTimeout(() => {
              Swal.fire({
                title: '正在匯入配置...',
                text: '正在處理檔案內容並同步至 Server，請稍後...',
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading()
              })
            }, 3000)

            const response = await request.post(
              '/api/mcp/import', 
              configData,
              { 
                params: { overwrite },
                headers: { 'Content-Type': 'application/json' } 
              }
            )
            
            clearTimeout(loadingTimer)
            if (Swal.isVisible()) Swal.close()

            if (response.data.success) {
              const result = response.data.result
              Swal.fire({
                icon: 'success',
                title: '匯入完成',
                html: `成功: ${result.success}<br>失敗: ${result.failed}<br>略過: ${result.skipped}`
              })
              await loadServers()
            }
          } catch (error) {
            if (loadingTimer) clearTimeout(loadingTimer)
            if (Swal.isVisible()) Swal.close()
            console.error('匯入失敗:', error)
            Swal.fire({
              icon: 'error',
              title: '匯入失敗',
              text: error.response?.data?.error || error.message
            })
          }
        }
        reader.readAsText(file)
      } catch (error) {
        console.error('讀取檔案失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '讀取失敗',
          text: '讀取檔案失敗'
        })
      } finally {
        // 清空 input 以便下次能選同個檔案
        event.target.value = ''
      }
    }

    const addArg = () => {
      serverForm.value.args.push('')
    }

    const removeArg = (index) => {
      serverForm.value.args.splice(index, 1)
    }

    const addEnv = () => {
      const key = prompt('請輸入環境變數名稱:')
      if (key) {
        serverForm.value.env[key] = ''
      }
    }

    const removeEnv = (key) => {
      delete serverForm.value.env[key]
    }

    const updateEnvKey = (event, oldKey) => {
      const newKey = event.target.value
      if (newKey !== oldKey) {
        const value = serverForm.value.env[oldKey]
        delete serverForm.value.env[oldKey]
        serverForm.value.env[newKey] = value
      }
    }
    
    // 來源切換處理
    const onSourceChange = () => {
      // 切換來源時設定預設 command
      if (serverForm.value.source === 'npm') {
        serverForm.value.command = 'npx'
        serverForm.value.args = ['-y', ''] // 預設帶上 -y
      } else {
        serverForm.value.command = 'python'
        serverForm.value.args = ['']
        serverForm.value.url = ''
      }
    }

    // Tools 管理方法
    const loadTools = async (serverName) => {
      loadingTools.value = true
      try {
        const response = await axios.get(`${API_URL}/api/mcp/servers/${serverName}/tools`)
        if (response.data.tools) {
          tools.value = response.data.tools
        }
      } catch (error) {
        console.error('載入 Tools 失敗:', error)
        tools.value = []
      } finally {
        loadingTools.value = false
      }
    }

    const quickTestTool = (tool) => {
      activeTab.value = 'playground'
      playgroundServer.value = selectedServerForTools.value
      playgroundTool.value = tool.name
      playgroundTools.value = tools.value
    }

    // Playground 方法
    const onServerChange = async () => {
      playgroundTool.value = ''
      playgroundArguments.value = {}
      playgroundResult.value = null
      
      if (playgroundServer.value) {
        await loadPlaygroundTools()
      }
    }

    const loadPlaygroundTools = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/mcp/servers/${playgroundServer.value}/tools`)
        if (response.data.tools) {
          playgroundTools.value = response.data.tools
        }
      } catch (error) {
        console.error('載入 Tools 失敗:', error)
        playgroundTools.value = []
      }
    }

    const onToolChange = () => {
      playgroundArguments.value = {}
      playgroundResult.value = null
    }

    const executePlayground = async () => {
      executing.value = true
      playgroundResult.value = null

      const loadingTimer = setTimeout(() => {
        Swal.fire({
          title: '工具執行中...',
          text: `正在執行 ${playgroundTool.value}，請稍後...`,
          allowOutsideClick: false,
          didOpen: () => Swal.showLoading()
        })
      }, 3000)

      try {
        const response = await axios.post(
          `${API_URL}/api/mcp/servers/${playgroundServer.value}/tools/${playgroundTool.value}/invoke`,
          { arguments: playgroundArguments.value }
        )
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()

        playgroundResult.value = response.data
        // ...
      } catch (error) {
        clearTimeout(loadingTimer)
        if (Swal.isVisible()) Swal.close()
        console.error('執行工具失敗:', error)
        // ...
      } finally {
        executing.value = false
      }
    }

    const loadHistoryItem = (item) => {
      playgroundServer.value = item.server
      playgroundTool.value = item.tool
      playgroundArguments.value = { ...item.arguments }
      playgroundResult.value = item.result
    }

    const formatTime = (date) => {
      return new Date(date).toLocaleTimeString('zh-TW')
    }

    // Watch
    watch(selectedServerForTools, (newServer) => {
      if (newServer) {
        loadTools(newServer)
      } else {
        tools.value = []
      }
    })

    // 初始化
    onMounted(async () => {
      await loadServers()
    })

    return {
      tabs,
      activeTab,
      servers,
      loadingServers,
      showAddServerDialog,
      editingServer,
      serverForm,
      enabledServers,
      fileInput,
      exportConfig,
      triggerImport,
      handleImportFile,
      toggleServer,
      editServer,
      testServer,
      testingServers,
      savingServer,
      deleteServer,
      closeServerDialog,
      saveServer,
      onSourceChange,
      addArg,
      removeArg,
      addEnv,
      removeEnv,
      updateEnvKey,
      selectedServerForTools,
      tools,
      loadingTools,
      quickTestTool,
      playgroundServer,
      playgroundTool,
      playgroundTools,
      playgroundArguments,
      playgroundResult,
      executing,
      executionHistory,
      selectedToolSchema,
      onServerChange,
      onToolChange,
      executePlayground,
      loadHistoryItem,
      formatTime
    }
  }
}
</script>

<style scoped>
.mcp-management {
  background: var(--color-background);
}

.page-header {
  background: var(--color-background-secondary);
  padding: 2rem;
  text-align: center;
  border-bottom: 1px solid var(--color-border);
}

.page-header h2 {
  font-size: 2rem;
  color: var(--color-primary-600);
  margin-bottom: 0.5rem;
}

.subtitle {
  color: var(--color-text-secondary);
  font-size: 1rem;
}

.tabs-container {
  background: var(--color-background-secondary);
  padding: 0 2rem;
  border-bottom: 1px solid var(--color-border);
}

.tabs {
  display: flex;
  gap: 0.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.tab {
  padding: 1rem 2rem;
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
}

.tab:hover {
  color: #667eea;
}

.tab.active {
  color: #667eea;
  border-bottom-color: #667eea;
}

.container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1rem 2rem 1rem;
}

.tab-content {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 2.5rem;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.card-header h3 {
  color: var(--color-primary-600);
  font-size: 1.4rem;
  margin: 0;
}

.loading, .empty-state {
  text-align: center;
  padding: 3rem;
  color: #999;
  font-size: 1.1rem;
}

.empty-state-small {
  text-align: center;
  padding: 2rem 1rem;
  color: #999;
  font-size: 0.9rem;
}

/* Servers Grid */
.servers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.server-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 1.5rem;
  background: var(--color-background);
  transition: all var(--transition-base);
}

.server-card:hover {
  border-color: var(--color-primary-400);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.server-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.server-header h4 {
  color: var(--color-text-primary);
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  font-weight: 700;
}

.server-description {
  color: #666;
  font-size: 0.9rem;
  margin: 0;
}

.server-info {
  margin: 1rem 0;
}

.info-row {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.info-row .label {
  font-weight: 600;
  color: var(--color-text-secondary);
  min-width: 80px;
}

.info-row code {
  background: var(--color-background-secondary);
  color: var(--color-text-primary);
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  font-size: 0.85rem;
  flex: 1;
  border: 1px solid var(--color-border);
}

.url-text {
  word-break: break-all;
}

.server-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
  flex-wrap: wrap;
}

/* Tools List */
.tools-list {
  display: grid;
  gap: 1rem;
}

.tool-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  transition: border-color 0.2s;
}

.tool-item:hover {
  border-color: #667eea;
}

.tool-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.tool-header h4 {
  color: #333;
  margin: 0;
  font-size: 1.1rem;
}

.tool-description {
  color: #666;
  margin-bottom: 0.5rem;
}

.tool-schema {
  margin-top: 0.5rem;
}

.tool-schema summary {
  cursor: pointer;
  color: #667eea;
  font-weight: 600;
}

.tool-schema pre {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  margin-top: 0.5rem;
  font-size: 0.9rem;
}

/* Playground */
.playground-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 1.5rem;
}

.playground-main {
  min-height: 600px;
}

.playground-sidebar {
  max-height: 600px;
  overflow-y: auto;
}

.playground-sidebar h4 {
  color: #667eea;
  margin-bottom: 1rem;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.history-item {
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  color: #c0392b;
  font-family: monospace;
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  border-color: #667eea;
  background: #f9fafb;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.history-tool {
  font-weight: 600;
  font-size: 0.9rem;
  color: #333;
}

.history-status {
  font-size: 1.2rem;
}

.history-status.success {
  color: #10b981;
}

.history-status.error {
  color: #ef4444;
}

.history-time {
  font-size: 0.75rem;
  color: #999;
}

/* Forms */
.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #334155;
}

.form-select,
.form-input {
  width: 100%;
  padding: 0.85rem 1rem;
  border: 1.5px solid var(--color-border);
  border-radius: 10px;
  font-size: 1rem;
  transition: all var(--transition-base);
  background: var(--color-background);
  color: var(--color-text-primary);
}

.form-select:focus,
.form-input:focus {
  outline: none;
  border-color: #667eea;
}

.param-input {
  margin-bottom: 1rem;
}

.param-label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.3rem;
  color: #555;
  font-size: 0.9rem;
}

.required {
  color: #ef4444;
}

.result-section {
  margin-top: 1.5rem;
}

.result-box {
  border-radius: 8px;
  padding: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.result-box.success {
  background: #d1fae5;
  border: 2px solid #10b981;
}

.result-box.error {
  background: #fee2e2;
  border: 2px solid #ef4444;
}

.result-box pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

/* Buttons */
.btn {
  padding: 0.75rem 1.75rem;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-base);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-sm {
  padding: 0.4rem 1rem;
  font-size: 0.9rem;
}

.btn-primary {
  background: var(--color-primary-600);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-700);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.btn-secondary {
  background: var(--color-background-secondary);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-background-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.btn-success {
  background: #10b981;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #059669;
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.btn-info {
  background: #3b82f6;
  color: white;
}

.btn-info:hover:not(:disabled) {
  background: #2563eb;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn-execute {
  background: #10b981;
  color: white;
  width: 100%;
  padding: 1rem;
  font-size: 1.1rem;
}

.btn-execute:hover:not(:disabled) {
  background: #059669;
  transform: scale(1.02);
}

/* Switch */
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
  background-color: #667eea;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

/* Modal */
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
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: 0;
  width: 95%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background-secondary);
}

.modal-header h3 {
  color: #667eea;
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  padding: 2rem;
  overflow-y: auto;
  flex: 1;
  max-height: calc(90vh - 160px);
}

.modal-body::-webkit-scrollbar {
  width: 6px;
}

.modal-body::-webkit-scrollbar-track {
  background: transparent;
}

.modal-body::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 10px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1.25rem;
  padding: 1.5rem 2rem;
  border-top: 1px solid var(--color-border);
  background: var(--color-background-secondary);
}

.args-input, .env-input {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.arg-row, .env-row {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.arg-row .form-input,
.env-row .form-input {
  flex: 1;
}

/* Responsive */
@media (max-width: 1024px) {
  .playground-layout {
    grid-template-columns: 1fr;
  }

  .playground-sidebar {
    max-height: 300px;
  }
}

@media (max-width: 768px) {
  .page-header h2 {
    font-size: 1.5rem;
  }

  .container {
    padding: 0 0.5rem 2rem 0.5rem;
  }

  .card {
    padding: 1rem;
  }

  .servers-grid {
    grid-template-columns: 1fr;
  }

  .tabs {
    overflow-x: auto;
  }

  .tab {
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
  }
}

/* 表單提示文字 */
.form-hint {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #666;
  font-style: italic;
}
/* 淺色模式背景覆蓋 */
[data-theme="light"] .mcp-management {
  background: var(--color-background);
}

[data-theme="light"] .page-header {
  background: var(--color-background);
}

[data-theme="light"] .card {
  background: var(--color-surface);
  color: var(--color-text-primary);
}

[data-theme="light"] .empty-state {
  color: var(--color-text-tertiary);
}
</style>
