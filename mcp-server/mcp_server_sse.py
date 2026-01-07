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
# REST API 端點 (完整管理介面)
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

async def get_mcp_server(request):
    """取得特定 MCP Server 配置"""
    try:
        server_name = request.path_params['server_name']
        server = config_manager.get_server(server_name)
        if server is None:
            return JSONResponse({
                "success": False,
                "error": f"Server not found: {server_name}"
            }, status_code=404)
        
        return JSONResponse({
            "success": True,
            "data": server
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

async def add_mcp_server(request):
    """新增 MCP Server"""
    try:
        try:
            data = await request.json()
        except Exception as json_error:
            logger.error(f"JSON 解析失敗: {json_error}")
            return JSONResponse({
                "success": False,
                "error": "Invalid JSON format in request body"
            }, status_code=400)
            
        server_name = data.get('name')
        config = data.get('config', {})
        if not server_name:
            return JSONResponse({"success": False, "error": "Server name is required"}, status_code=400)
        success = config_manager.add_server(server_name, config)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Server {server_name} added successfully"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "Failed to add server"
            }, status_code=400)
    except Exception as e:
        logger.error(f"新增 Server 失敗: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

async def update_mcp_server(request):
    """更新 MCP Server 配置"""
    try:
        server_name = request.path_params['server_name']
        
        try:
            config = await request.json()
        except Exception as json_error:
            logger.error(f"JSON 解析失敗: {json_error}")
            return JSONResponse({
                "success": False,
                "error": "Invalid JSON format in request body"
            }, status_code=400)
        
        success = config_manager.update_server(server_name, config)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Server {server_name} updated successfully"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "Failed to update server"
            }, status_code=400)
    except Exception as e:
        logger.error(f"更新 Server 失敗: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

async def delete_mcp_server(request):
    """刪除 MCP Server"""
    try:
        server_name = request.path_params['server_name']
        success = config_manager.delete_server(server_name)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f"Server {server_name} deleted successfully"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "Failed to delete server"
            }, status_code=400)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

