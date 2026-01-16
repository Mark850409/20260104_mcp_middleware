"""
權限管理 API 路由
提供權限的查詢與管理
"""
from flask import Blueprint, request, jsonify
import pymysql
from services.auth_service import require_role
import os

# 建立 Blueprint
permissions_bp = Blueprint('permissions', __name__, url_prefix='/api/permissions')

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}


@permissions_bp.route('', methods=['GET'])
@require_role('超級管理員')
def get_permissions():
    """取得權限列表"""
    try:
        permission_type = request.args.get('type', '').strip()
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 建立查詢條件
        where_clause = ""
        params = []
        
        if permission_type:
            where_clause = "WHERE p.type = %s"
            params.append(permission_type)
        
        cursor.execute(f"""
            SELECT
                p.id,
                p.code,
                p.name,
                p.type,
                p.resource_id,
                p.description,
                p.created_at,
                CASE
                    WHEN p.type = 'page' THEN pg.name
                    WHEN p.type = 'function' THEN f.name
                END as resource_name
            FROM permissions p
            LEFT JOIN pages pg ON p.type = 'page' AND p.resource_id = pg.id
            LEFT JOIN functions f ON p.type = 'function' AND p.resource_id = f.id
            {where_clause}
            ORDER BY p.type, p.created_at
        """, params)
        
        permissions = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'data': permissions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'取得權限列表失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


@permissions_bp.route('/tree', methods=['GET'])
@require_role('超級管理員')
def get_permissions_tree():
    """取得權限樹狀結構"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 查詢所有頁面權限
        cursor.execute("""
            SELECT
                p.id,
                p.code,
                p.name,
                p.type,
                p.resource_id,
                pg.name as page_name,
                pg.parent_id
            FROM permissions p
            INNER JOIN pages pg ON p.resource_id = pg.id
            WHERE p.type = 'page'
            ORDER BY pg.sort_order
        """)
        page_permissions = cursor.fetchall()
        
        # 查詢所有功能權限
        cursor.execute("""
            SELECT
                p.id,
                p.code,
                p.name,
                p.type,
                p.resource_id,
                f.name as function_name,
                f.page_id
            FROM permissions p
            INNER JOIN functions f ON p.resource_id = f.id
            WHERE p.type = 'function'
        """)
        function_permissions = cursor.fetchall()
        
        # 建立樹狀結構
        tree = {
            'pages': page_permissions,
            'functions': function_permissions
        }
        
        return jsonify({
            'success': True,
            'data': tree
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'取得權限樹狀結構失敗: {str(e)}'
        }), 500
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
