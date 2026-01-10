"""
Docker Provider - 透過 Docker 容器執行 MCP 工具
與容器內的 MCP Server 透過 HTTP/SSE 通訊
"""
import asyncio
import httpx
from typing import Dict, Any, List
import logging

from .base_provider import BaseMCPProvider

logger = logging.getLogger(__name__)


class DockerProvider(BaseMCPProvider):
    """Docker Provider - 管理 Docker 容器形式的 MCP Server"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.container_name = config.get("container_name", f"mcp-{name}")
        self.base_url = None
        self.client = None
        self.cached_tools = []
    
    async def start(self) -> bool:
        """啟動 Docker Provider - 連接到容器"""
        try:
            # 從 ports 配置推斷容器的 HTTP 端點
            # 格式: ["8001:8000"] -> http://localhost:8001
            ports = self.config.get("ports", [])
            if not ports:
                logger.error(f"[DockerProvider] {self.name}: 缺少 ports 配置")
                return False
            
            # 解析 port mapping (例如 "8001:8000")
            port_mapping = ports[0]
            host_port = port_mapping.split(":")[0]
            self.base_url = f"http://localhost:{host_port}"
            
            # 建立 HTTP 客戶端
            self.client = httpx.AsyncClient(timeout=10.0)
            
            # 測試連接
            health_ok = await self.health_check()
            if not health_ok:
                logger.warning(f"[DockerProvider] {self.name}: 容器可能尚未啟動,將在首次使用時重試")
            
            # 嘗試載入工具列表
            try:
                self.cached_tools = await self._fetch_tools()
                logger.info(f"[DockerProvider] {self.name}: 成功載入 {len(self.cached_tools)} 個工具")
            except Exception as e:
                logger.warning(f"[DockerProvider] {self.name}: 無法載入工具列表 - {e}")
            
            self.is_running = True
            return True
            
        except Exception as e:
            logger.error(f"[DockerProvider] {self.name}: 啟動失敗 - {e}")
            return False
    
    async def stop(self) -> bool:
        """停止 Docker Provider"""
        try:
            if self.client:
                await self.client.aclose()
                self.client = None
            
            self.is_running = False
            logger.info(f"[DockerProvider] {self.name}: 已停止")
            return True
        except Exception as e:
            logger.error(f"[DockerProvider] {self.name}: 停止失敗 - {e}")
            return False
    
    async def _fetch_tools(self) -> List[Dict[str, Any]]:
        """從容器的 API 取得工具列表"""
        if not self.client:
            raise RuntimeError("HTTP 客戶端未初始化")
        
        try:
            # 嘗試多個可能的端點
            endpoints = ["/tools", "/api/tools", "/mcp/tools"]
            
            for endpoint in endpoints:
                try:
                    response = await self.client.get(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        data = response.json()
                        # 處理不同的回應格式
                        if isinstance(data, list):
                            return data
                        elif isinstance(data, dict) and "tools" in data:
                            return data["tools"]
                except Exception:
                    continue
            
            logger.warning(f"[DockerProvider] {self.name}: 無法從任何端點取得工具列表")
            return []
            
        except Exception as e:
            logger.error(f"[DockerProvider] {self.name}: 取得工具列表失敗 - {e}")
            return []
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        # 如果有快取,直接返回
        if self.cached_tools:
            return self.cached_tools
        
        # 否則重新取得
        self.cached_tools = await self._fetch_tools()
        return self.cached_tools
    
    async def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """執行工具"""
        if not self.client:
            raise RuntimeError("HTTP 客戶端未初始化")
        
        try:
            # 嘗試多個可能的端點格式
            endpoints = [
                f"/tools/{tool_name}/invoke",
                f"/api/tools/{tool_name}/invoke",
                f"/mcp/tools/{tool_name}/invoke"
            ]
            
            for endpoint in endpoints:
                try:
                    response = await self.client.post(
                        f"{self.base_url}{endpoint}",
                        json={"arguments": arguments}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        # 處理不同的回應格式
                        if isinstance(data, dict):
                            return data.get("result", data)
                        return data
                except httpx.HTTPStatusError:
                    continue
            
            raise RuntimeError(f"無法執行工具 {tool_name},所有端點都失敗")
            
        except Exception as e:
            logger.error(f"[DockerProvider] {self.name}: 執行工具 {tool_name} 失敗 - {e}")
            raise
    
    async def health_check(self) -> bool:
        """健康檢查"""
        if not self.client:
            return False
        
        try:
            # 嘗試多個可能的健康檢查端點
            endpoints = ["/health", "/api/health", "/"]
            
            for endpoint in endpoints:
                try:
                    response = await self.client.get(f"{self.base_url}{endpoint}", timeout=5.0)
                    if response.status_code == 200:
                        return True
                except Exception:
                    continue
            
            return False
        except Exception:
            return False
