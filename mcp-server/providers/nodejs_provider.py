"""
Node.js Provider - 透過 subprocess 執行 Node.js MCP 工具
類似 Python Provider,但執行 Node.js 腳本
"""
import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
import logging

from .base_provider import BaseMCPProvider

logger = logging.getLogger(__name__)


class NodeJSProvider(BaseMCPProvider):
    """Node.js Provider - 執行 Node.js 腳本形式的 MCP 工具"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.process = None
        self.tools_cache = []
    
    async def start(self) -> bool:
        """啟動 Node.js Provider"""
        try:
            # 取得指令和參數
            command = self.config.get("command", "node")
            args = self.config.get("args", [])
            
            if not args:
                logger.error(f"[NodeJSProvider] {self.name}: 缺少 args 配置")
                return False
            
            # 檢查是否為 npx 指令
            is_npx = command.lower() == "npx"
            
            if not is_npx:
                # 本地 Node.js 腳本: 需要檢查檔案是否存在
                script_path = args[0]
                
                # 如果是相對路徑,轉換為絕對路徑
                if not os.path.isabs(script_path):
                    base_dir = os.path.dirname(os.path.dirname(__file__))
                    script_path = os.path.join(base_dir, script_path)
                
                script_path = Path(script_path).resolve()
                
                if not script_path.exists():
                    logger.error(f"[NodeJSProvider] {self.name}: 檔案不存在 {script_path}")
                    return False
                
                # 更新 args 為絕對路徑
                args = [str(script_path)] + args[1:]
            else:
                # npx 指令: 不需要檢查檔案,直接使用 args
                logger.info(f"[NodeJSProvider] {self.name}: 使用 npx 執行套件 {args}")
            
            # 檢查 Node.js/npx 是否可用
            check_command = "npx" if is_npx else "node"
            try:
                process = await asyncio.create_subprocess_exec(
                    check_command, "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                if process.returncode != 0:
                    raise RuntimeError(f"{check_command} 不可用")
            except Exception as e:
                logger.error(f"[NodeJSProvider] {self.name}: {check_command} 環境檢查失敗 - {e}")
                return False
            
            # 設定環境變數
            env = os.environ.copy()
            env_vars = self.config.get("env", {})
            for key, value in env_vars.items():
                if value:
                    env[key] = str(value)
            
            # 啟動進程 (stdio 模式)
            self.process = await asyncio.create_subprocess_exec(
                command, *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            # 等待進程啟動
            await asyncio.sleep(0.5)
            
            # MCP 協定初始化握手
            try:
                logger.info(f"[NodeJSProvider] {self.name}: 開始 MCP 初始化握手")
                
                # 1. 發送 initialize 請求
                init_result = await self._send_request("initialize", {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-platform",
                        "version": "1.0.0"
                    }
                })
                logger.info(f"[NodeJSProvider] {self.name}: initialize 成功 - {init_result}")
                
                # 2. 發送 initialized 通知
                await self._send_notification("notifications/initialized")
                logger.info(f"[NodeJSProvider] {self.name}: initialized 通知已發送")
                
            except Exception as e:
                logger.warning(f"[NodeJSProvider] {self.name}: MCP 初始化失敗 - {e}")
                # 初始化失敗不影響啟動,繼續嘗試取得工具
            
            # 嘗試取得工具列表
            try:
                self.tools_cache = await self._fetch_tools()
                logger.info(f"[NodeJSProvider] {self.name}: 成功載入 {len(self.tools_cache)} 個工具")
            except Exception as e:
                logger.warning(f"[NodeJSProvider] {self.name}: 無法載入工具列表 - {e}")
            
            self.is_running = True
            return True
            
        except Exception as e:
            logger.error(f"[NodeJSProvider] {self.name}: 啟動失敗 - {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def stop(self) -> bool:
        """停止 Node.js Provider"""
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
            logger.info(f"[NodeJSProvider] {self.name}: 已停止")
            return True
        except Exception as e:
            logger.error(f"[NodeJSProvider] {self.name}: 停止失敗 - {e}")
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
        response = json.loads(response_line.decode())
        
        if "error" in response:
            raise RuntimeError(f"RPC 錯誤: {response['error']}")
        
        return response.get("result")
    
    async def _send_notification(self, method: str, params: Dict[str, Any] = None) -> None:
        """透過 stdio 發送 JSON-RPC 通知 (不需要回應)"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("進程未啟動")
        
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        # 發送通知 (通知沒有 id,不需要等待回應)
        notification_str = json.dumps(notification) + "\n"
        self.process.stdin.write(notification_str.encode())
        await self.process.stdin.drain()
    
    async def _fetch_tools(self) -> List[Dict[str, Any]]:
        """從 Node.js 進程取得工具列表"""
        try:
            result = await self._send_request("tools/list")
            if isinstance(result, dict) and "tools" in result:
                return result["tools"]
            elif isinstance(result, list):
                return result
            return []
        except Exception as e:
            logger.error(f"[NodeJSProvider] {self.name}: 取得工具列表失敗 - {e}")
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
            
            logger.info(f"[NodeJSProvider] {self.name}: 工具 {tool_name} 執行成功")
            return result
            
        except Exception as e:
            logger.error(f"[NodeJSProvider] {self.name}: 執行工具 {tool_name} 失敗 - {e}")
            raise
    
    async def health_check(self) -> bool:
        """健康檢查"""
        if not self.process:
            return False
        
        # 檢查進程是否還在運行
        return self.process.returncode is None
