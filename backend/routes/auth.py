"""
認證 API 路由
提供註冊、登入、登出、個人資料管理等功能
"""
from flask import Blueprint, request, jsonify
import pymysql
from services.auth_service import AuthService, require_auth
from datetime import datetime
import os

# 建立 Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    使用者註冊
    
    Request Body:
        {
            "username": "使用者名稱",
            "email": "Email",
            "password": "密碼"
        }
    """
    try:
        data = request.get_json()
        
        # 驗證必填欄位
        if not data or not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({
                'success': False,
                'error': '缺少必填欄位'
            }), 400
        
        username = data['username'].strip()
        email = data['email'].strip()
        password = data['password']
        
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
        
        if '@' not in email:
            return jsonify({
                'success': False,
                'error': 'Email 格式不正確'
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
        
        # 分配預設角色 (一般使用者)
        cursor.execute("SELECT id FROM roles WHERE name = '一般使用者'")
        role = cursor.fetchone()
        if role:
            cursor.execute("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (%s, %s)
            """, (user_id, role['id']))
        
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': '註冊成功',
            'data': {
                'id': user_id,
                'username': username,
                'email': email
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'註冊失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    使用者登入
    
    Request Body:
        {
            "username": "使用者名稱或 Email",
            "password": "密碼"
        }
    """
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ['username', 'password']):
            return jsonify({
                'success': False,
                'error': '缺少必填欄位'
            }), 400
        
        username = data['username'].strip()
        password = data['password']
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 查詢使用者 (支援使用者名稱或 Email 登入)
        cursor.execute("""
            SELECT id, username, email, password_hash, status
            FROM users
            WHERE username = %s OR email = %s
        """, (username, username))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False,
                'error': '使用者名稱或密碼錯誤'
            }), 401
        
        # 檢查帳號狀態
        if user['status'] != 'active':
            return jsonify({
                'success': False,
                'error': '帳號已被停用或鎖定'
            }), 403
        
        # 驗證密碼
        if not AuthService.verify_password(password, user['password_hash']):
            return jsonify({
                'success': False,
                'error': '使用者名稱或密碼錯誤'
            }), 401
        
        # 取得使用者角色
        cursor.execute("""
            SELECT r.name
            FROM roles r
            INNER JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = %s
        """, (user['id'],))
        roles = [row['name'] for row in cursor.fetchall()]
        
        # 更新最後登入時間
        cursor.execute("""
            UPDATE users
            SET last_login_at = %s
            WHERE id = %s
        """, (datetime.now(), user['id']))
        connection.commit()
        
        # 生成 Token
        token = AuthService.generate_token(user['id'], user['username'], roles)
        
        # 取得使用者權限
        permissions = AuthService.get_user_permissions(user['id'])
        
        return jsonify({
            'success': True,
            'message': '登入成功',
            'data': {
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'roles': roles
                },
                'permissions': {
                    'pages': permissions['pages'],
                    'functions': permissions['functions']
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'登入失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """取得當前使用者資訊"""
    try:
        user_id = request.current_user['id']
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 查詢使用者資訊
        cursor.execute("""
            SELECT id, username, email, status, last_login_at, created_at
            FROM users
            WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False,
                'error': '使用者不存在'
            }), 404
        
        # 取得使用者權限
        permissions = AuthService.get_user_permissions(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'user': user,
                'roles': permissions['roles'],
                'permissions': {
                    'pages': permissions['pages'],
                    'functions': permissions['functions']
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'取得使用者資訊失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """
    更新個人資料
    
    Request Body:
        {
            "email": "新 Email"
        }
    """
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必填欄位'
            }), 400
        
        email = data['email'].strip()
        
        if '@' not in email:
            return jsonify({
                'success': False,
                'error': 'Email 格式不正確'
            }), 400
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
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
        
        # 更新 Email
        cursor.execute("""
            UPDATE users
            SET email = %s
            WHERE id = %s
        """, (email, user_id))
        
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': '個人資料更新成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'更新個人資料失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@auth_bp.route('/password', methods=['PUT'])
@require_auth
def change_password():
    """
    修改密碼
    
    Request Body:
        {
            "old_password": "舊密碼",
            "new_password": "新密碼"
        }
    """
    try:
        user_id = request.current_user['id']
        data = request.get_json()
        
        if not data or not all(k in data for k in ['old_password', 'new_password']):
            return jsonify({
                'success': False,
                'error': '缺少必填欄位'
            }), 400
        
        old_password = data['old_password']
        new_password = data['new_password']
        
        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'error': '新密碼至少需要 8 個字元'
            }), 400
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 查詢使用者
        cursor.execute("""
            SELECT password_hash
            FROM users
            WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False,
                'error': '使用者不存在'
            }), 404
        
        # 驗證舊密碼
        if not AuthService.verify_password(old_password, user['password_hash']):
            return jsonify({
                'success': False,
                'error': '舊密碼錯誤'
            }), 401
        
        # 雜湊新密碼
        new_password_hash = AuthService.hash_password(new_password)
        
        # 更新密碼
        cursor.execute("""
            UPDATE users
            SET password_hash = %s
            WHERE id = %s
        """, (new_password_hash, user_id))
        
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': '密碼修改成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'修改密碼失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """使用者登出 (前端需清除 Token)"""
    return jsonify({
        'success': True,
        'message': '登出成功'
    })
