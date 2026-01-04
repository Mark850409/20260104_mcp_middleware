"""
MCP Configuration Manager - 管理 MCP Server 配置
採用 Claude Desktop 的配置格式
"""
import os
import json
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MCPConfigManager:
    """MCP 配置管理器 - 處理配置的載入、儲存和驗證"""
    
    def __init__(self, config_file: str = "configs/mcp_servers.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置檔案路徑
        """
        self.config_file = Path(config_file)
        self.config_data: Dict[str, Any] = {"mcpServers": {}}
        self._ensure_config_dir()
        self.load_config()
    
    def _ensure_config_dir(self):
        """確保配置目錄存在"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果配置檔案不存在,建立預設配置
        if not self.config_file.exists():
            self._create_default_config()
    
    def _create_default_config(self):
        """建立預設配置檔案"""
        default_config = {
            "mcpServers": {}
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        logger.info(f"建立預設配置檔案: {self.config_file}")
    
    def load_config(self) -> Dict[str, Any]:
        """
        載入配置檔案
        
        Returns:
            配置資料字典
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            
            # 確保有 mcpServers 鍵
            if "mcpServers" not in self.config_data:
                self.config_data["mcpServers"] = {}
            
            # 替換環境變數
            self._resolve_env_vars()
            
            logger.info(f"成功載入配置檔案: {self.config_file}")
            return self.config_data
        except Exception as e:
            logger.error(f"載入配置檔案失敗: {e}")
            self.config_data = {"mcpServers": {}}
            return self.config_data
    
    def save_config(self) -> bool:
        """
        儲存配置到檔案
        
        Returns:
            是否成功儲存
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"成功儲存配置檔案: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"儲存配置檔案失敗: {e}")
            return False
    
    def _resolve_env_vars(self):
        """替換配置中的環境變數 ${VAR_NAME}"""
        def resolve_value(value):
            if isinstance(value, str):
                # 尋找 ${VAR_NAME} 格式的環境變數
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, value)
                for var_name in matches:
                    env_value = os.getenv(var_name, '')
                    value = value.replace(f'${{{var_name}}}', env_value)
                return value
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            return value
        
        self.config_data = resolve_value(self.config_data)
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """
        列出所有 MCP Server
        
        Returns:
            Server 列表
        """
        servers = []
        for name, config in self.config_data.get("mcpServers", {}).items():
            server_info = {
                "name": name,
                **config
            }
            servers.append(server_info)
        return servers
    
    def get_server(self, server_name: str) -> Optional[Dict[str, Any]]:
        """
        取得特定 Server 的配置
        
        Args:
            server_name: Server 名稱
            
        Returns:
            Server 配置,如果不存在則返回 None
        """
        return self.config_data.get("mcpServers", {}).get(server_name)
    
    def add_server(self, server_name: str, config: Dict[str, Any]) -> bool:
        """
        新增 MCP Server
        
        Args:
            server_name: Server 名稱
            config: Server 配置
            
        Returns:
            是否成功新增
        """
        if server_name in self.config_data.get("mcpServers", {}):
            logger.warning(f"Server 已存在: {server_name}")
            return False
        
        # 驗證配置
        if not self.validate_server_config(config):
            logger.error(f"Server 配置驗證失敗: {server_name}")
            return False
        
        self.config_data["mcpServers"][server_name] = config
        return self.save_config()
    
    def update_server(self, server_name: str, config: Dict[str, Any]) -> bool:
        """
        更新 MCP Server 配置
        
        Args:
            server_name: Server 名稱
            config: 新的配置
            
        Returns:
            是否成功更新
        """
        if server_name not in self.config_data.get("mcpServers", {}):
            logger.warning(f"Server 不存在: {server_name}")
            return False
        
        # 驗證配置
        if not self.validate_server_config(config):
            logger.error(f"Server 配置驗證失敗: {server_name}")
            return False
        
        self.config_data["mcpServers"][server_name] = config
        return self.save_config()
    
    def delete_server(self, server_name: str) -> bool:
        """
        刪除 MCP Server
        
        Args:
            server_name: Server 名稱
            
        Returns:
            是否成功刪除
        """
        if server_name not in self.config_data.get("mcpServers", {}):
            logger.warning(f"Server 不存在: {server_name}")
            return False
        
        del self.config_data["mcpServers"][server_name]
        return self.save_config()
    
    def toggle_server(self, server_name: str, enabled: bool) -> bool:
        """
        啟用/停用 MCP Server
        
        Args:
            server_name: Server 名稱
            enabled: 是否啟用
            
        Returns:
            是否成功切換
        """
        if server_name not in self.config_data.get("mcpServers", {}):
            logger.warning(f"Server 不存在: {server_name}")
            return False
        
        self.config_data["mcpServers"][server_name]["enabled"] = enabled
        return self.save_config()
    
    def validate_server_config(self, config: Dict[str, Any]) -> bool:
        """
        驗證 Server 配置
        
        Args:
            config: Server 配置
            
        Returns:
            配置是否有效
        """
        # 必要欄位
        required_fields = ["command", "args"]
        for field in required_fields:
            if field not in config:
                logger.error(f"缺少必要欄位: {field}")
                return False
        
        # 驗證 command 類型
        if not isinstance(config["command"], str):
            logger.error("command 必須是字串")
            return False
        
        # 驗證 args 類型
        if not isinstance(config["args"], list):
            logger.error("args 必須是陣列")
            return False
        
        # 驗證 env (如果存在)
        if "env" in config and not isinstance(config["env"], dict):
            logger.error("env 必須是字典")
            return False
        
        return True
    
    def get_enabled_servers(self) -> List[Dict[str, Any]]:
        """
        取得所有啟用的 Server
        
        Returns:
            啟用的 Server 列表
        """
        servers = self.list_servers()
        return [s for s in servers if s.get("enabled", True)]


# 建立全域配置管理器實例
config_manager = MCPConfigManager()
