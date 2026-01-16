# MCP Platform - 企業級 MCP 管理平台

一個基於 **Flask + Vue.js** 的 Docker 化 MCP (Model Context Protocol) 管理平台,提供完整的 MCP Server 管理、多 Provider 支援、RAG 知識庫、LINE Bot 整合,以及整合多家 AI 供應商的 Chatbot 功能。

## 📋 系統架構

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue.js)                        │
│                          Port: 8082                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐│
│  │ Chatbot  │ │   MCP    │ │   RAG    │ │   LINE   │ │Prompt ││
│  │          │ │  Manage  │ │    KB    │ │   Bot    │ │ Mgmt  ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────┘│
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP API
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend API (Flask)                         │
│                          Port: 5000                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐│
│  │   Chat   │ │   MCP    │ │   RAG    │ │   LINE   │ │Prompt ││
│  │  Routes  │ │  Routes  │ │  Routes  │ │  Routes  │ │Routes ││
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬───┘│
│       │            │            │            │            │    │
│  ┌────▼─────┐ ┌────▼─────┐ ┌────▼─────┐ ┌────▼─────┐ ┌───▼───┐│
│  │    AI    │ │   MCP    │ │   RAG    │ │   LINE   │ │Prompt ││
│  │  Client  │ │  Client  │ │  Service │ │  Client  │ │  DB   ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────┘│
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MCP Server (SSE/HTTP)                         │
│                          Port: 8000                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Provider Manager                       │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │  │
│  │  │ Python  │ │ Node.js │ │ Docker  │ │   SSE   │       │  │
│  │  │Provider │ │Provider │ │Provider │ │Provider │       │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Plugin Loader                          │  │
│  │  (動態載入 MCP Tools: weather_mcp_tool.py 等)            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MySQL Database                             │
│                          Port: 3307                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐│
│  │Conversa- │ │Messages  │ │   RAG    │ │   LINE   │ │Prompts││
│  │  tions   │ │          │ │   KBs    │ │  Config  │ │       ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────┘│
└─────────────────────────────────────────────────────────────────┘
```

## ✨ 核心功能

### 1. 認證與權限管理 (RBAC/Bypass)
- **多角色權限**: 基於角色的存取控制 (RBAC)，支援頁面級與功能級權限。
- **超級管理員 Bypass**: 超級管理員擁有所有權限規避邏輯，確保管理無阻。
- **Session 逾時管理**: 
    - 一般使用者支援 30 分鐘登入超時機制。
    - 前端即時倒數計時器（5 分鐘警告閃爍提醒）。
    - 管理員帳號永久在線，不執行逾時登出。

### 2. 多 Provider MCP Server 管理
- **Python Provider**: 執行本地 Python MCP 工具
- **Node.js Provider**: 執行 Node.js/NPM MCP 工具
- **Docker Provider**: 在隔離容器中執行 MCP 工具
- **SSE Provider**: 連接遠端 SSE MCP Server
- **動態配置**: 透過 GUI 新增、編輯、刪除 MCP Server
- **健康檢查**: 即時監控 Server 狀態
- **工具管理**: 查看、測試、啟用/停用 MCP 工具

### 3. AI Chatbot
- **多供應商支援**: OpenAI, Google Gemini, Anthropic Claude
- **MCP 工具整合**: 可選擇性啟用多個 MCP 工具調用
- **對話管理**: 建立、查看、切換、刪除多個對話
- **完整歷史**: 保存所有對話訊息與工具調用記錄
- **串流回應**: 支援 AI 回應串流顯示
- **工具調用追蹤**: 顯示工具調用過程與結果

### 4. RAG 知識庫系統
- **知識庫管理**: 建立、編輯、刪除知識庫
- **檔案上傳**: 支援 TXT, PDF, DOCX, MD 等格式
- **向量索引**: 自動建立向量索引
- **語意搜尋**: 基於向量相似度的語意檢索
- **多 Provider 支援**: OpenAI, Google, Anthropic Embeddings
- **進階索引**: 支援 FAISS, Annoy 等索引類型
- **Chatbot 整合**: 在對話中啟用知識庫增強回應

### 5. LINE Bot 整合
- **Webhook 處理**: 接收 LINE 訊息並回應
- **多 Bot 管理**: 支援多個 LINE Bot 配置
- **MCP 工具調用**: LINE Bot 可使用 MCP 工具
- **知識庫綁定**: 為 LINE Bot 綁定特定知識庫
- **對話同步**: LINE 對話與平台對話同步
- **Prompt 自訂**: 為每個 Bot 設定系統 Prompt

### 6. Prompt 管理
- **Prompt 庫**: 建立、編輯、刪除 Prompt 模板
- **分類管理**: 依類別組織 Prompt
- **快速套用**: 在 Chatbot 中快速套用 Prompt
- **變數支援**: 支援 Prompt 變數替換

## 🚀 快速啟動

### 前置需求

- Docker
- Docker Compose
- (選用) OpenAI/Google/Anthropic API Key
- (選用) LINE Messaging API 憑證

### 啟動步驟

1. **Clone 專案**
```bash
cd mcp-platform
```

2. **設定環境變數**
```bash
cp .env.example .env
# 編輯 .env 檔案,填入 API Keys
```

3. **啟動所有服務**
```bash
docker-compose up -d
```

4. **檢查服務狀態**
```bash
docker-compose ps
```

5. **訪問管理介面**
開啟瀏覽器訪問: http://localhost:8082

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

### 1. MCP Server 管理

#### 新增 MCP Server
1. 進入「MCP 管理」頁面
2. 點擊「新增 Server」
3. 選擇 Provider 類型 (Python/Node.js/Docker/SSE)
4. 填寫配置資訊:
   - **Python**: 提供 Python 檔案路徑
   - **Node.js**: 提供 Node.js 執行檔路徑和參數
   - **Docker**: 提供 Docker 映像名稱和啟動命令
   - **SSE**: 提供遠端 SSE Server URL
5. 儲存並啟動 Server

#### 測試 MCP 工具
1. 選擇已啟動的 Server
2. 點擊「測試」按鈕
3. 查看工具列表和健康狀態

#### 在 Chatbot 中使用
1. 進入「Chatbot」頁面
2. 點擊「+」按鈕選擇 MCP 工具
3. 在對話中 AI 會自動調用選定的工具

### 2. RAG 知識庫

#### 建立知識庫
1. 進入「知識庫管理」頁面
2. 點擊「新增知識庫」
3. 輸入名稱和描述
4. 選擇 Embedding Provider 和索引類型
5. 儲存知識庫

#### 上傳檔案
1. 選擇知識庫
2. 點擊「上傳檔案」
3. 選擇檔案 (支援 TXT, PDF, DOCX, MD)
4. 系統自動處理並建立索引

#### 在 Chatbot 中使用
1. 進入「Chatbot」頁面
2. 選擇知識庫
3. AI 會基於知識庫內容增強回應

### 3. LINE Bot

#### 設定 LINE Bot
1. 進入「LINE Bot 管理」頁面
2. 點擊「新增 Bot」
3. 填寫 LINE Channel 資訊
4. 選擇 AI Provider 和模型
5. (選用) 綁定知識庫
6. (選用) 設定系統 Prompt
7. 儲存並啟用

#### 設定 Webhook
1. 複製平台提供的 Webhook URL
2. 在 LINE Developers Console 設定 Webhook URL
3. 啟用 Webhook

### 4. Prompt 管理

#### 建立 Prompt
1. 進入「Prompt 管理」頁面
2. 點擊「新增 Prompt」
3. 輸入名稱、類別、內容
4. 儲存 Prompt

#### 使用 Prompt
1. 在 Chatbot 中點擊 Prompt 選擇器
2. 選擇要套用的 Prompt
3. Prompt 會自動填入對話框

## 🔧 API 文件

### Backend API 端點

#### 健康檢查
```
GET /api/health
```

#### Chat API
```
POST /api/chat                    # 建立新對話
GET /api/chat                     # 取得對話列表
GET /api/chat/{conversation_id}   # 取得對話訊息
POST /api/chat/message            # 發送訊息
DELETE /api/chat/{conversation_id} # 刪除對話
```

#### MCP API
```
GET /api/mcp/servers              # 取得 Server 列表
POST /api/mcp/servers             # 新增 Server
PUT /api/mcp/servers/{name}       # 更新 Server
DELETE /api/mcp/servers/{name}    # 刪除 Server
POST /api/mcp/servers/{name}/test # 測試 Server
POST /api/mcp/servers/{name}/toggle # 啟用/停用 Server
GET /api/mcp/tools                # 取得工具列表
```

#### RAG API
```
GET /api/rag/kb                   # 取得知識庫列表
POST /api/rag/kb                  # 建立知識庫
PUT /api/rag/kb/{kb_id}           # 更新知識庫
DELETE /api/rag/kb/{kb_id}        # 刪除知識庫
POST /api/rag/kb/{kb_id}/upload   # 上傳檔案
GET /api/rag/kb/{kb_id}/files     # 取得檔案列表
DELETE /api/rag/kb/{kb_id}/files/{file_id} # 刪除檔案
POST /api/rag/search              # 語意搜尋
```

#### LINE API
```
GET /api/line/bots                # 取得 Bot 列表
POST /api/line/bots               # 建立 Bot
PUT /api/line/bots/{bot_id}       # 更新 Bot
DELETE /api/line/bots/{bot_id}    # 刪除 Bot
POST /api/line/webhook/{bot_id}   # LINE Webhook 端點
```

#### Prompt API
```
GET /api/prompts                  # 取得 Prompt 列表
POST /api/prompts                 # 建立 Prompt
PUT /api/prompts/{prompt_id}      # 更新 Prompt
DELETE /api/prompts/{prompt_id}   # 刪除 Prompt
```

## 📁 專案結構

```
mcp-platform/
├── docker-compose.yml              # Docker Compose 配置
├── .env.example                    # 環境變數範例
├── README.md                       # 本文件
├── CHATBOT_GUIDE.md               # Chatbot 使用指南
├── LINE_BOT_README.md             # LINE Bot 整合說明
├── PACKAGE_OPTIMIZATION.md        # 套件優化說明
│
├── mcp-server/                     # MCP Server 服務
│   ├── Dockerfile
│   ├── mcp_server_sse.py          # 主要 SSE Server
│   ├── server.py                  # HTTP Server (備用)
│   ├── config_manager.py          # 配置管理
│   ├── provider_manager.py        # Provider 管理
│   ├── plugin_loader.py           # 動態插件載入
│   ├── providers/                 # Provider 實作
│   │   ├── base_provider.py      # Provider 基礎類別
│   │   ├── python_provider.py    # Python Provider
│   │   ├── nodejs_provider.py    # Node.js Provider
│   │   ├── docker_provider.py    # Docker Provider
│   │   ├── sse_provider.py       # SSE Provider
│   │   └── provider_factory.py   # Provider 工廠
│   ├── configs/                   # Server 配置檔案
│   ├── weather_mcp_tool.py        # 範例: 天氣工具
│   └── requirements.txt
│
├── backend/                        # Backend API 服務
│   ├── Dockerfile
│   ├── app.py                     # Flask 應用主程式
│   ├── docker-entrypoint.sh       # 容器啟動腳本
│   ├── routes/                    # API 路由
│   │   ├── chat.py               # Chat API
│   │   ├── mcp.py                # MCP API
│   │   ├── rag.py                # RAG API
│   │   ├── line.py               # LINE API
│   │   └── prompts.py            # Prompt API
│   ├── services/                  # 業務邏輯服務
│   │   ├── ai_client.py          # AI Client (OpenAI/Google/Anthropic)
│   │   ├── mcp_client.py         # MCP Client
│   │   ├── rag_service.py        # RAG Service
│   │   └── line_client.py        # LINE Client
│   ├── storage/                   # 檔案儲存目錄
│   ├── init_db.py                # 資料庫初始化
│   ├── init_rag_db.py            # RAG 資料庫初始化
│   ├── init_line_db.py           # LINE 資料庫初始化
│   ├── init_prompts_db.py        # Prompt 資料庫初始化
│   └── requirements.txt
│
└── gui/                            # Frontend Web 服務
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.js
        ├── App.vue                # 主元件
        ├── store/                 # 狀態管理
        ├── composables/           # 共用邏輯 (useAuth 等)
        ├── utils/                 # 工具函式
        └── components/
            ├── Chatbot.vue        # Chatbot 介面
            ├── MCPManagement.vue  # MCP 管理介面
            ├── KnowledgeBaseManagement.vue # RAG 管理介面
            ├── LineBotManagement.vue # LINE Bot 管理介面
            └── PromptManagement.vue # Prompt 管理介面
