"""
MCP Provider 抽象基類
定義所有 Provider 必須實作的介面
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class BaseMCPProvider(ABC):
    """MCP Provider 抽象基類 - 定義統一的 Provider 介面"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化 Provider
        
        Args:
            name: Provider 名稱 (對應 server_name)
            config: Provider 配置
        """
        self.name = name
        self.config = config
        self.is_running = False
        logger.info(f"[{self.__class__.__name__}] 初始化 Provider: {name}")
    
    @abstractmethod
    async def start(self) -> bool:
        """
        啟動 Provider
        
        Returns:
            是否成功啟動
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        停止 Provider
        
        Returns:
            是否成功停止
        """
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        列出所有工具
        
        Returns:
            工具列表,格式:
            [
                {
                    "name": "tool_name",
                    "description": "tool description",
                    "inputSchema": {...}
                }
            ]
        """
        pass
    
    @abstractmethod
    async def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        執行工具
        
        Args:
            tool_name: 工具名稱
            arguments: 工具參數
            
        Returns:
            工具執行結果
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康檢查
        
        Returns:
            Provider 是否健康
        """
        pass
    
    def get_type(self) -> str:
        """取得 Provider 類型"""
        return self.config.get("type", "unknown")
    
    def is_enabled(self) -> bool:
        """檢查 Provider 是否啟用"""
        return self.config.get("enabled", False)
