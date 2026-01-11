"""
測試 LINE BOT 知識庫綁定功能
"""
import pymysql
import os

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3307')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}

def test_line_bot_kb_binding():
    """測試 LINE BOT 知識庫綁定"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        print("=" * 60)
        print("測試 LINE BOT 知識庫綁定功能")
        print("=" * 60)
        
        # 1. 檢查 LINE BOT 設定
        print("\n[1] 檢查 LINE BOT 設定...")
        cursor.execute("""
            SELECT id, bot_name, kb_id, is_active 
            FROM line_bot_configs 
            WHERE is_active = TRUE
        """)
        bot_config = cursor.fetchone()
        
        if not bot_config:
            print("❌ 找不到啟用的 LINE BOT 設定")
            return
        
        print(f"✓ LINE BOT: {bot_config['bot_name']}")
        print(f"  - KB ID: {bot_config['kb_id']}")
        
        if not bot_config['kb_id']:
            print("⚠️  警告: LINE BOT 沒有綁定知識庫")
            return
        
        # 2. 檢查知識庫是否存在
        print(f"\n[2] 檢查知識庫 ID={bot_config['kb_id']}...")
        cursor.execute("""
            SELECT id, name, description 
            FROM knowledge_bases 
            WHERE id = %s
        """, (bot_config['kb_id'],))
        kb = cursor.fetchone()
        
        if not kb:
            print(f"❌ 找不到知識庫 ID={bot_config['kb_id']}")
            return
        
        print(f"✓ 知識庫: {kb['name']}")
        print(f"  - 描述: {kb['description'] or '無'}")
        
        # 3. 檢查 LINE 對話
        print(f"\n[3] 檢查 LINE 對話...")
        cursor.execute("""
            SELECT id, title, kb_id, line_user_id, created_at 
            FROM conversations 
            WHERE source = 'line'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        conversations = cursor.fetchall()
        
        if not conversations:
            print("ℹ️  尚無 LINE 對話")
        else:
            print(f"找到 {len(conversations)} 個 LINE 對話:")
            for conv in conversations:
                kb_status = "✓" if conv['kb_id'] == bot_config['kb_id'] else "✗"
                print(f"  {kb_status} 對話 #{conv['id']}: {conv['title']}")
                print(f"     - KB ID: {conv['kb_id']} (預期: {bot_config['kb_id']})")
                print(f"     - 建立時間: {conv['created_at']}")
        
        # 4. 檢查知識庫檔案
        print(f"\n[4] 檢查知識庫檔案...")
        cursor.execute("""
            SELECT COUNT(*) as file_count 
            FROM kb_files 
            WHERE kb_id = %s AND status = 'completed'
        """, (bot_config['kb_id'],))
        result = cursor.fetchone()
        file_count = result['file_count'] if result else 0
        
        print(f"✓ 已處理檔案數: {file_count}")
        
        if file_count == 0:
            print("⚠️  警告: 知識庫中沒有已處理的檔案")
        
        print("\n" + "=" * 60)
        print("測試完成!")
        print("=" * 60)
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    test_line_bot_kb_binding()
