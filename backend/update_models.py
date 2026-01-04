"""
更新資料庫中舊的模型名稱
將 gemini-pro 更新為 gemini-1.5-flash
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


def update_model_names():
    """更新資料庫中的模型名稱"""
    try:
        # 連接資料庫
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("正在更新模型名稱...")
        
        # 更新 gemini-pro 為 gemini-1.5-flash
        cursor.execute("""
            UPDATE conversations
            SET model_name = 'gemini-1.5-flash'
            WHERE model_name = 'gemini-pro'
        """)
        
        updated_count = cursor.rowcount
        print(f"✓ 更新了 {updated_count} 個對話的 Gemini 模型名稱")
        
        # 更新 gemini-pro-vision 為 gemini-1.5-pro
        cursor.execute("""
            UPDATE conversations
            SET model_name = 'gemini-1.5-pro'
            WHERE model_name = 'gemini-pro-vision'
        """)
        
        updated_count = cursor.rowcount
        print(f"✓ 更新了 {updated_count} 個對話的 Gemini Vision 模型名稱")
        
        # 更新 gpt-4-turbo-preview 為 gpt-4-turbo
        cursor.execute("""
            UPDATE conversations
            SET model_name = 'gpt-4-turbo'
            WHERE model_name = 'gpt-4-turbo-preview'
        """)
        
        updated_count = cursor.rowcount
        print(f"✓ 更新了 {updated_count} 個對話的 GPT-4 Turbo 模型名稱")
        
        connection.commit()
        print("\n模型名稱更新完成!")
        
    except Exception as e:
        print(f"更新失敗: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    print("開始更新模型名稱...")
    update_model_names()
