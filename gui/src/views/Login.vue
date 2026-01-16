<template>
  <div class="login-container">
    <div class="login-card">
      <!-- Logo 區域 -->
      <div class="logo-section">
        <i class="ri-rocket-2-fill logo-icon"></i>
        <h1 class="logo-text">MCP Platform</h1>
        <p class="subtitle">AI 驅動的智能管理平台</p>
      </div>

      <!-- 登入表單 -->
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">
            <i class="ri-user-line"></i>
            使用者名稱或 Email
          </label>
          <input
            id="username"
            v-model="formData.username"
            type="text"
            placeholder="請輸入使用者名稱或 Email"
            required
            autocomplete="username"
          />
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
              placeholder="請輸入密碼"
              required
              autocomplete="current-password"
            />
            <button
              type="button"
              class="toggle-password"
              @click="showPassword = !showPassword"
            >
              <i :class="showPassword ? 'ri-eye-off-line' : 'ri-eye-line'"></i>
            </button>
          </div>
        </div>

        <div class="form-options">
          <label class="checkbox-label">
            <input v-model="formData.remember" type="checkbox" />
            <span>記住我</span>
          </label>
        </div>

        <!-- 錯誤訊息 -->
        <div v-if="errorMessage" class="error-message">
          <i class="ri-error-warning-line"></i>
          {{ errorMessage }}
        </div>

        <!-- 登入按鈕 -->
        <button type="submit" class="btn-login" :disabled="loading">
          <span v-if="!loading">
            <i class="ri-login-box-line"></i>
            登入
          </span>
          <span v-else>
            <i class="ri-loader-4-line rotating"></i>
            登入中...
          </span>
        </button>

        <!-- 註冊連結 -->
        <div class="register-link">
          還沒有帳號?
          <router-link to="/register">立即註冊</router-link>
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const { login } = useAuth()
    
    const formData = ref({
      username: '',
      password: '',
      remember: false
    })
    
    const showPassword = ref(false)
    const loading = ref(false)
    const errorMessage = ref('')
    
    const handleLogin = async () => {
      try {
        loading.value = true
        errorMessage.value = ''
        
        await login(formData.value.username, formData.value.password, formData.value.remember)
        
        // 登入成功,跳轉到主頁
        router.push('/')
      } catch (error) {
        errorMessage.value = error.message || '登入失敗,請檢查您的帳號密碼'
      } finally {
        loading.value = false
      }
    }
    
    return {
      formData,
      showPassword,
      loading,
      errorMessage,
      handleLogin
    }
  }
}
</script>

<style scoped>
/* ============================================
   登入容器
   ============================================ */
.login-container {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: var(--spacing-4);
  overflow: hidden;
}

/* ============================================
   登入卡片
   ============================================ */
.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 440px;
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

/* Logo 區域 */
.logo-section {
  text-align: center;
  margin-bottom: var(--spacing-8);
}

.logo-icon {
  font-size: 4rem;
  color: #667eea;
  margin-bottom: var(--spacing-3);
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
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-slate-900);
  margin: 0 0 var(--spacing-2);
}

.subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-slate-600);
  margin: 0;
}

/* ============================================
   表單樣式
   ============================================ */
.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-5);
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

/* 密碼輸入框 */
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

.toggle-password i {
  font-size: 1.25rem;
}

/* 表單選項 */
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-sm);
  color: var(--color-slate-600);
  cursor: pointer;
  user-select: none;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #667eea;
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

.error-message i {
  font-size: 1.1rem;
  flex-shrink: 0;
}

/* 登入按鈕 */
.btn-login {
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

.btn-login:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
}

.btn-login:active:not(:disabled) {
  transform: translateY(0);
}

.btn-login:disabled {
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

/* 註冊連結 */
.register-link {
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--color-slate-600);
}

.register-link a {
  color: #667eea;
  font-weight: var(--font-weight-semibold);
  text-decoration: none;
  transition: all var(--transition-base);
}

.register-link a:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* ============================================
   背景裝飾
   ============================================ */
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
  animation-delay: 0s;
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

/* ============================================
   響應式設計
   ============================================ */
@media (max-width: 480px) {
  .login-card {
    padding: var(--spacing-6);
  }
  
  .logo-icon {
    font-size: 3rem;
  }
  
  .logo-text {
    font-size: var(--font-size-2xl);
  }
}
</style>
