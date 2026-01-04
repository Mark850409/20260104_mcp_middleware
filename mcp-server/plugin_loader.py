"""
MCP 插件載入器
自動發現和載入所有 MCP 工具插件
"""
import os
import sys
import importlib.util
import logging
from pathlib import Path
from typing import Dict, Any, Callable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PluginLoader:
    """MCP 插件載入器 - 自動發現和載入所有 *_mcp_tool.py 插件"""
    
    def __init__(self, plugin_dir: str):
        """
        初始化插件載入器
        
        Args:
            plugin_dir: 插件目錄路徑
        """
        self.plugin_dir = Path(plugin_dir).resolve()
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.loaded_plugins = []
        
        logger.info(f"[PluginLoader] 初始化插件載入器,目錄: {self.plugin_dir}")
    
    def discover_plugins(self) -> None:
        """
        自動發現所有 *_mcp_tool.py 檔案並載入
        """
        logger.info(f"[PluginLoader] 開始掃描插件...")
        
        # 尋找所有符合命名規範的插件檔案
        plugin_files = list(self.plugin_dir.glob("*_mcp_tool.py"))
        
        logger.info(f"[PluginLoader] 發現 {len(plugin_files)} 個插件檔案")
        
        for plugin_file in plugin_files:
            try:
                self.load_plugin(plugin_file)
            except Exception as e:
                logger.error(f"[PluginLoader] 載入插件失敗: {plugin_file.name}, 錯誤: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"[PluginLoader] 插件載入完成,共註冊 {len(self.tools)} 個工具")
    
    def load_plugin(self, plugin_path: Path) -> None:
        """
        載入單一插件模組
        
        Args:
            plugin_path: 插件檔案路徑
        """
        module_name = plugin_path.stem
        logger.info(f"[PluginLoader] 正在載入插件: {module_name}")
        
        try:
            # 動態載入模組
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None or spec.loader is None:
                logger.error(f"[PluginLoader] 無法載入模組規格: {module_name}")
                return
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # 檢查模組是否有 register_plugin 函數
            if not hasattr(module, 'register_plugin'):
                logger.warning(f"[PluginLoader] 插件 {module_name} 沒有 register_plugin 函數,跳過")
                return
            
            # 呼叫 register_plugin 取得工具註冊資訊
            register_func = getattr(module, 'register_plugin')
            plugin_tools = register_func()
            
            if not isinstance(plugin_tools, dict):
                logger.error(f"[PluginLoader] 插件 {module_name} 的 register_plugin 必須返回字典")
                return
            
            # 註冊所有工具
            for tool_name, tool_info in plugin_tools.items():
                if tool_name in self.tools:
                    logger.warning(f"[PluginLoader] 工具名稱衝突: {tool_name},將被 {module_name} 覆蓋")
                
                # 注入 server_name (plugin 名稱, 例如 'weather')
                if 'schema' in tool_info:
                    # 去掉 _mcp_tool 後綴作為 server_name
                    server_name = module_name.replace('_mcp_tool', '')
                    tool_info['schema']['server_name'] = server_name
                
                self.tools[tool_name] = tool_info
                logger.info(f"[PluginLoader] 註冊工具: {tool_name} (來自 {module_name})")
            
            self.loaded_plugins.append(module_name)
            logger.info(f"[PluginLoader] 插件 {module_name} 載入成功,註冊了 {len(plugin_tools)} 個工具")
            
        except Exception as e:
            logger.error(f"[PluginLoader] 載入插件 {module_name} 時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        取得所有已註冊的工具
        
        Returns:
            工具字典,格式: {
                "tool_name": {
                    "function": callable,
                    "is_async": bool,
                    "schema": {...}
                }
            }
        """
        return self.tools
    
    def get_tool(self, tool_name: str) -> Dict[str, Any]:
        """
        取得指定工具的資訊
        
        Args:
            tool_name: 工具名稱
            
        Returns:
            工具資訊字典,如果不存在則返回 None
        """
        return self.tools.get(tool_name)
    
    def list_tool_names(self) -> list:
        """
        列出所有工具名稱
        
        Returns:
            工具名稱列表
        """
        return list(self.tools.keys())
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """
        取得插件載入資訊
        
        Returns:
            包含載入統計的字典
        """
        return {
            "plugin_dir": str(self.plugin_dir),
            "loaded_plugins": self.loaded_plugins,
            "total_plugins": len(self.loaded_plugins),
            "total_tools": len(self.tools),
            "tools": self.list_tool_names()
        }
