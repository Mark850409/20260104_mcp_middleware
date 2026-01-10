"""
Provider Manager - 管理所有 MCP Provider 的生命週期和工具聚合
"""
import asyncio
from typing import Dict, Any, List, Tuple
import logging

from providers.base_provider import BaseMCPProvider
from providers.provider_factory import ProviderFactory

logger = logging.getLogger(__name__)


class ProviderManager:
    """管理所有 MCP Provider 的生命週期和工具聚合"""
    
    def __init__(self, config_manager):
        """
        初始化 Provider Manager
        
        Args:
            config_manager: 配置管理器實例
        """
        self.config_manager = config_manager
        self.providers: Dict[str, BaseMCPProvider] = {}
        self.tools: Dict[str, Dict[str, Any]] = {}
        logger.info("[ProviderManager] 初始化完成")
    
    async def initialize_providers(self) -> None:
        """初始化所有啟用的 Provider"""
        logger.info("[ProviderManager] 開始初始化 Providers...")
        
        servers = self.config_manager.get_enabled_servers()
        
        for server in servers:
            server_name = server.get("name")
            if not server_name:
                logger.warning("[ProviderManager] Server 缺少 name 欄位,跳過")
                continue
            
            # 建立配置字典(排除 name 欄位)
            config = {k: v for k, v in server.items() if k != "name"}
            # 跳過 Python 類型 (由 PluginLoader 處理)
            provider_type = config.get("type", "python")
            if provider_type == "python":
                logger.info(f"[ProviderManager] 跳過 Python Provider: {server_name} (由 PluginLoader 處理)")
                continue
            
            try:
                provider = ProviderFactory.create_provider(server_name, config)
                success = await provider.start()
                
                if success:
                    self.providers[server_name] = provider
                    # 載入該 Provider 的工具
                    await self._load_provider_tools(server_name, provider)
                    logger.info(f"[ProviderManager] Provider {server_name} 初始化成功")
                else:
                    logger.error(f"[ProviderManager] Provider {server_name} 啟動失敗")
                    
            except Exception as e:
                logger.error(f"[ProviderManager] 初始化 Provider {server_name} 失敗: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"[ProviderManager] 初始化完成,共 {len(self.providers)} 個 Provider")
    
    async def _load_provider_tools(self, server_name: str, provider: BaseMCPProvider) -> None:
        """
        載入 Provider 的工具到全域 TOOLS 字典
        
        Args:
            server_name: Server 名稱
            provider: Provider 實例
        """
        try:
            tools = await provider.list_tools()
            
            for tool in tools:
                tool_name = tool.get("name")
                if not tool_name:
                    logger.warning(f"[ProviderManager] {server_name}: 工具缺少 name 欄位")
                    continue
                
                # 建立工具包裝函數
                async def tool_wrapper(provider=provider, tool_name=tool_name, **arguments):
                    return await provider.invoke_tool(tool_name, arguments)
                
                self.tools[tool_name] = {
                    "function": tool_wrapper,
                    "is_async": True,
                    "schema": {
                        "name": tool_name,
                        "description": tool.get("description", ""),
                        "inputSchema": tool.get("inputSchema", {"type": "object", "properties": {}}),
                        "server_name": server_name
                    }
                }
            
            logger.info(f"[ProviderManager] {server_name}: 載入 {len(tools)} 個工具")
            
        except Exception as e:
            logger.error(f"[ProviderManager] 載入 {server_name} 工具失敗: {e}")
    
    def get_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        取得所有工具 (與現有 PluginLoader 格式相容)
        
        Returns:
            工具字典
        """
        return self.tools
    
    async def reload_provider(self, server_name: str) -> bool:
        """
        重新載入特定 Provider
        
        Args:
            server_name: Server 名稱
            
        Returns:
            是否成功重新載入
        """
        try:
            logger.info(f"[ProviderManager] 重新載入 Provider: {server_name}")
            
            # 停止舊的 Provider
            if server_name in self.providers:
                await self.providers[server_name].stop()
                del self.providers[server_name]
            
            # 移除該 Provider 的工具
            self.tools = {
                name: info 
                for name, info in self.tools.items() 
                if info["schema"].get("server_name") != server_name
            }
            
            # 重新初始化
            config = self.config_manager.get_server(server_name)
            if not config:
                logger.warning(f"[ProviderManager] Server {server_name} 配置不存在")
                return False
            
            if not config.get("enabled", False):
                logger.info(f"[ProviderManager] Server {server_name} 已停用,不重新載入")
                return True
            
            # 跳過 Python 類型
            provider_type = config.get("type", "python")
            if provider_type == "python":
                logger.info(f"[ProviderManager] 跳過 Python Provider: {server_name}")
                return True
            
            provider = ProviderFactory.create_provider(server_name, config)
            success = await provider.start()
            
            if success:
                self.providers[server_name] = provider
                await self._load_provider_tools(server_name, provider)
                logger.info(f"[ProviderManager] Provider {server_name} 重新載入成功")
                return True
            else:
                logger.error(f"[ProviderManager] Provider {server_name} 啟動失敗")
                return False
                
        except Exception as e:
            logger.error(f"[ProviderManager] 重新載入 Provider {server_name} 失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def shutdown_all(self) -> None:
        """關閉所有 Provider"""
        logger.info("[ProviderManager] 關閉所有 Providers...")
        
        for server_name, provider in self.providers.items():
            try:
                await provider.stop()
                logger.info(f"[ProviderManager] Provider {server_name} 已停止")
            except Exception as e:
                logger.error(f"[ProviderManager] 停止 Provider {server_name} 失敗: {e}")
        
        self.providers.clear()
        self.tools.clear()
        logger.info("[ProviderManager] 所有 Providers 已關閉")
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        檢查所有 Provider 的健康狀態
        
        Returns:
            Server 名稱到健康狀態的映射
        """
        results = {}
        
        for server_name, provider in self.providers.items():
            try:
                is_healthy = await provider.health_check()
                results[server_name] = is_healthy
            except Exception as e:
                logger.error(f"[ProviderManager] {server_name} 健康檢查失敗: {e}")
                results[server_name] = False
        
        return results
