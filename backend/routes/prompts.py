"""
系統提示詞管理 API
提供 CRUD 操作
"""
from flask import Blueprint, request, jsonify
import pymysql
import os

prompts_bp = Blueprint('prompts', __name__, url_prefix='/api')

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


@prompts_bp.route('/prompts', methods=['GET'])
def get_all_prompts():
    """
    獲取所有系統提示詞
    
    Returns:
        JSON: {success: bool, prompts: [...]}
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT id, name, description, content, is_default, created_at, updated_at
            FROM system_prompts
            ORDER BY is_default DESC, created_at DESC
        """)
        
        prompts = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "prompts": prompts
        })
        
    except Exception as e:
        print(f"獲取提示詞失敗: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@prompts_bp.route('/prompts/<int:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """
    獲取單一系統提示詞
    
    Args:
        prompt_id: 提示詞 ID
        
    Returns:
        JSON: {success: bool, prompt: {...}}
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT id, name, description, content, is_default, created_at, updated_at
            FROM system_prompts
            WHERE id = %s
        """, (prompt_id,))
        
        prompt = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if prompt:
            return jsonify({
                "success": True,
                "prompt": prompt
            })
        else:
            return jsonify({
                "success": False,
                "error": "提示詞不存在"
            }), 404
            
    except Exception as e:
        print(f"獲取提示詞失敗: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@prompts_bp.route('/prompts', methods=['POST'])
def create_prompt():
    """
    創建新的系統提示詞
    
    Request Body:
        {
            "name": str,
            "description": str (optional),
            "content": str,
            "is_default": bool (optional)
        }
        
    Returns:
        JSON: {success: bool, prompt_id: int}
    """
    try:
        data = request.json
        
        # 驗證必要欄位
        if not data.get('name') or not data.get('content'):
            return jsonify({
                "success": False,
                "error": "name 和 content 為必填欄位"
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 如果設為預設，先取消其他預設
        if data.get('is_default', False):
            cursor.execute("UPDATE system_prompts SET is_default = FALSE")
        
        # 插入新提示詞
        cursor.execute("""
            INSERT INTO system_prompts (name, description, content, is_default)
            VALUES (%s, %s, %s, %s)
        """, (
            data['name'],
            data.get('description', ''),
            data['content'],
            data.get('is_default', False)
        ))
        
        prompt_id = cursor.lastrowid
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "prompt_id": prompt_id,
            "message": "提示詞創建成功"
        }), 201
        
    except Exception as e:
        print(f"創建提示詞失敗: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@prompts_bp.route('/prompts/<int:prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """
    更新系統提示詞
    
    Args:
        prompt_id: 提示詞 ID
        
    Request Body:
        {
            "name": str (optional),
            "description": str (optional),
            "content": str (optional),
            "is_default": bool (optional)
        }
        
    Returns:
        JSON: {success: bool, message: str}
    """
    try:
        data = request.json
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 檢查提示詞是否存在
        cursor.execute("SELECT id FROM system_prompts WHERE id = %s", (prompt_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "error": "提示詞不存在"
            }), 404
        
        # 如果設為預設，先取消其他預設
        if data.get('is_default', False):
            cursor.execute("UPDATE system_prompts SET is_default = FALSE")
        
        # 構建更新語句
        update_fields = []
        update_values = []
        
        if 'name' in data:
            update_fields.append("name = %s")
            update_values.append(data['name'])
        
        if 'description' in data:
            update_fields.append("description = %s")
            update_values.append(data['description'])
        
        if 'content' in data:
            update_fields.append("content = %s")
            update_values.append(data['content'])
        
        if 'is_default' in data:
            update_fields.append("is_default = %s")
            update_values.append(data['is_default'])
        
        if not update_fields:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "error": "沒有提供要更新的欄位"
            }), 400
        
        # 執行更新
        update_values.append(prompt_id)
        cursor.execute(f"""
            UPDATE system_prompts 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """, tuple(update_values))
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "提示詞更新成功"
        })
        
    except Exception as e:
        print(f"更新提示詞失敗: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@prompts_bp.route('/prompts/<int:prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """
    刪除系統提示詞
    
    Args:
        prompt_id: 提示詞 ID
        
    Returns:
        JSON: {success: bool, message: str}
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 檢查提示詞是否存在
        cursor.execute("SELECT id FROM system_prompts WHERE id = %s", (prompt_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "error": "提示詞不存在"
            }), 404
        
        # 刪除提示詞（相關對話的 system_prompt_id 會自動設為 NULL，因為有 ON DELETE SET NULL）
        cursor.execute("DELETE FROM system_prompts WHERE id = %s", (prompt_id,))
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "提示詞刪除成功"
        })
        
    except Exception as e:
        print(f"刪除提示詞失敗: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
