"""
Backend API - Flask 應用主程式
提供 MCP 管理與操作的 REST API
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from services.mcp_client import mcp_client
from routes.chat import chat_bp
from routes.mcp import mcp_bp
from routes.line import line_bp
from routes.prompts import prompts_bp
from routes.rag import rag_bp
from routes.agents import agents_bp
# 認證相關路由
from routes.auth import auth_bp
from routes.users import users_bp
from routes.roles import roles_bp
from routes.permissions import permissions_bp
import os

# 建立 Flask 應用
app = Flask(__name__)

# 啟用 CORS (允許前端跨域請求,並支援 Authorization header)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 註冊 Blueprint
app.register_blueprint(chat_bp)
app.register_blueprint(mcp_bp)
app.register_blueprint(line_bp)
app.register_blueprint(prompts_bp)
app.register_blueprint(rag_bp)
app.register_blueprint(agents_bp)
# 認證相關 Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(roles_bp)
app.register_blueprint(permissions_bp)



@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康檢查端點
    
    Returns:
        健康狀態 JSON
    """
    return jsonify({
        "status": "healthy",
        "service": "MCP Backend API"
    })


@app.route('/api/mcp/status', methods=['GET'])
def get_mcp_status():
    """
    取得 MCP Server 連線狀態
    
    Returns:
        MCP Server 狀態 JSON
    """
    try:
        status = mcp_client.get_status()
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mcp/connect', methods=['POST'])
def connect_mcp():
    """
    連線到 MCP Server
    
    Returns:
        連線結果 JSON
    """
    try:
        success = mcp_client.connect()
        return jsonify({
            "success": success,
            "message": "連線成功" if success else "連線失敗"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mcp/disconnect', methods=['POST'])
def disconnect_mcp():
    """
    中斷 MCP Server 連線
    
    Returns:
        中斷連線結果 JSON
    """
    try:
        mcp_client.disconnect()
        return jsonify({
            "success": True,
            "message": "已中斷連線"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mcp/tools', methods=['GET'])
def get_tools():
    """
    取得 MCP Server 提供的工具清單
    
    Returns:
        工具清單 JSON
    """
    try:
        tools = mcp_client.list_tools()
        return jsonify({
            "success": True,
            "data": tools
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mcp/invoke', methods=['POST'])
def invoke_tool():
    """
    呼叫指定的 MCP 工具
    
    Request Body:
        {
            "tool_name": "工具名稱",
            "arguments": {參數物件}
        }
    
    Returns:
        工具執行結果 JSON
    """
    try:
        # 取得請求資料
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "請求資料不可為空"
            }), 400
        
        tool_name = data.get('tool_name')
        arguments = data.get('arguments', {})
        
        if not tool_name:
            return jsonify({
                "success": False,
                "error": "tool_name 為必填欄位"
            }), 400
        
        # 呼叫工具
        result = mcp_client.invoke_tool(tool_name, arguments)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mcp/tools/<tool_name>', methods=['GET'])
def get_tool_info(tool_name):
    """
    取得指定工具的詳細資訊
    
    Args:
        tool_name: 工具名稱
    
    Returns:
        工具資訊 JSON
    """
    try:
        tools = mcp_client.list_tools()
        tool = next((t for t in tools if t['name'] == tool_name), None)
        
        if not tool:
            return jsonify({
                "success": False,
                "error": f"找不到工具: {tool_name}"
            }), 404
        
        return jsonify({
            "success": True,
            "data": tool
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    # 啟動時自動連線 MCP Server
    print("正在連線 MCP Server...")
    mcp_client.connect()
    
    # 啟動 Flask 應用
    # 監聽所有介面的 5000 端口
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
