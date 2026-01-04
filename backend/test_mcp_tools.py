"""
測試 MCP 工具調用流程
用於驗證工具是否正確傳遞給 AI
"""
import sys
import os

# 添加 backend 目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.mcp_client import mcp_client
from services.ai_client import AIClientFactory

def test_mcp_tools():
    """測試 MCP 工具調用"""
    print("=" * 60)
    print("測試 MCP 工具調用流程")
    print("=" * 60)
    
    # 1. 測試 MCP Server 連線
    print("\n[1] 測試 MCP Server 連線...")
    if mcp_client.connect():
        print("✓ MCP Server 連線成功")
    else:
        print("✗ MCP Server 連線失敗")
        return
    
    # 2. 取得工具列表
    print("\n[2] 取得工具列表...")
    tools = mcp_client.list_tools()
    print(f"✓ 取得 {len(tools)} 個工具")
    for tool in tools:
        print(f"  - {tool.get('name')}: {tool.get('description')}")
    
    if not tools:
        print("✗ 沒有可用的工具!")
        return
    
    # 3. 測試 AI Client (使用 Google Gemini)
    print("\n[3] 測試 Gemini AI Client...")
    try:
        ai_client = AIClientFactory.create_client("google", "gemini-2.5-flash-latest-exp-0827")
        print("✓ AI Client 建立成功")
    except Exception as e:
        print(f"✗ AI Client 建立失敗: {str(e)}")
        return
    
    # 4. 發送測試訊息
    print("\n[4] 發送測試訊息...")
    messages = [
        {"role": "user", "content": "請告訴我現在的時間"}
    ]
    
    try:
        print("正在呼叫 AI (帶工具)...")
        response = ai_client.chat(messages, tools)
        print(f"\n✓ AI 回應:")
        print(f"  內容: {response.get('content', '')}")
        print(f"  工具調用數量: {len(response.get('tool_calls', []))}")
        
        if response.get('tool_calls'):
            print(f"\n✓ 工具調用詳情:")
            for tc in response['tool_calls']:
                print(f"  - 工具: {tc['function']['name']}")
                print(f"    參數: {tc['function']['arguments']}")
        else:
            print("\n✗ AI 沒有調用任何工具!")
            
    except Exception as e:
        print(f"✗ AI 呼叫失敗: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)

if __name__ == "__main__":
    test_mcp_tools()
