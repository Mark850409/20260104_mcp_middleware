<template>
  <div class="register-container">
    <div class="register-card">
      <!-- Logo 區域 -->
      <div class="logo-section">
        <i class="ri-rocket-2-fill logo-icon"></i>
        <h1 class="logo-text">建立帳號</h1>
        <p class="subtitle">加入 MCP Platform 開始您的 AI 之旅</p>
      </div>

      <!-- 註冊表單 -->
      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group">
          <label for="username">
            <i class="ri-user-line"></i>
            使用者名稱
          </label>
          <input
            id="username"
            v-model="formData.username"
            type="text"
            placeholder="至少 3 個字元"
            required
            autocomplete="username"
          />
          <span v-if="errors.username" class="field-error">{{ errors.username }}</span>
        </div>

        <div class="form-group">
          <label for="email">
            <i class="ri-mail-line"></i>
            Email
          </label>
          <input
            id="email"
            v-model="formData.email"
            type="email"
            placeholder="your@email.com"
            required
            autocomplete="email"
          />
          <span v-if="errors.email" class="field-error">{{ errors.email }}</span>
        </div>

        <div class="form-group">
          <label for="password">
            <i class="ri-lock-line"></i>
            密碼
          </label>
          <div class="password-input">
            <input
              id="password"
              v-model="formData.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="至少 8 個字元"
              required
              autocomplete="new-password"
            />
            <button
              type="button"
              class="toggle-password"
              @click="showPassword = !showPassword"
            >
              <i :class="showPassword ? 'ri-eye-off-line' : 'ri-eye-line'"></i>
            </button>
          </div>
          <div class="password-strength">
            <div class="strength-bar" :class="passwordStrength.class">
              <div class="strength-fill" :style="{ width: passwordStrength.width }"></div>
            </div>
            <span class="strength-text">{{ passwordStrength.text }}</span>
          </div>
        </div>

        <div class="form-group">
          <label for="confirmPassword">
            <i class="ri-lock-line"></i>
            確認密碼
          </label>
          <div class="password-input">
            <input
              id="confirmPassword"
              v-model="formData.confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              placeholder="再次輸入密碼"
              required
              autocomplete="new-password"
            />
            <button
              type="button"
              class="toggle-password"
              @click="showConfirmPassword = !showConfirmPassword"
            >
              <i :class="showConfirmPassword ? 'ri-eye-off-line' : 'ri-eye-line'"></i>
            </button>
          </div>
          <span v-if="errors.confirmPassword" class="field-error">{{ errors.confirmPassword }}</span>
        </div>

        <!-- 錯誤訊息 -->
        <div v-if="errorMessage" class="error-message">
          <i class="ri-error-warning-line"></i>
          {{ errorMessage }}
        </div>

        <!-- 成功訊息 -->
        <div v-if="successMessage" class="success-message">
          <i class="ri-checkbox-circle-line"></i>
          {{ successMessage }}
        </div>

        <!-- 註冊按鈕 -->
        <button type="submit" class="btn-register" :disabled="loading">
          <span v-if="!loading">
            <i class="ri-user-add-line"></i>
            註冊
          </span>
          <span v-else>
            <i class="ri-loader-4-line rotating"></i>
            註冊中...
          </span>
        </button>

        <!-- 登入連結 -->
        <div class="login-link">
          已經有帳號?
          <router-link to="/login">立即登入</router-link>
        </div>
      </form>
    </div>

    <!-- 背景裝飾 -->
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import request from '../utils/request'

