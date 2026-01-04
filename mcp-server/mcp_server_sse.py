import os
import asyncio
import logging
import contextvars
from typing import List
from urllib.parse import parse_qs
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# 定義一個 ContextVar 用於存放當前連線的過濾條件 (server_names)
tool_filter_context = contextvars.ContextVar("tool_filter", default=[])

# ... 後續程式碼 ...
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from plugin_loader import PluginLoader

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MCP-SSE-Server")

# 載入環境變數
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)
logger.info(f"載入環境變數檔案: {env_path}")

# ============================================
# 初始化 MCP 伺服器 (低階 API)
# ============================================

server = Server("MCP-Platform-SSE")

# ============================================
# 動態載入插件
# ============================================

logger.info("初始化插件載入器...")
plugin_loader = PluginLoader(os.path.dirname(__file__))
plugin_loader.discover_plugins()
TOOLS = plugin_loader.get_all_tools()

# ============================================
# 註冊 MCP 處理程序
# ============================================

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """列出工具，支援動態過濾"""
    filter_names = tool_filter_context.get()
    
    tools_list = []
    for name, info in TOOLS.items():
        schema = info["schema"]
        server_name = schema.get("server_name")
        
        # 如果有設定過濾條件，則進行篩選
        if filter_names and server_name not in filter_names:
            continue
            
        tools_list.append(Tool(
            name=name,
            description=schema.get("description", ""),
            inputSchema=schema.get("inputSchema", {"type": "object", "properties": {}})
        ))
    
    logger.info(f"回傳工具清單 (過濾條件: {filter_names})，共 {len(tools_list)} 個工具")
    return tools_list

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """處理工具調用請求"""
    logger.info(f"收到工具調用請求: {name}, 參數: {arguments}")
    
    if name not in TOOLS:
        return [TextContent(type="text", text=f"錯誤: 找不到工具 {name}")]
    
    try:
        tool_info = TOOLS[name]
        func = tool_info["function"]
        is_async = tool_info.get("is_async", False)
        
        # 執行工具
        if is_async:
            result = await func(**arguments)
        else:
            result = func(**arguments)
            
        logger.info(f"工具 {name} 執行成功")
        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        logger.error(f"執行工具 {name} 時出錯: {e}")
        return [TextContent(type="text", text=f"執行錯誤: {str(e)}")]

# ============================================
# 設置 SSE 傳輸與 Starlette (ASGI 整合)
# ============================================

sse = SseServerTransport("/messages")

class SseApp:
    """處理 SSE 連線的 ASGI 應用程式，支援透過 query parameter 過濾工具"""
    async def __call__(self, scope, receive, send):
        # 解析 Query String
        query_string = scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        
        # 取得要過濾的 server_names (例如 ?server_names=weather)
        server_names = params.get("server_names", [])
        if server_names:
            # parse_qs 的值是 list，我們取第一個並以逗號分割
            filter_list = [n.strip() for n in server_names[0].split(",") if n.strip()]
            token = tool_filter_context.set(filter_list)
            logger.info(f"SSE 連線已設定過濾條件: {filter_list}")
        else:
            token = None

        try:
            async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
                await server.run(read_stream, write_stream, server.create_initialization_options())
        finally:
            if token:
                tool_filter_context.reset(token)

class MessageApp:
    """處理訊息 POST 的 ASGI 應用程式"""
    async def __call__(self, scope, receive, send):
        await sse.handle_post_message(scope, receive, send)

async def health(request):
    """健康檢查端點"""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "healthy", "service": "MCP-SSE-Server"})

# ============================================
# REST API 端點 (回溯相容管理介面)
# ============================================

from starlette.responses import JSONResponse
from config_manager import config_manager

async def list_tools_rest(request):
    """列出所有可用工具 (REST)"""
    server_names_str = request.query_params.get('server_names', '')
    server_names = [n.strip() for n in server_names_str.split(',') if n.strip()]
    
    all_tools_schemas = [tool["schema"] for tool in TOOLS.values()]
    
    if not server_names:
        return JSONResponse({"tools": all_tools_schemas})
    
    filtered_tools = [t for t in all_tools_schemas if t.get('server_name') in server_names]
    return JSONResponse({"tools": filtered_tools})

async def list_mcp_servers(request):
    """列出所有 MCP Server 配置"""
    try:
        servers = config_manager.list_servers()
        return JSONResponse({"success": True, "data": servers})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

async def add_mcp_server(request):
    """新增 MCP Server"""
    try:
        data = await request.json()
        server_name = data.get('name')
        config = data.get('config', {})
        if not server_name:
            return JSONResponse({"success": False, "error": "Server name is required"}, status_code=400)
        success = config_manager.add_server(server_name, config)
        return JSONResponse({"success": success})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

async def delete_mcp_server(request):
    """刪除 MCP Server"""
    try:
        server_name = request.path_params['server_name']
        success = config_manager.delete_server(server_name)
        return JSONResponse({"success": success})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

async def invoke_tool_rest(request):
    """執行工具 (REST)"""
    tool_name = request.path_params['tool_name']
    logger.info(f"[REST] 收到工具調用請求: {tool_name}")
    
    if tool_name not in TOOLS:
        return JSONResponse({"error": f"Tool not found: {tool_name}"}, status_code=404)
    
    try:
        data = await request.json() or {}
        arguments = data.get('arguments', {})
        
        # 執行工具
        tool_info = TOOLS[tool_name]
        func = tool_info["function"]
        is_async = tool_info.get("is_async", False)
        
        if is_async:
            result = await func(**arguments)
        else:
            result = func(**arguments)
            
        return JSONResponse({
            "success": True,
            "result": result,
            "tool_name": tool_name
        })
    except Exception as e:
        logger.error(f"[REST] 執行錯誤: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "tool_name": tool_name
        }, status_code=500)

# 省略部分較少用的端點以保持簡潔，但確保 list/add/delete 運作正常

starlette_app = Starlette(
    routes=[
        Route("/health", endpoint=health),
        Route("/sse", endpoint=SseApp()),
        Route("/messages", endpoint=MessageApp(), methods=["POST"]),
        # REST API Routes
        Route("/tools", endpoint=list_tools_rest, methods=["GET"]),
        Route("/tools/{tool_name}/invoke", endpoint=invoke_tool_rest, methods=["POST"]),
        Route("/mcp-servers", endpoint=list_mcp_servers, methods=["GET"]),
        Route("/mcp-servers", endpoint=add_mcp_server, methods=["POST"]),
        Route("/mcp-servers/{server_name}", endpoint=delete_mcp_server, methods=["DELETE"]),
    ]
)

# ============================================
# 啟動伺服器
# ============================================

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP SSE Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the SSE server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    args = parser.parse_args()

    logger.info(f"正在啟動 SSE 伺服器於 http://{args.host}:{args.port}")
    logger.info(f"SSE 端點: http://{args.host}:{args.port}/sse")
    logger.info(f"訊息端點: http://{args.host}:{args.port}/messages")
    
    uvicorn.run(starlette_app, host=args.host, port=args.port)
