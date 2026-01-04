# AI Chatbot 功能使用指南

## 功能概述

AI Chatbot 是 MCP 管理平台的新增功能,提供與多家 AI 供應商模型的對話介面,並可選擇性整合 MCP 工具。

## 核心特性

### 1. 多供應商支援
- **OpenAI**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **Google**: Gemini Pro, Gemini Pro Vision
- **Anthropic**: Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku

### 2. MCP 工具整合
- 可選擇是否啟用 MCP 工具
- 啟用時:AI 可自動調用 MCP 工具並整合結果
- 未啟用時:AI 使用預設知識回答

### 3. 對話管理
- 建立多個獨立對話
- 保存完整對話歷史
- 切換不同對話

## 快速開始

### 1. 設定 API Keys

複製 `.env.example` 為 `.env` 並填入您的 API Keys:

```bash
cp .env.example .env
```

編輯 `.env` 檔案:
```env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. 初始化資料庫

```bash
docker-compose exec backend python init_db.py
```

### 3. 啟動服務

```bash
docker-compose up -d
```

### 4. 訪問 Chatbot

開啟瀏覽器訪問 http://localhost:8080,點擊「💬 AI Chatbot」標籤。

## 使用流程

### 建立新對話

1. 點擊左側「➕ 新對話」按鈕
2. 系統會使用當前選擇的模型與 MCP 設定建立對話

### 選擇模型

在頂部工具列:
1. 選擇供應商 (OpenAI / Google / Anthropic)
2. 選擇具體模型
3. 切換 MCP 工具開關

### 發送訊息

1. 在底部輸入框輸入訊息
2. 按 Enter 發送 (Shift+Enter 換行)
3. 等待 AI 回應

### MCP 工具調用

當啟用 MCP 工具時:
1. AI 會自動判斷是否需要使用工具
2. 工具調用過程會顯示在訊息中
3. 最終回應會整合工具結果

## 範例對話

### 範例 1: 不使用 MCP 工具

**設定**: OpenAI GPT-4, MCP 關閉

**使用者**: 你好,請介紹一下自己

**AI**: 您好!我是 GPT-4,由 OpenAI 開發的大型語言模型...

### 範例 2: 使用 MCP 工具

**設定**: OpenAI GPT-4, MCP 開啟

**使用者**: 現在幾點?

**AI**: 
```
🔧 工具調用: get_time
```
根據 MCP 工具回傳,現在時間是 2026-01-04T17:16:54+08:00

## API 端點

### 建立對話
```http
POST /api/chat/conversations
Content-Type: application/json

{
  "title": "新對話",
  "model_provider": "openai",
  "model_name": "gpt-4",
  "mcp_enabled": true
}
```

### 發送訊息
```http
POST /api/chat/conversations/{id}/messages
Content-Type: application/json

{
  "content": "你好"
}
```

### 取得對話列表
```http
GET /api/chat/conversations
```

### 取得對話詳情
```http
GET /api/chat/conversations/{id}
```

## 資料庫結構

### conversations 表
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INT | 主鍵 |
| title | VARCHAR(255) | 對話標題 |
| model_provider | VARCHAR(50) | 供應商 |
| model_name | VARCHAR(100) | 模型名稱 |
| mcp_enabled | BOOLEAN | 是否啟用 MCP |
| created_at | TIMESTAMP | 建立時間 |
| updated_at | TIMESTAMP | 更新時間 |

### messages 表
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INT | 主鍵 |
| conversation_id | INT | 對話 ID |
| role | VARCHAR(20) | user/assistant/tool |
| content | TEXT | 訊息內容 |
| tool_calls | JSON | 工具調用記錄 |
| created_at | TIMESTAMP | 建立時間 |

## 故障排除

### 問題: API Key 錯誤

**症狀**: 發送訊息時出現 API Key 相關錯誤

**解決方案**:
1. 確認 `.env` 檔案中的 API Key 正確
2. 重啟 backend 容器: `docker-compose restart backend`

### 問題: 資料庫連線失敗

**症狀**: 建立對話時出現資料庫錯誤

**解決方案**:
1. 確認資料庫已初始化: `docker-compose exec backend python init_db.py`
2. 檢查資料庫容器狀態: `docker-compose ps db`

### 問題: MCP 工具未調用

**症狀**: 啟用 MCP 但工具沒有被調用

**解決方案**:
1. 確認 MCP Server 已連線
2. 確認對話的 `mcp_enabled` 為 true
3. 嘗試更明確的提示詞,例如「請使用工具查詢時間」

## 擴充指南

### 新增 AI 供應商

1. 在 `backend/services/ai_client.py` 新增 Client 類別
2. 在 `AIClientFactory` 中註冊
3. 在 `backend/routes/chat.py` 的 `list_models()` 中新增模型列表

### 新增 MCP 工具

1. 在 `mcp-server/server.py` 中新增工具函式
2. 在 `TOOLS` 字典中註冊工具
3. 重啟 MCP Server

## 最佳實踐

1. **API Key 安全**: 不要將 API Keys 提交到版本控制
2. **對話管理**: 定期清理舊對話以節省資料庫空間
3. **MCP 工具**: 只在需要時啟用 MCP,以節省 API 成本
4. **模型選擇**: 根據任務複雜度選擇適當的模型

## 已知限制

1. **同步處理**: 目前為同步處理,長時間工具調用會阻塞
2. **無串流**: 不支援串流回應
3. **單一工具**: 一次對話只能調用一個工具

## 未來規劃

- [ ] 支援串流回應
- [ ] 支援多輪工具調用
- [ ] 支援檔案上傳
- [ ] 支援對話匯出
- [ ] 支援對話分享