async def toggle_mcp_server(request):
    """啟用/停用 MCP Server"""
    try:
        server_name = request.path_params['server_name']
        logger.info(f"切換 Server 狀態: {server_name}")
        
        # 讀取請求 body
        try:
            body = await request.body()
            logger.info(f"收到的 body: {body}")
            
            if not body or body == b'':
                data = {}
            else:
                import json as json_module
                data = json_module.loads(body.decode('utf-8'))
        except Exception as json_error:
            logger.error(f"JSON 解析失敗: {json_error}")
            import traceback
            traceback.print_exc()
            return JSONResponse({
                "success": False,
                "error": f"Invalid JSON format in request body: {str(json_error)}"
            }, status_code=400)
            
        enabled = data.get('enabled', True)
        logger.info(f"設定 enabled 為: {enabled}")
        
        success = config_manager.toggle_server(server_name, enabled)
        logger.info(f"toggle_server 結果: {success}")
        
        if success:
            status = "enabled" if enabled else "disabled"
            return JSONResponse({
                "success": True,
                "message": f"Server {server_name} {status} successfully"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "Failed to toggle server"
            }, status_code=400)
    except Exception as e:
        logger.error(f"切換 Server 狀態失敗: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

async def validate_mcp_server(request):
    """驗證 MCP Server 配置"""
    try:
        server_name = request.path_params['server_name']
        
        try:
            config = await request.json()
        except Exception as json_error:
            logger.error(f"JSON 解析失敗: {json_error}")
            return JSONResponse({
                "success": False,
                "error": "Invalid JSON format in request body"
            }, status_code=400)
        
        is_valid = config_manager.validate_server_config(config)
        
        return JSONResponse({
            "success": True,
            "valid": is_valid
        })
    except Exception as e:
        logger.error(f"驗證 Server 配置失敗: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

async def test_mcp_server(request):
    """測試 MCP Server:檢查配置、檔案與工具偵測"""
    try:
        server_name = request.path_params['server_name']
        logger.info(f"========== 開始測試 Server: {server_name} ==========")
        
        # 1. 檢查配置是否存在
        logger.info("步驟 1: 檢查配置是否存在")
        server_config = config_manager.get_server(server_name)
        logger.info(f"取得的配置: {server_config}")
        
        if not server_config:
            logger.error(f"找不到 Server 配置: {server_name}")
            return JSONResponse({
                "success": False,
                "error": f"Configuration for server '{server_name}' not found"
            }, status_code=404)
            
        # 2. 檢查檔案是否存在 (假設是 Python 類型且 args[0] 是路徑)
        logger.info("步驟 2: 檢查檔案是否存在")
        if server_config.get('command') == 'python':
            args = server_config.get('args', [])
            logger.info(f"args: {args}")
            
            if args:
                file_path = args[0]
                logger.info(f"原始檔案路徑: {file_path}")
                
                # 如果是相對路徑,轉換為絕對路徑
                if not os.path.isabs(file_path):
                    # 相對於 mcp-server 目錄
                    base_dir = os.path.dirname(__file__)
                    file_path = os.path.join(base_dir, file_path)
                    logger.info(f"轉換後的絕對路徑: {file_path}")
                
                logger.info(f"檢查檔案路徑: {file_path}")
                if not os.path.exists(file_path):
                    logger.error(f"檔案不存在: {file_path}")
                    return JSONResponse({
                        "success": False,
                        "error": f"File not found: {file_path}. Please check the path."
                    }, status_code=400)
                else:
                    logger.info(f"檔案存在: {file_path}")
        
        # 3. 檢查是否有偵測到該 Server 的工具
        logger.info("步驟 3: 檢查工具偵測")
        logger.info(f"所有工具: {list(TOOLS.keys())}")
        
        server_tools = [t for t in TOOLS.values() if t['schema'].get('server_name') == server_name]
        logger.info(f"偵測到 {len(server_tools)} 個工具")
        
        if not server_tools:
            logger.error(f"沒有偵測到任何工具: {server_name}")
            return JSONResponse({
                "success": False,
                "error": f"No tools detected for '{server_name}'. Ensure your file name ends with '_mcp_tool.py' and contains a register_plugin() function."
            }, status_code=400)
            
        logger.info(f"Server {server_name} 測試成功")
        return JSONResponse({
            "success": True,
            "message": f"Server '{server_name}' is healthy and provided {len(server_tools)} tool(s).",
            "tools_count": len(server_tools)
        })
        
    except Exception as e:
        logger.error(f"測試 Server 失敗: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": f"Test failed with error: {str(e)}"
        }, status_code=500)

async def list_server_tools(request):
    """列出特定 Server 的所有工具"""
    try:
        server_name = request.path_params['server_name']
        
        # 過濾出屬於該 server 的工具
        server_tools = [
            tool["schema"] 
            for tool in TOOLS.values() 
            if tool['schema'].get('server_name') == server_name
        ]
        
        return JSONResponse({"tools": server_tools})
    except Exception as e:
        logger.error(f"列出 Server 工具失敗: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

async def invoke_server_tool(request):
    """執行特定 Server 的工具"""
    server_name = request.path_params['server_name']
    tool_name = request.path_params['tool_name']
    logger.info(f"[REST] 收到工具調用請求: {server_name}/{tool_name}")
    
    if tool_name not in TOOLS:
        logger.error(f"[REST] 工具不存在: {tool_name}")
        return JSONResponse({
            "success": False,
            "error": f"Tool not found: {tool_name}"
        }, status_code=404)
    
    # 驗證工具是否屬於該 server
    tool_info = TOOLS[tool_name]
    if tool_info['schema'].get('server_name') != server_name:
        logger.error(f"[REST] 工具 {tool_name} 不屬於 server {server_name}")
        return JSONResponse({
            "success": False,
            "error": f"Tool {tool_name} does not belong to server {server_name}"
        }, status_code=400)
    
    try:
        data = await request.json() or {}
        arguments = data.get('arguments', {})
        
        logger.info(f"[REST] 執行參數: {arguments}")
        
        # 執行工具
        func = tool_info["function"]
        is_async = tool_info.get("is_async", False)
        
        if is_async:
            result = await func(**arguments)
        else:
            result = func(**arguments)
        
        logger.info(f"[REST] 執行成功: {result}")
            
        return JSONResponse({
            "success": True,
            "result": result,
            "tool_name": tool_name
        })
    except TypeError as e:
        error_msg = f"Invalid arguments: {str(e)}"
        logger.error(f"[REST] TypeError: {error_msg}")
        logger.error(f"[REST] 參數詳情: {arguments}")
        return JSONResponse({
            "success": False,
            "error": error_msg,
            "tool_name": tool_name
        }, status_code=400)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[REST] 執行錯誤: {error_msg}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": error_msg,
            "tool_name": tool_name
        }, status_code=500)

