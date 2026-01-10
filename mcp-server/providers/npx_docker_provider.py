"""
NPX Docker Provider - 為 NPX 套件動態建立 Docker 容器
每個 NPX 套件都會在獨立的 Node.js 容器中執行
"""
import asyncio
import json
import logging
from typing import Dict, Any, List
import docker
from docker.errors import DockerException, NotFound
import time

from .base_provider import BaseMCPProvider

logger = logging.getLogger(__name__)


class NPXDockerProvider(BaseMCPProvider):
    """NPX Docker Provider - 在 Docker 容器中執行 NPX 套件"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.docker_client = None
        self.container = None
        self.container_name = f"mcp-npx-{name}"
        self.tools_cache = []
        self.package_name = None
        self.extra_args = []
        self.request_id = 0
    
    async def start(self) -> bool:
        """啟動 NPX Docker Provider - 建立並啟動容器"""
        try:
            # 解析配置
            command = self.config.get("command", "")
            args = self.config.get("args", [])
            
            # 檢查是否為 npx 指令
            if command.lower() != "npx":
                logger.error(f"[NPXDockerProvider] {self.name}: command 必須是 'npx'")
                return False
            
            # 解析 args: ["-y", "package-name", ...其他參數]
            if len(args) < 2 or args[0] != "-y":
                logger.error(f"[NPXDockerProvider] {self.name}: args 格式錯誤,應為 ['-y', 'package-name', ...]")
                return False
            
            self.package_name = args[1]
            self.extra_args = args[2:] if len(args) > 2 else []
            
            logger.info(f"[NPXDockerProvider] {self.name}: 準備啟動容器執行 {self.package_name}")
            
            # 初始化 Docker 客戶端
            try:
                self.docker_client = docker.from_env()
                logger.info(f"[NPXDockerProvider] {self.name}: Docker 客戶端初始化成功")
            except DockerException as e:
                logger.error(f"[NPXDockerProvider] {self.name}: 無法連接到 Docker - {e}")
                return False
            
            # 停止並移除舊容器 (如果存在)
            await self._cleanup_old_container()
            
            # 準備環境變數
            env_vars = self.config.get("env", {})
            environment = {
                # npm 配置
                "NPM_CONFIG_UPDATE_NOTIFIER": "false",
                "NPM_CONFIG_FUND": "false",
                "NPM_CONFIG_AUDIT": "false",
                "NPM_CONFIG_LOGLEVEL": "error",
                # 設定 HOME 目錄讓 npm 可以建立快取
                "HOME": "/tmp",
                # 設定 npm 快取和前綴路徑到 /tmp,避免權限問題
                "NPM_CONFIG_CACHE": "/tmp/.npm",
                "NPM_CONFIG_PREFIX": "/tmp/.npm-global",
                # 清除可能干擾的 PATH
                "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            }
            # 合併使用者提供的環境變數
            environment.update({k: str(v) for k, v in env_vars.items() if v})
            
            # 建立並啟動容器
            try:
                logger.info(f"[NPXDockerProvider] {self.name}: 建立容器...")
                
                # 構建 npx 命令
                # 使用 --yes 而不是 -y,並確保在 /tmp 目錄執行
                cmd_parts = ["npx", "--yes", self.package_name] + self.extra_args
                cmd_str = " ".join(cmd_parts)
                
                # 使用 sh -c 並在 /tmp 目錄執行,確保 npm 有寫入權限
                full_cmd = f"cd /tmp && exec {cmd_str}"
                
                self.container = self.docker_client.containers.create(
                    image="node:20-alpine",
                    name=self.container_name,
                    command=["sh", "-c", full_cmd],
                    environment=environment,
                    stdin_open=True,
                    tty=False,
                    detach=True,
                    remove=False,
                    network_mode="bridge",
                    # 設定工作目錄
                    working_dir="/tmp"
                )
                
                logger.info(f"[NPXDockerProvider] {self.name}: 容器已建立 - {self.container.id[:12]}")
                
                # 啟動容器
                self.container.start()
                logger.info(f"[NPXDockerProvider] {self.name}: 容器已啟動")
                
                # 等待容器啟動和 npx 安裝套件
                await asyncio.sleep(5)
                
                # 檢查容器狀態
                self.container.reload()
                if self.container.status != "running":
                    logs = self.container.logs().decode('utf-8', errors='ignore')
                    logger.error(f"[NPXDockerProvider] {self.name}: 容器未正常運行\n日誌:\n{logs}")
                    return False
                
                logger.info(f"[NPXDockerProvider] {self.name}: 容器運行中,開始 MCP 初始化")
                
                # MCP 初始化握手
                await self._initialize_mcp()
                
                # 取得工具列表
                try:
                    self.tools_cache = await self._fetch_tools()
                    logger.info(f"[NPXDockerProvider] {self.name}: 成功載入 {len(self.tools_cache)} 個工具")
                except Exception as e:
                    logger.warning(f"[NPXDockerProvider] {self.name}: 無法載入工具列表 - {e}")
                    # 顯示容器日誌以便除錯
                    logs = self.container.logs().decode('utf-8', errors='ignore')
                    logger.error(f"[NPXDockerProvider] {self.name}: 容器日誌:\n{logs}")
                
                self.is_running = True
                return True
                
            except DockerException as e:
                logger.error(f"[NPXDockerProvider] {self.name}: 建立容器失敗 - {e}")
                return False
            
        except Exception as e:
            logger.error(f"[NPXDockerProvider] {self.name}: 啟動失敗 - {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def stop(self) -> bool:
        """停止 NPX Docker Provider"""
        try:
            if self.container:
                logger.info(f"[NPXDockerProvider] {self.name}: 停止容器...")
                self.container.stop(timeout=5)
                self.container.remove()
                self.container = None
            
            if self.docker_client:
                self.docker_client.close()
                self.docker_client = None
            
            self.is_running = False
            logger.info(f"[NPXDockerProvider] {self.name}: 已停止")
            return True
        except Exception as e:
            logger.error(f"[NPXDockerProvider] {self.name}: 停止失敗 - {e}")
            return False
    
    async def _cleanup_old_container(self):
        """清理舊的容器"""
        try:
            old_container = self.docker_client.containers.get(self.container_name)
            logger.info(f"[NPXDockerProvider] {self.name}: 發現舊容器,正在移除...")
            old_container.stop(timeout=5)
            old_container.remove()
        except NotFound:
            pass  # 沒有舊容器,正常
        except Exception as e:
            logger.warning(f"[NPXDockerProvider] {self.name}: 清理舊容器時出錯 - {e}")
    
    async def _initialize_mcp(self):
        """MCP 協定初始化握手"""
        try:
            logger.info(f"[NPXDockerProvider] {self.name}: 開始 MCP 初始化握手")
            
            # 1. 發送 initialize 請求
            init_result = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "mcp-platform",
                    "version": "1.0.0"
                }
            })
            logger.info(f"[NPXDockerProvider] {self.name}: initialize 成功 - {init_result}")
            
            # 2. 發送 initialized 通知
            await self._send_notification("notifications/initialized")
            logger.info(f"[NPXDockerProvider] {self.name}: initialized 通知已發送")
            
        except Exception as e:
            logger.warning(f"[NPXDockerProvider] {self.name}: MCP 初始化失敗 - {e}")
            raise
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Any:
        """透過 exec 發送 JSON-RPC 請求並讀取回應"""
        if not self.container:
            raise RuntimeError("容器未啟動")
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self.request_id
        }
        
        request_str = json.dumps(request) + "\n"
        logger.debug(f"[NPXDockerProvider] {self.name}: 發送請求: {request_str.strip()}")
        
        try:
            # 使用 exec_run 執行 echo 命令將 JSON 寫入容器的 stdin
            # 然後從 stdout 讀取回應
            exec_result = await asyncio.to_thread(
                self.container.exec_run,
                f'sh -c \'echo {json.dumps(request_str)} > /proc/1/fd/0 && head -n 1 /proc/1/fd/1\'',
                demux=True,
                stdin=False,
                tty=False
            )
            
            exit_code = exec_result.exit_code
            stdout, stderr = exec_result.output
            
            if exit_code != 0:
                stderr_str = stderr.decode('utf-8', errors='ignore') if stderr else ""
                logger.error(f"[NPXDockerProvider] {self.name}: exec 失敗 (exit {exit_code}): {stderr_str}")
                raise RuntimeError(f"exec 失敗: {stderr_str}")
            
            if not stdout:
                logger.error(f"[NPXDockerProvider] {self.name}: 沒有收到回應")
                raise RuntimeError("沒有收到回應")
            
            response_str = stdout.decode('utf-8', errors='ignore').strip()
            logger.debug(f"[NPXDockerProvider] {self.name}: 收到回應: {response_str}")
            
            response = json.loads(response_str)
            
            if "error" in response:
                raise RuntimeError(f"RPC 錯誤: {response['error']}")
            
            return response.get("result")
            
        except json.JSONDecodeError as e:
            logger.error(f"[NPXDockerProvider] {self.name}: JSON 解析失敗 - {e}")
            raise RuntimeError(f"JSON 解析失敗: {e}")
        except Exception as e:
            logger.error(f"[NPXDockerProvider] {self.name}: 發送請求失敗 - {e}")
            raise
    
    async def _send_notification(self, method: str, params: Dict[str, Any] = None) -> None:
        """發送 JSON-RPC 通知"""
        if not self.container:
            raise RuntimeError("容器未啟動")
        
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        notification_str = json.dumps(notification) + "\n"
        logger.debug(f"[NPXDockerProvider] {self.name}: 發送通知: {notification_str.strip()}")
        
        try:
            # 通知不需要等待回應
            await asyncio.to_thread(
                self.container.exec_run,
                f'sh -c \'echo {json.dumps(notification_str)} > /proc/1/fd/0\'',
                stdin=False,
                tty=False
            )
        except Exception as e:
            logger.warning(f"[NPXDockerProvider] {self.name}: 發送通知失敗 - {e}")
    
    async def _fetch_tools(self) -> List[Dict[str, Any]]:
        """從容器取得工具列表"""
        try:
            result = await self._send_request("tools/list")
            if isinstance(result, dict) and "tools" in result:
                return result["tools"]
            elif isinstance(result, list):
                return result
            return []
        except Exception as e:
            logger.error(f"[NPXDockerProvider] {self.name}: 取得工具列表失敗 - {e}")
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
            
            logger.info(f"[NPXDockerProvider] {self.name}: 工具 {tool_name} 執行成功")
            return result
            
        except Exception as e:
            logger.error(f"[NPXDockerProvider] {self.name}: 執行工具 {tool_name} 失敗 - {e}")
            raise
    
    async def health_check(self) -> bool:
        """健康檢查"""
        if not self.container:
            return False
        
        try:
            self.container.reload()
            return self.container.status == "running"
        except Exception:
            return False
