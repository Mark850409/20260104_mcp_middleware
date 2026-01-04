"""
MCP Client Service - 封裝 MCP 連線與工具呼叫邏輯
透過 HTTP API 與 MCP Server 互動
"""
import os
import requests
from typing import Dict, List, Any


class MCPClientService:
    """MCP Client 服務類別 - 管理與 MCP Server 的連線與互動"""
    
    def __init__(self):
        """初始化 MCP Client Service"""
        self.server_host = os.getenv('MCP_SERVER_HOST', 'mcp-server')
        self.server_port = int(os.getenv('MCP_SERVER_PORT', '8000'))
        self.base_url = f"http://{self.server_host}:{self.server_port}"
        self.is_connected = False
        
    def connect(self) -> bool:
        """
        連線到 MCP Server (檢查健康狀態)
        
        Returns:
            連線是否成功
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.is_connected = True
                print(f"成功連線到 MCP Server: {self.base_url}")
                return True
            else:
                self.is_connected = False
                return False
        except Exception as e:
            print(f"連線 MCP Server 失敗: {str(e)}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """中斷與 MCP Server 的連線"""
        self.is_connected = False
        print("已中斷 MCP Server 連線")
    
    def get_status(self) -> Dict[str, Any]:
        """
        取得 MCP Server 連線狀態
        
        Returns:
            狀態資訊字典
        """
        return {
            "connected": self.is_connected,
            "server_host": self.server_host,
            "server_port": self.server_port
        }
    
    def list_tools(self, server_ids: List[str] = None) -> List[Dict[str, Any]]:
        """
        取得 MCP Server 提供的工具清單 (支援特定伺服器過濾)
        
        Args:
            server_ids: 要過濾的伺服器名稱列表
            
        Returns:
            工具清單
        """
        try:
            params = {}
            if server_ids:
                params['server_names'] = ','.join(server_ids)
                
            response = requests.get(f"{self.base_url}/tools", params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('tools', [])
            else:
                print(f"取得工具清單失敗: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"取得工具清單失敗: {str(e)}")
            return []
    
    def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        呼叫指定的 MCP 工具
        
        Args:
            tool_name: 工具名稱
            arguments: 工具參數
        
        Returns:
            工具執行結果
        """
        try:
            print(f"[MCP Client] 準備調用工具: {tool_name}")
            print(f"[MCP Client] 參數: {arguments}")
            print(f"[MCP Client] 參數類型: {type(arguments)}")
            
            payload = {"arguments": arguments}
            print(f"[MCP Client] 發送的 payload: {payload}")
            
            response = requests.post(
                f"{self.base_url}/tools/{tool_name}/invoke",
                json=payload,
                timeout=10
            )
            
            print(f"[MCP Client] HTTP 狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"[MCP Client] 工具調用成功: {result}")
                return result
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                print(f"[MCP Client] 工具調用失敗: {error_data}")
                return {
                    "success": False,
                    "error": error_data.get('error', f"HTTP {response.status_code}"),
                    "tool_name": tool_name
                }
        except Exception as e:
            print(f"[MCP Client] 異常: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name
            }


# 建立全域 MCP Client 實例
mcp_client = MCPClientService()
