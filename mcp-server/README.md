# MCP Server 說明文件

## 概述

MCP Server 是基於 fastmcp 框架建立的 Model Context Protocol 工具伺服器,提供可擴充的工具執行環境。

## 技術規格

- **框架**: fastmcp 0.2.0
- **Python 版本**: 3.10+
- **傳輸協議**: stdio / sse (Server-Sent Events)
- **容器端口**: 8000

## 檔案結構

```
mcp-server/
├── Dockerfile          # Docker 映像配置
├── server.py          # MCP Server 主程式
└── requirements.txt   # Python 相依套件
```

## 工具清單

### 1. hello

問候工具,回傳個人化問候訊息。

**參數:**
- `name` (string, 必填): 要問候的名字

**範例:**
```python
hello(name="World")
# 回傳: "Hello, World!"
```

**實作:**
```python
@mcp.tool()
def hello(name: str) -> str:
    return f"Hello, {name}!"
```

### 2. get_time

時間工具,回傳當前 ISO 8601 格式時間。

**參數:** 無

**範例:**
```python
get_time()
# 回傳: "2026-01-04T16:37:10+08:00"
```

**實作:**
```python
@mcp.tool()
def get_time() -> str:
    return datetime.now().isoformat()
```

## 新增工具

### 步驟 1: 定義工具函式

在 `server.py` 中使用 `@mcp.tool()` 裝飾器:

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

### 步驟 2: 重新啟動容器

```bash
docker-compose restart mcp-server
```

## 本地開發

### 安裝相依套件

```bash
cd mcp-server
pip install -r requirements.txt
```

### 執行伺服器

```bash
python server.py
```

## Docker 部署

### 建置映像

```bash
docker build -t mcp-server .
```

### 執行容器

```bash
docker run -p 8000:8000 mcp-server
```

## 除錯

### 查看日誌

```bash
docker-compose logs -f mcp-server
```

### 進入容器

```bash
docker exec -it mcp-server bash
```

## SSE 支援與第三方整合 (如 Claude Desktop)

您可以使用 SSE 模式啟動伺服器,這允許外部應用程式(如 Claude Desktop)透過網路或 ngrok 與您的工具整合。

### 1. 啟動 SSE 伺服器

```bash
# 在 mcp-server 目錄下
python mcp_server_sse.py
```

伺服器預設會運行在 `http://localhost:8000`。

### 2. 使用 ngrok 建立公開網址 (地端測試)

若要在雲端或 Claude Desktop 中測試,您需要一個公開網址:

```bash
ngrok http 8000
```

獲取轉發網址,例如: `https://xxxx.ngrok-free.app`

### 3. 配置 Claude Desktop

1. 開啟 Claude Desktop 設定檔:
   `%APPDATA%\Claude\claude_desktop_config.json`

2. 在 `mcpServers` 區段加入以下配置:

```json
{
  "mcpServers": {
    "mcp-platform": {
      "url": "https://您的公開網址/sse"
    }
  }
}
```

> [!IMPORTANT]
> 請確保網址以 `/sse` 結尾。

3. 重啟 Claude Desktop 即可看到您的工具已連線。

## 最佳實踐
... (略)
