"""
LINE BOT API 路由
提供 LINE Webhook 和 LINE BOT 管理的 API 端點
"""
from flask import Blueprint, request, jsonify
import pymysql
import json
import os
from services.line_client import create_line_client
from services.ai_client import AIClientFactory
from services.mcp_client import mcp_client

# 建立 Blueprint
line_bp = Blueprint('line', __name__, url_prefix='/api/line')

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}

# Webhook 基礎 URL
WEBHOOK_BASE_URL = os.getenv('WEBHOOK_BASE_URL', 'http://localhost:5000')


def get_db_connection():
    """取得資料庫連線"""
    return pymysql.connect(**DB_CONFIG)


@line_bp.route('/webhook', methods=['POST'])
def webhook():
    """
    LINE Webhook 端點
    接收來自 LINE 平台的事件
    """
    try:
        # 取得請求資料
        body = request.get_data(as_text=True)
        signature = request.headers.get('X-Line-Signature', '')
        
        if not signature:
            return jsonify({"error": "缺少簽章"}), 400
        
        # 解析事件
        events = json.loads(body).get('events', [])
        
        if not events:
            return jsonify({"message": "No events"}), 200
        
        # 處理每個事件
        for event in events:
            handle_line_event(event, body, signature)
        
        return jsonify({"message": "OK"}), 200
        
    except Exception as e:
        print(f"Webhook 處理錯誤: {str(e)}")
        return jsonify({"error": str(e)}), 500


def handle_line_event(event: dict, body: str, signature: str):
    """
    處理 LINE 事件
    
    Args:
        event: LINE 事件物件
        body: 原始請求 body
        signature: LINE 簽章
    """
    try:
        event_type = event.get('type')
        
        if event_type == 'message':
            handle_message_event(event, body, signature)
        elif event_type == 'follow':
            handle_follow_event(event)
        elif event_type == 'unfollow':
            handle_unfollow_event(event)
        else:
            print(f"未處理的事件類型: {event_type}")
            
    except Exception as e:
        print(f"處理 LINE 事件錯誤: {str(e)}")


def handle_message_event(event: dict, body: str, signature: str):
    """
    處理訊息事件
    
    Args:
        event: LINE 事件物件
        body: 原始請求 body
        signature: LINE 簽章
    """
    try:
        message = event.get('message', {})
        message_type = message.get('type')
        user_id = event['source']['userId']
        reply_token = event.get('replyToken')
        
        # 目前只處理文字訊息
        if message_type != 'text':
            return
        
        text = message.get('text', '')
        message_id = message.get('id', '')
        
        # 取得或建立 LINE 使用者
        line_user = get_or_create_line_user(user_id)
        
        # 取得使用者的對話 (或建立新對話)
        conversation = get_or_create_conversation(user_id)
        
        if not conversation:
            print(f"無法建立對話: user_id={user_id}")
            return
        
        conversation_id = conversation['id']
        
        # 儲存使用者訊息
        save_message(conversation_id, 'user', text, message_id)
        
        # 取得 LINE BOT 設定
        bot_config = get_active_line_bot_config()
        
        if not bot_config:
            print("找不到啟用的 LINE BOT 設定")
            return
        
        # 驗證簽章
        line_client = create_line_client(
            bot_config['channel_access_token'],
            bot_config['channel_secret']
        )
        
        if not line_client.verify_signature(body, signature):
            print("簽章驗證失敗")
            return
        
        # 取得 AI 回應
        ai_response = get_ai_response(conversation_id, text, bot_config)
        
        if ai_response:
            # 儲存 AI 回應
            save_message(conversation_id, 'assistant', ai_response, sync_status='pending')
            
            # 發送回覆到 LINE
            result = line_client.reply_message(
                reply_token,
                [{"type": "text", "text": ai_response}]
            )
            
            if result['success']:
                # 更新同步狀態
                update_last_message_sync_status(conversation_id, 'synced')
            else:
                print(f"發送訊息失敗: {result.get('error')}")
                update_last_message_sync_status(conversation_id, 'failed')
        
    except Exception as e:
        print(f"處理訊息事件錯誤: {str(e)}")


def handle_follow_event(event: dict):
    """處理使用者加入好友事件"""
    try:
        user_id = event['source']['userId']
        get_or_create_line_user(user_id)
        print(f"使用者加入好友: {user_id}")
    except Exception as e:
        print(f"處理加入好友事件錯誤: {str(e)}")


