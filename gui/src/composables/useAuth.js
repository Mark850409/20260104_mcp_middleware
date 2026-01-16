/**
 * 認證 Composable
 * 提供登入、登出、使用者資訊管理、權限檢查等功能
 */
import { ref, computed } from 'vue'
import axios from 'axios'

// API 基礎 URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

// 使用者狀態
const user = ref(null)
const token = ref(localStorage.getItem('auth_token') || '')
const permissions = ref({
    pages: [],
    functions: []
})

// Session 計時狀態
const SESSION_TIMEOUT = 30 * 60 // 30 分鐘 (秒)
const sessionRemainingTime = ref(0)
let sessionTimer = null

export function useAuth() {
    // 是否已登入
    const isAuthenticated = computed(() => !!token.value && !!user.value)

    /**
     * 啟動 Session 計時器
     */
    const startSessionTimer = () => {
        if (sessionTimer) clearInterval(sessionTimer)

        const updateTimer = () => {
            const startTime = parseInt(localStorage.getItem('session_start_time'))
            if (!startTime) {
                sessionRemainingTime.value = 0
                return
            }

            const elapsed = Math.floor((Date.now() - startTime) / 1000)
            const remaining = Math.max(0, SESSION_TIMEOUT - elapsed)
            sessionRemainingTime.value = remaining

            // 如果時間到且不是超級管理員,強制登出
            if (remaining <= 0 && isAuthenticated.value) {
                if (!hasRole('超級管理員')) {
                    console.log('Session 逾時,自動登出')
                    logout()
                }
            }
        }

        updateTimer()
        sessionTimer = setInterval(updateTimer, 1000)
    }

    /**
     * 登入
     */
    const login = async (username, password, remember = false) => {
        try {
            const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
                username,
                password
            })

            if (response.data.success) {
                const { token: authToken, user: userData, permissions: userPermissions } = response.data.data

                // 儲存 Token
                token.value = authToken
                if (remember) {
                    localStorage.setItem('auth_token', authToken)
                } else {
                    sessionStorage.setItem('auth_token', authToken)
                }

                // 儲存 Session 開始時間
                localStorage.setItem('session_start_time', Date.now().toString())

                // 儲存使用者資訊
                user.value = userData
                permissions.value = userPermissions

                // 啟動計時器
                startSessionTimer()

                return userData
            } else {
                throw new Error(response.data.error || '登入失敗')
            }
        } catch (error) {
            console.error('登入錯誤:', error)
            throw error.response?.data || error
        }
    }

    /**
     * 登出
     */
    const logout = async () => {
        try {
            if (token.value) {
                await axios.post(`${API_BASE_URL}/api/auth/logout`, {}, {
                    headers: {
                        Authorization: `Bearer ${token.value}`
                    }
                })
            }
        } catch (error) {
            console.error('登出錯誤:', error)
        } finally {
            // 清除計時器
            if (sessionTimer) {
                clearInterval(sessionTimer)
                sessionTimer = null
            }
            // 清除本地資料
            token.value = ''
            user.value = null
            permissions.value = { pages: [], functions: [] }
            sessionRemainingTime.value = 0
            localStorage.removeItem('auth_token')
            localStorage.removeItem('session_start_time')
            sessionStorage.removeItem('auth_token')

            // 如果在頁面上,導向登入頁
            if (window.location.pathname !== '/login') {
                window.location.href = '/login'
            }
        }
    }

    /**
     * 取得當前使用者資訊
     */
    const fetchCurrentUser = async () => {
        try {
            const authToken = token.value || localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')

            if (!authToken) {
                return null
            }

            const response = await axios.get(`${API_BASE_URL}/api/auth/me`, {
                headers: {
                    Authorization: `Bearer ${authToken}`
                }
            })

            if (response.data.success) {
                token.value = authToken
                const userData = response.data.data.user
                // 從角色物件陣列中提取名稱字串
                const roles = response.data.data.roles.map(r => typeof r === 'string' ? r : r.name)
                userData.roles = roles
                user.value = userData
                permissions.value = response.data.data.permissions

                // 恢復計時器
                startSessionTimer()

                return userData
            }
        } catch (error) {
            console.error('取得使用者資訊錯誤:', error)
            // Token 無效,清除登入狀態
            await logout()
            return null
        }
    }

    /**
     * 檢查是否有特定頁面權限
     */
    const hasPagePermission = (pageCode) => {
        if (hasRole('超級管理員')) return true
        return permissions.value.pages.some(p => p.code === pageCode)
    }

    /**
     * 檢查是否有特定功能權限
     */
    const hasFunctionPermission = (functionCode) => {
        if (hasRole('超級管理員')) return true
        if (!permissions.value || !permissions.value.functions) return false
        return permissions.value.functions.some(f => f.code === functionCode)
    }

    /**
     * 檢查是否有特定角色
     */
    const hasRole = (roleName) => {
        if (!user.value || !user.value.roles) return false
        return user.value.roles.some(r => {
            if (typeof r === 'string') return r === roleName
            return r.name === roleName
        })
    }

    /**
     * 更新個人資料
     */
    const updateProfile = async (email) => {
        try {
            const response = await axios.put(
                `${API_BASE_URL}/api/auth/profile`,
                { email },
                {
                    headers: {
                        Authorization: `Bearer ${token.value}`
                    }
                }
            )

            if (response.data.success) {
                // 重新取得使用者資訊
                await fetchCurrentUser()
                return true
            }
            return false
        } catch (error) {
            console.error('更新個人資料錯誤:', error)
            throw error.response?.data || error
        }
    }

    /**
     * 修改密碼
     */
    const changePassword = async (oldPassword, newPassword) => {
        try {
            const response = await axios.put(
                `${API_BASE_URL}/api/auth/password`,
                {
                    old_password: oldPassword,
                    new_password: newPassword
                },
                {
                    headers: {
                        Authorization: `Bearer ${token.value}`
                    }
                }
            )

            return response.data.success
        } catch (error) {
            console.error('修改密碼錯誤:', error)
            throw error.response?.data || error
        }
    }

    return {
        // 狀態
        user,
        token,
        permissions,
        isAuthenticated,
        sessionRemainingTime,

        // 方法
        login,
        logout,
        fetchCurrentUser,
        hasPagePermission,
        hasFunctionPermission,
        hasRole,
        updateProfile,
        changePassword
    }
}