async def invoke_tool_rest(request):
    """執行工具 (REST) - 舊版相容端點"""
    tool_name = request.path_params['tool_name']
    logger.info(f"[REST] 收到工具調用請求 (舊版): {tool_name}")
    
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

from starlette.middleware.cors import CORSMiddleware

starlette_app = Starlette(
    routes=[
        # 健康檢查
        Route("/health", endpoint=health),
        
        # SSE 端點
        Route("/sse", endpoint=SseApp()),
        Route("/messages", endpoint=MessageApp(), methods=["POST"]),
        
        # 工具 API (舊版相容)
        Route("/tools", endpoint=list_tools_rest, methods=["GET"]),
        Route("/tools/{tool_name}/invoke", endpoint=invoke_tool_rest, methods=["POST"]),
        
        # MCP Server 管理 API (新版路徑: /api/mcp/servers/...)
        Route("/api/mcp/servers", endpoint=list_mcp_servers, methods=["GET"]),
        Route("/api/mcp/servers", endpoint=add_mcp_server, methods=["POST"]),
        Route("/api/mcp/servers/{server_name}", endpoint=get_mcp_server, methods=["GET"]),
        Route("/api/mcp/servers/{server_name}", endpoint=update_mcp_server, methods=["PUT"]),
        Route("/api/mcp/servers/{server_name}", endpoint=delete_mcp_server, methods=["DELETE"]),
        Route("/api/mcp/servers/{server_name}/toggle", endpoint=toggle_mcp_server, methods=["POST"]),
        Route("/api/mcp/servers/{server_name}/validate", endpoint=validate_mcp_server, methods=["POST"]),
        Route("/api/mcp/servers/{server_name}/test", endpoint=test_mcp_server, methods=["POST"]),
        Route("/api/mcp/servers/{server_name}/tools", endpoint=list_server_tools, methods=["GET"]),
        Route("/api/mcp/servers/{server_name}/tools/{tool_name}/invoke", endpoint=invoke_server_tool, methods=["POST"]),
        
        # 舊版相容路徑 (與 server.py 的 Flask 路徑一致)
        Route("/mcp-servers", endpoint=list_mcp_servers, methods=["GET"]),
        Route("/mcp-servers", endpoint=add_mcp_server, methods=["POST"]),
        Route("/mcp-servers/{server_name}", endpoint=get_mcp_server, methods=["GET"]),
        Route("/mcp-servers/{server_name}", endpoint=update_mcp_server, methods=["PUT"]),
        Route("/mcp-servers/{server_name}", endpoint=delete_mcp_server, methods=["DELETE"]),
        Route("/mcp-servers/{server_name}/toggle", endpoint=toggle_mcp_server, methods=["POST"]),
        Route("/mcp-servers/{server_name}/validate", endpoint=validate_mcp_server, methods=["POST"]),
        Route("/mcp-servers/{server_name}/test", endpoint=test_mcp_server, methods=["POST"]),
        Route("/mcp-servers/{server_name}/tools", endpoint=list_server_tools, methods=["GET"]),
        Route("/mcp-servers/{server_name}/tools/{tool_name}/invoke", endpoint=invoke_server_tool, methods=["POST"]),
    ]
)

# 添加 CORS 中間件
starlette_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有 HTTP 方法
    allow_headers=["*"],  # 允許所有 headers
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
