"""
認證服務
提供密碼雜湊、JWT Token 生成與驗證、權限檢查等功能
"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import pymysql

# JWT 設定
JWT_SECRET = os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-change-this-in-production')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}


class AuthService:
    """認證服務類別"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用 bcrypt 雜湊密碼
        
        Args:
            password: 明文密碼
            
        Returns:
            密碼雜湊值
        """
        rounds = int(os.getenv('BCRYPT_ROUNDS', '12'))
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=rounds)).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        驗證密碼
        
        Args:
            password: 明文密碼
            password_hash: 密碼雜湊值
            
        Returns:
            密碼是否正確
        """
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def generate_token(user_id: int, username: str, roles: list = None) -> str:
        """
        生成 JWT Token
        
        Args:
            user_id: 使用者 ID
            username: 使用者名稱
            roles: 使用者角色列表
            
        Returns:
            JWT Token
        """
        payload = {
            'user_id': user_id,
            'username': username,
            'roles': roles or [],
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """
        驗證 JWT Token
        
        Args:
            token: JWT Token
            
        Returns:
            解析後的 payload,如果驗證失敗則返回 None
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def get_user_permissions(user_id: int) -> dict:
        """
        取得使用者的所有權限
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            權限字典 {
                'roles': [...],
                'permissions': [...],
                'pages': [...],
                'functions': [...]
            }
        """
        try:
            connection = pymysql.connect(**DB_CONFIG)
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            # 取得使用者角色
            cursor.execute("""
                SELECT r.id, r.name, r.description
                FROM roles r
                INNER JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = %s
            """, (user_id,))
            roles = cursor.fetchall()
            
            if not roles:
                return {
                    'roles': [],
                    'permissions': [],
                    'pages': [],
                    'functions': []
                }
            
            role_ids = [role['id'] for role in roles]
            
            # 取得角色的所有權限
            cursor.execute("""
                SELECT DISTINCT p.id, p.code, p.name, p.type, p.resource_id
                FROM permissions p
                INNER JOIN role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role_id IN %s
            """, (role_ids,))
            permissions = cursor.fetchall()
            
            # 分離頁面權限和功能權限
            page_permissions = [p for p in permissions if p['type'] == 'page']
            function_permissions = [p for p in permissions if p['type'] == 'function']
            
            # 取得頁面詳細資訊
            if page_permissions:
                page_ids = [p['resource_id'] for p in page_permissions]
                cursor.execute("""
                    SELECT id, code, name, route, icon, parent_id, sort_order
                    FROM pages
                    WHERE id IN %s
                    ORDER BY sort_order
                """, (page_ids,))
                pages = cursor.fetchall()
            else:
                pages = []
            
            # 取得功能詳細資訊
            if function_permissions:
                function_ids = [p['resource_id'] for p in function_permissions]
                cursor.execute("""
                    SELECT id, code, name, api_endpoint, method, page_id
                    FROM functions
                    WHERE id IN %s
                """, (function_ids,))
                functions = cursor.fetchall()
            else:
                functions = []
            
            return {
                'roles': roles,
                'permissions': permissions,
                'pages': pages,
                'functions': functions
            }
            
        except Exception as e:
            print(f"取得使用者權限失敗: {str(e)}")
            return {
                'roles': [],
                'permissions': [],
                'pages': [],
                'functions': []
            }
        finally:
            if 'connection' in locals():
                cursor.close()
                connection.close()
    
    @staticmethod
    def has_permission(user_id: int, permission_code: str) -> bool:
        """
        檢查使用者是否擁有特定權限
        
        Args:
            user_id: 使用者 ID
            permission_code: 權限代碼
            
        Returns:
            是否擁有權限
        """
        # 超級管理員擁有所有權限
        if AuthService.has_role(user_id, '超級管理員'):
            return True
            
        permissions = AuthService.get_user_permissions(user_id)
        return any(p['code'] == permission_code for p in permissions['permissions'])
    
    @staticmethod
    def has_role(user_id: int, role_name: str) -> bool:
        """
        檢查使用者是否擁有特定角色
        
        Args:
            user_id: 使用者 ID
            role_name: 角色名稱
            
        Returns:
            是否擁有角色
        """
        permissions = AuthService.get_user_permissions(user_id)
        return any(r['name'] == role_name for r in permissions['roles'])


# 認證裝飾器
def require_auth(f):
    """
    要求認證的裝飾器
    驗證 JWT Token 並將使用者資訊注入到 request.current_user
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 從 Header 取得 Token
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False,
                'error': '未提供認證 Token'
            }), 401
        
        # 解析 Token (格式: "Bearer <token>")
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({
                'success': False,
                'error': 'Token 格式錯誤'
            }), 401
        
        # 驗證 Token
        payload = AuthService.verify_token(token)
        if not payload:
            return jsonify({
                'success': False,
                'error': 'Token 無效或已過期'
            }), 401
        
        # 將使用者資訊注入到 request
        request.current_user = {
            'id': payload['user_id'],
            'username': payload['username'],
            'roles': payload.get('roles', [])
        }
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_permission(permission_code: str):
    """
    要求特定權限的裝飾器
    
    Args:
        permission_code: 權限代碼
    """
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user_id = request.current_user['id']
            
            if not AuthService.has_permission(user_id, permission_code):
                return jsonify({
                    'success': False,
                    'error': f'沒有權限執行此操作 (需要權限: {permission_code})'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def require_role(role_name: str):
    """
    要求特定角色的裝飾器
    
    Args:
        role_name: 角色名稱
    """
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user_id = request.current_user['id']
            
            if not AuthService.has_role(user_id, role_name):
                return jsonify({
                    'success': False,
                    'error': f'沒有權限執行此操作 (需要角色: {role_name})'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


# 建立服務實例
auth_service = AuthService()
