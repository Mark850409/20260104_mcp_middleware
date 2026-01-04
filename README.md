# MCP Platform - Docker 化的 MCP 管理後台系統

一個基於 **Flask + Vue.js** 的 Docker 化 MCP (Model Context Protocol) 管理平台,提供完整的 MCP Server 管理、工具操作介面,以及整合多家 AI 供應商的 Chatbot 功能。

## 📋 系統架構

```
┌─────────────┐      HTTP      ┌──────────────┐    HTTP API    ┌─────────────┐
│             │ ◄────────────► │              │ ◄────────────► │             │
│  GUI (Vue)  │                │ Backend API  │                │ MCP Server  │
│   :8080     │                │  (Flask)     │                │  (Flask)    │
│             │                │   :5000      │                │   :8000     │
└─────────────┘                └──────┬───────┘                └─────────────┘
                                      │
                                      ▼
                               ┌─────────────┐
                               │   MySQL DB  │
                               │    :3306    │
                               └─────────────┘
```

### 元件說明

1. **mcp-server**: Flask HTTP API 提供 MCP 工具
   - 提供 `hello` 和 `get_time` 工具
   - RESTful API 介面

2. **backend**: Flask REST API
   - MCP Client (透過 HTTP 連接 MCP Server)
   - AI Chatbot API (支援 OpenAI, Google Gemini, Anthropic Claude)
   - 對話管理與訊息記錄

3. **gui**: Vue.js 前端管理介面
   - MCP Server 狀態監控與工具管理
   - AI Chatbot 聊天介面
   - 多頁面切換

4. **db**: MySQL 資料庫
   - 對話與訊息記錄
   - MCP 配置 (預留擴充)

## ✨ 核心功能

### MCP 工具管理
- MCP Server 狀態監控
- 工具列表查看與管理
- 工具參數動態輸入
- 工具執行與結果顯示

### AI Chatbot
- **多供應商支援**: OpenAI, Google Gemini, Anthropic Claude
- **MCP 工具整合**: 可選擇性啟用 MCP 工具調用
- **對話管理**: 建立、查看、切換多個對話
- **完整歷史**: 保存所有對話訊息與工具調用記錄

## 🚀 快速啟動

### 前置需求

- Docker
- Docker Compose

### 啟動步驟

1. **Clone 專案**
```bash
cd mcp-platform
```

2. **啟動所有服務**
```bash
docker-compose up -d
```

3. **檢查服務狀態**
```bash
docker-compose ps
```

4. **訪問管理介面**
開啟瀏覽器訪問: http://localhost:8080

### 停止服務

```bash
docker-compose down
```

### 查看日誌

```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f mcp-server
docker-compose logs -f backend
docker-compose logs -f gui
```

## 📖 使用說明

### 1. MCP Server 狀態管理

- **連線狀態**: 顯示與 MCP Server 的連線狀態
- **連線/中斷**: 手動控制連線
- **重新整理**: 更新狀態資訊

### 2. Tool 管理

- **工具清單**: 顯示所有可用的 MCP 工具
- **啟用/停用**: 使用開關控制工具啟用狀態
- **參數 Schema**: 查看工具的參數定義

### 3. Tool 操作

1. 從下拉選單選擇要執行的工具
2. 根據 Schema 填寫必要參數
3. 點擊「執行 Tool」按鈕
4. 查看執行結果 (JSON 格式)

### 預設工具

#### hello
問候工具,回傳問候訊息

**參數:**
- `name` (string, 必填): 要問候的名字

**範例:**
```json
{
  "name": "World"
}
```

**回傳:**
```
Hello, World!
```

#### get_time
時間工具,回傳當前 ISO 8601 格式時間

**參數:** 無

**回傳:**
```
2026-01-04T16:37:10+08:00
```

## 🔧 API 文件

### Backend API 端點

#### 健康檢查
```
GET /api/health
```

#### MCP Server 狀態
```
GET /api/mcp/status
```

#### 連線 MCP Server
```
POST /api/mcp/connect
```

#### 中斷連線
```
POST /api/mcp/disconnect
```

#### 取得工具清單
```
GET /api/mcp/tools
```

#### 執行工具
```
POST /api/mcp/invoke
Content-Type: application/json

{
  "tool_name": "hello",
  "arguments": {
    "name": "World"
  }
}
```

#### 取得工具資訊
```
GET /api/mcp/tools/{tool_name}
```

## 📁 專案結構

```
mcp-platform/
├── docker-compose.yml          # Docker Compose 配置
├── mcp-server/                 # MCP Server 服務
│   ├── Dockerfile
│   ├── server.py              # FastMCP 伺服器
│   └── requirements.txt
├── backend/                    # Backend API 服務
│   ├── Dockerfile
│   ├── app.py                 # Flask 應用
│   ├── services/
│   │   └── mcp_client.py      # MCP Client Service
│   └── requirements.txt
├── gui/                        # GUI Web 服務
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       └── App.vue            # Vue 主元件
└── README.md
```

## 🔨 開發指南

### 新增 MCP Tool

1. **編輯 mcp-server/server.py**

```python
@mcp.tool()
def your_tool_name(param1: str, param2: int) -> str:
    """
    工具描述
    
    Args:
        param1: 參數1說明
        param2: 參數2說明
    
    Returns:
        回傳值說明
    """
    # 實作邏輯
    return f"Result: {param1}, {param2}"
```

2. **更新 backend/services/mcp_client.py**

在 `list_tools()` 方法中新增工具定義:

```python
{
    "name": "your_tool_name",
    "description": "工具描述",
    "inputSchema": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "參數1說明"},
            "param2": {"type": "integer", "description": "參數2說明"}
        },
        "required": ["param1", "param2"]
    }
}
```

3. **重新啟動服務**

```bash
docker-compose restart mcp-server backend
```

### 本地開發

#### Backend 本地開發

```bash
cd backend
pip install -r requirements.txt
python app.py
```

#### GUI 本地開發

```bash
cd gui
npm install
npm run dev
```

## 🎯 擴充方向

### 1. 多 MCP Server 支援
- 支援連接多個 MCP Server
- Server 配置管理介面
- Server 切換功能

### 2. 工具執行歷史
- 記錄工具執行歷史
- 執行結果查詢
- 統計分析

### 3. 使用者認證
- 登入/登出功能
- 權限管理
- API Token 管理

### 4. 工具排程
- 定時執行工具
- Cron 表達式支援
- 執行結果通知

### 5. 資料庫整合
- 使用 MySQL 儲存配置
- Server 配置持久化
- 執行歷史記錄

## 🐛 故障排除

### 容器無法啟動

```bash
# 查看容器日誌
docker-compose logs [service-name]

# 重新建置映像
docker-compose build --no-cache

# 清理並重啟
docker-compose down -v
docker-compose up -d
```

### 無法連接 MCP Server

1. 檢查 mcp-server 容器是否正常運行
2. 檢查網路連線
3. 查看 backend 日誌

### GUI 無法載入

1. 檢查 backend API 是否正常
2. 確認環境變數 `VITE_API_URL` 設定正確
3. 清除瀏覽器快取

## 📝 技術規格

- **Python**: 3.10+
- **FastMCP**: 0.2.0
- **Flask**: 3.0.0
- **Vue.js**: 3.4.0
- **MySQL**: 8.0
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

## 📄 授權

MIT License

## 👥 貢獻

歡迎提交 Issue 和 Pull Request!

## 📧 聯絡

如有問題或建議,請開啟 Issue 討論。

---

**MCP Platform** - 讓 MCP 工具管理更簡單 🚀