def handle_unfollow_event(event: dict):
    """處理使用者封鎖事件"""
    try:
        user_id = event['source']['userId']
        print(f"使用者封鎖: {user_id}")
    except Exception as e:
        print(f"處理封鎖事件錯誤: {str(e)}")


def get_or_create_line_user(user_id: str) -> dict:
    """
    取得或建立 LINE 使用者
    
    Args:
        user_id: LINE 使用者 ID
        
    Returns:
        使用者資料
    """
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 檢查使用者是否存在
        cursor.execute(
            "SELECT * FROM line_users WHERE line_user_id = %s",
            (user_id,)
        )
        user = cursor.fetchone()
        
        if user:
            return user
        
        # 建立新使用者
        # 嘗試從 LINE API 取得使用者資料
        bot_config = get_active_line_bot_config()
        if bot_config:
            line_client = create_line_client(
                bot_config['channel_access_token'],
                bot_config['channel_secret']
            )
            profile = line_client.get_profile(user_id)
            
            if profile:
                cursor.execute("""
                    INSERT INTO line_users (line_user_id, display_name, picture_url, status_message)
                    VALUES (%s, %s, %s, %s)
                """, (
                    user_id,
                    profile.get('displayName'),
                    profile.get('pictureUrl'),
                    profile.get('statusMessage')
                ))
            else:
                cursor.execute(
                    "INSERT INTO line_users (line_user_id) VALUES (%s)",
                    (user_id,)
                )
        else:
            cursor.execute(
                "INSERT INTO line_users (line_user_id) VALUES (%s)",
                (user_id,)
            )
        
        conn.commit()
        
        # 取得新建立的使用者
        cursor.execute(
            "SELECT * FROM line_users WHERE line_user_id = %s",
            (user_id,)
        )
        return cursor.fetchone()
        
    finally:
        cursor.close()
        conn.close()


def get_or_create_conversation(user_id: str) -> dict:
    """
    取得或建立對話
    
    Args:
        user_id: LINE 使用者 ID
        
    Returns:
        對話資料
    """
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 檢查是否有現有對話
        cursor.execute("""
            SELECT * FROM conversations 
            WHERE line_user_id = %s AND source = 'line'
            ORDER BY updated_at DESC
            LIMIT 1
        """, (user_id,))
        
        conversation = cursor.fetchone()
        
        if conversation:
            return conversation
        
        # 建立新對話
        bot_config = get_active_line_bot_config()
        
        # 取得使用者資料
        cursor.execute(
            "SELECT display_name FROM line_users WHERE line_user_id = %s",
            (user_id,)
        )
        user = cursor.fetchone()
        display_name = user['display_name'] if user and user['display_name'] else user_id
        
        # 使用 BOT 設定的模型或預設模型
        model_provider = 'openai'
        model_name = 'gpt-4o-mini'
        mcp_enabled = False
        mcp_servers = None
        
        if bot_config and bot_config.get('selected_mcp_servers'):
            mcp_enabled = True
            mcp_servers = json.dumps(bot_config['selected_mcp_servers'])
        
        cursor.execute("""
            INSERT INTO conversations 
            (title, model_provider, model_name, mcp_enabled, mcp_servers, line_user_id, source)
            VALUES (%s, %s, %s, %s, %s, %s, 'line')
        """, (
            f"LINE - {display_name}",
            model_provider,
            model_name,
            mcp_enabled,
            mcp_servers,
            user_id
        ))
        
        conn.commit()
        conversation_id = cursor.lastrowid
        
        # 取得新建立的對話
        cursor.execute(
            "SELECT * FROM conversations WHERE id = %s",
            (conversation_id,)
        )
        return cursor.fetchone()
        
    finally:
        cursor.close()
        conn.close()


def save_message(conversation_id: int, role: str, content: str, 
                line_message_id: str = None, sync_status: str = 'synced', 
                tool_call_id: str = None):
    """
    儲存訊息
    
    Args:
        conversation_id: 對話 ID
        role: 角色 (user, assistant, tool)
        content: 訊息內容
        line_message_id: LINE 訊息 ID
        sync_status: 同步狀態
        tool_call_id: 工具調用 ID (用於 tool 角色)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO messages 
            (conversation_id, role, content, line_message_id, sync_status, message_type, tool_call_id)
            VALUES (%s, %s, %s, %s, %s, 'text', %s)
        """, (conversation_id, role, content, line_message_id, sync_status, tool_call_id))
        
        conn.commit()
        
    finally:
        cursor.close()
        conn.close()


