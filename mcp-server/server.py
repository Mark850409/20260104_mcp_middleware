"""
MCP Server - 提供 MCP 工具的 HTTP API
使用 Flask 建立 REST API
支援多 MCP Server 配置管理
支援動態插件載入
"""
import asyncio
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from config_manager import config_manager
from plugin_loader import PluginLoader

# 載入環境變數 (從專案根目錄)
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)
print(f"[MCP Server] 載入環境變數檔案: {env_path}")
print(f"[MCP Server] WEATHER_API_KEY 已設定: {'是' if os.getenv('WEATHER_API_KEY') else '否'}")

# 建立 Flask 應用
app = Flask(__name__)
CORS(app)


# ============================================
# 動態載入所有 MCP 工具插件
# ============================================

print("[MCP Server] 初始化插件載入器...")
plugin_loader = PluginLoader(os.path.dirname(__file__))
plugin_loader.discover_plugins()

# 取得所有已註冊的工具
TOOLS = plugin_loader.get_all_tools()

print(f"[MCP Server] 插件載入完成,共註冊 {len(TOOLS)} 個工具")
print(f"[MCP Server] 可用工具: {', '.join(TOOLS.keys())}")


# ============================================
# 基礎 API 端點
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """健康檢查"""
    return jsonify({"status": "healthy", "service": "MCP Server"})


@app.route('/tools', methods=['GET'])
def list_tools():
    """列出所有可用工具 (支援根據 server_names 過濾)"""
    # 取得要過濾的 server 名稱列表
    server_names_str = request.args.get('server_names', '')
    server_names = [n.strip() for n in server_names_str.split(',') if n.strip()]
    
    all_tools_schemas = [tool["schema"] for tool in TOOLS.values()]
    
    if not server_names:
        return jsonify({"tools": all_tools_schemas})
    
    # 根據 server_name 欄位進行過濾
    filtered_tools = [t for t in all_tools_schemas if t.get('server_name') in server_names]
    
    print(f"[MCP Server] 根據過濾條件 {server_names} 回傳 {len(filtered_tools)} 個工具")
    return jsonify({"tools": filtered_tools})


@app.route('/tools/<tool_name>', methods=['GET'])
def get_tool(tool_name):
    """取得指定工具的資訊"""
    if tool_name not in TOOLS:
        return jsonify({"error": f"Tool not found: {tool_name}"}), 404
    return jsonify(TOOLS[tool_name]["schema"])


@app.route('/tools/<tool_name>/invoke', methods=['POST'])
def invoke_tool(tool_name):
    """執行指定工具"""
    print(f"[MCP Server] 收到工具調用請求: {tool_name}")
    
    if tool_name not in TOOLS:
        print(f"[MCP Server] 錯誤: 工具不存在 - {tool_name}")
        return jsonify({"error": f"Tool not found: {tool_name}"}), 404
    
    try:
        # 取得參數
        data = request.get_json() or {}
        print(f"[MCP Server] 收到的資料: {data}")
        
        arguments = data.get('arguments', {})
        print(f"[MCP Server] 解析的參數: {arguments}")
        
        # 確保 arguments 是字典
        if isinstance(arguments, str):
            import json
            try:
                arguments = json.loads(arguments)
                print(f"[MCP Server] 將字串參數轉換為字典: {arguments}")
            except:
                print(f"[MCP Server] 警告: 無法解析參數字串")
                arguments = {}
        
        # 執行工具
        tool_info = TOOLS[tool_name]
        tool_func = tool_info["function"]
        is_async = tool_info.get("is_async", False)
        
        print(f"[MCP Server] 正在執行工具函數... (async={is_async})")
        
        # 根據是否為非同步函數選擇執行方式
        if is_async:
            result = asyncio.run(tool_func(**arguments))
        else:
            result = tool_func(**arguments)
        
        print(f"[MCP Server] 工具執行成功,結果: {result}")
        
        return jsonify({
            "success": True,
            "result": result,
            "tool_name": tool_name
        })
    except TypeError as e:
        error_msg = f"Invalid arguments: {str(e)}"
        print(f"[MCP Server] TypeError: {error_msg}")
        print(f"[MCP Server] 參數詳情: {arguments}")
        return jsonify({
            "success": False,
            "error": error_msg,
            "tool_name": tool_name
        }), 400
    except Exception as e:
        error_msg = str(e)
        print(f"[MCP Server] 執行錯誤: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": error_msg,
            "tool_name": tool_name
        }), 500


