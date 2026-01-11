<template>
  <div class="prompt-management">
    <div class="header">
      <h2>📝 系統提示詞管理</h2>
      <button @click="showCreateDialog = true" class="btn-create">
        ➕ 新增提示詞
      </button>
    </div>

    <div class="prompts-list">
      <div v-if="prompts.length === 0" class="empty-state">
        尚無提示詞，點擊上方按鈕創建
      </div>

      <div
        v-for="prompt in prompts"
        :key="prompt.id"
        class="prompt-card"
        :class="{ 'is-default': prompt.is_default }"
      >
        <div class="prompt-header">
          <div class="prompt-title">
            <h3>{{ prompt.name }}</h3>
            <span v-if="prompt.is_default" class="default-badge">⭐ 預設</span>
          </div>
          <div class="prompt-actions">
            <button @click="editPrompt(prompt)" class="btn-edit" title="編輯">
              ✏️
            </button>
            <button @click="deletePrompt(prompt)" class="btn-delete" title="刪除">
              🗑️
            </button>
          </div>
        </div>

        <p v-if="prompt.description" class="prompt-description">
          {{ prompt.description }}
        </p>

        <div class="prompt-content">
          {{ prompt.content }}
        </div>

        <div class="prompt-footer">
          <span class="prompt-date">
            {{ formatDate(prompt.created_at) }}
          </span>
          <button
            v-if="!prompt.is_default"
            @click="setAsDefault(prompt.id)"
            class="btn-set-default"
          >
            設為預設
          </button>
        </div>
      </div>
    </div>

    <!-- 創建/編輯對話框 -->
    <div v-if="showCreateDialog || showEditDialog" class="dialog-overlay" @click.self="closeDialog">
      <div class="dialog">
        <div class="dialog-header">
          <h3>{{ isEditing ? '編輯提示詞' : '新增提示詞' }}</h3>
          <button @click="closeDialog" class="btn-close">✕</button>
        </div>

        <div class="dialog-body">
          <div class="form-group">
            <label>名稱 *</label>
            <input
              v-model="formData.name"
              type="text"
              placeholder="例如：專業助手"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label>描述</label>
            <input
              v-model="formData.description"
              type="text"
              placeholder="簡短描述這個提示詞的用途"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label>提示詞內容 *</label>
            <textarea
              v-model="formData.content"
              placeholder="輸入系統提示詞內容..."
              rows="8"
              class="form-textarea"
            ></textarea>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input
                v-model="formData.is_default"
                type="checkbox"
              />
              <span>設為預設提示詞</span>
            </label>
          </div>
        </div>

        <div class="dialog-footer">
          <button @click="closeDialog" class="btn-cancel">取消</button>
          <button @click="savePrompt" class="btn-save">
            {{ isEditing ? '更新' : '創建' }}
          </button>
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
  name: 'PromptManagement',
  setup() {
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

    const prompts = ref([])
    const showCreateDialog = ref(false)
    const showEditDialog = ref(false)
    const isEditing = ref(false)
    const editingId = ref(null)

    const formData = ref({
      name: '',
      description: '',
      content: '',
      is_default: false
    })

    const loadPrompts = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/prompts`)
        if (response.data.success) {
          prompts.value = response.data.prompts
        }
      } catch (error) {
        console.error('載入提示詞失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '載入失敗',
          text: error.message
        })
      }
    }

    const editPrompt = (prompt) => {
      isEditing.value = true
      editingId.value = prompt.id
      formData.value = {
        name: prompt.name,
        description: prompt.description || '',
        content: prompt.content,
        is_default: prompt.is_default
      }
      showEditDialog.value = true
    }

    const deletePrompt = async (prompt) => {
      const result = await Swal.fire({
        title: '確定要刪除嗎？',
        text: `確定要刪除「${prompt.name}」嗎？此操作無法復原。`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: '確定刪除',
        cancelButtonText: '取消'
      })

      if (!result.isConfirmed) return

      try {
        const response = await axios.delete(`${API_URL}/api/prompts/${prompt.id}`)
        if (response.data.success) {
          await loadPrompts()
          Swal.fire({
            icon: 'success',
            title: '已刪除',
            text: response.data.message,
            timer: 1500,
            showConfirmButton: false
          })
        }
      } catch (error) {
        console.error('刪除提示詞失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '刪除失敗',
          text: error.response?.data?.error || error.message
        })
      }
    }

    const setAsDefault = async (promptId) => {
      try {
        const response = await axios.put(`${API_URL}/api/prompts/${promptId}`, {
          is_default: true
        })
        if (response.data.success) {
          await loadPrompts()
          Swal.fire({
            icon: 'success',
            title: '已設為預設',
            timer: 1500,
            showConfirmButton: false
          })
        }
      } catch (error) {
        console.error('設定預設失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '設定失敗',
          text: error.message
        })
      }
    }

    const savePrompt = async () => {
      if (!formData.value.name || !formData.value.content) {
        Swal.fire({
          icon: 'warning',
          title: '請填寫必填欄位',
          text: '名稱和內容為必填欄位'
        })
        return
      }

      try {
        let response
        if (isEditing.value) {
          response = await axios.put(
            `${API_URL}/api/prompts/${editingId.value}`,
            formData.value
          )
        } else {
          response = await axios.post(`${API_URL}/api/prompts`, formData.value)
        }

        if (response.data.success) {
          await loadPrompts()
          closeDialog()
          Swal.fire({
            icon: 'success',
            title: isEditing.value ? '更新成功' : '創建成功',
            timer: 1500,
            showConfirmButton: false
          })
        }
      } catch (error) {
        console.error('保存提示詞失敗:', error)
        Swal.fire({
          icon: 'error',
          title: '保存失敗',
          text: error.response?.data?.error || error.message
        })
      }
    }

    const closeDialog = () => {
      showCreateDialog.value = false
      showEditDialog.value = false
      isEditing.value = false
      editingId.value = null
      formData.value = {
        name: '',
        description: '',
        content: '',
        is_default: false
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      })
    }

    onMounted(() => {
      loadPrompts()
    })

    return {
      prompts,
      showCreateDialog,
      showEditDialog,
      isEditing,
      formData,
      editPrompt,
      deletePrompt,
      setAsDefault,
      savePrompt,
      closeDialog,
      formatDate
    }
  }
}
</script>

<style scoped>
.prompt-management {
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
  margin: 0;
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.btn-create {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-create:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.prompts-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 3rem;
  color: #94a3b8;
  font-size: 1.1rem;
}

.prompt-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
  transition: all 0.3s;
}

.prompt-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
  border-color: rgba(102, 126, 234, 0.3);
}

.prompt-card.is-default {
  border-color: rgba(251, 191, 36, 0.5);
  background: linear-gradient(135deg, rgba(254, 243, 199, 0.3), rgba(255, 255, 255, 0.95));
}

.prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.prompt-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.prompt-title h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: #1e293b;
}

.default-badge {
  padding: 0.25rem 0.75rem;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: white;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.prompt-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-edit,
.btn-delete {
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1rem;
}

.btn-edit:hover {
  background: #eff6ff;
  border-color: #3b82f6;
}

.btn-delete:hover {
  background: #fef2f2;
  border-color: #ef4444;
}

.prompt-description {
  color: #64748b;
  font-size: 0.9rem;
  margin-bottom: 1rem;
  font-style: italic;
}

.prompt-content {
  background: #f8fafc;
  padding: 1rem;
  border-radius: 8px;
  color: #334155;
  font-size: 0.9rem;
  line-height: 1.6;
  max-height: 150px;
  overflow-y: auto;
  margin-bottom: 1rem;
}

.prompt-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.prompt-date {
  color: #94a3b8;
  font-size: 0.85rem;
}

.btn-set-default {
  padding: 0.4rem 0.8rem;
  background: white;
  color: #667eea;
  border: 1px solid #667eea;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-set-default:hover {
  background: #667eea;
  color: white;
}

/* Dialog Styles */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 20px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e2e8f0;
}

.dialog-header h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
}

.btn-close {
  padding: 0.5rem;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #64748b;
  transition: color 0.2s;
}

.btn-close:hover {
  color: #1e293b;
}

.dialog-body {
  padding: 2rem;
  max-height: calc(90vh - 200px);
  overflow-y: auto;
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

.form-input,
.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 1rem;
  font-family: inherit;
  transition: all 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 150px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem 2rem;
  border-top: 1px solid #e2e8f0;
}

.btn-cancel,
.btn-save {
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: white;
  color: #64748b;
  border: 2px solid #e2e8f0;
}

.btn-cancel:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.btn-save {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-save:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}
</style>
