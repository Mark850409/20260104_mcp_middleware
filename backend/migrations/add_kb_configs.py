#!/usr/bin/env python3
"""
知識庫配置表遷移腳本
為每個知識庫添加可配置的向量化處理參數
"""
import pymysql
import os
import sys

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}

def run_migration():
    """執行資料庫遷移"""
    try:
        print("=" * 60)
        print("知識庫配置表遷移")
        print("=" * 60)
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 1. 檢查 kb_configs 表是否存在
        print("\n[1/3] 檢查 kb_configs 表...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'kb_configs'
        """, (DB_CONFIG['database'],))
        
        if cursor.fetchone()[0] == 0:
            print("創建 kb_configs 表...")
            cursor.execute("""
                CREATE TABLE kb_configs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    kb_id INT NOT NULL,
                    
                    -- 切分配置
                    chunk_strategy VARCHAR(50) DEFAULT 'character' COMMENT '切分策略: character, token, semantic, recursive',
                    chunk_size INT DEFAULT 500 COMMENT 'Chunk 大小',
                    chunk_overlap INT DEFAULT 50 COMMENT 'Chunk 重疊大小',
                    
                    -- Embedding 配置
                    embedding_provider VARCHAR(50) DEFAULT 'openai' COMMENT 'Embedding 提供者: openai, google, local',
                    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small' COMMENT 'Embedding 模型名稱',
                    embedding_dimension INT DEFAULT 1536 COMMENT 'Embedding 維度',
                    
                    -- 索引配置
                    index_type VARCHAR(50) DEFAULT 'flat' COMMENT '索引類型: flat, ivf, hnsw',
                    index_params JSON COMMENT '索引特定參數',
                    
                    -- 檢索配置
                    retrieval_top_k INT DEFAULT 3 COMMENT '檢索返回數量',
                    similarity_threshold FLOAT DEFAULT 0.0 COMMENT '相似度閾值',
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                    UNIQUE KEY uk_kb_id (kb_id),
                    INDEX idx_chunk_strategy (chunk_strategy),
                    INDEX idx_embedding_provider (embedding_provider)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='知識庫向量化配置表'
            """)
            connection.commit()
            print("✓ kb_configs 表創建成功")
        else:
            print("✓ kb_configs 表已存在,跳過")
        
        # 2. 為現有知識庫創建預設配置
        print("\n[2/3] 為現有知識庫創建預設配置...")
        cursor.execute("""
            SELECT id FROM knowledge_bases 
            WHERE id NOT IN (SELECT kb_id FROM kb_configs)
        """)
        existing_kbs = cursor.fetchall()
        
        if existing_kbs:
            print(f"發現 {len(existing_kbs)} 個知識庫需要配置...")
            for (kb_id,) in existing_kbs:
                cursor.execute("""
                    INSERT INTO kb_configs (kb_id) VALUES (%s)
                """, (kb_id,))
                print(f"  ✓ 為知識庫 {kb_id} 創建預設配置")
            connection.commit()
            print(f"✓ 成功為 {len(existing_kbs)} 個知識庫創建配置")
        else:
            print("✓ 所有知識庫都已有配置")
        
        # 3. 驗證遷移結果
        print("\n[3/3] 驗證遷移結果...")
        cursor.execute("SELECT COUNT(*) FROM kb_configs")
        config_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM knowledge_bases")
        kb_count = cursor.fetchone()[0]
        
        print(f"  知識庫數量: {kb_count}")
        print(f"  配置數量: {config_count}")
        
        if config_count == kb_count:
            print("✓ 驗證成功:所有知識庫都有配置")
        else:
            print(f"⚠ 警告:配置數量({config_count})與知識庫數量({kb_count})不符")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 60)
        print("✓ 遷移完成!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n✗ 遷移失敗: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(run_migration())
