/**
 * HTTP 請求工具
 * 基於 Axios,自動附加 JWT Token 並處理認證錯誤
 */
import axios from 'axios'
import { useAuth } from '../composables/useAuth'

// API 基礎 URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

// 建立 Axios 實例
const request = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
})

// 請求攔截器 - 自動附加 Token
request.interceptors.request.use(
    (config) => {
        // 從 localStorage 或 sessionStorage 取得 Token
        const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')

        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }

        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// 回應攔截器 - 處理錯誤
request.interceptors.response.use(
    (response) => {
        return response
    },
    async (error) => {
        const { response } = error

        // 401 未授權 - Token 無效或過期
        if (response && response.status === 401) {
            const { logout } = useAuth()

            // 清除登入狀態
            await logout()

            // 重導向到登入頁
            if (window.location.pathname !== '/login') {
                window.location.href = '/login'
            }
        }

        // 403 禁止訪問 - 沒有權限
        if (response && response.status === 403) {
            console.error('沒有權限執行此操作')
        }

        return Promise.reject(error)
    }
)

export default request
