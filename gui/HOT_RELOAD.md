# Hot Reload 功能說明

## ✨ 已啟用功能

您的前端專案現在已經完整啟用 **Hot Module Replacement (HMR)** 功能!

## 🔧 配置詳情

### Vite 配置 (vite.config.js)

```javascript
{
  // Vue 3 HMR 支援
  plugins: [
    vue({
      reactivityTransform: true  // 啟用響應式轉換
    })
  ],
  
  // 開發伺服器設定
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: false,
    
    // HMR 配置
    hmr: {
      overlay: true,      // 顯示錯誤覆蓋層
      clientPort: 5173
    },
    
    // 文件監聽
    watch: {
      usePolling: true,   // 輪詢模式(適用於各種環境)
      interval: 100       // 檢查間隔 100ms
    }
  },
  
  // 依賴優化
  optimizeDeps: {
    include: ['vue', 'axios', 'sweetalert2', 'marked']
  }
}
```

## 🚀 使用方式

### 啟動開發伺服器

```bash
cd e:\Project\AI\MCP\20260104_mcp\mcp-platform\gui
npm run dev
```

伺服器將在 `http://localhost:5173` 啟動

### Hot Reload 效果

當您修改以下文件時,瀏覽器會**自動更新**,無需手動刷新:

- ✅ **Vue 組件** (`.vue` 文件)
  - Template 變更 → 即時更新
  - Script 變更 → 保持狀態更新
  - Style 變更 → 即時套用

- ✅ **CSS 文件** (`.css` 文件)
  - 樣式變更 → 即時套用,不刷新頁面

- ✅ **JavaScript 文件** (`.js` 文件)
  - 程式碼變更 → 熱更新

## 🎯 HMR 特色

### 1. 保持狀態
修改組件時,應用程式的狀態會被保留:
- 表單輸入內容不會丟失
- 當前頁面位置不變
- 對話框狀態保持

### 2. 錯誤提示
當程式碼有錯誤時,會在瀏覽器上顯示錯誤覆蓋層,方便除錯

### 3. 快速反饋
- 修改後 **100ms** 內檢測到變更
- **毫秒級**的更新速度
- 無需等待完整重新載入

## 📝 最佳實踐

### 1. 開發時保持 Dev Server 運行
```bash
npm run dev
```

### 2. 在瀏覽器中打開
```
http://localhost:5173
```

### 3. 編輯文件
- 修改 `.vue` 組件
- 修改 `.css` 樣式
- 修改 `.js` 邏輯

### 4. 查看即時更新
瀏覽器會自動更新,無需手動刷新!

## 🔍 除錯技巧

### 如果 HMR 沒有作用:

1. **檢查終端機輸出**
   - 查看是否有錯誤訊息
   - 確認文件變更被偵測到

2. **檢查瀏覽器控制台**
   - 查看是否有 WebSocket 連接錯誤
   - 確認 HMR 連接狀態

3. **手動刷新**
   - 按 `Ctrl + R` 或 `F5` 刷新頁面
   - 清除快取: `Ctrl + Shift + R`

4. **重啟開發伺服器**
   ```bash
   # 停止伺服器 (Ctrl + C)
   # 重新啟動
   npm run dev
   ```

## 🎨 支援的文件類型

| 文件類型 | HMR 支援 | 說明 |
|---------|---------|------|
| `.vue` | ✅ 完整支援 | 組件熱重載,保持狀態 |
| `.css` | ✅ 完整支援 | 樣式即時套用 |
| `.js` | ✅ 完整支援 | 模組熱更新 |
| `.html` | ⚠️ 需刷新 | 修改 index.html 需手動刷新 |

## 💡 提示

- **開發時**: 使用 `npm run dev` 享受 HMR
- **生產環境**: 使用 `npm run build` 建立優化的生產版本
- **預覽**: 使用 `npm run preview` 預覽生產版本

## 🎉 享受開發!

現在您可以享受流暢的開發體驗,修改程式碼後立即看到效果,大幅提升開發效率!
