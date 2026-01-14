"""
Agent API 路由
提供 AI Agent 管理相關的 API 端點
"""
from flask import Blueprint, request, jsonify
import pymysql
import json
import os

# 建立 Blueprint
agents_bp = Blueprint('agents', __name__, url_prefix='/api/agents')

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}


def get_db_connection():
    """取得資料庫連線"""
    return pymysql.connect(**DB_CONFIG)


@agents_bp.route('', methods=['GET'])
def list_agents():
    """取得所有 Agent 列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 取得所有 Agent
        cursor.execute("""
            SELECT 
                a.id, a.name, a.description, a.avatar_url,
                a.model_provider, a.model_name, a.system_prompt_id,
                a.is_active, a.created_at, a.updated_at,
                sp.name as system_prompt_name
            FROM agents a
            LEFT JOIN system_prompts sp ON a.system_prompt_id = sp.id
            ORDER BY a.created_at DESC
        """)
        
        agents = cursor.fetchall()
        
        # 為每個 Agent 載入關聯的知識庫和 MCP 工具
        for agent in agents:
            agent_id = agent['id']
            
            # 載入知識庫
            cursor.execute("""
                SELECT kb.id, kb.name, akb.priority
                FROM agent_knowledge_bases akb
                JOIN knowledge_bases kb ON akb.kb_id = kb.id
                WHERE akb.agent_id = %s
                ORDER BY akb.priority ASC
            """, (agent_id,))
            agent['knowledge_bases'] = cursor.fetchall()
            
            # 載入 MCP 工具
            cursor.execute("""
                SELECT mcp_server_name, is_enabled
                FROM agent_mcp_tools
                WHERE agent_id = %s
            """, (agent_id,))
            agent['mcp_tools'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "agents": agents
        })
        
    except Exception as e:
        print(f"[ERROR] 取得 Agent 列表失敗: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agents_bp.route('', methods=['POST'])
def create_agent():
    """建立新 Agent"""
    try:
        data = request.get_json()
        
        # 驗證必填欄位
        if not data.get('name'):
            return jsonify({
                "success": False,
                "error": "Agent 名稱為必填"
            }), 400
        
        if not data.get('model_provider') or not data.get('model_name'):
            return jsonify({
                "success": False,
                "error": "模型供應商和模型名稱為必填"
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 檢查名稱是否重複
        cursor.execute("SELECT id FROM agents WHERE name = %s", (data['name'],))
        if cursor.fetchone():
            return jsonify({
                "success": False,
                "error": "Agent 名稱已存在"
            }), 400
        
        # 建立 Agent
        cursor.execute("""
            INSERT INTO agents (
                name, description, avatar_url, 
                model_provider, model_name, system_prompt_id, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data['name'],
            data.get('description', ''),
            data.get('avatar_url', ''),
            data['model_provider'],
            data['model_name'],
            data.get('system_prompt_id'),
            data.get('is_active', True)
        ))
        
        agent_id = cursor.lastrowid
        
        # 新增知識庫關聯
        if data.get('knowledge_bases'):
            for idx, kb_id in enumerate(data['knowledge_bases']):
                cursor.execute("""
                    INSERT INTO agent_knowledge_bases (agent_id, kb_id, priority)
                    VALUES (%s, %s, %s)
                """, (agent_id, kb_id, idx))
        
        # 新增 MCP 工具關聯
        if data.get('mcp_tools'):
            for tool_name in data['mcp_tools']:
                cursor.execute("""
                    INSERT INTO agent_mcp_tools (agent_id, mcp_server_name, is_enabled)
                    VALUES (%s, %s, %s)
                """, (agent_id, tool_name, True))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "message": "Agent 建立成功"
        })
        
    except Exception as e:
        print(f"[ERROR] 建立 Agent 失敗: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agents_bp.route('/<int:agent_id>', methods=['GET'])
def get_agent(agent_id):
    """取得單一 Agent 詳情"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 取得 Agent 基本資訊
        cursor.execute("""
            SELECT 
                a.id, a.name, a.description, a.avatar_url,
                a.model_provider, a.model_name, a.system_prompt_id,
                a.is_active, a.created_at, a.updated_at,
                sp.name as system_prompt_name, sp.content as system_prompt_content
            FROM agents a
            LEFT JOIN system_prompts sp ON a.system_prompt_id = sp.id
            WHERE a.id = %s
        """, (agent_id,))
        
        agent = cursor.fetchone()
        
        if not agent:
            return jsonify({
                "success": False,
                "error": "Agent 不存在"
            }), 404
        
        # 載入知識庫
        cursor.execute("""
            SELECT kb.id, kb.name, kb.description, akb.priority
            FROM agent_knowledge_bases akb
            JOIN knowledge_bases kb ON akb.kb_id = kb.id
            WHERE akb.agent_id = %s
            ORDER BY akb.priority ASC
        """, (agent_id,))
        agent['knowledge_bases'] = cursor.fetchall()
        
        # 載入 MCP 工具
        cursor.execute("""
            SELECT mcp_server_name, is_enabled
            FROM agent_mcp_tools
            WHERE agent_id = %s
        """, (agent_id,))
        agent['mcp_tools'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "agent": agent
        })
        
    except Exception as e:
        print(f"[ERROR] 取得 Agent 失敗: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agents_bp.route('/<int:agent_id>', methods=['PUT'])
def update_agent(agent_id):
    """更新 Agent"""
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 檢查 Agent 是否存在
        cursor.execute("SELECT id FROM agents WHERE id = %s", (agent_id,))
        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "error": "Agent 不存在"
            }), 404
        
        # 如果更新名稱,檢查是否重複
        if data.get('name'):
            cursor.execute(
                "SELECT id FROM agents WHERE name = %s AND id != %s", 
                (data['name'], agent_id)
            )
            if cursor.fetchone():
                return jsonify({
                    "success": False,
                    "error": "Agent 名稱已存在"
                }), 400
        
        # 建立更新 SQL
        update_parts = []
        params = []
        
        if 'name' in data:
            update_parts.append("name = %s")
            params.append(data['name'])
        
        if 'description' in data:
            update_parts.append("description = %s")
            params.append(data['description'])
        
        if 'avatar_url' in data:
            update_parts.append("avatar_url = %s")
            params.append(data['avatar_url'])
        
        if 'model_provider' in data:
            update_parts.append("model_provider = %s")
            params.append(data['model_provider'])
        
        if 'model_name' in data:
            update_parts.append("model_name = %s")
            params.append(data['model_name'])
        
        if 'system_prompt_id' in data:
            update_parts.append("system_prompt_id = %s")
            params.append(data['system_prompt_id'])
        
        if 'is_active' in data:
            update_parts.append("is_active = %s")
            params.append(data['is_active'])
        
        # 執行更新
        if update_parts:
            sql = f"UPDATE agents SET {', '.join(update_parts)} WHERE id = %s"
            params.append(agent_id)
            cursor.execute(sql, tuple(params))
        
        # 更新知識庫關聯
        if 'knowledge_bases' in data:
            # 刪除舊關聯
            cursor.execute("DELETE FROM agent_knowledge_bases WHERE agent_id = %s", (agent_id,))
            # 新增新關聯
            for idx, kb_id in enumerate(data['knowledge_bases']):
                cursor.execute("""
                    INSERT INTO agent_knowledge_bases (agent_id, kb_id, priority)
                    VALUES (%s, %s, %s)
                """, (agent_id, kb_id, idx))
        
        # 更新 MCP 工具關聯
        if 'mcp_tools' in data:
            # 刪除舊關聯
            cursor.execute("DELETE FROM agent_mcp_tools WHERE agent_id = %s", (agent_id,))
            # 新增新關聯
            for tool_name in data['mcp_tools']:
                cursor.execute("""
                    INSERT INTO agent_mcp_tools (agent_id, mcp_server_name, is_enabled)
                    VALUES (%s, %s, %s)
                """, (agent_id, tool_name, True))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Agent 更新成功"
        })
        
    except Exception as e:
        print(f"[ERROR] 更新 Agent 失敗: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agents_bp.route('/<int:agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """刪除 Agent"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 檢查 Agent 是否存在
        cursor.execute("SELECT id FROM agents WHERE id = %s", (agent_id,))
        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "error": "Agent 不存在"
            }), 404
        
        # 刪除 Agent (會自動級聯刪除關聯表)
        cursor.execute("DELETE FROM agents WHERE id = %s", (agent_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Agent 刪除成功"
        })
        
    except Exception as e:
        print(f"[ERROR] 刪除 Agent 失敗: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
