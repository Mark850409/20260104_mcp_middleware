"""
使用者管理 API 路由
提供使用者的 CRUD 操作 (需管理員權限)
"""
from flask import Blueprint, request, jsonify
import pymysql
from services.auth_service import AuthService, require_auth, require_role, require_permission
import os

# 建立 Blueprint
users_bp = Blueprint('users', __name__, url_prefix='/api/users')

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}


@users_bp.route('', methods=['GET'])
@require_auth
def get_users():
    """
    取得使用者列表 (支援分頁、搜尋、篩選)
    
    Query Parameters:
        page: 頁碼 (預設 1)
        page_size: 每頁筆數 (預設 20)
        search: 搜尋關鍵字 (使用者名稱或 Email)
        status: 狀態篩選 (active, inactive, locked)
        role_id: 角色篩選
    """
    try:
        # 取得查詢參數
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        role_id = request.args.get('role_id', '').strip()
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 建立查詢條件
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(u.username LIKE %s OR u.email LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        if status:
            where_conditions.append("u.status = %s")
            params.append(status)
        
        if role_id:
            where_conditions.append("ur.role_id = %s")
            params.append(int(role_id))
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # 查詢總筆數
        count_query = f"""
            SELECT COUNT(DISTINCT u.id)
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            WHERE {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()['COUNT(DISTINCT u.id)']
        
        # 查詢使用者列表
        offset = (page - 1) * page_size
        list_query = f"""
            SELECT DISTINCT
                u.id,
                u.username,
                u.email,
                u.status,
                u.last_login_at,
                u.created_at,
                GROUP_CONCAT(DISTINCT r.name) as roles
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            WHERE {where_clause}
            GROUP BY u.id
            ORDER BY u.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(list_query, params + [page_size, offset])
        users = cursor.fetchall()
        
        # 處理角色欄位
        for user in users:
            user['roles'] = user['roles'].split(',') if user['roles'] else []
        
        return jsonify({
            'success': True,
            'data': {
                'users': users,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': (total + page_size - 1) // page_size
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'取得使用者列表失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@users_bp.route('/<int:user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    """取得使用者詳細資料"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 查詢使用者
        cursor.execute("""
            SELECT id, username, email, status, last_login_at, created_at, updated_at
            FROM users
            WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False,
                'error': '使用者不存在'
            }), 404
        
        # 查詢使用者角色
        cursor.execute("""
            SELECT r.id, r.name, r.description
            FROM roles r
            INNER JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = %s
        """, (user_id,))
        
        user['roles'] = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'data': user
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'取得使用者資料失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@users_bp.route('', methods=['POST'])
@require_permission('func_user_create')
def create_user():
    """
    建立使用者
    
    Request Body:
        {
            "username": "使用者名稱",
            "email": "Email",
            "password": "密碼",
            "role_ids": [角色ID列表]
        }
    """
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({
                'success': False,
                'error': '缺少必填欄位'
            }), 400
        
        username = data['username'].strip()
        email = data['email'].strip()
        password = data['password']
        role_ids = data.get('role_ids', [])
        
        # 驗證資料格式
        if len(username) < 3:
            return jsonify({
                'success': False,
                'error': '使用者名稱至少需要 3 個字元'
            }), 400
        
        if len(password) < 8:
            return jsonify({
                'success': False,
                'error': '密碼至少需要 8 個字元'
            }), 400
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 檢查使用者名稱是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'error': '使用者名稱已被使用'
            }), 400
        
        # 檢查 Email 是否已存在
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'error': 'Email 已被使用'
            }), 400
        
        # 雜湊密碼
        password_hash = AuthService.hash_password(password)
        
        # 建立使用者
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, status)
            VALUES (%s, %s, %s, 'active')
        """, (username, email, password_hash))
        
        user_id = cursor.lastrowid
        
        # 分配角色
        if role_ids:
            for role_id in role_ids:
                cursor.execute("""
                    INSERT INTO user_roles (user_id, role_id)
                    VALUES (%s, %s)
                """, (user_id, role_id))
        
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': '使用者建立成功',
            'data': {
                'id': user_id,
                'username': username,
                'email': email
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'建立使用者失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@users_bp.route('/<int:user_id>', methods=['PUT'])
@require_permission('func_user_edit')
def update_user(user_id):
    """
    更新使用者資料
    
    Request Body:
        {
            "email": "新 Email",
            "status": "新狀態"
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
        
        # 檢查使用者是否存在
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'error': '使用者不存在'
            }), 404
        
        # 建立更新欄位
        update_fields = []
        params = []
        
        if 'email' in data:
            email = data['email'].strip()
            # 檢查 Email 是否已被其他使用者使用
            cursor.execute("""
                SELECT id FROM users
                WHERE email = %s AND id != %s
            """, (email, user_id))
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': 'Email 已被使用'
                }), 400
            update_fields.append("email = %s")
            params.append(email)
        
        if 'status' in data:
            status = data['status']
            if status not in ['active', 'inactive', 'locked']:
                return jsonify({
                    'success': False,
                    'error': '狀態值不正確'
                }), 400
            update_fields.append("status = %s")
            params.append(status)
        
        if not update_fields:
            return jsonify({
                'success': False,
                'error': '沒有要更新的欄位'
            }), 400
        
        # 更新使用者
        params.append(user_id)
        update_query = f"""
            UPDATE users
            SET {', '.join(update_fields)}
            WHERE id = %s
        """
        cursor.execute(update_query, params)
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': '使用者資料更新成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'更新使用者資料失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@require_permission('func_user_delete')
def delete_user(user_id):
    """刪除使用者"""
    try:
        # 不允許刪除自己
        if user_id == request.current_user['id']:
            return jsonify({
                'success': False,
                'error': '不能刪除自己的帳號'
            }), 400
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 檢查使用者是否存在
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'error': '使用者不存在'
            }), 404
        
        # 刪除使用者 (會自動刪除關聯的 user_roles)
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': '使用者刪除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'刪除使用者失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@users_bp.route('/<int:user_id>/roles', methods=['PUT'])
@require_permission('func_user_role')
def update_user_roles(user_id):
    """
    設定使用者角色
    
    Request Body:
        {
            "role_ids": [角色ID列表]
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'role_ids' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必填欄位'
            }), 400
        
        role_ids = data['role_ids']
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 檢查使用者是否存在
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'error': '使用者不存在'
            }), 404
        
        # 刪除現有角色
        cursor.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
        
        # 新增新角色
        for role_id in role_ids:
            cursor.execute("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (%s, %s)
            """, (user_id, role_id))
        
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': '使用者角色設定成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'設定使用者角色失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
