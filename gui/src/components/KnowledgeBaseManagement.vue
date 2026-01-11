<template>
  <div class="kb-management">
    <div class="header">
      <h2>📚 知識庫管理</h2>
      <button class="btn-primary" @click="showCreateModal = true">➕ 建立知識庫</button>
    </div>

    <!-- 知識庫列表 -->
    <div class="kb-grid">
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

    <!-- 檔案管理區域 (選中知識庫後顯示) -->
    <div v-if="selectedKB" class="file-management mt-8">
      <div class="header">
        <h3>📁 檔案管理: {{ selectedKB.name }}</h3>
        <div class="file-ops">
          <input type="file" ref="fileInput" style="display: none" @change="handleFileUpload" accept=".pdf,.docx,.txt,.md" />
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

      <div class="file-list">
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
      const file = event.target.files[0]
      if (!file) return

      const formData = new FormData()
      formData.append('file', file)

      uploading.ref = true
      try {
        const res = await axios.post(`${API_URL}/api/rag/upload`, formData)
        if (res.data.success) {
          alert('上傳成功')
          fetchFiles()
        }
      } catch (err) {
        alert('上傳失敗: ' + err.message)
      } finally {
        uploading.value = false
      }
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
      createKB, openEditModal, updateKB, deleteKB, selectKB, handleFileUpload, processFiles, deleteSingleFile, batchDeleteFiles, formatDate, formatSize, formatStatus, toggleAllFiles
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
</style>
