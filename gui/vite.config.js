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
        // HMR 配置
        hmr: {
            overlay: true, // 顯示錯誤覆蓋層
            clientPort: 8080
        },
        // 監聽文件變化
        watch: {
            usePolling: true, // 在某些環境下需要輪詢
            interval: 100
        }
    },
    // 優化依賴預構建
    optimizeDeps: {
        include: ['vue', 'axios', 'sweetalert2', 'marked']
    }
})
