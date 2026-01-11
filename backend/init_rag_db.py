"""
RAG 功能資料庫初始化腳本
創建檔案管理與知識庫相關資料表
"""
import pymysql
import os
import time

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}

def get_connection(retries=5, delay=2):
    """建立資料庫連線，支援重試"""
    last_exception = None
    for i in range(retries):
        try:
            return pymysql.connect(**DB_CONFIG)
        except Exception as e:
            last_exception = e
            print(f"嘗試連線資料庫失敗 ({i+1}/{retries})... {str(e)}")
            time.sleep(delay)
    raise last_exception

def init_db():
    print("正在初始化 RAG 資料庫...")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. 創建 files 資料表
        print("創建 files 資料表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL COMMENT '原始檔名',
                file_path VARCHAR(512) NOT NULL COMMENT '儲存路徑',
                file_type VARCHAR(50) NOT NULL COMMENT '副檔名',
                size INT NOT NULL COMMENT '檔案大小(bytes)',
                status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        # 2. 創建 knowledge_bases 資料表
        print("創建 knowledge_bases 資料表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_bases (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        # 3. 創建 kb_files 關聯表
        print("創建 kb_files 關聯表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kb_files (
                kb_id INT NOT NULL,
                file_id INT NOT NULL,
                PRIMARY KEY (kb_id, file_id),
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        # 4. 修改 conversations 表，增加 kb_id
        print("檢查並修改 conversations 表 (增加 kb_id)...")
        cursor.execute("SHOW COLUMNS FROM conversations LIKE 'kb_id'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE conversations 
                ADD COLUMN kb_id INT DEFAULT NULL,
                ADD CONSTRAINT fk_conv_kb FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE SET NULL
            """)
            print("已添加 kb_id 到 conversations 表")
        else:
            print("conversations 表已存在 kb_id 欄位")
            
        # 5. 修改 line_bot_configs 表，增加 kb_id
        print("檢查並修改 line_bot_configs 表 (增加 kb_id)...")
        cursor.execute("SHOW COLUMNS FROM line_bot_configs LIKE 'kb_id'")
        if not cursor.fetchone():
            # 由於 line_bot_configs 之前可能沒有 auto_increment id，我們先確認
            cursor.execute("""
                ALTER TABLE line_bot_configs 
                ADD COLUMN kb_id INT DEFAULT NULL,
                ADD CONSTRAINT fk_line_kb FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE SET NULL
            """)
            print("已添加 kb_id 到 line_bot_configs 表")
        else:
            print("line_bot_configs 表已存在 kb_id 欄位")
            
        conn.commit()
        print("RAG 資料庫初始化完成！")
        
    except Exception as e:
        print(f"初始化失敗: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    init_db()