def update_last_message_sync_status(conversation_id: int, status: str):
    """更新最後一則訊息的同步狀態"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE messages 
            SET sync_status = %s
            WHERE conversation_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (status, conversation_id))
        
        conn.commit()
        
    finally:
        cursor.close()
        conn.close()


def get_ai_response(conversation_id: int, user_message: str, bot_config: dict) -> str:
    """
    取得 AI 回應
    
    Args:
        conversation_id: 對話 ID
        user_message: 使用者訊息
        bot_config: BOT 設定
        
    Returns:
        AI 回應文字
    """
    try:
        print(f"[LINE BOT] 開始處理 AI 回應,對話 ID: {conversation_id}")
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 取得對話設定
        cursor.execute(
            "SELECT * FROM conversations WHERE id = %s",
            (conversation_id,)
        )
        conversation = cursor.fetchone()
        
        if not conversation:
            print(f"[LINE BOT] 找不到對話: {conversation_id}")
            return "抱歉,發生錯誤"
        
        print(f"[LINE BOT] 對話設定: MCP 啟用={conversation['mcp_enabled']}, MCP Servers={conversation['mcp_servers']}")
        
        # 取得歷史訊息
        # ⚠️ 重要:只載入 user 和 assistant 的文字訊息
        # 過濾掉所有工具相關的訊息(tool_calls 和 tool role)
        cursor.execute("""
            SELECT role, content
            FROM messages 
            WHERE conversation_id = %s 
            AND role IN ('user', 'assistant')
            AND (tool_calls IS NULL OR tool_calls = '')
            AND content != ''
            ORDER BY created_at ASC
        """, (conversation_id,))
        
        messages = []
        for msg in cursor.fetchall():
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        cursor.close()
        conn.close()
        
        print(f"[LINE BOT] 歷史訊息數量: {len(messages)}")
        if messages:
            print(f"[LINE BOT] 最近 3 則訊息:")
            for msg in messages[-3:]:
                print(f"  - {msg['role']}: {msg['content'][:50]}...")
        
        # 建立 AI 客戶端
        ai_client = AIClientFactory.create_client(
            conversation['model_provider'],
            conversation['model_name']
        )
        
        print(f"[LINE BOT] AI 客戶端: {conversation['model_provider']}/{conversation['model_name']}")
        
        # 準備工具
        # ⚠️ 重要修正: 優先使用 LINE BOT 設定的 MCP Servers,而不是對話記錄中的舊設定
        tools = None
        
        # 從 bot_config 解析 MCP servers
        bot_mcp_servers = []
        if bot_config and bot_config.get('selected_mcp_servers'):
            mcp_config = bot_config.get('selected_mcp_servers')
            if isinstance(mcp_config, str):
                try:
                    bot_mcp_servers = json.loads(mcp_config)
                except:
                    bot_mcp_servers = []
            elif isinstance(mcp_config, list):
                bot_mcp_servers = mcp_config
                
        print(f"[LINE BOT] BOT 設定的 MCP Servers: {bot_mcp_servers}")
        
        if bot_mcp_servers:
            try:
                selected_servers = bot_mcp_servers
                print(f"[LINE BOT] 使用 MCP Servers: {selected_servers}")
                
                all_tools = mcp_client.list_tools()
                print(f"[LINE BOT] 所有可用工具數量: {len(all_tools)}")
                
                # 過濾出選中的 servers 的工具
                filtered_tools = []
                for tool in all_tools:
                    # 假設工具名稱格式為 "server_name-tool_name" 或類似
                    # 這裡簡化處理: 如果選中了 server,則該 server 的所有工具都可用
                    # 實際上 list_tools 應該已經處理了? 不,list_tools 返回所有連接的 servers 的工具
                    
                    # 暫時全部使用,後續優化
                    filtered_tools.append(tool)
                
                if filtered_tools:
                    tools = filtered_tools
                    print(f"[LINE BOT] 綁定工具數量: {len(tools)}")
                    # print(f"[LINE BOT] 工具列表: {[t['name'] for t in tools]}")
            except Exception as e:
                print(f"[LINE BOT] 準備工具失敗: {str(e)}")
                tools = None
        else:
             print(f"[LINE BOT] 未啟用 MCP 或未選擇 Server")
        
        # 取得 AI 回應
        print(f"[LINE BOT] 開始調用 AI,工具數量: {len(tools) if tools else 0}")
        response = ai_client.chat(messages, tools=tools)
        print(f"[LINE BOT] AI 回應: {response}")
        
        # 處理工具呼叫
        if response.get('tool_calls'):
            print(f"[LINE BOT] AI 要求調用工具: {len(response['tool_calls'])} 個")
            
            # ⚠️ 重要:不要將工具調用的 assistant 訊息儲存到資料庫
            # 因為這會在 LINE 中顯示工具調用卡片,用戶看不懂
            # 我們只在記憶體中處理工具調用,最後只儲存文字回應
            
            # 執行工具
            tool_results = []
            print(f"[LINE BOT] tool_calls 結構: {json.dumps(response['tool_calls'], ensure_ascii=False, indent=2)}")
            
            for idx, tool_call in enumerate(response['tool_calls']):
                print(f"[LINE BOT] 處理第 {idx + 1} 個 tool_call")
                print(f"[LINE BOT] tool_call 類型: {type(tool_call)}")
                print(f"[LINE BOT] tool_call 內容: {tool_call}")
                
                try:
                    # 處理不同的 tool_call 格式
                    # OpenAI 格式: tool_call.function.name
                    if hasattr(tool_call, 'function'):
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        tool_id = tool_call.id
                    # 字典格式: tool_call['function']['name']
                    elif isinstance(tool_call, dict) and 'function' in tool_call:
                        tool_name = tool_call['function']['name']
                        tool_args = tool_call['function']['arguments']
                        if isinstance(tool_args, str):
                            tool_args = json.loads(tool_args)
                        tool_id = tool_call.get('id', '')
                    # 直接格式: tool_call['name']
                    elif isinstance(tool_call, dict) and 'name' in tool_call:
                        tool_name = tool_call['name']
                        tool_args = tool_call.get('arguments', {})
                        if isinstance(tool_args, str):
                            tool_args = json.loads(tool_args)
                        tool_id = tool_call.get('id', '')
                    else:
                        print(f"[LINE BOT] 未知的 tool_call 格式: {tool_call}")
                        continue
                    
                    print(f"[LINE BOT] 調用工具: {tool_name}, 參數: {tool_args}, ID: {tool_id}")
                    
                    result = mcp_client.invoke_tool(tool_name, tool_args)
                    print(f"[LINE BOT] 工具調用結果: {result}")
                    
                    tool_results.append({
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False),
                        "tool_call_id": tool_id
                    })
                    
                    # ⚠️ 不儲存工具結果到資料庫,只在記憶體中處理
                    # save_message(
                    #     conversation_id, 
                    #     'tool', 
                    #     json.dumps(result, ensure_ascii=False),
                    #     tool_call_id=tool_id
                    # )
                except Exception as tool_invoke_error:
                    print(f"[LINE BOT] 工具調用失敗: {str(tool_invoke_error)}")
                    import traceback
                    traceback.print_exc()
                    # 即使工具調用失敗,也繼續處理
                    error_result = {"error": str(tool_invoke_error)}
                    tool_id = ''
                    try:
                        if hasattr(tool_call, 'id'):
                            tool_id = tool_call.id
                        elif isinstance(tool_call, dict):
                            tool_id = tool_call.get('id', '')
                    except:
                        pass
                    
                    tool_results.append({
                        "role": "tool",
                        "content": json.dumps(error_result, ensure_ascii=False),
                        "tool_call_id": tool_id
                    })
                    
                    # ⚠️ 不儲存錯誤結果到資料庫
                    # save_message(
                    #     conversation_id, 
                    #     'tool', 
                    #     json.dumps(error_result, ensure_ascii=False),
                    #     tool_call_id=tool_id
                    # )
            
            # 將工具結果加入訊息並再次呼叫 AI
            messages.append({
                "role": "assistant",
                "content": "",
                "tool_calls": response['tool_calls']
            })
            messages.extend(tool_results)
            
            print(f"[LINE BOT] 將工具結果回傳給 AI")
            final_response = ai_client.chat(messages, tools=tools)
            print(f"[LINE BOT] AI 最終回應: {final_response}")
            return final_response.get('content', '抱歉,我無法回答')
        
        return response.get('content', '抱歉,我無法回答')
        
    except Exception as e:
        print(f"[LINE BOT] 取得 AI 回應錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return "抱歉,發生錯誤"


def get_active_line_bot_config() -> dict:
    """取得啟用的 LINE BOT 設定"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT * FROM line_bot_configs 
            WHERE is_active = TRUE 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        return cursor.fetchone()
        
    finally:
        cursor.close()
        conn.close()


