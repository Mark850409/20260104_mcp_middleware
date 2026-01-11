"""
資料庫遷移腳本 - LINE BOT 整合
建立 LINE 相關的資料表並修改現有表格
"""
import os
import pymysql

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}


def migrate_line_tables():
    """建立 LINE 相關資料表並修改現有表格"""
    try:
        # 連接資料庫
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("正在建立 LINE 相關資料表...")
        
        # 1. 建立 line_users 表
        print("\n[1/4] 建立 line_users 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS line_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                line_user_id VARCHAR(255) UNIQUE NOT NULL,
                display_name VARCHAR(255),
                picture_url TEXT,
                status_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_line_user_id (line_user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ line_users 表建立完成")
        
        # 2. 建立 line_bot_configs 表
        print("\n[2/4] 建立 line_bot_configs 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS line_bot_configs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bot_name VARCHAR(255) NOT NULL,
                channel_access_token TEXT NOT NULL,
                channel_secret VARCHAR(255) NOT NULL,
                webhook_url TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                selected_mcp_servers JSON COMMENT '選中的 MCP server 名稱列表',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_is_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ line_bot_configs 表建立完成")
        
        # 3. 修改 conversations 表 - 新增 LINE 相關欄位
        print("\n[3/4] 修改 conversations 表...")
        
        # 檢查 line_user_id 欄位是否存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'conversations' 
            AND COLUMN_NAME = 'line_user_id'
        """, (DB_CONFIG['database'],))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE conversations 
                ADD COLUMN line_user_id VARCHAR(255) AFTER mcp_servers,
                ADD COLUMN source ENUM('web', 'line') DEFAULT 'web' AFTER line_user_id
            """)
            print("✓ 新增 line_user_id 和 source 欄位")
        else:
            print("✓ line_user_id 欄位已存在,跳過")
        
        # 檢查外鍵是否存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'conversations' 
            AND COLUMN_NAME = 'line_user_id'
            AND REFERENCED_TABLE_NAME = 'line_users'
        """, (DB_CONFIG['database'],))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE conversations 
                ADD CONSTRAINT fk_line_user 
                FOREIGN KEY (line_user_id) REFERENCES line_users(line_user_id)
                ON DELETE SET NULL
            """)
            print("✓ 新增外鍵約束")
        else:
            print("✓ 外鍵約束已存在,跳過")
        
        # 4. 修改 messages 表 - 新增 LINE 訊息相關欄位
        print("\n[4/4] 修改 messages 表...")
        
        # 檢查 line_message_id 欄位是否存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'messages' 
            AND COLUMN_NAME = 'line_message_id'
        """, (DB_CONFIG['database'],))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE messages 
                ADD COLUMN line_message_id VARCHAR(255) AFTER tool_calls,
                ADD COLUMN sync_status ENUM('pending', 'synced', 'failed') DEFAULT 'synced' AFTER line_message_id,
                ADD COLUMN message_type ENUM('text', 'image', 'video', 'audio', 'file') DEFAULT 'text' AFTER sync_status,
                ADD COLUMN tool_call_id VARCHAR(255) AFTER message_type,
                ADD INDEX idx_line_message_id (line_message_id),
                ADD INDEX idx_sync_status (sync_status)
            """)
            print("✓ 新增 LINE 訊息相關欄位")
        else:
            print("✓ LINE 訊息欄位已存在,跳過")
        
        connection.commit()
        
        # 顯示最終結構
        print("\n" + "="*60)
        print("資料表結構驗證:")
        print("="*60)
        
        # 顯示 line_users 表結構
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'line_users'
            ORDER BY ORDINAL_POSITION
        """, (DB_CONFIG['database'],))
        print("\n📋 line_users 表:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}")
        
        # 顯示 line_bot_configs 表結構
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'line_bot_configs'
            ORDER BY ORDINAL_POSITION
        """, (DB_CONFIG['database'],))
        print("\n📋 line_bot_configs 表:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}")
        
        print("\n" + "="*60)
        print("✅ LINE BOT 資料庫遷移完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 資料庫遷移失敗: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    print("="*60)
    print("開始 LINE BOT 資料庫遷移...")
    print("="*60)
    migrate_line_tables()
