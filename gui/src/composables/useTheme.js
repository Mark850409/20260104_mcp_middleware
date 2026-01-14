import { ref, watch } from 'vue'

const theme = ref('dark')
const isInitialized = ref(false)

export function useTheme() {
    // 初始化主題
    const initTheme = () => {
        if (isInitialized.value) return

        const savedTheme = localStorage.getItem('theme') || 'dark'
        setTheme(savedTheme)
        isInitialized.value = true
    }

    // 設定主題
    const setTheme = (newTheme) => {
        const themeValue = newTheme.toLowerCase()
        theme.value = themeValue
        document.documentElement.setAttribute('data-theme', themeValue)
        localStorage.setItem('theme', themeValue)
    }

    // 切換主題
    const toggleTheme = () => {
        const newTheme = theme.value === 'dark' ? 'light' : 'dark'
        setTheme(newTheme)
    }

    // 取得當前主題
    const getCurrentTheme = () => {
        return theme.value
    }

    // 檢查是否為深色主題
    const isDark = () => {
        return theme.value === 'dark'
    }

    return {
        theme,
        initTheme,
        setTheme,
        toggleTheme,
        getCurrentTheme,
        isDark
    }
}
