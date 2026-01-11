"""
Chat API 路由
提供 Chatbot 相關的 API 端點
"""
from flask import Blueprint, request, jsonify
import pymysql
import json
import os
from services.ai_client import AIClientFactory
from services.mcp_client import mcp_client
from services.rag_service import rag_service

# 建立 Blueprint
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4'
}


def get_db_connection():
    """取得資料庫連線"""
    return pymysql.connect(**DB_CONFIG)


@chat_bp.route('/conversations', methods=['POST'])
def create_conversation():
    """建立新對話"""
    try:
        data = request.get_json()
        title = data.get('title', '新對話')
        model_provider = data.get('model_provider', 'openai')
        model_name = data.get('model_name', 'gpt-4')
        mcp_enabled = data.get('mcp_enabled', False)
        mcp_servers = data.get('mcp_servers', [])  # 新增:支援多選 MCP servers
        system_prompt_id = data.get('system_prompt_id', None)  # 新增:系統提示詞
        kb_id = data.get('kb_id', None)  # 新增:知識庫 ID
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 將 mcp_servers 轉換為 JSON 字串
        mcp_servers_json = json.dumps(mcp_servers) if mcp_servers else None
        
        cursor.execute("""
            INSERT INTO conversations (title, model_provider, model_name, mcp_enabled, mcp_servers, system_prompt_id, kb_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (title, model_provider, model_name, mcp_enabled, mcp_servers_json, system_prompt_id, kb_id))
        
        conversation_id = cursor.lastrowid
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "conversation_id": conversation_id
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@chat_bp.route('/conversations', methods=['GET'])
def list_conversations():
    """取得對話列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 取得活躍的 LINE BOT 設定 (用於同步 LINE 對話的顯示狀態)
        cursor.execute("""
            SELECT selected_mcp_servers FROM line_bot_configs 
            WHERE is_active = TRUE 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        bot_config = cursor.fetchone()
        bot_mcp_servers = []
        if bot_config and bot_config['selected_mcp_servers']:
             try:
                 config_val = bot_config['selected_mcp_servers']
                 if isinstance(config_val, str):
                     bot_mcp_servers = json.loads(config_val)
                 else:
                     bot_mcp_servers = config_val
             except:
                 bot_mcp_servers = []
        
        cursor.execute("""
            SELECT id, title, model_provider, model_name, mcp_enabled, mcp_servers, system_prompt_id, kb_id, source, line_user_id, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC
        """)
        
        conversations = cursor.fetchall()
        
        # 解析 mcp_servers JSON 並同步 LINE 設定
        for conv in conversations:
            if conv['source'] == 'line':
                #如果是 LINE 對話,強制使用 BOT 全域設定
                conv['mcp_servers'] = bot_mcp_servers
                conv['mcp_enabled'] = len(bot_mcp_servers) > 0
            elif conv['mcp_servers']:
                if isinstance(conv['mcp_servers'], str):
                    try:
                        conv['mcp_servers'] = json.loads(conv['mcp_servers'])
                    except:
                        conv['mcp_servers'] = []
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "conversations": conversations
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@chat_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """取得對話詳情(包含訊息)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 取得對話資訊
        cursor.execute("""
            SELECT id, title, model_provider, model_name, mcp_enabled, mcp_servers, system_prompt_id, kb_id, source, line_user_id, created_at, updated_at
            FROM conversations
            WHERE id = %s
        """, (conversation_id,))
        
        conversation = cursor.fetchone()
        
        if not conversation:
            return jsonify({
                "success": False,
                "error": "對話不存在"
            }), 404
            
        # 處理 MCP 設定
        if conversation['source'] == 'line':
            # 取得活躍的 LINE BOT 設定
            cursor.execute("""
                SELECT selected_mcp_servers FROM line_bot_configs 
                WHERE is_active = TRUE 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            bot_config = cursor.fetchone()
            bot_mcp_servers = []
            if bot_config and bot_config['selected_mcp_servers']:
                 try:
                     config_val = bot_config['selected_mcp_servers']
                     if isinstance(config_val, str):
                         bot_mcp_servers = json.loads(config_val)
                     else:
                         bot_mcp_servers = config_val
                 except:
                     bot_mcp_servers = []
            
            # 強制使用 BOT 全域設定
            conversation['mcp_servers'] = bot_mcp_servers
            conversation['mcp_enabled'] = len(bot_mcp_servers) > 0
            
        elif conversation['mcp_servers']:
            if isinstance(conversation['mcp_servers'], str):
                conversation['mcp_servers'] = json.loads(conversation['mcp_servers'])
        
        # 取得訊息列表
        cursor.execute("""
            SELECT id, role, content, tool_calls, created_at
            FROM messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
        """, (conversation_id,))
        
        messages = cursor.fetchall()
        
        # 解析 tool_calls JSON
        for msg in messages:
            if msg['tool_calls']:
                msg['tool_calls'] = json.loads(msg['tool_calls'])
        
        conversation['messages'] = messages
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "conversation": conversation
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@chat_bp.route('/conversations/<int:conversation_id>/messages', methods=['POST'])
def send_message(conversation_id):
    """發送訊息並取得 AI 回應"""
    try:
        data = request.get_json()
        user_message = data.get('content', '')
        
        if not user_message:
            return jsonify({
                "success": False,
                "error": "訊息內容不可為空"
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 取得對話設定
        cursor.execute("""
            SELECT model_provider, model_name, mcp_enabled, mcp_servers, system_prompt_id, kb_id
            FROM conversations
            WHERE id = %s
        """, (conversation_id,))
        
        conversation = cursor.fetchone()
        
        if not conversation:
            return jsonify({
                "success": False,
                "error": "對話不存在"
            }), 404
        
        # 儲存使用者訊息
        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content)
            VALUES (%s, %s, %s)
        """, (conversation_id, 'user', user_message))
        conn.commit()
        
        # 取得對話歷史
        cursor.execute("""
            SELECT role, content
            FROM messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
        """, (conversation_id,))
        
        history = cursor.fetchall()
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
        
        # 如果有知識庫，進行 RAG 檢索
        if conversation['kb_id']:
            print(f"[RAG] 正在從知識庫 {conversation['kb_id']} 檢索相關內容...")
            context_chunks = rag_service.query_kb(conversation['kb_id'], user_message)
            if context_chunks:
                context_str = "\n".join(context_chunks)
                rag_prompt = f"以下是相關的參考資料，請根據這些資料來回答使用者的問題：\n\n{context_str}\n\n"
                # 將檢索到的資料插入到最後一則訊息之前 (或是作為 system prompt)
                # 這裡選擇插入到最後一則訊息前
                messages.insert(-1, {"role": "system", "content": rag_prompt})
                print(f"[RAG] 已加入 {len(context_chunks)} 條參考資料")
        
        # 如果有系統提示詞，插入到訊息開頭
        if conversation['system_prompt_id']:
            cursor.execute("""
                SELECT content FROM system_prompts WHERE id = %s
            """, (conversation['system_prompt_id'],))
            prompt_row = cursor.fetchone()
            if prompt_row:
                system_prompt = prompt_row['content']
                messages.insert(0, {"role": "system", "content": system_prompt})
                print(f"[SYSTEM PROMPT] 使用系統提示詞: {system_prompt[:50]}...")
        
        # 準備 AI Client
        ai_client = AIClientFactory.create_client(
            conversation['model_provider'],
            conversation['model_name']
        )
        
        # 如果啟用 MCP,取得工具列表
        tools = None
        if conversation['mcp_enabled']:
            try:
                # 取得該對話選中的 MCP servers
                mcp_servers = conversation.get('mcp_servers')
                if isinstance(mcp_servers, str):
                    mcp_servers = json.loads(mcp_servers)
                
                print(f"[MCP] MCP 已啟用, 選中服務: {mcp_servers}, 正在取得工具列表...")
                # 根據選中的 servers 過濾工具
                tools = mcp_client.list_tools(server_ids=mcp_servers)
                print(f"[MCP] 取得 {len(tools)} 個過濾後的工具")
                if tools:
                    print(f"[MCP] 工具名稱: {[t.get('name', 'unknown') for t in tools]}")
                    print(f"[MCP] 工具詳情: {tools}")
                else:
                    print(f"[MCP] 警告: 工具列表為空!")
            except Exception as e:
                print(f"[MCP] 取得工具失敗: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[MCP] MCP 未啟用")
        
        # 呼叫 AI
        print(f"[AI] 呼叫 {conversation['model_provider']} - {conversation['model_name']}")
        print(f"[AI] 工具數量: {len(tools) if tools else 0}")

        ai_response = ai_client.chat(messages, tools)
        print(f"[AI] 回應: {ai_response.get('content', '')[:100]}...")
        print(f"[AI] 工具調用: {len(ai_response.get('tool_calls', []))} 個")
        
        # 處理工具調用
        if ai_response.get('tool_calls'):
            print(f"[MCP] 開始執行工具調用")
            # 執行工具並取得結果
            for tool_call in ai_response['tool_calls']:
                func_name = tool_call['function']['name']
                func_args_str = tool_call['function']['arguments']
                
                print(f"[MCP] 工具名稱: {func_name}")
                print(f"[MCP] 原始參數: {func_args_str}")
                print(f"[MCP] 參數類型: {type(func_args_str)}")
                
                # 解析參數
                try:
                    if isinstance(func_args_str, str):
                        func_args = json.loads(func_args_str)
                        print(f"[MCP] 成功解析參數字串: {func_args}")
                    elif isinstance(func_args_str, dict):
                        func_args = func_args_str
                        print(f"[MCP] 參數已是字典格式: {func_args}")
                    else:
                        print(f"[MCP] 警告: 未知的參數類型,嘗試轉換為字典")
                        func_args = dict(func_args_str) if func_args_str else {}
                except json.JSONDecodeError as e:
                    print(f"[MCP] JSON 解析失敗: {str(e)}")
                    print(f"[MCP] 原始參數內容: {repr(func_args_str)}")
                    func_args = {}
                except Exception as e:
                    print(f"[MCP] 參數解析異常: {str(e)}")
                    print(f"[MCP] 原始參數內容: {repr(func_args_str)}")
                    import traceback
                    traceback.print_exc()
                    func_args = {}
                
                # 驗證參數
                if not func_args:
                    print(f"[MCP] 警告: 參數為空字典,可能導致工具調用失敗!")
                
                print(f"[MCP] 執行工具: {func_name}, 最終參數: {func_args}")
                
                # 呼叫 MCP 工具
                try:
                    result = mcp_client.invoke_tool(func_name, func_args)
                    print(f"[MCP] 工具結果: {result}")
                    # 儲存結果到 tool_call
                    tool_call['result'] = result
                except Exception as e:
                    print(f"[MCP] 工具執行失敗: {str(e)}")
                    tool_call['result'] = {"error": str(e)}
            
            # 將工具結果加入訊息歷史
            messages.append({
                "role": "assistant",
                "content": ai_response.get('content', ''),
                "tool_calls": ai_response['tool_calls']
            })
            
            # 加入工具結果訊息
            for tool_call in ai_response['tool_calls']:
                tool_message = {
                    "role": "tool",
                    "content": json.dumps(tool_call.get('result', {}))
                }
                
                # OpenAI 要求 role='tool' 的訊息必須包含 tool_call_id
                if 'id' in tool_call:
                    tool_message['tool_call_id'] = tool_call['id']
                
                # 某些 AI 供應商也需要 name 參數
                if 'function' in tool_call and 'name' in tool_call['function']:
                    tool_message['name'] = tool_call['function']['name']
                
                messages.append(tool_message)
            
            # 再次呼叫 AI 以整合工具結果
            print(f"[AI] 整合工具結果,再次呼叫 AI")
            final_response = ai_client.chat(messages)
            print(f"[AI] 最終回應: {final_response.get('content', '')[:100]}...")
            
            # 更新回應內容,但保留 tool_calls
            ai_response['content'] = final_response['content']
        
        # 儲存 AI 回應 (包含工具調用結果)
        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, tool_calls)
            VALUES (%s, %s, %s, %s)
        """, (
            conversation_id,
            'assistant',
            ai_response['content'],
            json.dumps(ai_response.get('tool_calls')) if ai_response.get('tool_calls') else None
        ))
        
        message_id = cursor.lastrowid
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": {
                "id": message_id,
                "role": "assistant",
                "content": ai_response['content'],
                "tool_calls": ai_response.get('tool_calls')
            }
        })
        
    except Exception as e:
        print(f"[ERROR] 發送訊息失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@chat_bp.route('/conversations/<int:conversation_id>', methods=['PATCH'])
def update_conversation(conversation_id):
    """更新對話配置 (例如切換模型或 MCP 工具)"""
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 建立更新 SQL
        update_parts = []
        params = []
        
        if 'title' in data:
            update_parts.append("title = %s")
            params.append(data['title'])
            
        if 'model_provider' in data:
            update_parts.append("model_provider = %s")
            params.append(data['model_provider'])
            
        if 'model_name' in data:
            update_parts.append("model_name = %s")
            params.append(data['model_name'])
            
        if 'mcp_servers' in data:
            mcp_servers = data['mcp_servers']
            update_parts.append("mcp_servers = %s")
            params.append(json.dumps(mcp_servers))
            
            # 同步更新 mcp_enabled 狀態
            update_parts.append("mcp_enabled = %s")
            params.append(len(mcp_servers) > 0)
        
        if 'system_prompt_id' in data:
            update_parts.append("system_prompt_id = %s")
            params.append(data['system_prompt_id'])
            
        if 'kb_id' in data:
            update_parts.append("kb_id = %s")
            params.append(data['kb_id'])
            
        if not update_parts:
            return jsonify({
                "success": True,
                "message": "沒有欄位需要更新"
            })
            
        # 組合 SQL
        sql = f"UPDATE conversations SET {', '.join(update_parts)} WHERE id = %s"
        params.append(conversation_id)
        
        cursor.execute(sql, tuple(params))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "對話配置已更新"
        })
        
    except Exception as e:
        print(f"[ERROR] 更新對話失敗: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@chat_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """刪除對話"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM conversations WHERE id = %s
        """, (conversation_id,))
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "對話已刪除"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@chat_bp.route('/conversations/clear-all', methods=['DELETE'])
def clear_all_conversations():
    """清空所有對話紀錄"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 刪除所有對話(會自動級聯刪除訊息)
        cursor.execute("DELETE FROM conversations")
        deleted_count = cursor.rowcount
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"已清空 {deleted_count} 個對話"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@chat_bp.route('/models', methods=['GET'])
def list_models():
    """動態取得可用的模型列表"""
    models = {
        "openai": [],
        "google": [],
        "anthropic": []
    }
    
    # 取得 OpenAI 模型
    try:
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            openai_models = client.models.list()
            
            # 過濾出 GPT 模型
            gpt_models = []
            for model in openai_models.data:
                model_id = model.id
                if 'gpt-4' in model_id or 'gpt-3.5' in model_id:
                    # 排除 fine-tuned 模型
                    if not model_id.startswith('ft:'):
                        display_name = model_id.upper().replace('-', ' ').replace('TURBO', 'Turbo')
                        gpt_models.append({
                            "name": model_id,
                            "display_name": display_name
                        })
            
            # 排序並去重
            seen = set()
            for model in sorted(gpt_models, key=lambda x: x['name'], reverse=True):
                if model['name'] not in seen:
                    models["openai"].append(model)
                    seen.add(model['name'])
    except Exception as e:
        print(f"取得 OpenAI 模型失敗: {str(e)}")
        # 使用預設模型列表
        models["openai"] = [
            {"name": "gpt-4o", "display_name": "GPT-4o"},
            {"name": "gpt-4-turbo", "display_name": "GPT-4 Turbo"},
            {"name": "gpt-4", "display_name": "GPT-4"},
            {"name": "gpt-3.5-turbo", "display_name": "GPT-3.5 Turbo"}
        ]
    
    # 取得 Google Gemini 模型
    try:
        google_key = os.getenv('GOOGLE_API_KEY')
        if google_key:
            import google.generativeai as genai
            genai.configure(api_key=google_key)
            
            gemini_models = []
            for model in genai.list_models():
                # 只取支援 generateContent 的模型
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.replace('models/', '')
                    # 只取 gemini 模型
                    if 'gemini' in model_name.lower():
                        display_name = model_name.replace('gemini-', 'Gemini ').replace('-', ' ').title()
                        gemini_models.append({
                            "name": model_name,
                            "display_name": display_name
                        })
            
            models["google"] = sorted(gemini_models, key=lambda x: x['name'], reverse=True)
    except Exception as e:
        print(f"取得 Gemini 模型失敗: {str(e)}")
        # 使用預設模型列表
        models["google"] = [
            {"name": "gemini-1.5-pro", "display_name": "Gemini 1.5 Pro"},
            {"name": "gemini-1.5-flash", "display_name": "Gemini 1.5 Flash"},
            {"name": "gemini-1.0-pro", "display_name": "Gemini 1.0 Pro"}
        ]
    
    # 取得 Anthropic Claude 模型
    try:
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            # Anthropic 沒有提供 list models API,使用已知的模型列表
            models["anthropic"] = [
                {"name": "claude-3-5-sonnet-20241022", "display_name": "Claude 3.5 Sonnet"},
                {"name": "claude-3-opus-20240229", "display_name": "Claude 3 Opus"},
                {"name": "claude-3-sonnet-20240229", "display_name": "Claude 3 Sonnet"},
                {"name": "claude-3-haiku-20240307", "display_name": "Claude 3 Haiku"}
            ]
    except Exception as e:
        print(f"設定 Anthropic 模型失敗: {str(e)}")
        models["anthropic"] = [
            {"name": "claude-3-5-sonnet-20241022", "display_name": "Claude 3.5 Sonnet"},
            {"name": "claude-3-opus-20240229", "display_name": "Claude 3 Opus"}
        ]
    
    return jsonify({
        "success": True,
        "models": models
    })

