<template>
  <div class="kb-management">
    <div class="header">
      <h2>📚 知識庫管理</h2>
      <button class="btn-primary" @click="showCreateModal = true">➕ 建立知識庫</button>
    </div>

    <!-- 知識庫列表 -->
    <div v-if="kbs.length > 0" class="kb-grid">
      <div v-for="kb in kbs" :key="kb.id" class="kb-card">
        <div class="kb-info">
          <h3>{{ kb.name }}</h3>
          <p>{{ kb.description || '無描述' }}</p>
          <div class="kb-meta">
            <span>📅 {{ formatDate(kb.created_at) }}</span>
          </div>
        </div>
        <div class="kb-actions">
          <button class="btn-secondary" @click="selectKB(kb)">📂 管理檔案</button>
          <button class="btn-warning" @click="openEditModal(kb)">✏️ 編輯</button>
          <button class="btn-danger" @click="deleteKB(kb.id)">🗑️ 刪除</button>
        </div>
      </div>
    </div>

    <!-- 沒有知識庫的空狀態 -->
    <div v-else class="empty-state-kb">
      <div class="empty-icon">📚</div>
      <h3>尚未建立任何知識庫</h3>
      <p>建立您的第一個知識庫,開始管理文件和資料</p>
      <button class="btn-primary-large" @click="showCreateModal = true">
        ➕ 建立第一個知識庫
      </button>
      <div class="kb-features">
        <div class="feature-item">
          <span class="feature-icon">📄</span>
          <span>支援多種文件格式</span>
        </div>
        <div class="feature-item">
          <span class="feature-icon">🔍</span>
          <span>智能向量化搜尋</span>
        </div>
        <div class="feature-item">
          <span class="feature-icon">🤖</span>
          <span>AI 知識問答</span>
        </div>
      </div>
    </div>

    <!-- 未選擇知識庫的提示 -->
    <div v-if="kbs.length > 0 && !selectedKB" class="select-kb-hint">
      <div class="hint-icon">👆</div>
      <p>請選擇一個知識庫以管理檔案</p>
    </div>

    <!-- 檔案管理區域 (選中知識庫後顯示) -->
    <div v-if="selectedKB" class="file-management mt-8">
      <div class="header">
        <h3>📁 檔案管理: {{ selectedKB.name }}</h3>
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
            {{ uploading ? '上傳中...' : '📤 上傳檔案' }}
          </button>
          <button class="btn-success ml-2" @click="processFiles" :disabled="processing || selectedFiles.length === 0">
            {{ processing ? '處理中...' : '⚙️ 開始向量化處理' }}
          </button>
          <button class="btn-danger-outline ml-2" @click="batchDeleteFiles" :disabled="selectedFiles.length === 0">
            🗑️ 批次刪除
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
          <div class="upload-icon">📁</div>
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
                <button class="btn-icon-danger" @click="deleteSingleFile(file.id)" title="刪除檔案">🗑️</button>
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
        <div class="form-group">
          <label>名稱</label>
          <input v-model="newKB.name" placeholder="輸入知識庫名稱" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="newKB.description" placeholder="輸入描述"></textarea>
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
        <div class="form-group">
          <label>名稱</label>
          <input v-model="editKBData.name" placeholder="輸入知識庫名稱" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="editKBData.description" placeholder="輸入描述"></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showEditModal = false">取消</button>
          <button class="btn-primary" @click="updateKB">儲存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

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
    const uploading = ref(false)
    const processing = ref(false)
    const newKB = ref({ name: '', description: '' })
    const editKBData = ref({ id: null, name: '', description: '' })
    const isDragging = ref(false)
    const uploadQueue = ref([])
    const uploadedCount = ref(0)

    const fetchKBs = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/rag/kb`)
        if (res.data.success) kbs.value = res.data.data
      } catch (err) {
        alert('取得知識庫失敗: ' + err.message)
      }
    }

    const createKB = async () => {
      try {
        const res = await axios.post(`${API_URL}/api/rag/kb`, newKB.value)
        if (res.data.success) {
          fetchKBs()
          showCreateModal.value = false
          newKB.value = { name: '', description: '' }
        }
      } catch (err) {
        alert('建立失敗: ' + err.message)
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
          fetchKBs()
          showEditModal.value = false
          if (selectedKB.value && selectedKB.value.id === editKBData.value.id) {
            selectedKB.value = { ...selectedKB.value, ...editKBData.value }
          }
        }
      } catch (err) {
        alert('更新失敗: ' + err.message)
      }
    }

    const deleteKB = async (id) => {
      if (!confirm('確定要刪除此知識庫嗎？此操作無法復原。')) return
      try {
        const res = await axios.delete(`${API_URL}/api/rag/kb/${id}`)
        if (res.data.success) {
          fetchKBs()
          if (selectedKB.value && selectedKB.value.id === id) {
            selectedKB.value = null
          }
        }
      } catch (err) {
        alert('刪除失敗: ' + err.message)
      }
    }

    const selectKB = (kb) => {
      selectedKB.value = kb
      // 這裡假設我們有一個 API 可以取得所有檔案或是該 KB 的檔案
      // 為了簡化，我們先拿取所有檔案 (之後可優化)
      fetchFiles()
    }

    const fetchFiles = async () => {
      // 這裡需要後端提供 list files API，目前 rag.py 沒寫，我們先補一個或直接處理
      // 假設後端已經有這個端點
      try {
        const res = await axios.get(`${API_URL}/api/rag/files`)
        if (res.data.success) files.value = res.data.data
      } catch (err) {
        console.error('取得檔案失敗', err)
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
        alert('請先選擇知識庫')
        return
      }

      // 過濾檔案類型
      const allowedExtensions = ['.pdf', '.docx', '.txt', '.md']
      const validFiles = fileArray.filter(file => {
        const ext = '.' + file.name.split('.').pop().toLowerCase()
        return allowedExtensions.includes(ext)
      })

      if (validFiles.length === 0) {
        alert('沒有支援的檔案格式')
        return
      }

      if (validFiles.length < fileArray.length) {
        alert(`已過濾 ${fileArray.length - validFiles.length} 個不支援的檔案`)
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
      processing.value = true
      try {
        const res = await axios.post(`${API_URL}/api/rag/kb/${selectedKB.value.id}/process`, {
          file_ids: selectedFiles.value
        })
        if (res.data.success) {
          alert('處理完成')
          fetchFiles()
          selectedFiles.value = []
        }
      } catch (err) {
        alert('處理失敗: ' + err.message)
      } finally {
        processing.value = false
      }
    }

    const deleteSingleFile = (fileId) => {
      if (confirm('確定要刪除此檔案嗎？')) {
        deleteFiles([fileId])
      }
    }

    const batchDeleteFiles = () => {
      if (selectedFiles.value.length === 0) return
      if (confirm(`確定要刪除選中的 ${selectedFiles.value.length} 個檔案嗎？`)) {
        deleteFiles(selectedFiles.value)
      }
    }

    const deleteFiles = async (fileIds) => {
      try {
        const res = await axios.post(`${API_URL}/api/rag/files/delete`, { file_ids: fileIds })
        if (res.data.success) {
          fetchFiles()
          selectedFiles.value = selectedFiles.value.filter(id => !fileIds.includes(id))
        }
      } catch (err) {
        alert('刪除檔案失敗: ' + err.message)
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

    onMounted(fetchKBs)

    return {
      kbs, files, selectedKB, selectedFiles, showCreateModal, showEditModal, uploading, processing, newKB, editKBData,
      isDragging, uploadQueue, uploadedCount,
      fetchKBs, createKB, openEditModal, updateKB, deleteKB, selectKB, handleFileUpload, handleDrop, processFiles, batchDeleteFiles, deleteSingleFile,
      formatDate, formatSize, formatStatus, toggleAllFiles
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

.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.kb-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.kb-info h3 {
  margin-bottom: 0.5rem;
  color: #1e293b;
}

.kb-info p {
  color: #64748b;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.kb-meta {
  font-size: 0.75rem;
  color: #94a3b8;
}

.kb-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1.5rem;
}

.btn-primary { background: #4f46e5; color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }
.btn-secondary { background: #f1f5f9; color: #475569; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }
.btn-warning { background: #fff7ed; color: #ea580c; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }
.btn-danger { background: #fee2e2; color: #ef4444; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }
.btn-danger-outline { background: white; color: #ef4444; border: 1px solid #fee2e2; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }
.btn-success { background: #10b981; color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }

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
  background: white;
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
  border-bottom: 1px solid #f1f5f9;
}

th { background: #f8fafc; font-weight: 600; color: #475569; }

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
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.form-group input, .form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
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
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 16px;
  padding: 4rem 2rem;
  text-align: center;
  margin-top: 1rem;
  border: 2px dashed #cbd5e1;
  transition: all 0.3s ease;
}

.empty-state:hover {
  border-color: #94a3b8;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
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
  color: #1e293b;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.empty-state p {
  color: #64748b;
  font-size: 1rem;
  margin-bottom: 2rem;
}

.btn-primary-large {
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
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
  background: linear-gradient(135deg, #4338ca 0%, #4f46e5 100%);
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
  background: white;
  color: #4f46e5;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.format-badge:hover {
  transform: scale(1.05);
  border-color: #4f46e5;
  box-shadow: 0 4px 8px rgba(79, 70, 229, 0.2);
}

/* 知識庫空狀態樣式 */
.empty-state-kb {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 20px;
  padding: 5rem 2rem;
  text-align: center;
  margin: 2rem 0;
  border: 2px dashed #7dd3fc;
  transition: all 0.3s ease;
}

.empty-state-kb:hover {
  border-color: #38bdf8;
  background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
  transform: translateY(-2px);
}

.empty-state-kb .empty-icon {
  font-size: 6rem;
  margin-bottom: 1.5rem;
  animation: float 3s ease-in-out infinite;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
}

.empty-state-kb h3 {
  color: #0c4a6e;
  font-size: 2rem;
  margin-bottom: 0.75rem;
  font-weight: 700;
}

.empty-state-kb p {
  color: #0369a1;
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
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
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
  color: #475569;
  font-size: 0.95rem;
  font-weight: 500;
}

/* 選擇知識庫提示 */
.select-kb-hint {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
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

.select-kb-hint p {
  color: #92400e;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0;
}

/* 拖曳上傳區域 */
.drag-drop-area {
  border: 3px dashed #cbd5e1;
  border-radius: 12px;
  padding: 3rem 2rem;
  text-align: center;
  background: #f8fafc;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 2rem;
}

.drag-drop-area:hover {
  border-color: #6366f1;
  background: #eef2ff;
}

.drag-drop-area.drag-over {
  border-color: #4f46e5;
  background: #e0e7ff;
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
  color: #1e293b;
  font-size: 1.5rem;
  margin: 0 0 0.5rem 0;
}

.drag-drop-area p {
  color: #64748b;
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
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.upload-progress h4 {
  color: #1e293b;
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
}

.progress-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 0.75rem;
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
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
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



</style>