```

## 🔨 開發指南

### 新增 MCP Tool (Plugin 方式)

1. **建立工具檔案 (mcp-server/your_tool.py)**

```python
from fastmcp import FastMCP

mcp = FastMCP("Your Tool Name")

@mcp.tool()
def your_function(param: str) -> str:
    """
    工具描述
    
    Args:
        param: 參數說明
    
    Returns:
        回傳值說明
    """
    # 實作邏輯
    return f"Result: {param}"
```

2. **將檔案放入 mcp-server 目錄**

3. **透過 GUI 新增 Server**
   - Provider 類型: Python
   - 檔案路徑: `/app/your_tool.py`

4. **重新啟動 MCP Server**
```bash
docker-compose restart mcp-server
```

### 新增 Provider 類型

1. **建立 Provider 類別 (mcp-server/providers/your_provider.py)**

```python
from .base_provider import BaseProvider

class YourProvider(BaseProvider):
    def __init__(self, config: dict):
        super().__init__(config)
        # 初始化邏輯
    
    async def start(self):
        # 啟動邏輯
        pass
    
    async def stop(self):
        # 停止邏輯
        pass
    
    async def list_tools(self):
        # 列出工具
        return []
    
    async def call_tool(self, tool_name: str, arguments: dict):
        # 調用工具
        pass
