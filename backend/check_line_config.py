"""
檢查 LINE Bot 配置的腳本
用於診斷 401 認證錯誤
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

def check_line_config():
    """檢查 LINE Bot 配置"""
    try:
        print("=" * 60)
        print("檢查 LINE Bot 配置")
        print("=" * 60)
        
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 查詢啟用的 LINE Bot 配置
        cursor.execute("""
            SELECT id, bot_name, 
                   LENGTH(channel_access_token) as token_length,
                   SUBSTRING(channel_access_token, 1, 10) as token_prefix,
                   LENGTH(channel_secret) as secret_length,
                   is_active
            FROM line_bot_configs 
            WHERE is_active = TRUE
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        config = cursor.fetchone()
        
        if config:
            print(f"\n找到啟用的 LINE Bot 配置:")
            print(f"  ID: {config['id']}")
            print(f"  Bot 名稱: {config['bot_name']}")
            print(f"  Token 長度: {config['token_length']}")
            print(f"  Token 前10字: {config['token_prefix']}")
            print(f"  Secret 長度: {config['secret_length']}")
            print(f"  是否啟用: {config['is_active']}")
            
            # 檢查 Token 格式
            if config['token_length'] == 0:
                print("\n❌ 錯誤: Channel Access Token 為空！")
            elif config['token_length'] < 100:
                print(f"\n⚠️  警告: Token 長度 ({config['token_length']}) 似乎太短")
            else:
                print(f"\n✓ Token 長度正常")
            
            # 檢查 Secret 格式
            if config['secret_length'] == 0:
                print("❌ 錯誤: Channel Secret 為空！")
            elif config['secret_length'] != 32:
                print(f"⚠️  警告: Secret 長度 ({config['secret_length']}) 不是標準的 32 字元")
            else:
                print("✓ Secret 長度正常")
                
        else:
            print("\n❌ 找不到啟用的 LINE Bot 配置")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ 檢查失敗: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_line_config()
