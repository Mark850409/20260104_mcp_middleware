# Backend API 說明文件

## 概述

Backend API 是基於 Flask 建立的 REST API 服務,作為 MCP Client 與管理介面的中介層。

## 技術規格

- **框架**: Flask 3.0.0
- **Python 版本**: 3.10+
- **端口**: 5000
- **CORS**: 已啟用

## 檔案結構

```
backend/
├── Dockerfile              # Docker 映像配置
├── app.py                 # Flask 應用主程式
├── requirements.txt       # Python 相依套件
└── services/
    ├── __init__.py
    └── mcp_client.py      # MCP Client Service
```

## API 端點

### 健康檢查

```
GET /api/health
```

**回應:**
```json
{
  "status": "healthy",
  "service": "MCP Backend API"
}
```

### MCP Server 狀態

```
GET /api/mcp/status
```

**回應:**
```json
{
  "success": true,
  "data": {
    "connected": true,
    "server_host": "mcp-server",
    "server_port": 8000
  }
}
```

### 連線 MCP Server

```
POST /api/mcp/connect
```

**回應:**
```json
{
  "success": true,
  "message": "連線成功"
}
```

### 中斷連線

```
POST /api/mcp/disconnect
```

**回應:**
```json
{
  "success": true,
  "message": "已中斷連線"
}
```

### 取得工具清單

```
GET /api/mcp/tools
```

**回應:**
```json
{
  "success": true,
  "data": [
    {
      "name": "hello",
      "description": "問候工具 - 回傳問候訊息",
      "inputSchema": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "description": "要問候的名字"
          }
        },
        "required": ["name"]
      }
    }
  ]
}
```

### 執行工具

```
POST /api/mcp/invoke
Content-Type: application/json
```

**請求:**
```json
{
  "tool_name": "hello",
  "arguments": {
    "name": "World"
  }
}
```

**回應:**
```json
{
  "success": true,
  "result": "Hello, World!",
  "tool_name": "hello"
}
```

### 取得工具資訊

```
GET /api/mcp/tools/{tool_name}
```

**回應:**
```json
{
  "success": true,
  "data": {
    "name": "hello",
    "description": "問候工具 - 回傳問候訊息",
    "inputSchema": { ... }
  }
}
```

## MCP Client Service

### 類別: MCPClientService

MCP Client 服務類別,封裝與 MCP Server 的互動邏輯。

#### 方法

##### `__init__()`
初始化 MCP Client Service。

##### `connect() -> bool`
連線到 MCP Server。

**回傳:** 連線是否成功

##### `disconnect()`
中斷與 MCP Server 的連線。

##### `get_status() -> Dict[str, Any]`
取得 MCP Server 連線狀態。

**回傳:** 狀態資訊字典

##### `list_tools() -> List[Dict[str, Any]]`
取得 MCP Server 提供的工具清單。

**回傳:** 工具清單

##### `invoke_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]`
呼叫指定的 MCP 工具。

**參數:**
- `tool_name`: 工具名稱
- `arguments`: 工具參數

**回傳:** 工具執行結果

## 環境變數

| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `FLASK_ENV` | Flask 環境 | development |
| `MCP_SERVER_HOST` | MCP Server 主機 | mcp-server |
| `MCP_SERVER_PORT` | MCP Server 端口 | 8000 |
| `DB_HOST` | 資料庫主機 | db |
| `DB_PORT` | 資料庫端口 | 3306 |
| `DB_NAME` | 資料庫名稱 | mcp_platform |
| `DB_USER` | 資料庫使用者 | mcp_user |
| `DB_PASSWORD` | 資料庫密碼 | mcp_password |

## 本地開發

### 安裝相依套件

```bash
cd backend
pip install -r requirements.txt
```

### 執行應用

```bash
python app.py
```

應用將在 http://localhost:5000 啟動。

## Docker 部署

### 建置映像

```bash
docker build -t mcp-backend .
```

### 執行容器

```bash
docker run -p 5000:5000 \
  -e MCP_SERVER_HOST=mcp-server \
  -e MCP_SERVER_PORT=8000 \
  mcp-backend
```

## 測試

### 使用 curl 測試

```bash
# 健康檢查
curl http://localhost:5000/api/health

# 取得工具清單
curl http://localhost:5000/api/mcp/tools

# 執行工具
curl -X POST http://localhost:5000/api/mcp/invoke \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"hello","arguments":{"name":"Test"}}'
```

## 除錯

### 查看日誌

```bash
docker-compose logs -f backend
```

### 進入容器

```bash
docker exec -it mcp-backend bash
```

## 擴充指南

### 新增 API 端點

在 `app.py` 中新增路由:

```python
@app.route('/api/your-endpoint', methods=['GET'])
def your_endpoint():
    try:
        # 實作邏輯
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
```

### 擴充 MCP Client Service

在 `services/mcp_client.py` 中新增方法:

```python
def your_method(self, param: str) -> Any:
    """方法說明"""
    # 實作邏輯
    return result
```

## 最佳實踐

1. **錯誤處理**: 使用 try-except 處理異常
2. **回應格式**: 統一使用 `{"success": bool, "data": any}` 格式
3. **HTTP 狀態碼**: 正確使用 HTTP 狀態碼
4. **日誌記錄**: 記錄重要操作與錯誤
5. **參數驗證**: 驗證請求參數的有效性
