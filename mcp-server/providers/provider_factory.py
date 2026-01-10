"""
Provider Factory - 根據配置建立對應的 Provider
"""
from typing import Dict, Any
import logging

from .base_provider import BaseMCPProvider
from .python_provider import PythonProvider
from .docker_provider import DockerProvider
from .nodejs_provider import NodeJSProvider
from .sse_provider import SSEProvider
from .npx_docker_provider import NPXDockerProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Provider 工廠類別 - 根據配置建立對應的 Provider"""
    
    # Provider 類型映射
    PROVIDERS = {
        "python": PythonProvider,
        "docker": DockerProvider,
        "nodejs": NodeJSProvider,
        "node": NodeJSProvider,  # 別名
        "npx": NPXDockerProvider,  # NPX 套件使用 Docker 容器
        "sse": SSEProvider,
        "remote": SSEProvider,  # 別名
    }
    
    @classmethod
    def create_provider(cls, name: str, config: Dict[str, Any]) -> BaseMCPProvider:
        """
        建立 Provider 實例
        
        Args:
            name: Provider 名稱
            config: Provider 配置
            
        Returns:
            Provider 實例
            
        Raises:
            ValueError: 不支援的 Provider 類型
        """
        # 優先檢查 command
        command = config.get("command", "").lower()
        
        if command == "npx":
            # npx 指令使用 NodeJSProvider (支援本地 npx 執行)
            provider_type = "nodejs"
        elif command == "python":
            provider_type = "python"
        elif command in ["node", "nodejs"]:
            provider_type = "nodejs"
        elif command in ["http", "https", "sse"]:
            provider_type = "sse"
        else:
            # 如果沒有 command 或無法識別,使用 type 欄位
            provider_type = config.get("type", "python").lower()
        
        provider_class = cls.PROVIDERS.get(provider_type)
        
        if not provider_class:
            supported_types = ", ".join(cls.PROVIDERS.keys())
            raise ValueError(
                f"不支援的 Provider 類型: {provider_type}. "
                f"支援的類型: {supported_types}"
            )
        
        logger.info(f"[ProviderFactory] 建立 {provider_type} Provider: {name}")
        return provider_class(name, config)
    
    @classmethod
    def get_supported_types(cls) -> list:
        """取得所有支援的 Provider 類型"""
        return list(cls.PROVIDERS.keys())
