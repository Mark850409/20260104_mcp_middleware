"""
資料庫初始化腳本 - AI Agent 功能
建立 Agent 相關的資料表
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


def init_agents_tables():
    """初始化 Agent 相關資料表"""
    try:
        # 連接資料庫
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("正在建立 Agent 相關資料表...")
        
        # 1. 建立 agents 表
        print("\n[1/4] 建立 agents 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL COMMENT 'Agent 名稱',
                description TEXT COMMENT 'Agent 說明',
                avatar_url TEXT COMMENT '頭像 URL',
                model_provider VARCHAR(50) NOT NULL COMMENT 'AI 供應商: openai, google, anthropic',
                model_name VARCHAR(100) NOT NULL COMMENT '模型名稱',
                system_prompt_id INT DEFAULT NULL COMMENT '系統提示詞 ID',
                is_active BOOLEAN DEFAULT TRUE COMMENT '是否啟用',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_name (name),
                INDEX idx_is_active (is_active),
                INDEX idx_created_at (created_at),
                FOREIGN KEY (system_prompt_id) REFERENCES system_prompts(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ agents 表建立完成")
        
        # 2. 建立 agent_knowledge_bases 表 (多對多關聯)
        print("\n[2/4] 建立 agent_knowledge_bases 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_knowledge_bases (
                id INT AUTO_INCREMENT PRIMARY KEY,
                agent_id INT NOT NULL COMMENT 'Agent ID',
                kb_id INT NOT NULL COMMENT '知識庫 ID',
                priority INT DEFAULT 0 COMMENT '優先順序 (數字越小優先級越高)',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_agent_kb (agent_id, kb_id),
                INDEX idx_agent_id (agent_id),
                INDEX idx_kb_id (kb_id),
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ agent_knowledge_bases 表建立完成")
        
        # 3. 建立 agent_mcp_tools 表 (多對多關聯)
        print("\n[3/4] 建立 agent_mcp_tools 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_mcp_tools (
                id INT AUTO_INCREMENT PRIMARY KEY,
                agent_id INT NOT NULL COMMENT 'Agent ID',
                mcp_server_name VARCHAR(255) NOT NULL COMMENT 'MCP Server 名稱',
                is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否啟用',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_agent_tool (agent_id, mcp_server_name),
                INDEX idx_agent_id (agent_id),
                INDEX idx_server_name (mcp_server_name),
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ agent_mcp_tools 表建立完成")
        
        # 4. 修改 conversations 表 - 新增 agent_id 欄位
        print("\n[4/4] 修改 conversations 表...")
        
        # 檢查 agent_id 欄位是否存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'conversations' 
            AND COLUMN_NAME = 'agent_id'
        """, (DB_CONFIG['database'],))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE conversations 
                ADD COLUMN agent_id INT AFTER kb_id,
                ADD INDEX idx_agent_id (agent_id)
            """)
            print("✓ 新增 agent_id 欄位")
            
            # 新增外鍵約束
            cursor.execute("""
                ALTER TABLE conversations 
                ADD CONSTRAINT fk_agent 
                FOREIGN KEY (agent_id) REFERENCES agents(id)
                ON DELETE SET NULL
            """)
            print("✓ 新增外鍵約束")
        else:
            print("✓ agent_id 欄位已存在,跳過")
        
        connection.commit()
        
        # 顯示最終結構
        print("\n" + "="*60)
        print("資料表結構驗證:")
        print("="*60)
        
        # 顯示 agents 表結構
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'agents'
            ORDER BY ORDINAL_POSITION
        """, (DB_CONFIG['database'],))
        print("\n📋 agents 表:")
        for row in cursor.fetchall():
            comment = f" -- {row[2]}" if row[2] else ""
            print(f"  - {row[0]}: {row[1]}{comment}")
        
        # 顯示 agent_knowledge_bases 表結構
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'agent_knowledge_bases'
            ORDER BY ORDINAL_POSITION
        """, (DB_CONFIG['database'],))
        print("\n📋 agent_knowledge_bases 表:")
        for row in cursor.fetchall():
            comment = f" -- {row[2]}" if row[2] else ""
            print(f"  - {row[0]}: {row[1]}{comment}")
        
        # 顯示 agent_mcp_tools 表結構
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'agent_mcp_tools'
            ORDER BY ORDINAL_POSITION
        """, (DB_CONFIG['database'],))
        print("\n📋 agent_mcp_tools 表:")
        for row in cursor.fetchall():
            comment = f" -- {row[2]}" if row[2] else ""
            print(f"  - {row[0]}: {row[1]}{comment}")
        
        print("\n" + "="*60)
        print("✅ Agent 資料庫初始化完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 資料庫初始化失敗: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    print("="*60)
    print("開始 Agent 資料庫初始化...")
    print("="*60)
    init_agents_tables()
