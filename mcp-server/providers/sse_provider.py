"""
SSE Provider - 連接到遠端 MCP Server (透過 SSE)
支援連接到外部的 MCP Server
"""
import asyncio
import httpx
from httpx_sse import aconnect_sse, ServerSentEvent
import json
from typing import Dict, Any, List, Optional
import logging

from .base_provider import BaseMCPProvider

logger = logging.getLogger(__name__)


class SSEProvider(BaseMCPProvider):
    """SSE Provider - 連接到遠端 MCP Server"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.url = config.get("url")
        self.headers = config.get("headers", {})
        self.client = None
        self.cached_tools = []
        self.session_id = None
        self.messages_url = None
        self._request_counter = 0  # 請求計數器
    
    async def start(self) -> bool:
        """啟動 SSE Provider - 連接到遠端 Server"""
        try:
            # 初始化 HTTP 客戶端
            # 初始化 HTTP 客戶端，停用 trust_env 以免受 Docker 環境代理影響
            self.client = httpx.AsyncClient(timeout=30.0, trust_env=False)
            
            # 健康檢查
            health_ok = await self.health_check()
            if not health_ok:
                logger.warning(f"[SSEProvider] {self.name}: 健康檢查未通過，但繼續嘗試連接")
            
            # 嘗試載入工具列表
            try:
                self.cached_tools = await self._fetch_tools()
                logger.info(f"[SSEProvider] {self.name}: 成功載入 {len(self.cached_tools)} 個工具")
            except Exception as e:
                logger.error(f"[SSEProvider] {self.name}: 無法載入工具列表 - {e}")
                if self.client:
                    await self.client.aclose()
                return False
            
            self.is_running = True
            return True
            
        except Exception as e:
            logger.error(f"[SSEProvider] {self.name}: 啟動失敗 - {e}")
            return False
    
    async def stop(self) -> bool:
        """停止 SSE Provider"""
        try:
            if self.client:
                await self.client.aclose()
                self.client = None
            
            self.is_running = False
            self.cached_tools = []
            self.session_id = None
            self.messages_url = None
            logger.info(f"[SSEProvider] {self.name}: 已停止")
            return True
            
        except Exception as e:
            logger.error(f"[SSEProvider] {self.name}: 停止失敗 - {e}")
            return False
    
    async def _fetch_tools_via_sse(self) -> List[Dict[str, Any]]:
        """通過真正的 SSE 協議取得工具列表"""
        if not self.client:
            raise RuntimeError("HTTP 客戶端未初始化")
        
        try:
            # 推測 messages 端點
            base_url = self.url.rsplit("/", 1)[0]
            possible_messages_urls = [
                self.url.replace("/sse", "/messages"),
                self.url.replace("/mcp", "/messages"),
                f"{base_url}/messages",
            ]
            
            messages_url = None
            for url in possible_messages_urls:
                if url != self.url:
                    messages_url = url
                    break
            
            if messages_url is None:
                messages_url = f"{base_url}/messages"
            
            # 準備帶有過濾參數的 URL
            url = self.url
            if "?" in url:
                url += f"&server_names={self.name}"
            else:
                url += f"?server_names={self.name}"
            
            logger.info(f"[SSEProvider] {self.name}: 嘗試 SSE 連接: {url}")
            logger.info(f"[SSEProvider] {self.name}: Messages 端點: {messages_url}")
            
            # 準備 headers
            headers = dict(self.headers)
            headers["Accept"] = "text/event-stream"
            headers["Cache-Control"] = "no-cache"
            
            tools_result = None
            session_id = None
            actual_messages_url = messages_url
            
            async with aconnect_sse(self.client, "GET", url, headers=headers, timeout=30.0) as event_source:
                logger.info(f"[SSEProvider] {self.name}: SSE 連接已建立")
                
                post_headers = dict(self.headers)
                post_headers["Content-Type"] = "application/json"
                
                endpoint_received = False
                init_sent = False
                init_received = False
                initialized_sent = False
                tools_sent = False
                
                request_id = 1
                
                # 單一事件循環
                async for sse in event_source.aiter_sse():
                    logger.debug(f"[SSEProvider] {self.name}: SSE 事件: {sse.event}")
                    
                    # 1. 處理 endpoint
                    if sse.event == "endpoint" and not endpoint_received:
                        logger.info(f"[SSEProvider] {self.name}: endpoint: {sse.data}")
                        try:
                            endpoint_url = sse.data.strip()
                            if "session_id=" in endpoint_url:
                                session_id = endpoint_url.split("session_id=")[1].split("&")[0]
                                if endpoint_url.startswith("http"):
                                    actual_messages_url = endpoint_url
                                else:
                                    actual_messages_url = f"{base_url}{endpoint_url}"
                                
                                self.session_id = session_id
                                self.messages_url = actual_messages_url
                                
                                logger.info(f"[SSEProvider] {self.name}: session_id: {session_id}")
                                endpoint_received = True
                        except Exception as e:
                            logger.warning(f"[SSEProvider] {self.name}: 處理 endpoint 失敗: {e}")
                    
                    # 2. 發送 initialize
                    if endpoint_received and not init_sent:
                        init_req = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "method": "initialize",
                            "params": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {},
                                "clientInfo": {"name": "mcp-platform", "version": "1.0.0"}
                            }
                        }
                        
                        logger.info(f"[SSEProvider] {self.name}: 發送 initialize")
                        resp = await self.client.post(actual_messages_url, json=init_req, headers=post_headers)
                        
                        if resp.status_code not in [200, 202]:
                            raise RuntimeError(f"Initialize 失敗: {resp.status_code}")
                        
                        init_sent = True
                        continue
                    
                    # 3. 處理 initialize 響應
                    if init_sent and not init_received and sse.data:
                        try:
                            data = json.loads(sse.data)
                            if data.get("id") == request_id:
                                logger.info(f"[SSEProvider] {self.name}: Initialize 成功")
                                init_received = True
                                request_id += 1
                        except:
                            pass
                    
                    # 4. 發送 initialized
                    if init_received and not initialized_sent:
                        notif = {
                            "jsonrpc": "2.0",
                            "method": "notifications/initialized",
                            "params": {}
                        }
                        
                        logger.info(f"[SSEProvider] {self.name}: 發送 initialized")
                        await self.client.post(actual_messages_url, json=notif, headers=post_headers)
                        initialized_sent = True
                        # 不要 continue
                    
                    # 5. 發送 tools/list
                    if initialized_sent and not tools_sent:
                        tools_req = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "method": "tools/list",
                            "params": {}
                        }
                        
                        logger.info(f"[SSEProvider] {self.name}: 發送 tools/list")
                        resp = await self.client.post(actual_messages_url, json=tools_req, headers=post_headers)
                        
                        if resp.status_code not in [200, 202]:
                            raise RuntimeError(f"Tools/list 失敗: {resp.status_code}")
                        
                        tools_sent = True
                        # 不要 continue
                    
                    # 6. 處理 tools/list 響應
                    if tools_sent and sse.data:
                        try:
                            data = json.loads(sse.data)
                            if data.get("id") == request_id:
                                if "result" in data and "tools" in data["result"]:
                                    tools_result = data["result"]["tools"]
                                    logger.info(f"[SSEProvider] {self.name}: 成功取得 {len(tools_result)} 個工具")
                                    break
                                elif "error" in data:
                                    raise RuntimeError(f"Tools/list 錯誤: {data['error']}")
                        except:
                            pass
            
            if tools_result is not None:
                return tools_result
            else:
                raise RuntimeError("未能從 SSE 連接取得工具列表")
                
        except Exception as e:
            logger.error(f"[SSEProvider] {self.name}: SSE 連接失敗 - {e}")
            raise
    
    async def _fetch_tools(self) -> List[Dict[str, Any]]:
        """從遠端 API 取得工具列表"""
        if not self.client:
            raise RuntimeError("HTTP 客戶端未初始化")
        
        try:
            logger.info(f"[SSEProvider] {self.name}: 嘗試使用 SSE 協議連接")
            return await self._fetch_tools_via_sse()
        except Exception as e:
            logger.warning(f"[SSEProvider] {self.name}: SSE 協議失敗 - {e}")
            raise
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        if self.cached_tools:
            return self.cached_tools
        
        self.cached_tools = await self._fetch_tools()
        return self.cached_tools
    
    async def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """執行工具 - 建立臨時 SSE 連接並完成完整握手"""
        if not self.client:
            raise RuntimeError("客戶端未初始化")
        
        try:
            # 準備 headers
            headers = dict(self.headers)
            headers["Accept"] = "text/event-stream"
            headers["Cache-Control"] = "no-cache"
            
            post_headers = dict(self.headers)
            post_headers["Content-Type"] = "application/json"
            
            # 使用遞增的 request_id
            self._request_counter += 1
            init_request_id = 1
            call_request_id = 2
            
            call_request = {
                "jsonrpc": "2.0",
                "id": call_request_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            logger.info(f"[SSEProvider] {self.name}: 調用工具 {tool_name}, 參數: {arguments}")
            
            result = None
            base_url = self.url.rsplit("/", 1)[0]
            
            # 準備帶有過濾參數的 URL
            url = self.url
            if "?" in url:
                url += f"&server_names={self.name}"
            else:
                url += f"?server_names={self.name}"
            
            # 建立臨時 SSE 連接
            async with aconnect_sse(self.client, "GET", url, headers=headers, timeout=20.0) as event_source:
                temp_messages_url = None
                endpoint_received = False
                init_sent = False
                init_received = False
                initialized_sent = False
                call_sent = False
                
                # 單一事件循環
                async for sse in event_source.aiter_sse():
                    # 1. 獲取 endpoint
                    if sse.event == "endpoint" and not endpoint_received:
                        endpoint_url = sse.data.strip()
                        if "session_id=" in endpoint_url:
                            if endpoint_url.startswith("http"):
                                temp_messages_url = endpoint_url
                            else:
                                temp_messages_url = f"{base_url}{endpoint_url}"
                            logger.info(f"[SSEProvider] {self.name}: 臨時 session: {temp_messages_url}")
                            endpoint_received = True
                    
                    # 2. 發送 initialize
                    if endpoint_received and not init_sent:
                        init_req = {
                            "jsonrpc": "2.0",
                            "id": init_request_id,
                            "method": "initialize",
                            "params": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {},
                                "clientInfo": {"name": "mcp-platform", "version": "1.0.0"}
                            }
                        }
                        
                        resp = await self.client.post(temp_messages_url, json=init_req, headers=post_headers)
                        if resp.status_code not in [200, 202]:
                            raise RuntimeError(f"Initialize 失敗: {resp.status_code}")
                        
                        init_sent = True
                        continue
                    
                    # 3. 處理 initialize 響應
                    if init_sent and not init_received and sse.data:
                        try:
                            data = json.loads(sse.data)
                            if data.get("id") == init_request_id:
                                init_received = True
                        except:
                            pass
                    
                    # 4. 發送 initialized
                    if init_received and not initialized_sent:
                        notif = {
                            "jsonrpc": "2.0",
                            "method": "notifications/initialized",
                            "params": {}
                        }
                        await self.client.post(temp_messages_url, json=notif, headers=post_headers)
                        initialized_sent = True
                    
                    # 5. 發送工具調用
                    if initialized_sent and not call_sent:
                        resp = await self.client.post(temp_messages_url, json=call_request, headers=post_headers)
                        logger.info(f"[SSEProvider] {self.name}: Tools/call 狀態: {resp.status_code}")
                        
                        if resp.status_code not in [200, 202]:
                            raise RuntimeError(f"Tools/call 失敗: {resp.status_code}")
                        
                        call_sent = True
                    
                    # 6. 處理工具調用響應
                    if call_sent and sse.data:
                        try:
                            data = json.loads(sse.data)
                            if data.get("id") == call_request_id:
                                if "result" in data:
                                    result = data["result"]
                                    logger.info(f"[SSEProvider] {self.name}: 工具調用成功")
                                    break
                                elif "error" in data:
                                    error_msg = data["error"].get("message", str(data["error"]))
                                    raise RuntimeError(f"工具調用錯誤: {error_msg}")
                        except json.JSONDecodeError:
                            pass
            
            if result is not None:
                return result
            else:
                raise RuntimeError("未能取得工具調用結果")
                
        except Exception as e:
            logger.error(f"[SSEProvider] {self.name}: 工具調用失敗 - {e}")
            raise
    
    async def health_check(self) -> bool:
        """健康檢查 - 探測伺服器是否在線"""
        if not self.client:
            return False
        
        # 優先檢查 SSE 端點本身是否可達 (GET /sse)
        # 這是最準確的方式，且能省去探測 /health 的 404 延遲
        check_urls = [
            self.url,
            f"{self.url.rsplit('/', 1)[0]}/health",
            f"{self.url}/health",
        ]
        
        for url in check_urls:
            try:
                logger.info(f"[SSEProvider] {self.name}: 正在探測: {url}")
                response = await self.client.get(url, headers=self.headers, timeout=5.0)
                
                # 代表伺服器有在運行 (即使是 404/405)
                if response.status_code < 500:
                    logger.info(f"[SSEProvider] {self.name}: 伺服器已響應 (狀態碼: {response.status_code})")
                    return True
            except Exception as e:
                logger.debug(f"[SSEProvider] {self.name}: 探測 {url} 失敗: {e}")
        
        return False
