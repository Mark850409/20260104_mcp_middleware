"""
清理 LINE 對話記錄
刪除所有 LINE 來源的對話和訊息,以便重新開始測試
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


def clean_line_conversations():
    """清理所有 LINE 對話記錄"""
    try:
        # 連接資料庫
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("正在清理 LINE 對話記錄...")
        
        # 1. 取得所有 LINE 對話的 ID
        cursor.execute("""
            SELECT id FROM conversations 
            WHERE source = 'line'
        """)
        conversation_ids = [row[0] for row in cursor.fetchall()]
        
        if not conversation_ids:
            print("✓ 沒有找到 LINE 對話記錄")
            return
        
        print(f"找到 {len(conversation_ids)} 個 LINE 對話")
        
        # 2. 刪除這些對話的所有訊息
        for conv_id in conversation_ids:
            cursor.execute("""
                DELETE FROM messages 
                WHERE conversation_id = %s
            """, (conv_id,))
        
        deleted_messages = cursor.rowcount
        print(f"✓ 刪除了 {deleted_messages} 則訊息")
        
        # 3. 刪除對話記錄
        cursor.execute("""
            DELETE FROM conversations 
            WHERE source = 'line'
        """)
        
        deleted_conversations = cursor.rowcount
        print(f"✓ 刪除了 {deleted_conversations} 個對話")
        
        connection.commit()
        
        print("\n✅ LINE 對話記錄清理完成!")
        print("現在可以重新測試 LINE BOT 了")
        
    except Exception as e:
        print(f"\n❌ 清理失敗: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


def clean_tool_messages():
    """清理所有對話中的工具相關訊息"""
    try:
        # 連接資料庫
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("正在清理工具相關訊息...")
        
        # 1. 刪除所有 tool 角色的訊息
        cursor.execute("""
            DELETE FROM messages 
            WHERE role = 'tool'
        """)
        deleted_tool = cursor.rowcount
        print(f"✓ 刪除了 {deleted_tool} 則 tool 訊息")
        
        # 2. 刪除所有包含 tool_calls 的 assistant 訊息
        cursor.execute("""
            DELETE FROM messages 
            WHERE role = 'assistant' 
            AND tool_calls IS NOT NULL 
            AND tool_calls != ''
        """)
        deleted_tool_calls = cursor.rowcount
        print(f"✓ 刪除了 {deleted_tool_calls} 則包含 tool_calls 的訊息")
        
        connection.commit()
        
        print("\n✅ 工具相關訊息清理完成!")
        
    except Exception as e:
        print(f"\n❌ 清理失敗: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    print("="*60)
    print("清理 LINE 對話記錄")
    print("="*60)
    
    print("\n請選擇清理選項:")
    print("1. 清理所有 LINE 對話記錄(包含訊息)")
    print("2. 只清理工具相關訊息(保留對話)")
    print("3. 兩者都清理")
    
    choice = input("\n請輸入選項 (1/2/3): ")
    
    if choice == '1':
        confirm = input("\n確定要刪除所有 LINE 對話記錄嗎? (yes/no): ")
        if confirm.lower() == 'yes':
            clean_line_conversations()
        else:
            print("已取消")
    elif choice == '2':
        confirm = input("\n確定要刪除所有工具相關訊息嗎? (yes/no): ")
        if confirm.lower() == 'yes':
            clean_tool_messages()
        else:
            print("已取消")
    elif choice == '3':
        confirm = input("\n確定要刪除所有 LINE 對話記錄和工具訊息嗎? (yes/no): ")
        if confirm.lower() == 'yes':
            clean_tool_messages()
            clean_line_conversations()
        else:
            print("已取消")
    else:
        print("無效的選項")
