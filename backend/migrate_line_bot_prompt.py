"""
資料庫遷移腳本 - 為 LINE BOT 添加系統提示詞支援
"""
import os
import pymysql

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3307')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}


def add_system_prompt_to_line_bot():
    """為 line_bot_configs 表添加 system_prompt_id 欄位"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("=" * 60)
        print("為 LINE BOT 添加系統提示詞支援")
        print("=" * 60)
        
        # 檢查 system_prompt_id 欄位是否存在
        print("\n[1/2] 檢查 line_bot_configs 表...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'line_bot_configs' 
            AND COLUMN_NAME = 'system_prompt_id'
        """, (DB_CONFIG['database'],))
        
        if cursor.fetchone()[0] == 0:
            print("添加 system_prompt_id 欄位...")
            cursor.execute("""
                ALTER TABLE line_bot_configs 
                ADD COLUMN system_prompt_id INT DEFAULT NULL AFTER selected_mcp_servers,
                ADD CONSTRAINT fk_line_bot_system_prompt 
                FOREIGN KEY (system_prompt_id) 
                REFERENCES system_prompts(id) 
                ON DELETE SET NULL
            """)
            connection.commit()
            print("✓ 成功添加 system_prompt_id 欄位")
        else:
            print("✓ system_prompt_id 欄位已存在,跳過")
        
        # 顯示表結構
        print("\n[2/2] 驗證表結構...")
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'line_bot_configs'
            ORDER BY ORDINAL_POSITION
        """, (DB_CONFIG['database'],))
        
        print("\n📋 line_bot_configs 表結構:")
        for row in cursor.fetchall():
            nullable = "NULL" if row[2] == "YES" else "NOT NULL"
            default = f"DEFAULT {row[3]}" if row[3] else ""
            print(f"  - {row[0]}: {row[1]} {nullable} {default}")
        
        print("\n" + "=" * 60)
        print("✅ 遷移完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 遷移失敗: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    add_system_prompt_to_line_bot()
