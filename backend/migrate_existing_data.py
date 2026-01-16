"""
資料遷移腳本
為現有資料表新增 user_id 欄位,並建立預設管理員帳號與權限配置
"""
import os
import pymysql
import bcrypt
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

# 預設管理員設定
DEFAULT_ADMIN = {
    'username': os.getenv('DEFAULT_ADMIN_USERNAME', 'admin'),
    'email': os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@example.com'),
    'password': os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
}


def migrate_database():
    """執行資料遷移"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("開始資料遷移...")
        
        # ========================================
        # 步驟 1: 建立預設角色
        # ========================================
        print("\n[步驟 1] 建立預設角色...")
        
        roles_data = [
            ('super_admin', '超級管理員', '擁有所有權限,可管理系統所有功能', True),
            ('admin', '管理員', '可管理大部分功能,但無法修改系統設定', True),
            ('user', '一般使用者', '可使用基本功能,無管理權限', True),
            ('guest', '訪客', '僅可查看部分內容', True)
        ]
        
        role_ids = {}
        for role_code, role_name, description, is_system in roles_data:
            cursor.execute("""
                INSERT INTO roles (name, description, is_system)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE description = VALUES(description)
            """, (role_name, description, is_system))
            
            cursor.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
            role_ids[role_code] = cursor.fetchone()[0]
            print(f"  ✓ 建立角色: {role_name}")
        
        # ========================================
        # 步驟 2: 建立預設管理員帳號
        # ========================================
        print("\n[步驟 2] 建立預設管理員帳號...")
        
        # 生成密碼雜湊
        password_hash = bcrypt.hashpw(
            DEFAULT_ADMIN['password'].encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, status)
            VALUES (%s, %s, %s, 'active')
            ON DUPLICATE KEY UPDATE email = VALUES(email)
        """, (DEFAULT_ADMIN['username'], DEFAULT_ADMIN['email'], password_hash))
        
        cursor.execute("SELECT id FROM users WHERE username = %s", (DEFAULT_ADMIN['username'],))
        admin_user_id = cursor.fetchone()[0]
        print(f"  ✓ 建立管理員: {DEFAULT_ADMIN['username']} (ID: {admin_user_id})")
        
        # 分配超級管理員角色
        cursor.execute("""
            INSERT INTO user_roles (user_id, role_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE user_id = VALUES(user_id)
        """, (admin_user_id, role_ids['super_admin']))
        print(f"  ✓ 分配角色: 超級管理員")
        
        # ========================================
        # 步驟 3: 建立預設頁面資源
        # ========================================
        print("\n[步驟 3] 建立預設頁面資源...")
        
        pages_data = [
            # (code, name, route, icon, parent_id, sort_order)
            ('ai_system', 'AI 對話系統', None, 'ri-chat-3-line', None, 1),
            ('chatbot', 'AI Chatbot', '/chatbot', 'ri-chat-3-line', None, 2),
            ('agents', 'Agent 管理', '/agents', 'ri-robot-2-line', None, 3),
            
            ('tools', '工具與整合', None, 'ri-tools-line', None, 4),
            ('mcp', 'MCP 工具管理', '/mcp', 'ri-tools-line', None, 5),
            ('linebot', 'LINE BOT', '/linebot', 'ri-line-fill', None, 6),
            
            ('content', '內容管理', None, 'ri-file-text-line', None, 7),
            ('prompts', '提示詞管理', '/prompts', 'ri-file-text-line', None, 8),
            ('rag', '知識庫管理', '/rag', 'ri-book-2-line', None, 9),
            
            ('system', '系統管理', None, 'ri-settings-3-line', None, 10),
            ('users', '使用者管理', '/users', 'ri-user-line', None, 11),
            ('roles', '角色管理', '/roles', 'ri-shield-user-line', None, 12),
            ('permissions', '權限管理', '/permissions', 'ri-lock-line', None, 13),
            ('pages_mgmt', '頁面管理', '/pages', 'ri-pages-line', None, 14),
            ('functions_mgmt', '功能管理', '/functions', 'ri-function-line', None, 15),
        ]
        
        page_ids = {}
        for page_data in pages_data:
            code, name, route, icon, parent_id, sort_order = page_data
            cursor.execute("""
                INSERT INTO pages (code, name, route, icon, parent_id, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE name = VALUES(name), route = VALUES(route)
            """, (code, name, route, icon, parent_id, sort_order))
            
            cursor.execute("SELECT id FROM pages WHERE code = %s", (code,))
            page_ids[code] = cursor.fetchone()[0]
            print(f"  ✓ 建立頁面: {name}")
        
        # ========================================
        # 步驟 4: 建立預設功能資源
        # ========================================
        print("\n[步驟 4] 建立預設功能資源...")
        
        functions_data = [
            # 使用者管理功能
            ('user_create', '新增使用者', '/api/users', 'POST', page_ids.get('users'), '建立新使用者'),
            ('user_edit', '編輯使用者', '/api/users/:id', 'PUT', page_ids.get('users'), '編輯使用者資料'),
            ('user_delete', '刪除使用者', '/api/users/:id', 'DELETE', page_ids.get('users'), '刪除使用者'),
            ('user_view', '查看使用者', '/api/users', 'GET', page_ids.get('users'), '查看使用者列表'),
            
            # 角色管理功能
            ('role_create', '新增角色', '/api/roles', 'POST', page_ids.get('roles'), '建立新角色'),
            ('role_edit', '編輯角色', '/api/roles/:id', 'PUT', page_ids.get('roles'), '編輯角色資料'),
            ('role_delete', '刪除角色', '/api/roles/:id', 'DELETE', page_ids.get('roles'), '刪除角色'),
            ('role_view', '查看角色', '/api/roles', 'GET', page_ids.get('roles'), '查看角色列表'),
            
            # Chatbot 功能
            ('chat_create', '建立對話', '/api/chat/conversations', 'POST', page_ids.get('chatbot'), '建立新對話'),
            ('chat_delete', '刪除對話', '/api/chat/conversations/:id', 'DELETE', page_ids.get('chatbot'), '刪除對話'),
            
            # 提示詞管理功能
            ('prompt_create', '新增提示詞', '/api/prompts', 'POST', page_ids.get('prompts'), '建立新提示詞'),
            ('prompt_edit', '編輯提示詞', '/api/prompts/:id', 'PUT', page_ids.get('prompts'), '編輯提示詞'),
            ('prompt_delete', '刪除提示詞', '/api/prompts/:id', 'DELETE', page_ids.get('prompts'), '刪除提示詞'),
        ]
        
        function_ids = {}
        for func_data in functions_data:
            code, name, api_endpoint, method, page_id, description = func_data
            cursor.execute("""
                INSERT INTO functions (code, name, api_endpoint, method, page_id, description)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE name = VALUES(name)
            """, (code, name, api_endpoint, method, page_id, description))
            
            cursor.execute("SELECT id FROM functions WHERE code = %s", (code,))
            function_ids[code] = cursor.fetchone()[0]
            print(f"  ✓ 建立功能: {name}")
        
        # ========================================
        # 步驟 5: 建立預設權限
        # ========================================
        print("\n[步驟 5] 建立預設權限...")
        
        # 頁面權限
        for page_code, page_id in page_ids.items():
            perm_code = f"page_{page_code}"
            cursor.execute("""
                INSERT INTO permissions (code, name, type, resource_id, description)
                VALUES (%s, %s, 'page', %s, %s)
                ON DUPLICATE KEY UPDATE name = VALUES(name)
            """, (perm_code, f"訪問{page_code}頁面", page_id, f"允許訪問{page_code}頁面"))
            print(f"  ✓ 建立頁面權限: {perm_code}")
        
        # 功能權限
        for func_code, func_id in function_ids.items():
            perm_code = f"func_{func_code}"
            cursor.execute("""
                INSERT INTO permissions (code, name, type, resource_id, description)
                VALUES (%s, %s, 'function', %s, %s)
                ON DUPLICATE KEY UPDATE name = VALUES(name)
            """, (perm_code, f"執行{func_code}功能", func_id, f"允許執行{func_code}功能"))
            print(f"  ✓ 建立功能權限: {perm_code}")
        
        # ========================================
        # 步驟 6: 分配超級管理員所有權限
        # ========================================
        print("\n[步驟 6] 分配超級管理員權限...")
        
        cursor.execute("SELECT id FROM permissions")
        all_permissions = cursor.fetchall()
        
        for (perm_id,) in all_permissions:
            cursor.execute("""
                INSERT INTO role_permissions (role_id, permission_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE role_id = VALUES(role_id)
            """, (role_ids['super_admin'], perm_id))
        
        print(f"  ✓ 已分配 {len(all_permissions)} 個權限給超級管理員")
        
        # ========================================
        # 步驟 7: 為現有資料表新增 user_id 欄位
        # ========================================
        print("\n[步驟 7] 為現有資料表新增 user_id 欄位...")
        
        tables_to_migrate = [
            'conversations',
            'prompts',
            'agents',
            'knowledge_bases',
            'line_configs'
        ]
        
        for table in tables_to_migrate:
            try:
                # 檢查表是否存在
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if cursor.fetchone():
                    # 檢查欄位是否已存在
                    cursor.execute(f"SHOW COLUMNS FROM {table} LIKE 'user_id'")
                    if not cursor.fetchone():
                        cursor.execute(f"""
                            ALTER TABLE {table}
                            ADD COLUMN user_id INT NULL COMMENT '使用者ID',
                            ADD INDEX idx_user_id (user_id),
                            ADD FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                        """)
                        print(f"  ✓ 為 {table} 表新增 user_id 欄位")
                        
                        # 將現有資料關聯到預設管理員
                        cursor.execute(f"""
                            UPDATE {table}
                            SET user_id = %s
                            WHERE user_id IS NULL
                        """, (admin_user_id,))
                        print(f"  ✓ 將 {table} 表現有資料關聯到管理員")
                    else:
                        print(f"  ⊙ {table} 表已有 user_id 欄位,跳過")
                else:
                    print(f"  ⊙ {table} 表不存在,跳過")
            except Exception as e:
                print(f"  ✗ 處理 {table} 表時發生錯誤: {str(e)}")
        
        connection.commit()
        print("\n" + "="*50)
        print("資料遷移完成!")
        print("="*50)
        print(f"\n預設管理員帳號:")
        print(f"  使用者名稱: {DEFAULT_ADMIN['username']}")
        print(f"  密碼: {DEFAULT_ADMIN['password']}")
        print(f"  Email: {DEFAULT_ADMIN['email']}")
        print("\n請記得修改預設密碼!")
        
    except Exception as e:
        print(f"\n資料遷移失敗: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    migrate_database()
