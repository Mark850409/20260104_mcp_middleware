"""
角色管理 API 路由
提供角色的 CRUD 操作與權限管理
"""
from flask import Blueprint, request, jsonify
import pymysql
from services.auth_service import require_role, require_permission, require_auth
import os

# 建立 Blueprint
roles_bp = Blueprint('roles', __name__, url_prefix='/api/roles')

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}


@roles_bp.route('', methods=['GET'])
@require_permission('func_role_view')
def get_roles():
    """取得角色列表"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT
                r.id,
                r.name,
                r.description,
                r.is_system,
                r.created_at,
                COUNT(DISTINCT ur.user_id) as user_count,
                COUNT(DISTINCT rp.permission_id) as permission_count
            FROM roles r
            LEFT JOIN user_roles ur ON r.id = ur.role_id
            LEFT JOIN role_permissions rp ON r.id = rp.role_id
            GROUP BY r.id
            ORDER BY r.created_at ASC
        """)
        
        roles = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'data': roles
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'取得角色列表失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@roles_bp.route('/<int:role_id>', methods=['GET'])
@require_permission('func_role_view')
def get_role(role_id):
    """取得角色詳細資料"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 查詢角色
        cursor.execute("""
            SELECT id, name, description, is_system, created_at, updated_at
            FROM roles
            WHERE id = %s
        """, (role_id,))
        
        role = cursor.fetchone()
        
        if not role:
            return jsonify({
                'success': False,
                'error': '角色不存在'
            }), 404
        
        # 查詢角色權限
        cursor.execute("""
            SELECT p.id, p.code, p.name, p.type, p.resource_id
            FROM permissions p
            INNER JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = %s
        """, (role_id,))
        
        role['permissions'] = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'data': role
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'取得角色資料失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@roles_bp.route('', methods=['POST'])
@require_permission('func_role_create')
def create_role():
    """
    建立角色
    
    Request Body:
        {
            "name": "角色名稱",
            "description": "角色描述"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必填欄位'
            }), 400
        
        name = data['name'].strip()
        description = data.get('description', '').strip()
        
        if len(name) < 2:
            return jsonify({
                'success': False,
                'error': '角色名稱至少需要 2 個字元'
            }), 400
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 檢查角色名稱是否已存在
        cursor.execute("SELECT id FROM roles WHERE name = %s", (name,))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'error': '角色名稱已存在'
            }), 400
        
        # 建立角色
        cursor.execute("""
            INSERT INTO roles (name, description, is_system)
            VALUES (%s, %s, FALSE)
        """, (name, description))
        
        role_id = cursor.lastrowid
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': '角色建立成功',
            'data': {
                'id': role_id,
                'name': name,
                'description': description
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'建立角色失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@roles_bp.route('/<int:role_id>', methods=['PUT'])
@require_permission('func_role_edit')
def update_role(role_id):
    """
    更新角色
    
    Request Body:
        {
            "name": "新角色名稱",
            "description": "新角色描述"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少必填欄位'
            }), 400
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 檢查角色是否存在
        cursor.execute("SELECT is_system FROM roles WHERE id = %s", (role_id,))
        role = cursor.fetchone()
        
        if not role:
            return jsonify({
                'success': False,
                'error': '角色不存在'
            }), 404
        
        # 不允許修改系統角色
        if role['is_system']:
            return jsonify({
                'success': False,
                'error': '不能修改系統角色'
            }), 400
        
        # 建立更新欄位
        update_fields = []
        params = []
        
        if 'name' in data:
            name = data['name'].strip()
            if len(name) < 2:
                return jsonify({
                    'success': False,
                    'error': '角色名稱至少需要 2 個字元'
                }), 400
            # 檢查名稱是否已被其他角色使用
            cursor.execute("""
                SELECT id FROM roles
                WHERE name = %s AND id != %s
            """, (name, role_id))
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': '角色名稱已存在'
                }), 400
            update_fields.append("name = %s")
            params.append(name)
        
        if 'description' in data:
            update_fields.append("description = %s")
            params.append(data['description'].strip())
        
        if not update_fields:
            return jsonify({
                'success': False,
                'error': '沒有要更新的欄位'
            }), 400
        
        # 更新角色
        params.append(role_id)
        update_query = f"""
            UPDATE roles
            SET {', '.join(update_fields)}
            WHERE id = %s
        """
        cursor.execute(update_query, params)
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': '角色更新成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'更新角色失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@roles_bp.route('/<int:role_id>', methods=['DELETE'])
@require_permission('func_role_delete')
def delete_role(role_id):
    """刪除角色"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 檢查角色是否存在
        cursor.execute("SELECT is_system FROM roles WHERE id = %s", (role_id,))
        role = cursor.fetchone()
        
        if not role:
            return jsonify({
                'success': False,
                'error': '角色不存在'
            }), 404
        
        # 不允許刪除系統角色
        if role['is_system']:
            return jsonify({
                'success': False,
                'error': '不能刪除系統角色'
            }), 400
        
        # 檢查是否有使用者使用此角色
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM user_roles
            WHERE role_id = %s
        """, (role_id,))
        
        if cursor.fetchone()['count'] > 0:
            return jsonify({
                'success': False,
                'error': '此角色仍有使用者使用,無法刪除'
            }), 400
        
        # 刪除角色 (會自動刪除關聯的 role_permissions)
        cursor.execute("DELETE FROM roles WHERE id = %s", (role_id,))
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': '角色刪除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'刪除角色失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@roles_bp.route('/<int:role_id>/permissions', methods=['GET'])
@require_permission('func_role_view')
def get_role_permissions(role_id):
    """取得角色權限"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 檢查角色是否存在
        cursor.execute("SELECT id FROM roles WHERE id = %s", (role_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'error': '角色不存在'
            }), 404
        
        # 查詢角色權限
        cursor.execute("""
            SELECT p.id, p.code, p.name, p.type, p.resource_id
            FROM permissions p
            INNER JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = %s
        """, (role_id,))
        
        permissions = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'data': permissions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'取得角色權限失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@roles_bp.route('/<int:role_id>/permissions', methods=['PUT'])
@require_permission('func_role_permission')
def update_role_permissions(role_id):
    """
    設定角色權限
    
    Request Body:
        {
            "permission_ids": [權限ID列表]
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'permission_ids' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必填欄位'
            }), 400
        
        permission_ids = data['permission_ids']
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 檢查角色是否存在
        cursor.execute("SELECT id FROM roles WHERE id = %s", (role_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'error': '角色不存在'
            }), 404
        
        # 刪除現有權限
        cursor.execute("DELETE FROM role_permissions WHERE role_id = %s", (role_id,))
        
        # 新增新權限
        for permission_id in permission_ids:
            cursor.execute("""
                INSERT INTO role_permissions (role_id, permission_id)
                VALUES (%s, %s)
            """, (role_id, permission_id))
        
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': '角色權限設定成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'設定角色權限失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