```

2. **註冊 Provider (mcp-server/providers/provider_factory.py)**

```python
from .your_provider import YourProvider

def create_provider(config: dict):
    provider_type = config.get('type')
    if provider_type == 'your_type':
        return YourProvider(config)
    # ...
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

#### MCP Server 本地開發

```bash
cd mcp-server
pip install -r requirements.txt
python mcp_server_sse.py
```

## 🎯 進階功能

### SSE 遠端連線

MCP Server 支援 SSE (Server-Sent Events) 協定,可供外部工具 (如 Claude Desktop) 連接。

#### Claude Desktop 配置範例

```json
{
  "mcpServers": {
    "mcp-platform": {
      "url": "http://localhost:8000/sse",
      "transport": "sse"
    }
  }
}
```

### Docker Provider 隔離執行

Docker Provider 可在隔離容器中執行 MCP 工具,提供更好的安全性和資源控制。

#### 配置範例
- Provider 類型: Docker
- Docker 映像: `node:18-alpine`
- 啟動命令: `npx -y @modelcontextprotocol/server-memory`

### RAG 進階配置

#### 支援的 Embedding Providers
- OpenAI: `text-embedding-3-small`, `text-embedding-3-large`
- Google: `models/embedding-001`
- Anthropic: (透過 Voyage AI)

