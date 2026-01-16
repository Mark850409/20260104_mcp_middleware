"""
認證與權限管理資料庫初始化腳本
建立 RBAC 所需的資料表
"""
import os
import pymysql
from datetime import datetime

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}


def init_auth_database():
    """初始化認證與權限管理資料表"""
    try:
        # 連接資料庫
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("正在建立認證與權限管理資料表...")
        
        # 1. 建立 users 表 - 使用者基本資料
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE COMMENT '使用者名稱',
                email VARCHAR(100) NOT NULL UNIQUE COMMENT 'Email',
                password_hash VARCHAR(255) NOT NULL COMMENT '密碼雜湊',
                status ENUM('active', 'inactive', 'locked') DEFAULT 'active' COMMENT '帳號狀態',
                last_login_at TIMESTAMP NULL COMMENT '最後登入時間',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_username (username),
                INDEX idx_email (email),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ 建立 users 表")
        
        # 2. 建立 roles 表 - 角色定義
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE COMMENT '角色名稱',
                description TEXT COMMENT '角色描述',
                is_system BOOLEAN DEFAULT FALSE COMMENT '是否為系統角色(不可刪除)',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ 建立 roles 表")
        
        # 3. 建立 user_roles 表 - 使用者角色關聯
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '使用者ID',
                role_id INT NOT NULL COMMENT '角色ID',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
                UNIQUE KEY uk_user_role (user_id, role_id),
                INDEX idx_user_id (user_id),
                INDEX idx_role_id (role_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ 建立 user_roles 表")
        
        # 4. 建立 pages 表 - 頁面資源
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(50) NOT NULL UNIQUE COMMENT '頁面代碼',
                name VARCHAR(100) NOT NULL COMMENT '頁面名稱',
                route VARCHAR(200) COMMENT '路由路徑',
                icon VARCHAR(50) COMMENT '圖示類別',
                parent_id INT NULL COMMENT '父頁面ID',
                sort_order INT DEFAULT 0 COMMENT '排序順序',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES pages(id) ON DELETE SET NULL,
                INDEX idx_code (code),
                INDEX idx_parent_id (parent_id),
                INDEX idx_sort_order (sort_order)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ 建立 pages 表")
        
        # 5. 建立 functions 表 - 功能資源
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS functions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(50) NOT NULL UNIQUE COMMENT '功能代碼',
                name VARCHAR(100) NOT NULL COMMENT '功能名稱',
                api_endpoint VARCHAR(200) COMMENT 'API 端點',
                method VARCHAR(10) COMMENT 'HTTP 方法',
                page_id INT NULL COMMENT '所屬頁面ID',
                description TEXT COMMENT '功能描述',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE SET NULL,
                INDEX idx_code (code),
                INDEX idx_page_id (page_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ 建立 functions 表")
        
        # 6. 建立 permissions 表 - 權限定義
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(100) NOT NULL UNIQUE COMMENT '權限代碼',
                name VARCHAR(100) NOT NULL COMMENT '權限名稱',
                type ENUM('page', 'function') NOT NULL COMMENT '權限類型',
                resource_id INT NOT NULL COMMENT '資源ID(page_id或function_id)',
                description TEXT COMMENT '權限描述',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_code (code),
                INDEX idx_type (type),
                INDEX idx_resource_id (resource_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ 建立 permissions 表")
        
        # 7. 建立 role_permissions 表 - 角色權限關聯
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                role_id INT NOT NULL COMMENT '角色ID',
                permission_id INT NOT NULL COMMENT '權限ID',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
                FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
                UNIQUE KEY uk_role_permission (role_id, permission_id),
                INDEX idx_role_id (role_id),
                INDEX idx_permission_id (permission_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ 建立 role_permissions 表")
        
        connection.commit()
        print("\n認證與權限管理資料表建立完成!")
        
    except Exception as e:
        print(f"資料庫初始化失敗: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    print("開始初始化認證與權限管理資料庫...")
    init_auth_database()
