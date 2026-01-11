"""
系統提示詞資料庫初始化腳本
用於創建 system_prompts 表並修改 conversations 表
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

def init_system_prompts_db():
    """初始化系統提示詞相關資料表"""
    try:
        print("=" * 60)
        print("初始化系統提示詞資料庫")
        print("=" * 60)
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 1. 創建 system_prompts 表
        print("\n[1/3] 創建 system_prompts 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_prompts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL COMMENT '提示詞名稱',
                description TEXT COMMENT '提示詞描述',
                content TEXT NOT NULL COMMENT '提示詞內容',
                is_default BOOLEAN DEFAULT FALSE COMMENT '是否為預設提示詞',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_is_default (is_default)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ system_prompts 表創建完成")
        
        # 2. 檢查並修改 conversations 表
        print("\n[2/3] 修改 conversations 表...")
        
        # 檢查 system_prompt_id 欄位是否存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'conversations' 
            AND COLUMN_NAME = 'system_prompt_id'
        """, (DB_CONFIG['database'],))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE conversations 
                ADD COLUMN system_prompt_id INT DEFAULT NULL AFTER mcp_servers
            """)
            print("✓ 新增 system_prompt_id 欄位")
            
            # 添加外鍵約束
            cursor.execute("""
                ALTER TABLE conversations 
                ADD CONSTRAINT fk_system_prompt 
                FOREIGN KEY (system_prompt_id) 
                REFERENCES system_prompts(id) 
                ON DELETE SET NULL
            """)
            print("✓ 新增外鍵約束")
        else:
            print("✓ system_prompt_id 欄位已存在，跳過")
        
        # 3. 插入預設提示詞
        print("\n[3/3] 插入預設提示詞...")
        
        # 檢查是否已有提示詞
        cursor.execute("SELECT COUNT(*) FROM system_prompts")
        if cursor.fetchone()[0] == 0:
            default_prompts = [
                {
                    'name': '通用助手',
                    'description': '適合一般對話和問答的通用助手',
                    'content': '你是一個專業、友善且樂於助人的 AI 助手。請用清晰、準確的方式回答用戶的問題。',
                    'is_default': True
                },
                {
                    'name': '程式設計助手',
                    'description': '專門協助程式設計和技術問題',
                    'content': '你是一個專業的程式設計助手。請提供清晰的程式碼範例，並解釋技術概念。使用 Markdown 格式化程式碼，並遵循最佳實踐。',
                    'is_default': False
                },
                {
                    'name': '創意寫作',
                    'description': '協助創意寫作和內容創作',
                    'content': '你是一個富有創意的寫作助手。請用生動、引人入勝的方式協助用戶創作內容。發揮想像力，提供獨特的觀點和表達方式。',
                    'is_default': False
                },
                {
                    'name': '專業翻譯',
                    'description': '提供專業的翻譯服務',
                    'content': '你是一個專業的翻譯助手。請提供準確、流暢的翻譯，保持原文的語氣和風格。必要時提供文化背景說明。',
                    'is_default': False
                }
            ]
            
            for prompt in default_prompts:
                cursor.execute("""
                    INSERT INTO system_prompts (name, description, content, is_default)
                    VALUES (%s, %s, %s, %s)
                """, (prompt['name'], prompt['description'], prompt['content'], prompt['is_default']))
            
            print(f"✓ 插入 {len(default_prompts)} 個預設提示詞")
        else:
            print("✓ 提示詞已存在，跳過插入")
        
        connection.commit()
        
        # 顯示最終結構
        print("\n" + "=" * 60)
        print("資料表結構驗證:")
        print("=" * 60)
        
        # 顯示 system_prompts 表結構
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'system_prompts'
            ORDER BY ORDINAL_POSITION
        """, (DB_CONFIG['database'],))
        print("\n📋 system_prompts 表:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}")
        
        # 顯示提示詞數量
        cursor.execute("SELECT COUNT(*) FROM system_prompts")
        count = cursor.fetchone()[0]
        print(f"\n📊 目前共有 {count} 個系統提示詞")
        
        print("\n" + "=" * 60)
        print("✅ 系統提示詞資料庫初始化完成!")
        print("=" * 60)
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"\n❌ 資料庫初始化失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    init_system_prompts_db()
