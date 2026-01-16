import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [
        vue({
            // 啟用 Vue 3 的 HMR
            reactivityTransform: true
        })
    ],
    server: {
        host: '0.0.0.0',
        port: 8080,
        strictPort: false,
        // 允許的主機列表 (解決 Blocked request 錯誤)
        allowedHosts: ['zanehsu.myqnapcloud.com'],
        // HMR 配置
        hmr: {
            overlay: true // 顯示錯誤覆蓋層
        },
        // 監聽文件變化
        watch: {
            usePolling: true,
            interval: 1000 // 降低輪詢頻率 (每秒 1 次)
        }
    },
    // 優化依賴預構建
    optimizeDeps: {
        include: ['vue', 'axios', 'sweetalert2', 'marked']
    }
})
