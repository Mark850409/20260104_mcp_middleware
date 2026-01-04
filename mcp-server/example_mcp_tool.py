"""
範例 MCP 工具插件
示範如何建立簡單的 MCP 工具
"""
from datetime import datetime


def hello(name: str = "World") -> str:
    """
    問候工具 - 回傳問候訊息
    
    Args:
        name: 要問候的名字
    
    Returns:
        問候訊息字串
    """
    print(f"[hello] 收到參數 name={name}")
    return f"Hello, {name}!"


def get_time() -> str:
    """
    時間工具 - 回傳當前 ISO 8601 格式時間
    
    Returns:
        ISO 8601 格式的時間字串
    """
    print(f"[get_time] 被調用")
    return datetime.now().isoformat()


def register_plugin():
    """
    註冊範例工具插件
    
    Returns:
        dict: 工具註冊資訊
    """
    return {
        "hello": {
            "function": hello,
            "is_async": False,
            "schema": {
                "name": "hello",
                "description": "問候工具 - 回傳問候訊息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "要問候的名字"
                        }
                    },
                    "required": ["name"]
                }
            }
        },
        "get_time": {
            "function": get_time,
            "is_async": False,
            "schema": {
                "name": "get_time",
                "description": "時間工具 - 回傳當前 ISO 8601 格式時間",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    }