export default {
  name: 'Register',
  setup() {
    const router = useRouter()
    
    const formData = ref({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })
    
    const showPassword = ref(false)
    const showConfirmPassword = ref(false)
    const loading = ref(false)
    const errorMessage = ref('')
    const successMessage = ref('')
    const errors = ref({})
    
    // 密碼強度計算
    const passwordStrength = computed(() => {
      const password = formData.value.password
      if (!password) {
        return { class: '', width: '0%', text: '' }
      }
      
      let strength = 0
      if (password.length >= 8) strength++
      if (password.length >= 12) strength++
      if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++
      if (/\d/.test(password)) strength++
      if (/[^a-zA-Z0-9]/.test(password)) strength++
      
      if (strength <= 1) {
        return { class: 'weak', width: '25%', text: '弱' }
      } else if (strength <= 3) {
        return { class: 'medium', width: '50%', text: '中等' }
      } else if (strength <= 4) {
        return { class: 'strong', width: '75%', text: '強' }
      } else {
        return { class: 'very-strong', width: '100%', text: '非常強' }
      }
    })
    
    // 表單驗證
    const validateForm = () => {
      errors.value = {}
      
      if (formData.value.username.length < 3) {
        errors.value.username = '使用者名稱至少需要 3 個字元'
      }
      
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.value.email)) {
        errors.value.email = 'Email 格式不正確'
      }
      
      if (formData.value.password.length < 8) {
        errors.value.password = '密碼至少需要 8 個字元'
      }
      
      if (formData.value.password !== formData.value.confirmPassword) {
        errors.value.confirmPassword = '兩次輸入的密碼不一致'
      }
      
      return Object.keys(errors.value).length === 0
    }
    
    const handleRegister = async () => {
      try {
        loading.value = true
        errorMessage.value = ''
        successMessage.value = ''
        
        // 驗證表單
        if (!validateForm()) {
          return
        }
        
        const response = await request.post('/api/auth/register', {
          username: formData.value.username,
          email: formData.value.email,
          password: formData.value.password
        })
        
        if (response.data.success) {
          successMessage.value = '註冊成功!即將跳轉到登入頁面...'
          
          // 3 秒後跳轉到登入頁
          setTimeout(() => {
            router.push('/login')
          }, 3000)
        } else {
          errorMessage.value = response.data.error || '註冊失敗'
        }
      } catch (error) {
        errorMessage.value = error.response?.data?.error || '註冊失敗,請稍後再試'
      } finally {
        loading.value = false
      }
    }
    
    return {
      formData,
      showPassword,
      showConfirmPassword,
      loading,
      errorMessage,
      successMessage,
      errors,
      passwordStrength,
      handleRegister
    }
  }
}
</script>

<style scoped>
/* 繼承登入頁面的樣式 */
.register-container {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: var(--spacing-4);
  overflow: hidden;
}

.register-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 480px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: var(--radius-xl);
  padding: var(--spacing-8);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.logo-section {
  text-align: center;
  margin-bottom: var(--spacing-6);
}

.logo-icon {
  font-size: 3.5rem;
  color: #667eea;
  margin-bottom: var(--spacing-2);
  display: inline-block;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.logo-text {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-slate-900);
  margin: 0 0 var(--spacing-2);
}

.subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-slate-600);
  margin: 0;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.form-group label {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-slate-700);
}

.form-group label i {
  font-size: 1.1rem;
  color: #667eea;
}

.form-group input[type="text"],
.form-group input[type="email"],
.form-group input[type="password"] {
  width: 100%;
  padding: var(--spacing-3) var(--spacing-4);
  font-size: var(--font-size-base);
  border: 2px solid var(--color-slate-200);
  border-radius: var(--radius-base);
  transition: all var(--transition-base);
  background: white;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.password-input {
  position: relative;
}

.password-input input {
  padding-right: 45px;
}

.toggle-password {
  position: absolute;
  right: var(--spacing-3);
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--color-slate-500);
  cursor: pointer;
  padding: var(--spacing-2);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-base);
  transition: all var(--transition-base);
}

.toggle-password:hover {
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

/* 密碼強度指示器 */
.password-strength {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.strength-bar {
  flex: 1;
  height: 4px;
  background: var(--color-slate-200);
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  transition: all var(--transition-base);
}

.strength-bar.weak .strength-fill {
  background: #ef4444;
}

.strength-bar.medium .strength-fill {
  background: #f59e0b;
}

.strength-bar.strong .strength-fill {
  background: #10b981;
}

.strength-bar.very-strong .strength-fill {
  background: #059669;
}

.strength-text {
  font-size: var(--font-size-xs);
  color: var(--color-slate-600);
  min-width: 60px;
}

/* 欄位錯誤訊息 */
.field-error {
  font-size: var(--font-size-xs);
  color: #ef4444;
  margin-top: -4px;
}

/* 錯誤訊息 */
.error-message {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  background: #fee;
  border: 1px solid #fcc;
  border-radius: var(--radius-base);
  color: #c33;
  font-size: var(--font-size-sm);
}

/* 成功訊息 */
.success-message {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  border-radius: var(--radius-base);
  color: #065f46;
  font-size: var(--font-size-sm);
}

.btn-register {
  width: 100%;
  padding: var(--spacing-4);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: white;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: var(--radius-base);
  cursor: pointer;
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
}

.btn-register:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
}

.btn-register:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.login-link {
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--color-slate-600);
}

.login-link a {
  color: #667eea;
  font-weight: var(--font-weight-semibold);
  text-decoration: none;
  transition: all var(--transition-base);
}

.login-link a:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* 背景裝飾 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float-circle 20s ease-in-out infinite;
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  left: -100px;
}

.circle-2 {
  width: 200px;
  height: 200px;
  bottom: -50px;
  right: -50px;
  animation-delay: 5s;
}

.circle-3 {
  width: 150px;
  height: 150px;
  top: 50%;
  right: 10%;
  animation-delay: 10s;
}

@keyframes float-circle {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -30px) scale(1.1);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.9);
  }
}
</style>
