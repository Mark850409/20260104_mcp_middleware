"""
建立 mcp_servers 資料表
"""
import os
import pymysql
# 載入環境變數
# 注意: 在 Docker 環境中, 環境變數通常已經由 docker-compose 載入
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass # 如果沒有安裝 python-dotenv，假設環境變數已由外部提供

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}

def create_table():
    """建立 mcp_servers 資料表"""
    try:
        print(f"連接資料庫: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("正在建立 mcp_servers 資料表...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcp_servers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE COMMENT 'Server 名稱',
                description TEXT COMMENT 'Server 描述',
                command VARCHAR(100) NOT NULL COMMENT '執行命令: python, node, npx 等',
                args JSON NOT NULL COMMENT '命令參數陣列',
                env JSON DEFAULT NULL COMMENT '環境變數',
                type VARCHAR(50) DEFAULT 'python' COMMENT 'Provider 類型: python, nodejs, docker 等',
                enabled BOOLEAN DEFAULT TRUE COMMENT '是否啟用',
                url VARCHAR(255) DEFAULT NULL COMMENT 'HTTP/SSE URL',
                headers JSON DEFAULT NULL COMMENT 'HTTP Headers',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_name (name),
                INDEX idx_enabled (enabled)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        connection.commit()
        print("✓ 建立 mcp_servers 資料表成功")

        # 嘗試新增欄位 (如果資料表已存在但缺少欄位)
        try:
            print("檢查並更新資料表結構...")
            cursor.execute("ALTER TABLE mcp_servers ADD COLUMN url VARCHAR(255) DEFAULT NULL COMMENT 'HTTP/SSE URL'")
            print("✓ 新增 url 欄位")
        except Exception as e:
            if "Duplicate column name" not in str(e):
                print(f"新增 url 欄位略過: {str(e)}")
        
        try:
            cursor.execute("ALTER TABLE mcp_servers ADD COLUMN headers JSON DEFAULT NULL COMMENT 'HTTP Headers'")
            print("✓ 新增 headers 欄位")
        except Exception as e:
            if "Duplicate column name" not in str(e):
                print(f"新增 headers 欄位略過: {str(e)}")
        
        # 嘗試修改 command 欄位為 NULLABLE (如果有的話) 或者保持 NOT NULL 但預設為 ''
        # 這裡我們不修改 command schema，但在程式碼中提供預設值
        
        connection.commit()
        print("✓ 資料表結構更新完成")
        
    except Exception as e:
        print(f"建立資料表失敗: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    create_table()