# ============================================
# MCP Server 配置管理 API
# ============================================

@app.route('/mcp-servers', methods=['GET'])
def list_mcp_servers():
    """列出所有 MCP Server 配置"""
    try:
        servers = config_manager.list_servers()
        return jsonify({
            "success": True,
            "data": servers
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/mcp-servers/<server_name>', methods=['GET'])
def get_mcp_server(server_name):
    """取得特定 MCP Server 配置"""
    try:
        server = config_manager.get_server(server_name)
        if server is None:
            return jsonify({
                "success": False,
                "error": f"Server not found: {server_name}"
            }), 404
        
        return jsonify({
            "success": True,
            "data": server
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/mcp-servers', methods=['POST'])
def add_mcp_server():
    """新增 MCP Server"""
    try:
        data = request.get_json()
        server_name = data.get('name')
        config = data.get('config', {})
        
        if not server_name:
            return jsonify({
                "success": False,
                "error": "Server name is required"
            }), 400
        
        success = config_manager.add_server(server_name, config)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Server {server_name} added successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to add server"
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/mcp-servers/<server_name>', methods=['PUT'])
def update_mcp_server(server_name):
    """更新 MCP Server 配置"""
    try:
        config = request.get_json()
        
        success = config_manager.update_server(server_name, config)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Server {server_name} updated successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to update server"
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/mcp-servers/<server_name>', methods=['DELETE'])
def delete_mcp_server(server_name):
    """刪除 MCP Server"""
    try:
        success = config_manager.delete_server(server_name)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Server {server_name} deleted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to delete server"
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/mcp-servers/<server_name>/toggle', methods=['POST'])
def toggle_mcp_server(server_name):
    """啟用/停用 MCP Server"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', True)
        
        success = config_manager.toggle_server(server_name, enabled)
        
        if success:
            status = "enabled" if enabled else "disabled"
            return jsonify({
                "success": True,
                "message": f"Server {server_name} {status} successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to toggle server"
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/mcp-servers/<server_name>/validate', methods=['POST'])
def validate_mcp_server(server_name):
    """驗證 MCP Server 配置"""
    try:
        config = request.get_json()
        
        is_valid = config_manager.validate_server_config(config)
        
        return jsonify({
            "success": True,
            "valid": is_valid
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/mcp-servers/<server_name>/test', methods=['POST'])
def test_mcp_server_full(server_name):
    """強化版測試: 檢查配置、檔案與工具偵測"""
    try:
        # 1. 檢查配置是否存在
        server_config = config_manager.get_server(server_name)
        if not server_config:
            return jsonify({
                "success": False,
                "error": f"Configuration for server '{server_name}' not found"
            }), 404
            
        # 2. 檢查檔案是否存在 (假設是 Python 類型且 args[0] 是路徑)
        if server_config.get('command') == 'python':
            args = server_config.get('args', [])
            if args:
                file_path = args[0]
                # 這裡路徑可能相對於 mcp-server 目錄
                # 我們用 os.path.exists 檢查
                if not os.path.exists(file_path):
                    return jsonify({
                        "success": False,
                        "error": f"File not found: {file_path}. Please check the path."
                    }), 400
        
        # 3. 檢查是否有偵測到該 Server 的工具
        # 在之前我們已經在工具 schema 注入了 server_name
        server_tools = [t for t in TOOLS.values() if t['schema'].get('server_name') == server_name]
        
        if not server_tools:
            return jsonify({
                "success": False,
                "error": f"No tools detected for '{server_name}'. Ensure your file name ends with '_mcp_tool.py' and contains a register_plugin() function."
            }), 400
            
        return jsonify({
            "success": True,
            "message": f"Server '{server_name}' is healthy and provided {len(server_tools)} tool(s).",
            "tools_count": len(server_tools)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Test failed with error: {str(e)}"
        }), 500


if __name__ == "__main__":
    print("Starting MCP Server on port 8000...")
    print(f"Available tools: {', '.join(TOOLS.keys())}")
    print(f"Loaded MCP Servers: {len(config_manager.list_servers())}")
    app.run(host='0.0.0.0', port=8000, debug=False)
