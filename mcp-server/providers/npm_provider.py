"""
NPM Provider - 透過 npx 執行線上安裝的 MCP 套件
支援自動安裝和執行 npm 套件
"""
import os
import asyncio
import json
from typing import Dict, Any, List
import logging

from .base_provider import BaseMCPProvider

logger = logging.getLogger(__name__)


class NPMProvider(BaseMCPProvider):
    """NPM Provider - 執行線上 npm 套件形式的 MCP 工具"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.process = None
        self.tools_cache = []
        self.package_name = config.get("package", "")
    
    async def start(self) -> bool:
        """啟動 NPM Provider"""
        try:
            if not self.package_name:
                logger.error(f"[NPMProvider] {self.name}: 缺少 package 配置")
                return False
            
            # 檢查 npx 是否可用
            try:
                process = await asyncio.create_subprocess_exec(
                    "npx", "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                if process.returncode != 0:
                    raise RuntimeError("npx 不可用")
            except Exception as e:
                logger.error(f"[NPMProvider] {self.name}: npx 環境檢查失敗 - {e}")
                return False
            
            # 設定環境變數
            env = os.environ.copy()
            env_vars = self.config.get("env", {})
            for key, value in env_vars.items():
                if value:
                    env[key] = str(value)
            
            # 使用 npx 啟動套件 (自動安裝)
            logger.info(f"[NPMProvider] {self.name}: 啟動 npm 套件 {self.package_name}")
            
            # 取得額外參數
            extra_args = self.config.get("args", [])
            
            # 建立完整指令
            cmd = ["npx", "-y", self.package_name] + extra_args
            
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            # 等待一小段時間確保進程啟動
            await asyncio.sleep(1)
            
            # 檢查進程是否還在運行
            if self.process.returncode is not None:
                stderr = await self.process.stderr.read()
                logger.error(f"[NPMProvider] {self.name}: 套件啟動失敗 - {stderr.decode()}")
                return False
            
            # 嘗試取得工具列表
            try:
                self.tools_cache = await self._fetch_tools()
                logger.info(f"[NPMProvider] {self.name}: 成功載入 {len(self.tools_cache)} 個工具")
            except Exception as e:
                logger.warning(f"[NPMProvider] {self.name}: 無法載入工具列表 - {e}")
            
            self.is_running = True
            return True
            
        except Exception as e:
            logger.error(f"[NPMProvider] {self.name}: 啟動失敗 - {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def stop(self) -> bool:
        """停止 NPM Provider"""
        try:
            if self.process:
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self.process.kill()
                    await self.process.wait()
                
                self.process = None
            
            self.is_running = False
            logger.info(f"[NPMProvider] {self.name}: 已停止")
            return True
        except Exception as e:
            logger.error(f"[NPMProvider] {self.name}: 停止失敗 - {e}")
            return False
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Any:
        """透過 stdio 發送 JSON-RPC 請求"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("進程未啟動")
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }
        
        # 發送請求
        request_str = json.dumps(request) + "\n"
        self.process.stdin.write(request_str.encode())
        await self.process.stdin.drain()
        
        # 讀取回應
        response_line = await self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("未收到回應")
            
        response = json.loads(response_line.decode())
        
        if "error" in response:
            raise RuntimeError(f"RPC 錯誤: {response['error']}")
        
        return response.get("result")
    
    async def _fetch_tools(self) -> List[Dict[str, Any]]:
        """從 npm 套件取得工具列表"""
        try:
            result = await self._send_request("tools/list")
            if isinstance(result, dict) and "tools" in result:
                return result["tools"]
            elif isinstance(result, list):
                return result
            return []
        except Exception as e:
            logger.error(f"[NPMProvider] {self.name}: 取得工具列表失敗 - {e}")
            return []
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        if self.tools_cache:
            return self.tools_cache
        
        self.tools_cache = await self._fetch_tools()
        return self.tools_cache
    
    async def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """執行工具"""
        try:
            result = await self._send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            
            logger.info(f"[NPMProvider] {self.name}: 工具 {tool_name} 執行成功")
            return result
            
        except Exception as e:
            logger.error(f"[NPMProvider] {self.name}: 執行工具 {tool_name} 失敗 - {e}")
            raise
    
    async def health_check(self) -> bool:
        """健康檢查"""
        if not self.process:
            return False
        
        # 檢查進程是否還在運行
        return self.process.returncode is None
