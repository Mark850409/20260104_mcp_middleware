"""
MCP 路由 - 處理 MCP Server 管理相關的 API 請求
"""
from flask import Blueprint, request, jsonify
import requests
import os

mcp_bp = Blueprint('mcp', __name__, url_prefix='/api/mcp')

# MCP Server 配置
MCP_SERVER_HOST = os.getenv('MCP_SERVER_HOST', 'mcp-server')
MCP_SERVER_PORT = int(os.getenv('MCP_SERVER_PORT', '8000'))
MCP_SERVER_URL = f"http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}"


# ============================================
# MCP Server 管理 API
# ============================================

@mcp_bp.route('/servers', methods=['GET'])
def list_servers():
    """列出所有 MCP Server"""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/mcp-servers", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch servers"
            }), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@mcp_bp.route('/servers/<server_name>', methods=['GET'])
def get_server(server_name):
    """取得特定 MCP Server 資訊"""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/mcp-servers/{server_name}", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "success": False,
                "error": f"Server not found: {server_name}"
            }), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@mcp_bp.route('/servers', methods=['POST'])
def add_server():
    """新增 MCP Server"""
    try:
        data = request.get_json()
        response = requests.post(f"{MCP_SERVER_URL}/mcp-servers", json=data, timeout=60)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@mcp_bp.route('/servers/<server_name>', methods=['PUT'])
def update_server(server_name):
    """更新 MCP Server 配置"""
    try:
        config = request.get_json()
        response = requests.put(f"{MCP_SERVER_URL}/mcp-servers/{server_name}", json=config, timeout=60)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@mcp_bp.route('/servers/<server_name>', methods=['DELETE'])
def delete_server(server_name):
    """刪除 MCP Server"""
    try:
        response = requests.delete(f"{MCP_SERVER_URL}/mcp-servers/{server_name}", timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@mcp_bp.route('/servers/<server_name>/toggle', methods=['POST'])
def toggle_server(server_name):
    """啟用/停用 MCP Server"""
    try:
        data = request.get_json()
        response = requests.post(f"{MCP_SERVER_URL}/mcp-servers/{server_name}/toggle", json=data, timeout=30)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@mcp_bp.route('/servers/<server_name>/test', methods=['POST'])
def test_server(server_name):
    """測試 MCP Server 連線 (強化版: 偵測工具與檔案)"""
    try:
        # 調用 mcp-server 的強化版測試端點
        response = requests.post(f"{MCP_SERVER_URL}/mcp-servers/{server_name}/test", timeout=60)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================
# MCP Tool 管理 API
# ============================================

@mcp_bp.route('/servers/<server_name>/tools', methods=['GET'])
def get_server_tools(server_name):
    """取得特定 Server 的 Tools"""
    try:
        # 將 server_name 作為過濾參數傳遞
        response = requests.get(
            f"{MCP_SERVER_URL}/tools", 
            params={"server_names": server_name},
            timeout=30
        )
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch tools"
            }), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@mcp_bp.route('/servers/<server_name>/tools/<tool_name>/invoke', methods=['POST'])
def invoke_server_tool(server_name, tool_name):
    """執行特定 Server 的 Tool"""
    try:
        data = request.get_json()
        response = requests.post(
            f"{MCP_SERVER_URL}/tools/{tool_name}/invoke",
            json=data,
            timeout=30
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================
# 舊版 API (向後相容)
# ============================================

@mcp_bp.route('/status', methods=['GET'])
def get_status():
    """取得 MCP Server 連線狀態"""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            return jsonify({
                "success": True,
                "data": {
                    "connected": True,
                    "server_host": MCP_SERVER_HOST,
                    "server_port": MCP_SERVER_PORT
                }
            })
        else:
            return jsonify({
                "success": True,
                "data": {
                    "connected": False,
                    "server_host": MCP_SERVER_HOST,
                    "server_port": MCP_SERVER_PORT
                }
            })
    except Exception as e:
        return jsonify({
            "success": True,
            "data": {
                "connected": False,
                "server_host": MCP_SERVER_HOST,
                "server_port": MCP_SERVER_PORT
            }
        })


@mcp_bp.route('/connect', methods=['POST'])
def connect():
    """連線到 MCP Server"""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            return jsonify({
                "success": True,
                "message": "Connected to MCP Server"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to connect"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@mcp_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """中斷與 MCP Server 的連線"""
    return jsonify({
        "success": True,
        "message": "Disconnected from MCP Server"
    })


@mcp_bp.route('/tools', methods=['GET'])
def get_tools():
    """取得 MCP Server 提供的工具清單"""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/tools", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch tools"
            }), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@mcp_bp.route('/invoke', methods=['POST'])
def invoke_tool():
    """呼叫指定的 MCP 工具"""
    try:
        data = request.get_json()
        tool_name = data.get('tool_name')
        arguments = data.get('arguments', {})
        
        response = requests.post(
            f"{MCP_SERVER_URL}/tools/{tool_name}/invoke",
            json={"arguments": arguments},
            timeout=30
        )
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@mcp_bp.route('/export', methods=['GET'])
def export_config():
    """匯出 MCP Server 配置"""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/api/mcp/export", timeout=10)
        if response.status_code == 200:
            from flask import Response
            # 排除某些不適合直接轉發的 headers
            excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
            headers = [(name, value) for (name, value) in response.headers.items()
                       if name.lower() not in excluded_headers]
            
            return Response(response.content, response.status_code, headers)
        else:
            return jsonify({
                "success": False,
                "error": "Failed to export config"
            }), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@mcp_bp.route('/import', methods=['POST'])
def import_config():
    """匯入 MCP Server 配置"""
    try:
        data = request.get_json()
        overwrite = request.args.get('overwrite', 'false')
        
        response = requests.post(
            f"{MCP_SERVER_URL}/api/mcp/import", 
            json=data, 
            params={"overwrite": overwrite},
            timeout=60
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
