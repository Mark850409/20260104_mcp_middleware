"""
資料庫遷移腳本 - 新增 mcp_servers 欄位
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


def migrate_database():
    """新增 mcp_servers 欄位到 conversations 表"""
    try:
        # 連接資料庫
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("正在檢查資料庫結構...")
        
        # 檢查欄位是否已存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'conversations' 
            AND COLUMN_NAME = 'mcp_servers'
        """, (DB_CONFIG['database'],))
        
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✓ mcp_servers 欄位已存在,無需遷移")
            return
        
        print("正在新增 mcp_servers 欄位...")
        
        # 新增欄位
        cursor.execute("""
            ALTER TABLE conversations 
            ADD COLUMN mcp_servers JSON DEFAULT NULL COMMENT '選中的 MCP server ID 列表'
            AFTER mcp_enabled
        """)
        
        connection.commit()
        print("✓ 成功新增 mcp_servers 欄位")
        
        # 驗證
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'conversations'
            ORDER BY ORDINAL_POSITION
        """, (DB_CONFIG['database'],))
        
        print("\n當前 conversations 表結構:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} ({row[2]})")
        
        print("\n資料庫遷移完成!")
        
    except Exception as e:
        print(f"資料庫遷移失敗: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    print("開始資料庫遷移...")
    migrate_database()
