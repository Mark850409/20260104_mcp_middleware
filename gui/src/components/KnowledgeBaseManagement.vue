<template>
  <div class="kb-management">
    <div class="header">
      <h2><i class="ri-book-2-line"></i> 知識庫管理</h2>
      <button class="btn-primary" @click="showCreateModal = true"><i class="ri-add-line"></i> 建立知識庫</button>
    </div>

    <!-- 知識庫列表 -->
    <div v-if="kbs.length > 0" class="kb-grid">
      <div v-for="kb in kbs" :key="kb.id" class="kb-card">
        <div class="kb-info">
          <h3>{{ kb.name }}</h3>
          <p>{{ kb.description || '無描述' }}</p>
          <div class="kb-meta">
            <span><i class="ri-calendar-line"></i> {{ formatDate(kb.created_at) }}</span>
          </div>
        </div>
        <div class="kb-actions">
          <button class="btn-secondary" @click="selectKB(kb)"><i class="ri-folder-open-line"></i> 管理檔案</button>
          <button class="btn-warning" @click="openEditModal(kb)"><i class="ri-edit-line"></i> 編輯</button>
          <button class="btn-danger" @click="deleteKB(kb.id)"><i class="ri-delete-bin-line"></i> 刪除</button>
        </div>
      </div>
    </div>

    <!-- 沒有知識庫的空狀態 -->
    <div v-else class="empty-state-kb">
      <div class="empty-icon"><i class="ri-book-2-line"></i></div>
      <h3>尚未建立任何知識庫</h3>
      <p>建立您的第一個知識庫,開始管理文件和資料</p>
      <button class="btn-primary-large" @click="showCreateModal = true">
        <i class="ri-add-line"></i> 建立第一個知識庫
      </button>
      <div class="kb-features">
        <div class="feature-item">
          <span class="feature-icon"><i class="ri-file-search-line"></i></span>
          <span>支援多種文件格式</span>
        </div>
        <div class="feature-item">
          <span class="feature-icon"><i class="ri-radar-line"></i></span>
          <span>智能向量化搜尋</span>
        </div>
        <div class="feature-item">
          <span class="feature-icon"><i class="ri-robot-2-line"></i></span>
          <span>AI 知識問答</span>
        </div>
      </div>
    </div>

    <!-- 未選擇知識庫的提示 -->
    <div v-if="kbs.length > 0 && !selectedKB" class="select-kb-hint">
      <div class="hint-icon"><i class="ri-hand-up-line"></i></div>
      <p>請選擇一個知識庫以管理檔案</p>
    </div>

    <!-- 檔案管理區域 (選中知識庫後顯示) -->
    <div v-if="selectedKB" class="file-management mt-8">
      <div class="header">
        <div class="header-left">
          <h3><i class="ri-folder-open-line"></i> 檔案管理: {{ selectedKB.name }}</h3>
          <button class="btn-config" @click="showConfigModal = true" title="配置向量化參數">
            <i class="ri-settings-3-line"></i> 向量化配置
          </button>
        </div>
        <div class="file-ops">
          <input 
            type="file" 
            ref="fileInput" 
            style="display: none" 
            @change="handleFileUpload" 
            accept=".pdf,.docx,.txt,.md"
            multiple
          />
          <button class="btn-primary" @click="$refs.fileInput.click()" :disabled="uploading">
            <i :class="uploading ? 'ri-loader-4-line ri-spin' : 'ri-upload-2-line'"></i>
            {{ uploading ? '上傳中...' : '上傳檔案' }}
          </button>
          <button class="btn-success ml-2" @click="processFiles" :disabled="processing || selectedFiles.length === 0">
            <i :class="processing ? 'ri-loader-4-line ri-spin' : 'ri-settings-line'"></i>
            {{ processing ? '處理中...' : '開始向量化處理' }}
          </button>
          <button class="btn-danger-outline ml-2" @click="batchDeleteFiles" :disabled="selectedFiles.length === 0">
            <i class="ri-delete-bin-line"></i> 批次刪除
          </button>
        </div>
      </div>

      <!-- 拖曳上傳區域 -->
      <div 
        class="drag-drop-area"
        :class="{ 'drag-over': isDragging }"
        @drop.prevent="handleDrop"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @click="$refs.fileInput.click()"
      >
        <div class="drag-drop-content">
          <div class="upload-icon"><i class="ri-folder-upload-line"></i></div>
          <h4>拖曳檔案到此處上傳</h4>
          <p>或點擊選擇檔案</p>
          <div class="supported-formats">
            <span>支援格式:</span>
            <span class="format-badge">PDF</span>
            <span class="format-badge">DOCX</span>
            <span class="format-badge">TXT</span>
            <span class="format-badge">MD</span>
          </div>
        </div>
      </div>

      <!-- 上傳進度 -->
      <div v-if="uploadQueue.length > 0" class="upload-progress">
        <h4>上傳進度 ({{ uploadedCount }}/{{ uploadQueue.length }})</h4>
        <div v-for="(item, index) in uploadQueue" :key="index" class="progress-item">
          <div class="progress-info">
            <span class="file-name">{{ item.file.name }}</span>
            <span class="file-size">{{ formatSize(item.file.size) }}</span>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar" :style="{ width: item.progress + '%' }"></div>
          </div>
          <span class="progress-status">
            {{ item.status === 'uploading' ? '上傳中...' : item.status === 'success' ? '✓ 完成' : '✗ 失敗' }}
          </span>
        </div>
      </div>

      <!-- 檔案列表 -->
      <div v-if="files.length > 0" class="file-list">
        <table>
          <thead>
            <tr>
              <th><input type="checkbox" @change="toggleAllFiles" /></th>
              <th>檔名</th>
              <th>大小</th>
              <th>狀態</th>
              <th>上傳時間</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="file in files" :key="file.id">
              <td><input type="checkbox" v-model="selectedFiles" :value="file.id" /></td>
              <td>{{ file.name }}</td>
              <td>{{ formatSize(file.size) }}</td>
              <td>
                <span :class="['status-badge', file.status]">
                  {{ formatStatus(file.status) }}
                </span>
              </td>
              <td>{{ formatDate(file.created_at) }}</td>
              <td>
                <button class="btn-icon-danger" @click="deleteSingleFile(file.id)" title="刪除檔案">
                  <i class="ri-delete-bin-line"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 建立知識庫 Modal -->
    <div v-if="showCreateModal" class="modal-overlay">
      <div class="modal">
        <h3>建立新知識庫</h3>
        <div class="modal-body">
          <div class="form-group">
            <label>名稱</label>
            <input v-model="newKB.name" placeholder="輸入知識庫名稱" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="newKB.description" placeholder="輸入描述"></textarea>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showCreateModal = false">取消</button>
          <button class="btn-primary" @click="createKB">建立</button>
        </div>
      </div>
    </div>

    <!-- 編輯知識庫 Modal -->
    <div v-if="showEditModal" class="modal-overlay">
      <div class="modal">
        <h3>編輯知識庫</h3>
        <div class="modal-body">
          <div class="form-group">
            <label>名稱</label>
            <input v-model="editKBData.name" placeholder="輸入知識庫名稱" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="editKBData.description" placeholder="輸入描述"></textarea>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showEditModal = false">取消</button>
          <button class="btn-primary" @click="updateKB">儲存</button>
        </div>
      </div>
    </div>
  </div>

  <!-- 向量化配置 Modal -->
  <div v-if="showConfigModal" class="modal-overlay" @click.self="showConfigModal = false">
    <div class="modal config-modal">
      <div class="modal-header">
        <h2><i class="ri-settings-3-line"></i> 向量化配置</h2>
        <button class="modal-close" @click="showConfigModal = false">×</button>
      </div>
      <div class="modal-body">
        <div class="config-section">
          <h3><i class="ri-layout-grid-line"></i> 切分策略</h3>
          <div class="form-group">
            <label>切分方法</label>
            <select v-model="kbConfig.chunk_strategy" class="form-input">
              <option value="character">字符切分 (Character Split)</option>
              <option value="token">Token 切分 (Token Split)</option>
              <option value="semantic">語義切分 (Semantic Split)</option>
              <option value="recursive">遞歸切分 (Recursive Split)</option>
            </select>
            <p class="help-text">{{ getStrategyDescription(kbConfig.chunk_strategy) }}</p>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Chunk 大小: {{ kbConfig.chunk_size }}</label>
              <input 
                type="range" 
                v-model.number="kbConfig.chunk_size" 
                min="100" 
                max="2000" 
                step="50"
                class="form-range"
              />
              <p class="help-text">建議: 500-1000 字元/tokens</p>
            </div>

            <div class="form-group">
              <label>重疊大小: {{ kbConfig.chunk_overlap }}</label>
              <input 
                type="range" 
                v-model.number="kbConfig.chunk_overlap" 
                min="0" 
                max="500" 
                step="10"
                class="form-range"
              />
              <p class="help-text">建議: chunk_size 的 10-20%</p>
            </div>
          </div>
        </div>

        <div class="config-section">
          <h3><i class="ri-openai-fill"></i> Embedding 配置</h3>
          <div class="form-row">
            <div class="form-group">
              <label>提供者</label>
              <select v-model="kbConfig.embedding_provider" class="form-input">
                <option value="openai">OpenAI</option>
                <option value="google">Google Gemini</option>
                <option value="local">本地模型 (SentenceTransformers)</option>
              </select>
            </div>

            <div class="form-group">
              <label>模型</label>
              <select v-model="kbConfig.embedding_model" class="form-input">
                <option v-if="kbConfig.embedding_provider === 'openai'" value="text-embedding-3-small">text-embedding-3-small (1536維)</option>
                <option v-if="kbConfig.embedding_provider === 'openai'" value="text-embedding-3-large">text-embedding-3-large (3072維)</option>
                <option v-if="kbConfig.embedding_provider === 'google'" value="text-embedding-004">text-embedding-004 (768維)</option>
                <option v-if="kbConfig.embedding_provider === 'local'" value="paraphrase-multilingual-MiniLM-L12-v2">Multi-MiniLM (384維, 推薦)</option>
                <option v-if="kbConfig.embedding_provider === 'local'" value="all-MiniLM-L6-v2">all-MiniLM-L6-v2 (384維)</option>
              </select>
            </div>
          </div>
        </div>

        <div class="config-section">
          <h3><i class="ri-flashlight-line"></i> 索引配置</h3>
          <div class="form-group">
            <label>索引類型</label>
            <select v-model="kbConfig.index_type" class="form-input">
              <option value="flat">Flat (精確搜尋, 適合小數據)</option>
              <option value="ivf">IVF (倒排索引, 適合中大數據)</option>
              <option value="hnsw">HNSW (圖索引, 適合大規模檢索)</option>
            </select>
            <p class="help-text">{{ getIndexDescription(kbConfig.index_type) }}</p>
          </div>
        </div>

        <div class="config-section">
          <h3><i class="ri-search-line"></i> 檢索配置</h3>
          <div class="form-group">
            <label>返回數量 (Top K): {{ kbConfig.retrieval_top_k }}</label>
            <input 
              type="range" 
              v-model.number="kbConfig.retrieval_top_k" 
              min="1" 
              max="15" 
              step="1"
              class="form-range"
            />
            <p class="help-text">檢索時返回最相關的 K 個結果</p>
          </div>
        </div>

        <div class="config-preview">
          <h4><i class="ri-bar-chart-box-line"></i> 配置預覽</h4>
          <div class="preview-grid">
            <div class="preview-item">
              <span class="preview-label">切分策略:</span>
              <span class="preview-value">{{ getStrategyName(kbConfig.chunk_strategy) }}</span>
            </div>
            <div class="preview-item">
              <span class="preview-label">Chunk 大小:</span>
              <span class="preview-value">{{ kbConfig.chunk_size }}</span>
            </div>
            <div class="preview-item">
              <span class="preview-label">重疊大小:</span>
              <span class="preview-value">{{ kbConfig.chunk_overlap }}</span>
            </div>
            <div class="preview-item">
              <span class="preview-label">Embedding:</span>
              <span class="preview-value">{{ kbConfig.embedding_model }}</span>
            </div>
            <div class="preview-item">
              <span class="preview-label">Top K:</span>
              <span class="preview-value">{{ kbConfig.retrieval_top_k }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="modal-actions">
        <button class="btn-secondary" @click="showConfigModal = false">取消</button>
        <button class="btn-primary" @click="saveConfig">儲存配置</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import Swal from 'sweetalert2'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

export default {
  name: 'KnowledgeBaseManagement',
  setup() {
    const kbs = ref([])
    const files = ref([])
    const selectedKB = ref(null)
    const selectedFiles = ref([])
    const showCreateModal = ref(false)
    const showEditModal = ref(false)
    const showConfigModal = ref(false)
    const uploading = ref(false)
    const processing = ref(false)
    const newKB = ref({ name: '', description: '' })
    const editKBData = ref({ id: null, name: '', description: '' })
    const isDragging = ref(false)
    const uploadQueue = ref([])
    const uploadedCount = ref(0)
    const kbConfig = ref({
      chunk_strategy: 'character',
      chunk_size: 500,
      chunk_overlap: 50,
      embedding_provider: 'openai',
      embedding_model: 'text-embedding-3-small',
      index_type: 'flat',
      retrieval_top_k: 3
    })

    const fetchKBs = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/rag/kb`)
        if (res.data.success) kbs.value = res.data.data
      } catch (err) {
        Swal.fire({
          icon: 'error',
          title: '取得失敗',
          text: '取得知識庫失敗: ' + err.message,
          confirmButtonText: '確定'
        })
      }
    }

    const createKB = async () => {
      if (!newKB.value.name) return
      try {
        const res = await axios.post(`${API_URL}/api/rag/kb`, newKB.value)
        if (res.data.success) {
          showCreateModal.value = false
          newKB.value = { name: '', description: '' }
          fetchKBs()
          Swal.fire({
            icon: 'success',
            title: '建立成功',
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
          })
        }
      } catch (err) {
        Swal.fire({
          icon: 'error',
          title: '建立失敗',
          text: err.message
        })
      }
    }

    const openEditModal = (kb) => {
      editKBData.value = { ...kb }
      showEditModal.value = true
    }

    const updateKB = async () => {
      try {
        const res = await axios.put(`${API_URL}/api/rag/kb/${editKBData.value.id}`, {
          name: editKBData.value.name,
          description: editKBData.value.description
        })
        if (res.data.success) {
          showEditModal.value = false
          fetchKBs()
          Swal.fire({
            icon: 'success',
            title: '更新成功',
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000
          })
        }
      } catch (err) {
        Swal.fire({
          icon: 'error',
          title: '更新失敗',
          text: err.message
        })
      }
    }

    const deleteKB = async (id) => {
      const result = await Swal.fire({
        title: '確定要刪除嗎？',
        text: '此操作將永久刪除知識庫及其所有關聯檔案！',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: '是的，刪除它',
        cancelButtonText: '取消',
        reverseButtons: true
      })

      if (!result.isConfirmed) return

      try {
        const res = await axios.delete(`${API_URL}/api/rag/kb/${id}`)
        if (res.data.success) {
          fetchKBs()
          if (selectedKB.value && selectedKB.value.id === id) {
            selectedKB.value = null
          }
          Swal.fire({
            icon: 'success',
            title: '已刪除',
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000
          })
        }
      } catch (err) {
        Swal.fire({
          icon: 'error',
          title: '刪除失敗',
          text: err.message
        })
      }
    }

    const selectKB = async (kb) => {
      selectedKB.value = kb
      // 載入知識庫配置
      await loadKBConfig(kb.id)
      // 載入檔案列表
      fetchFiles()
    }

    const loadKBConfig = async (kbId) => {
      try {
        const res = await axios.get(`${API_URL}/api/rag/kb/${kbId}/config`)
        if (res.data.success && res.data.data) {
          kbConfig.value = {
            chunk_strategy: res.data.data.chunk_strategy || 'character',
            chunk_size: res.data.data.chunk_size || 500,
            chunk_overlap: res.data.data.chunk_overlap || 50,
            embedding_provider: res.data.data.embedding_provider || 'openai',
            embedding_model: res.data.data.embedding_model || 'text-embedding-3-small',
            index_type: res.data.data.index_type || 'flat',
            retrieval_top_k: res.data.data.retrieval_top_k || 3
          }
        }
      } catch (err) {
        console.error('載入配置失敗:', err)
        // 使用預設配置
      }
    }

    const saveConfig = async () => {
      if (!selectedKB.value) return
      
      try {
        const res = await axios.put(
          `${API_URL}/api/rag/kb/${selectedKB.value.id}/config`,
          kbConfig.value
        )
        
        if (res.data.success) {
          Swal.fire({
            icon: 'success',
            title: '配置已儲存',
            text: '請重新處理檔案以套用新配置。',
            confirmButtonText: '確定',
            confirmButtonColor: '#6366f1'
          })
          showConfigModal.value = false
        }
      } catch (err) {
        Swal.fire({
          icon: 'error',
          title: '儲存失敗',
          text: err.message
        })
      }
    }

    const fetchFiles = async () => {
      if (!selectedKB.value) return
      try {
        const res = await axios.get(`${API_URL}/api/rag/kb/${selectedKB.value.id}/files`)
        if (res.data.success) files.value = res.data.data
      } catch (err) {
        console.error('取得檔案列表失敗:', err)
      }
    }

    const handleFileUpload = async (event) => {
      const fileList = event.target.files
      if (!fileList || fileList.length === 0) return

      await uploadFiles(Array.from(fileList))
      
      // 清空 input
      event.target.value = ''
    }

    const handleDrop = async (event) => {
      isDragging.value = false
      const fileList = event.dataTransfer.files
      if (!fileList || fileList.length === 0) return

      await uploadFiles(Array.from(fileList))
    }

    const uploadFiles = async (fileArray) => {
      if (!selectedKB.value) {
        Swal.fire({
          icon: 'info',
          title: '提示',
          text: '請先選擇知識庫'
        })
        return
      }

      // 過濾檔案類型
      const allowedExtensions = ['.pdf', '.docx', '.txt', '.md']
      const validFiles = fileArray.filter(file => {
        const ext = '.' + file.name.split('.').pop().toLowerCase()
        return allowedExtensions.includes(ext)
      })

      if (validFiles.length === 0) {
        Swal.fire({
          icon: 'warning',
          title: '不支援的格式',
          text: '請選擇 PDF, DOCX, TXT 或 MD 檔案'
        })
        return
      }

      if (validFiles.length < fileArray.length) {
        Swal.fire({
          icon: 'info',
          title: '檔案過濾',
          text: `已過濾 ${fileArray.length - validFiles.length} 個不支援的檔案`
        })
      }

      // 初始化上傳隊列
      uploadQueue.value = validFiles.map(file => ({
        file,
        progress: 0,
        status: 'pending'
      }))
      uploadedCount.value = 0
      uploading.value = true

      // 依序上傳每個檔案
      for (let i = 0; i < uploadQueue.value.length; i++) {
        const item = uploadQueue.value[i]
        item.status = 'uploading'

        try {
          const formData = new FormData()
          formData.append('file', item.file)
          formData.append('kb_id', selectedKB.value.id)

          const res = await axios.post(`${API_URL}/api/rag/upload`, formData, {
            onUploadProgress: (progressEvent) => {
              item.progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            }
          })

          if (res.data.success) {
            item.status = 'success'
            item.progress = 100
            uploadedCount.value++
          } else {
            item.status = 'error'
          }
        } catch (err) {
          console.error(`上傳 ${item.file.name} 失敗:`, err)
          item.status = 'error'
        }
      }

      uploading.value = false
      
      // 刷新檔案列表
      await fetchFiles()

      // 3秒後清空上傳隊列
      setTimeout(() => {
        uploadQueue.value = []
        uploadedCount.value = 0
      }, 3000)
    }

    const processFiles = async () => {
      if (!selectedKB.value) return
      if (selectedFiles.value.length === 0) {
        Swal.fire({
          icon: 'info',
          title: '提醒',
          text: '請先選擇要處理的檔案',
          confirmButtonColor: '#6366f1'
        })
        return
      }
      
      processing.value = true
      try {
        const res = await axios.post(`${API_URL}/api/rag/kb/${selectedKB.value.id}/process`, {
          file_ids: selectedFiles.value
        })
        
        if (res.data.success) {
          const { chunks_count, config } = res.data
          const strategyName = getStrategyName(config.strategy)
          
          Swal.fire({
            icon: 'success',
            title: '向量化處理完成',
            html: `
              <div style="text-align: left; padding: 10px; background: #f8fafc; border-radius: 8px;">
                <p>📊 <b>處理結果：</b></p>
                <ul style="list-style: none; padding-left: 0;">
                  <li style="margin-bottom: 5px;">📍 產生區塊：<span style="color: #6366f1; font-weight: bold;">${chunks_count}</span> 個</li>
                  <li style="margin-bottom: 5px;">🧩 切分策略：<span style="color: #6366f1; font-weight: bold;">${strategyName}</span></li>
                  <li>📏 Chunk 大小：<span style="color: #6366f1; font-weight: bold;">${config.chunk_size}</span></li>
                </ul>
                <p style="margin-top: 10px; font-size: 0.9em; color: #64748b;">索引已建立並可供檢索。</p>
              </div>
            `,
            confirmButtonText: '確定',
            confirmButtonColor: '#6366f1'
          })
          
          fetchFiles()
          selectedFiles.value = []
        }
      } catch (err) {
        Swal.fire({
          icon: 'error',
          title: '處理失敗',
          text: err.message
        })
      } finally {
        processing.value = false
      }
    }

    const deleteSingleFile = (fileId) => {
      Swal.fire({
        title: '確定要刪除嗎？',
        text: '刪除後將無法從知識庫中檢索此檔案內容！',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: '確定刪除',
        cancelButtonText: '取消',
        reverseButtons: true
      }).then((result) => {
        if (result.isConfirmed) {
          deleteFiles([fileId])
        }
      })
    }

    const batchDeleteFiles = () => {
      if (selectedFiles.value.length === 0) return
      Swal.fire({
        title: '確定要批次刪除嗎？',
        text: `確定要刪除選中的 ${selectedFiles.value.length} 個檔案嗎？`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: '確定刪除',
        cancelButtonText: '取消',
        reverseButtons: true
      }).then((result) => {
        if (result.isConfirmed) {
          deleteFiles(selectedFiles.value)
        }
      })
    }

    const deleteFiles = async (fileIds) => {
      try {
        const res = await axios.post(`${API_URL}/api/rag/files/delete`, { file_ids: fileIds })
        if (res.data.success) {
          fetchFiles()
          selectedFiles.value = selectedFiles.value.filter(id => !fileIds.includes(id))
          Swal.fire({
            icon: 'success',
            title: '檔案已刪除',
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 2000
          })
        }
      } catch (err) {
        Swal.fire({
          icon: 'error',
          title: '刪除失敗',
          text: err.message
        })
      }
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleString()
    }

    const formatSize = (bytes) => {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const formatStatus = (status) => {
      const map = {
        'pending': '等待處理',
        'processing': '處理中...',
        'completed': '已完成',
        'failed': '失敗'
      }
      return map[status] || status
    }

    const toggleAllFiles = (event) => {
      if (event.target.checked) {
        selectedFiles.value = files.value.map(f => f.id)
      } else {
        selectedFiles.value = []
      }
    }

    const getStrategyName = (strategy) => {
      const names = {
        'character': '字符切分',
        'token': 'Token 切分',
        'semantic': '語義切分',
        'recursive': '遞歸切分'
      }
      return names[strategy] || strategy
    }

    const getStrategyDescription = (strategy) => {
      const descriptions = {
        'character': '簡單快速的字符切分,適用於一般文件',
        'token': '基於 Token 的切分,精確控制長度,適用於技術文件',
        'semantic': '基於句子的語義切分,保持語義完整性,適用於對話和文章',
        'recursive': '遞歸切分,智能處理不同層級,適用於結構化文件'
      }
      return descriptions[strategy] || ''
    }

    const getIndexDescription = (type) => {
      const descriptions = {
        'flat': '暴力搜尋,最精確但速度隨數據量增加而下降,適用於小於 1 萬條的數據',
        'ivf': '倒排索引,透過聚類加速搜尋,適合中大型數據集',
        'hnsw': '圖索引,極速檢索且精確度高,是目前大規模檢索的業界標準'
      }
      return descriptions[type] || ''
    }

    onMounted(fetchKBs)

    return {
      kbs, files, selectedKB, selectedFiles, showCreateModal, showEditModal, showConfigModal, uploading, processing, newKB, editKBData,
      isDragging, uploadQueue, uploadedCount, kbConfig,
      fetchKBs, createKB, openEditModal, updateKB, deleteKB, selectKB, loadKBConfig, saveConfig,
      handleFileUpload, handleDrop, processFiles, batchDeleteFiles, deleteSingleFile,
      formatDate, formatSize, formatStatus, toggleAllFiles,
      getStrategyName, getStrategyDescription, getIndexDescription
    }
  }
}
</script>

<style scoped>
.kb-management {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.header h2 {
  color: var(--color-text-primary);
  font-size: 1.8rem;
  font-weight: 700;
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.kb-card {
  background: var(--color-slate-800);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--color-border);
}

.kb-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  border-color: var(--color-primary-500);
}

.kb-info h3 {
  margin-bottom: 0.5rem;
  color: var(--color-text-primary);
}

.kb-info p {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.kb-meta {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.kb-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-primary {
  background: var(--color-primary-600);
  color: white;
  border: none;
  padding: 0.6rem 1.25rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all var(--transition-base);
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
  padding: 0.6rem 1.25rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all var(--transition-base);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-background-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.btn-warning {
  background: #fff7ed;
  color: #ea580c;
  border: 1.5px solid #fdba74;
  padding: 0.6rem 1.25rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all var(--transition-base);
}

.btn-warning:hover:not(:disabled) {
  background: #ffedd5;
  border-color: #f97316;
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.btn-danger {
  background: #fee2e2;
  color: #ef4444;
  border: 1.5px solid #fecaca;
  padding: 0.6rem 1.25rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all var(--transition-base);
}

.btn-danger:hover:not(:disabled) {
  background: #fef2f2;
  border-color: #dc2626;
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.btn-success {
  background: #10b981;
  color: white;
  border: none;
  padding: 0.6rem 1.25rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all var(--transition-base);
}

.btn-success:hover:not(:disabled) {
  background: #059669;
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.btn-icon-danger {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.btn-icon-danger:hover {
  background: #fee2e2;
}

.btn-primary:hover { background: #4338ca; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.file-list {
  background: var(--color-slate-800);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  margin-top: 1rem;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-primary);
}

th { background: var(--color-slate-800); font-weight: 600; color: var(--color-text-primary); }

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-badge.pending { background: #fef3c7; color: #d97706; }
.status-badge.processing { background: #dbeafe; color: #2563eb; }
.status-badge.completed { background: #d1fae5; color: #059669; }
.status-badge.failed { background: #fee2e2; color: #dc2626; }

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: var(--color-surface);
  padding: 0;
  border-radius: var(--radius-xl);
  width: 95%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
}

.modal h3 {
  padding: 1.5rem 2rem;
  margin: 0;
  background: var(--color-background-secondary);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-primary);
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.form-group input, .form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-background);
  color: var(--color-text-primary);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.mt-8 { margin-top: 2rem; }
.ml-2 { margin-left: 0.5rem; }

/* 空狀態樣式 */
.empty-state {
  background: var(--color-slate-100);
  border-radius: 16px;
  padding: 4rem 2rem;
  text-align: center;
  margin-top: 1rem;
  border: 2px dashed #cbd5e1;
  transition: all 0.3s ease;
}

.empty-state:hover {
  border-color: #94a3b8;
  background: var(--color-slate-200);
}

.empty-icon {
  font-size: 5rem;
  margin-bottom: 1.5rem;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.empty-state h3 {
  color: var(--color-text-primary);
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.empty-state p {
  color: var(--color-text-secondary);
  font-size: 1rem;
  margin-bottom: 2rem;
}

.btn-primary-large {
  background: var(--color-primary-600);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
  transition: all 0.3s ease;
}

.btn-primary-large:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
  background: var(--color-primary-700);
}

.btn-primary-large:active {
  transform: translateY(0px);
}

.supported-formats {
  margin-top: 2rem;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.supported-formats > span:first-child {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 500;
}

.format-badge {
  background: var(--color-background-secondary);
  color: var(--color-text-tertiary);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
  transition: all var(--transition-base) ease;
}

.format-badge:hover {
  transform: scale(1.05);
  border-color: #4f46e5;
  box-shadow: 0 4px 8px rgba(79, 70, 229, 0.2);
}

/* 知識庫空狀態樣式 */
.empty-state-kb {
  background: var(--color-background-secondary);
  border-radius: 24px;
  padding: 5rem 2rem;
  text-align: center;
  margin: 2rem 0;
  border: 2px dashed var(--color-border);
  transition: all var(--transition-base) ease;
}

.empty-state-kb:hover {
  border-color: #38bdf8;
  background: var(--color-blue-200);
  transform: translateY(-2px);
}

.empty-state-kb .empty-icon {
  font-size: 6rem;
  margin-bottom: 1.5rem;
  animation: float 3s ease-in-out infinite;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
}

.empty-state-kb h3 {
  color: var(--color-text-primary);
  font-size: 2rem;
  margin-bottom: 0.75rem;
  font-weight: 700;
}

.empty-state-kb p {
  color: var(--color-text-secondary);
  font-size: 1.1rem;
  margin-bottom: 2.5rem;
}

.kb-features {
  margin-top: 3rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.feature-item {
  background: var(--color-surface);
  padding: 1.75rem;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
  transition: all var(--transition-base) ease;
}

.feature-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(79, 70, 229, 0.15);
}

.feature-icon {
  font-size: 2.5rem;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.feature-item span:last-child {
  color: var(--color-text-secondary);
  font-size: 0.95rem;
  font-weight: 500;
}

/* 選擇知識庫提示 */
.select-kb-hint {
  background: var(--color-orange-200);
  border-radius: 16px;
  padding: 3rem 2rem;
  text-align: center;
  margin: 2rem 0;
  border: 2px dashed #fbbf24;
  animation: pulse-hint 2s ease-in-out infinite;
}

@keyframes pulse-hint {
  0%, 100% {
    transform: scale(1);
    border-color: #fbbf24;
  }
  50% {
    transform: scale(1.01);
    border-color: #f59e0b;
  }
}

.file-management h3 {
  font-size: 1.3rem;
  margin-bottom: 1rem;
  color: var(--color-text-primary);
}
.hint-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.btn-process {
  background: var(--color-green-600);
  color: white;
  padding: 0.75rem 1.75rem;
  border-radius: 10px;
  border: none;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
  transition: all var(--transition-base) ease;
}

.btn-process:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 15px rgba(16, 185, 129, 0.35);
  background: var(--color-green-700);
}

.btn-process:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  background: #9ca3af;
  box-shadow: none;
}

.btn-config {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  padding: 0.75rem 1.25rem;
  border-radius: 10px;
  color: var(--color-text-secondary);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all var(--transition-base);
  cursor: pointer;
}

.btn-config:hover {
  border-color: #6366f1;
  color: #6366f1;
  box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.1);
}

/* Config Modal Specifics */
.config-modal {
  max-width: 800px;
  width: 95%;
  max-height: 90vh;
  overflow: hidden;
  background: var(--color-surface);
  z-index: 10000;
  padding: 0;
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--color-border);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1.25rem;
  padding: 1.5rem 2rem;
  border-top: 1px solid var(--color-border);
  background: var(--color-background-secondary);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  background: var(--color-background-secondary);
  z-index: 10;
}

.modal-header h2 {
  font-size: 1.5rem;
  color: #1e293b;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #94a3b8;
  cursor: pointer;
  padding: 0.5rem;
  line-height: 1;
  transition: color 0.2s;
}

.modal-close:hover {
  color: #1e293b;
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

.config-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.config-section:last-of-type {
  border-bottom: none;
}

.config-section h3 {
  font-size: 1.1rem;
  color: #1e293b;
  margin-bottom: 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.form-input {
  width: 100%;
  padding: 0.85rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background-color: var(--color-background);
  font-size: 1rem;
  color: var(--color-text-primary);
  transition: all var(--transition-base) ease;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2364748b'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 1.25rem;
}

.form-input:hover {
  border-color: #cbd5e1;
  background-color: #f8fafc;
}

.form-input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-range {
  width: 100%;
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  outline: none;
  appearance: none;
  margin: 1.25rem 0;
  cursor: pointer;
}

.form-range::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  background: #6366f1;
  border-radius: 50%;
  cursor: pointer;
  border: 3px solid white;
  box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
  transition: transform 0.2s ease;
}

.form-range::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.help-text {
  font-size: 0.85rem;
  color: #64748b;
  margin-top: 0.25rem;
  line-height: 1.4;
}

.config-preview {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 8px;
  margin-top: 1.5rem;
}

.config-preview h4 {
  font-size: 0.95rem;
  color: #475569;
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: white;
  border: 1px solid #edf2f7;
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.preview-label {
  font-size: 0.85rem;
  color: var(--color-text-tertiary);
}

.preview-value {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}

/* 拖曳上傳區域 */
.drag-drop-area {
  border: 3px dashed var(--color-border);
  border-radius: 20px;
  padding: 4rem 2rem;
  text-align: center;
  background: var(--color-background-secondary);
  cursor: pointer;
  transition: all var(--transition-base) ease;
  margin-bottom: 2rem;
}

.drag-drop-area:hover {
  border-color: var(--color-primary-500);
  background: var(--color-surface-hover);
}

.drag-drop-area.drag-over {
  border-color: var(--color-primary-600);
  background: var(--color-primary-100);
  transform: scale(1.02);
}

.drag-drop-content {
  pointer-events: none;
}

.upload-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.drag-drop-area h4 {
  color: var(--color-text-primary);
  font-size: 1.5rem;
  margin: 0 0 0.5rem 0;
}

.drag-drop-area p {
  color: var(--color-text-secondary);
  font-size: 1rem;
  margin: 0 0 1.5rem 0;
}

.supported-formats {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.supported-formats > span:first-child {
  color: #64748b;
  font-size: 0.9rem;
}

.format-badge {
  background: #e0e7ff;
  color: #4f46e5;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
}

/* 上傳進度 */
.upload-progress {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 1.75rem;
  margin-bottom: 2rem;
  box-shadow: var(--shadow-sm);
}

.upload-progress h4 {
  color: #1e293b;
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
}

.progress-item {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding: 1rem;
  background: var(--color-background-secondary);
  border-radius: 12px;
  margin-bottom: 1rem;
}

.progress-item:last-child {
  margin-bottom: 0;
}

.progress-info {
  flex: 0 0 200px;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.file-name {
  color: #1e293b;
  font-weight: 500;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  color: #64748b;
  font-size: 0.8rem;
}

.progress-bar-container {
  flex: 1;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: var(--color-primary-600);
  transition: width 0.3s ease;
  border-radius: 4px;
}

.progress-status {
  flex: 0 0 80px;
  text-align: right;
  font-size: 0.85rem;
  font-weight: 500;
}

.progress-status:contains('完成') {
  color: #059669;
}

.progress-status:contains('失敗') {
  color: #dc2626;
}

.progress-status:contains('上傳中') {
  color: #6366f1;
}

/* ============================================
   淺色主題覆蓋樣式
   ============================================ */
[data-theme="light"] .kb-card {
  background: var(--color-surface);
  border-color: var(--color-border);
}

[data-theme="light"] .kb-card h3 {
  color: var(--color-text-primary);
}

[data-theme="light"] .kb-card p {
  color: var(--color-text-secondary);
}

[data-theme="light"] .file-list table {
  background: var(--color-background);
}

[data-theme="light"] .file-list th {
  background: var(--color-slate-100);
  color: var(--color-text-primary);
}

[data-theme="light"] .file-list td {
  color: var(--color-text-primary);
  border-bottom-color: var(--color-border);
}

[data-theme="light"] .file-list tr:hover {
  background: var(--color-slate-50);
}

[data-theme="light"] .drag-drop-area {
  background: var(--color-slate-50);
  border-color: var(--color-border);
}

[data-theme="light"] .drag-drop-area h4,
[data-theme="light"] .drag-drop-area p {
  color: var(--color-text-primary);
}

[data-theme="light"] .modal {
  background: var(--color-surface);
  color: var(--color-text-primary);
}

[data-theme="light"] .modal h2,
[data-theme="light"] .modal h3,
[data-theme="light"] .modal h4 {
  color: var(--color-text-primary);
}

[data-theme="light"] .form-input {
  background: var(--color-background);
  border-color: var(--color-border);
  color: var(--color-text-primary);
}

[data-theme="light"] .help-text {
  color: var(--color-text-tertiary);
}

[data-theme="light"] .config-preview {
  background: var(--color-slate-50);
}

[data-theme="light"] .preview-label {
  color: var(--color-text-secondary);
}

[data-theme="light"] .preview-value {
  color: var(--color-text-primary);
}

</style>
