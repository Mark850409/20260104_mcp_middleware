"""
Python Provider - 透過 subprocess 執行 Python MCP 工具
支援現有的 *_mcp_tool.py 插件格式
"""
import os
import sys
import asyncio
import importlib.util
from pathlib import Path
from typing import Dict, Any, List
import logging

from .base_provider import BaseMCPProvider

logger = logging.getLogger(__name__)


class PythonProvider(BaseMCPProvider):
    """Python Provider - 執行 Python 腳本形式的 MCP 工具"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.module = None
    
    async def start(self) -> bool:
        """啟動 Python Provider - 載入 Python 模組"""
        try:
            # 取得腳本路徑
            args = self.config.get("args", [])
            if not args:
                logger.error(f"[PythonProvider] {self.name}: 缺少 args 配置")
                return False
            
            script_path = args[0]
            
            # 如果是相對路徑,轉換為絕對路徑
            if not os.path.isabs(script_path):
                base_dir = os.path.dirname(os.path.dirname(__file__))
                script_path = os.path.join(base_dir, script_path)
            
            script_path = Path(script_path).resolve()
            
            if not script_path.exists():
                logger.error(f"[PythonProvider] {self.name}: 檔案不存在 {script_path}")
                return False
            
            # 動態載入模組
            module_name = f"mcp_provider_{self.name}"
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            
            if spec is None or spec.loader is None:
                logger.error(f"[PythonProvider] {self.name}: 無法載入模組規格")
                return False
            
            self.module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = self.module
            
            # 設定環境變數
            env_vars = self.config.get("env", {})
            for key, value in env_vars.items():
                if value:  # 只設定非空值
                    os.environ[key] = str(value)
            
            # 執行模組
            spec.loader.exec_module(self.module)
            
            # 檢查是否有 register_plugin 函數
            if not hasattr(self.module, 'register_plugin'):
                logger.error(f"[PythonProvider] {self.name}: 模組缺少 register_plugin 函數")
                return False
            
            # 註冊工具
            register_func = getattr(self.module, 'register_plugin')
            plugin_tools = register_func()
            
            if not isinstance(plugin_tools, dict):
                logger.error(f"[PythonProvider] {self.name}: register_plugin 必須返回字典")
                return False
            
            self.tools = plugin_tools
            self.is_running = True
            
            logger.info(f"[PythonProvider] {self.name}: 成功載入 {len(self.tools)} 個工具")
            return True
            
        except Exception as e:
            logger.error(f"[PythonProvider] {self.name}: 啟動失敗 - {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def stop(self) -> bool:
        """停止 Python Provider"""
        try:
            self.tools = {}
            self.module = None
            self.is_running = False
            logger.info(f"[PythonProvider] {self.name}: 已停止")
            return True
        except Exception as e:
            logger.error(f"[PythonProvider] {self.name}: 停止失敗 - {e}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        tools_list = []
        
        for tool_name, tool_info in self.tools.items():
            schema = tool_info.get("schema", {})
            tools_list.append({
                "name": tool_name,
                "description": schema.get("description", ""),
                "inputSchema": schema.get("inputSchema", {"type": "object", "properties": {}})
            })
        
        return tools_list
    
    async def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """執行工具"""
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在: {tool_name}")
        
        try:
            tool_info = self.tools[tool_name]
            func = tool_info["function"]
            is_async = tool_info.get("is_async", False)
            
            # 執行工具
            if is_async:
                result = await func(**arguments)
            else:
                result = func(**arguments)
            
            logger.info(f"[PythonProvider] {self.name}: 工具 {tool_name} 執行成功")
            return result
            
        except Exception as e:
            logger.error(f"[PythonProvider] {self.name}: 工具 {tool_name} 執行失敗 - {e}")
            raise
    
    async def health_check(self) -> bool:
        """健康檢查"""
        return self.is_running and len(self.tools) > 0
