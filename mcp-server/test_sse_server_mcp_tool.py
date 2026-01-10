"""
最簡單的 MCP SSE Server 範例
用於測試 SSE 客戶端連接
"""
from fastmcp import FastMCP

# 創建 MCP Server
mcp = FastMCP("Simple SSE Test Server")

@mcp.tool()
def hello(name: str) -> str:
    """
    簡單的問候工具
    
    Args:
        name: 要問候的名字
    
    Returns:
        問候訊息
    """
    return f"Hello, {name}! 這是來自 SSE Server 的問候。"

@mcp.tool()
def add(a: int, b: int) -> int:
    """
    簡單的加法工具
    
    Args:
        a: 第一個數字
        b: 第二個數字
    
    Returns:
        兩數之和
    """
    return a + b

@mcp.tool()
def get_info() -> dict:
    """
    獲取 Server 資訊
    
    Returns:
        Server 資訊字典
    """
    return {
        "server_name": "Simple SSE Test Server",
        "version": "1.0.0",
        "description": "用於測試 SSE 連接的簡單 MCP Server",
        "tools_count": 3
    }

if __name__ == "__main__":
    # 啟動 SSE Server
    # 預設會在 http://0.0.0.0:8001 啟動
    # SSE 端點: http://localhost:8001/sse
    # Messages 端點: http://localhost:8001/messages
    mcp.run(transport="sse", host="0.0.0.0", port=8001)