#### 支援的索引類型
- Simple: 簡單向量搜尋
- FAISS: Facebook AI Similarity Search
- Annoy: Spotify's Approximate Nearest Neighbors

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

### MCP Server 連線失敗

1. 檢查 mcp-server 容器是否正常運行
2. 檢查 Provider 配置是否正確
3. 查看 mcp-server 日誌: `docker-compose logs -f mcp-server`
4. 測試 Server 健康狀態: `curl http://localhost:8000/health`

### RAG 檔案上傳失敗

1. 檢查檔案格式是否支援
2. 檢查檔案大小是否超過限制
3. 確認 Embedding Provider API Key 已設定
4. 查看 backend 日誌

### LINE Bot 無法回應

1. 確認 Webhook URL 已正確設定
2. 檢查 LINE Channel Access Token 是否有效
3. 確認 Bot 已啟用
4. 查看 backend 日誌中的 LINE webhook 請求

### GUI 無法載入

1. 檢查 backend API 是否正常: `curl http://localhost:5000/api/health`
2. 確認環境變數 `VITE_API_URL` 設定正確
3. 清除瀏覽器快取
4. 檢查瀏覽器 Console 錯誤訊息

## 📝 技術規格

### 後端技術
- **Python**: 3.10+
- **Flask**: 3.0.0
- **FastMCP**: 0.2.0
- **MySQL**: 8.0
- **SQLAlchemy**: ORM
- **LangChain**: RAG 框架
- **FAISS/Annoy**: 向量索引

### 前端技術
- **Vue.js**: 3.4.0
- **Vite**: 5.0+
- **Axios**: HTTP Client

### AI Providers
- **OpenAI**: GPT-4, GPT-3.5, Embeddings
- **Google**: Gemini Pro, Gemini Flash, Embeddings
- **Anthropic**: Claude 3 系列

### 容器化
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

## 📄 授權

MIT License

## 👥 貢獻

歡迎提交 Issue 和 Pull Request!

## 📚 相關文件

- [Chatbot 使用指南](CHATBOT_GUIDE.md)
- [LINE Bot 整合說明](LINE_BOT_README.md)
- [套件優化說明](PACKAGE_OPTIMIZATION.md)

## 📧 聯絡

如有問題或建議,請開啟 Issue 討論。

---

**MCP Platform** - 企業級 MCP 工具管理平台 🚀
