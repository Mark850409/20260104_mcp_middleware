# GUI Web 說明文件

## 概述

GUI Web 是基於 Vue.js 3 建立的管理介面,提供 MCP Server 管理與工具操作的視覺化介面。

## 技術規格

- **框架**: Vue.js 3.4.0
- **建置工具**: Vite 5.0.0
- **HTTP 客戶端**: Axios 1.6.0
- **端口**: 8080

## 檔案結構

```
gui/
├── Dockerfile          # Docker 映像配置
├── package.json       # npm 專案配置
├── vite.config.js     # Vite 配置
├── index.html         # HTML 模板
└── src/
    ├── main.js        # 應用進入點
    └── App.vue        # 主應用元件
```

## 功能模組

### 1. MCP Server 狀態區

顯示與管理 MCP Server 連線狀態。

**功能:**
- 顯示連線狀態 (已連線/未連線)
- 顯示 Server 位址與端口
- 連線/中斷連線按鈕
- 重新整理狀態按鈕

**狀態指示:**
- 🟢 綠色徽章: 已連線
- 🔴 紅色徽章: 未連線

### 2. MCP Tool 管理區

顯示與管理 MCP 工具清單。

**功能:**
- 顯示所有可用工具
- 工具名稱與描述
- 啟用/停用開關
- 參數 Schema 查看 (可展開)

**工具資訊:**
- 工具名稱
- 工具描述
- 參數定義 (JSON Schema)
- 必填參數標示

### 3. Tool 操作區

執行 MCP 工具的操作介面。

**功能:**
- 工具下拉選單
- 動態參數輸入欄位
- 執行按鈕
- 結果顯示區

**參數輸入:**
- 根據 Schema 動態生成輸入欄位
- 必填參數標示 (紅色星號)
- 參數類型驗證

**結果顯示:**
- 成功: 綠色背景
- 失敗: 紅色背景
- JSON 格式化顯示

## 元件結構

### App.vue

主應用元件,包含所有功能模組。

#### 資料狀態

```javascript
const mcpStatus = ref({
  connected: false,
  server_host: 'mcp-server',
  server_port: 8000
})
const tools = ref([])
const selectedTool = ref('')
const toolArguments = ref({})
const result = ref(null)
```

#### 計算屬性

- `enabledTools`: 已啟用的工具清單
- `selectedToolSchema`: 選中工具的參數 Schema

#### 方法

- `refreshStatus()`: 重新整理 MCP Server 狀態
- `connectMCP()`: 連線 MCP Server
- `disconnectMCP()`: 中斷連線
- `loadTools()`: 載入工具清單
- `invokeTool()`: 執行選中的工具

## 環境變數

| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `VITE_API_URL` | Backend API URL | http://localhost:5000 |

## 本地開發

### 安裝相依套件

```bash
cd gui
npm install
```

### 啟動開發伺服器

```bash
npm run dev
```

應用將在 http://localhost:8080 啟動。

### 建置生產版本

```bash
npm run build
```

建置結果將輸出到 `dist/` 目錄。

## Docker 部署

### 建置映像

```bash
docker build -t mcp-gui .
```

### 執行容器

```bash
docker run -p 8080:8080 \
  -e VITE_API_URL=http://localhost:5000 \
  mcp-gui
```

## 樣式設計

### 色彩配置

- **主色**: #667eea (紫色)
- **成功**: #10b981 (綠色)
- **錯誤**: #ef4444 (紅色)
- **警告**: #f59e0b (橙色)
- **中性**: #6b7280 (灰色)

### 設計特點

- 漸層背景
- 卡片式佈局
- 懸停效果
- 響應式設計
- 現代化 UI 元素

## 使用流程

### 執行工具的完整流程

1. **檢查連線狀態**
   - 確認 MCP Server 狀態為「已連線」
   - 如未連線,點擊「連線」按鈕

2. **選擇工具**
   - 在「Tool 操作區」的下拉選單中選擇工具
   - 系統會自動載入該工具的參數 Schema

3. **輸入參數**
   - 根據動態生成的輸入欄位填寫參數
   - 必填參數會標示紅色星號

4. **執行工具**
   - 點擊「🚀 執行 Tool」按鈕
   - 等待執行完成

5. **查看結果**
   - 結果會顯示在下方的結果區
   - 成功顯示綠色背景
   - 失敗顯示紅色背景

## 響應式設計

### 桌面版 (> 768px)
- 完整佈局
- 大字體
- 寬鬆間距

### 行動版 (≤ 768px)
- 縮小標題字體
- 緊湊間距
- 單欄佈局

## 除錯

### 瀏覽器開發者工具

1. 開啟開發者工具 (F12)
2. 查看 Console 標籤頁的錯誤訊息
3. 查看 Network 標籤頁的 API 請求

### 常見問題

**問題**: 無法連接 Backend API

**解決方案:**
1. 檢查 `VITE_API_URL` 環境變數
2. 確認 Backend 服務正在運行
3. 檢查 CORS 設定

**問題**: 工具清單為空

**解決方案:**
1. 確認 MCP Server 已連線
2. 檢查 Backend API `/api/mcp/tools` 端點
3. 查看瀏覽器 Console 錯誤訊息

## 擴充指南

### 新增功能模組

在 `App.vue` 的 `<template>` 中新增 section:

```vue
<section class="card">
  <h2>🎯 新功能</h2>
  <div class="content">
    <!-- 功能內容 -->
  </div>
</section>
```

### 新增 API 呼叫

在 `<script setup>` 中新增方法:

```javascript
const yourMethod = async () => {
  try {
    const response = await axios.get(`${API_URL}/api/your-endpoint`)
    // 處理回應
  } catch (error) {
    console.error('錯誤:', error)
  }
}
```

### 自訂樣式

在 `<style scoped>` 中新增 CSS:

```css
.your-class {
  /* 樣式定義 */
}
```

## 最佳實踐

1. **元件化**: 將複雜功能拆分為獨立元件
2. **狀態管理**: 使用 Vue 3 Composition API
3. **錯誤處理**: 適當處理 API 錯誤
4. **使用者體驗**: 提供載入狀態與錯誤提示
5. **程式碼品質**: 保持程式碼簡潔易讀

## 效能優化

1. **懶載入**: 使用動態 import 載入大型元件
2. **快取**: 適當快取 API 回應
3. **防抖**: 對頻繁操作使用 debounce
4. **虛擬滾動**: 處理大量資料時使用虛擬滾動
