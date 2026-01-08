"""
資料庫遷移腳本 - 添加 tool_call_id 欄位
修復 OpenAI API 工具調用錯誤
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


def add_tool_call_id_column():
    """添加 tool_call_id 欄位到 messages 表"""
    try:
        # 連接資料庫
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("正在檢查並添加 tool_call_id 欄位...")
        
        # 檢查 tool_call_id 欄位是否存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'messages' 
            AND COLUMN_NAME = 'tool_call_id'
        """, (DB_CONFIG['database'],))
        
        if cursor.fetchone()[0] == 0:
            print("添加 tool_call_id 欄位...")
            cursor.execute("""
                ALTER TABLE messages 
                ADD COLUMN tool_call_id VARCHAR(255) AFTER tool_calls,
                ADD INDEX idx_tool_call_id (tool_call_id)
            """)
            connection.commit()
            print("✓ tool_call_id 欄位添加完成")
        else:
            print("✓ tool_call_id 欄位已存在,跳過")
        
        # 顯示 messages 表結構
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'messages'
            ORDER BY ORDINAL_POSITION
        """, (DB_CONFIG['database'],))
        
        print("\n📋 messages 表結構:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}")
        
        print("\n✅ 遷移完成!")
        
    except Exception as e:
        print(f"\n❌ 遷移失敗: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    print("="*60)
    print("開始添加 tool_call_id 欄位...")
    print("="*60)
    add_tool_call_id_column()