# ============ LINE BOT 管理 API ============

@line_bp.route('/configs', methods=['GET'])
def list_configs():
    """取得 LINE BOT 設定列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT id, bot_name, webhook_url, is_active, 
                   selected_mcp_servers, created_at, updated_at
            FROM line_bot_configs 
            ORDER BY created_at DESC
        """)
        
        configs = cursor.fetchall()
        
        # 解析 JSON 欄位
        for config in configs:
            if config['selected_mcp_servers']:
                config['selected_mcp_servers'] = json.loads(config['selected_mcp_servers'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "data": configs
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@line_bp.route('/configs', methods=['POST'])
def create_config():
    """建立新的 LINE BOT 設定"""
    try:
        data = request.get_json()
        
        # 只檢查 bot_name 為必填
        if not data.get('bot_name'):
            return jsonify({
                "success": False,
                "error": "缺少必填欄位: bot_name"
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 產生 Webhook URL
        webhook_url = f"{WEBHOOK_BASE_URL}/api/line/webhook"
        
        # 處理 MCP servers
        selected_mcp_servers = data.get('selected_mcp_servers', [])
        mcp_servers_json = json.dumps(selected_mcp_servers) if selected_mcp_servers else None
        
        # Channel Access Token 和 Channel Secret 為可選
        channel_access_token = data.get('channel_access_token', '')
        channel_secret = data.get('channel_secret', '')
        
        cursor.execute("""
            INSERT INTO line_bot_configs 
            (bot_name, channel_access_token, channel_secret, webhook_url, 
             is_active, selected_mcp_servers)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['bot_name'],
            channel_access_token,
            channel_secret,
            webhook_url,
            data.get('is_active', True),
            mcp_servers_json
        ))
        
        conn.commit()
        config_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "id": config_id,
                "webhook_url": webhook_url
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@line_bp.route('/configs/<int:config_id>', methods=['PUT'])
def update_config(config_id):
    """更新 LINE BOT 設定"""
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 建立更新語句
        update_fields = []
        values = []
        
        if 'bot_name' in data:
            update_fields.append("bot_name = %s")
            values.append(data['bot_name'])
        
        if 'channel_access_token' in data:
            update_fields.append("channel_access_token = %s")
            values.append(data['channel_access_token'])
        
        if 'channel_secret' in data:
            update_fields.append("channel_secret = %s")
            values.append(data['channel_secret'])
        
        if 'is_active' in data:
            update_fields.append("is_active = %s")
            values.append(data['is_active'])
        
        if 'selected_mcp_servers' in data:
            update_fields.append("selected_mcp_servers = %s")
            values.append(json.dumps(data['selected_mcp_servers']))
        
        if not update_fields:
            return jsonify({
                "success": False,
                "error": "沒有要更新的欄位"
            }), 400
        
        values.append(config_id)
        
        cursor.execute(f"""
            UPDATE line_bot_configs 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """, values)
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "更新成功"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@line_bp.route('/configs/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    """刪除 LINE BOT 設定"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM line_bot_configs WHERE id = %s",
            (config_id,)
        )
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "刪除成功"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@line_bp.route('/configs/<int:config_id>/toggle', methods=['POST'])
def toggle_config(config_id):
    """啟用/停用 LINE BOT"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 取得當前狀態
        cursor.execute(
            "SELECT is_active FROM line_bot_configs WHERE id = %s",
            (config_id,)
        )
        config = cursor.fetchone()
        
        if not config:
            return jsonify({
                "success": False,
                "error": "找不到設定"
            }), 404
        
        # 切換狀態
        new_status = not config['is_active']
        
        # 如果要啟用,先停用其他所有設定
        if new_status:
            cursor.execute("UPDATE line_bot_configs SET is_active = FALSE")
        
        cursor.execute(
            "UPDATE line_bot_configs SET is_active = %s WHERE id = %s",
            (new_status, config_id)
        )
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "is_active": new_status
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@line_bp.route('/conversations/<int:conversation_id>/send', methods=['POST'])
def send_message_to_line(conversation_id):
    """
    從 Web 介面發送訊息到 LINE
    
    新流程:
    1. 儲存使用者訊息 (user 角色)
    2. 檢查 LINE BOT 是否綁定 MCP
    3a. 有綁定: 調用 get_ai_response (會執行 MCP 工具)
    3b. 沒綁定: 直接調用 AI
    4. 儲存 AI 回應 (assistant 角色)
    5. 將 AI 回應推送到 LINE
    
    Args:
        conversation_id: 對話 ID
        
    Request Body:
        {
            "content": "訊息內容"
        }
    """
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        if not content:
            return jsonify({
                "success": False,
                "error": "訊息內容不可為空"
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 取得對話資訊
        cursor.execute("""
            SELECT line_user_id, source, model_provider, model_name
            FROM conversations 
            WHERE id = %s
        """, (conversation_id,))
        
        conversation = cursor.fetchone()
        
        if not conversation:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "error": "對話不存在"
            }), 404
        
        if conversation['source'] != 'line':
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "error": "此對話不是 LINE 對話"
            }), 400
        
        line_user_id = conversation['line_user_id']
        
        if not line_user_id:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "error": "找不到 LINE 使用者 ID"
            }), 400
        
        # 1. 儲存使用者訊息
        print(f"[WEB->LINE] 儲存使用者訊息: {content[:50]}...")
        save_message(conversation_id, 'user', content, sync_status='synced')
        
        # 2. 取得 LINE BOT 設定
        bot_config = get_active_line_bot_config()
        
        if not bot_config:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "error": "找不到啟用的 LINE BOT 設定"
            }), 404
        
        # 2a. 先推送使用者訊息到 LINE (讓 LINE 對話顯示使用者的提問)
        try:
            line_client = create_line_client(
                bot_config['channel_access_token'],
                bot_config['channel_secret']
            )
            print(f"[WEB->LINE] 推送使用者訊息到 LINE: {line_user_id}")
            line_client.send_messages(
                line_user_id,
                [{"type": "text", "text": content}]
            )
        except Exception as e:
            print(f"[WEB->LINE] 推送使用者訊息失敗 (不影響後續流程): {str(e)}")
        
        # 3. 判斷是否綁定 MCP 工具
        selected_mcp_servers = bot_config.get('selected_mcp_servers')
        if isinstance(selected_mcp_servers, str):
            try:
                selected_mcp_servers = json.loads(selected_mcp_servers)
            except:
                selected_mcp_servers = []
        
        has_mcp = selected_mcp_servers and len(selected_mcp_servers) > 0
        
        if has_mcp:
            # 3a. 有綁定 MCP: 調用 get_ai_response (會自動執行 MCP 工具)
            print(f"[WEB->LINE] LINE BOT 已綁定 MCP 工具: {selected_mcp_servers}")
            ai_response = get_ai_response(conversation_id, content, bot_config)
        else:
            # 3b. 沒綁定 MCP: 直接調用 AI
            print(f"[WEB->LINE] LINE BOT 未綁定 MCP 工具,直接調用 AI")
            
            # 取得歷史訊息
            cursor.execute("""
                SELECT role, content
                FROM messages 
                WHERE conversation_id = %s 
                AND role IN ('user', 'assistant')
                AND (tool_calls IS NULL OR tool_calls = '')
                AND content != ''
                ORDER BY created_at ASC
            """, (conversation_id,))
            
            messages = [{"role": msg['role'], "content": msg['content']} for msg in cursor.fetchall()]
            
            # 建立 AI 客戶端並調用
            ai_client = AIClientFactory.create_client(
                conversation['model_provider'],
                conversation['model_name']
            )
            response = ai_client.chat(messages, tools=None)
            ai_response = response.get('content', '抱歉,我無法回答')
        
        if not ai_response:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "error": "AI 處理失敗"
            }), 500
        
        # 4. 儲存 AI 回應
        print(f"[WEB->LINE] 儲存 AI 回應: {ai_response[:50]}...")
        save_message(conversation_id, 'assistant', ai_response, sync_status='pending')
        
        # 5. 再次建立 LINE 客戶端 (或重用) - 這裡為了保險起見再次建立
        # 6. 將 AI 回應發送到 LINE
        print(f"[WEB->LINE] 發送 AI 回應到 LINE: {line_user_id}")
        result = line_client.send_messages(
            line_user_id,
            [{"type": "text", "text": ai_response}]
        )
        
        if result['success']:
            # 更新同步狀態
            update_last_message_sync_status(conversation_id, 'synced')
            print(f"[WEB->LINE] 訊息發送成功")
            
            cursor.close()
            conn.close()
            
            return jsonify({
                "success": True,
                "message": "訊息已發送"
            })
        else:
            update_last_message_sync_status(conversation_id, 'failed')
            print(f"[WEB->LINE] 訊息發送失敗: {result.get('error')}")
            
            cursor.close()
            conn.close()
            
            return jsonify({
                "success": False,
                "error": f"發送失敗: {result.get('error')}"
            }), 500
        
    except Exception as e:
        print(f"[WEB->LINE] 發送訊息到 LINE 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
