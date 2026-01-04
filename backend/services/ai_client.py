"""
AI Client Service - 支援多家 AI 供應商的統一介面
支援: OpenAI, Google Gemini, Anthropic Claude
"""
import os
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class AIClient(ABC):
    """AI Client 抽象基類"""
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        發送聊天請求
        
        Args:
            messages: 訊息列表
            tools: MCP 工具定義(可選)
        
        Returns:
            AI 回應
        """
        pass


class OpenAIClient(AIClient):
    """OpenAI API Client"""
    
    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 環境變數未設定")
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("請安裝 openai 套件: pip install openai")
    
    def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """使用 OpenAI API 進行對話"""
        try:
            # 準備請求參數
            params = {
                "model": self.model_name,
                "messages": messages
            }
            
            # 如果有提供工具,加入 tools 參數
            if tools:
                params["tools"] = self._convert_tools_to_openai_format(tools)
            
            # 發送請求
            response = self.client.chat.completions.create(**params)
            
            # 解析回應
            message = response.choices[0].message
            
            result = {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": []
            }
            
            # 處理工具調用
            if hasattr(message, 'tool_calls') and message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            
            return result
            
        except Exception as e:
            raise Exception(f"OpenAI API 錯誤: {str(e)}")
    
    def _convert_tools_to_openai_format(self, tools: List[Dict]) -> List[Dict]:
        """將 MCP 工具格式轉換為 OpenAI 格式"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            }
            for tool in tools
        ]


class GeminiClient(AIClient):
    """Google Gemini API Client"""
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name
        self.api_key = os.getenv('GOOGLE_API_KEY')
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY 環境變數未設定")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        except ImportError:
            raise ImportError("請安裝 google-generativeai 套件: pip install google-generativeai")
    
    def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """使用 Google Gemini API 進行對話"""
        try:
            import google.generativeai as genai
            
            # 將訊息轉換為 Gemini 格式
            prompt = self._convert_messages_to_prompt(messages)
            
            # 如果有工具,需要使用 function calling
            if tools:
                print(f"[Gemini] 收到 {len(tools)} 個工具")
                print(f"[Gemini] 工具列表: {[t.get('name') for t in tools]}")
                
                # Gemini 的工具格式
                try:
                    gemini_tools = self._convert_tools_to_gemini_format(tools)
                    print(f"[Gemini] 工具轉換成功,共 {len(gemini_tools)} 個")
                except Exception as e:
                    print(f"[Gemini] 工具轉換失敗: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    raise
                
                # 使用 generate_content 並傳入工具
                print(f"[Gemini] 正在呼叫 API (帶工具)...")
                response = self.model.generate_content(
                    prompt,
                    tools=gemini_tools
                )
                print(f"[Gemini] API 回應成功")
                
                # 檢查是否有 function call
                if response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call'):
                            # 有工具調用
                            print(f"[Gemini] 偵測到工具調用: {part.function_call.name}")
                            return {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": [{
                                    "id": "gemini_tool_call",
                                    "type": "function",
                                    "function": {
                                        "name": part.function_call.name,
                                        "arguments": str(dict(part.function_call.args))
                                    }
                                }]
                            }
                
                # 沒有工具調用,返回文字回應
                print(f"[Gemini] 沒有工具調用,返回文字回應")
                return {
                    "role": "assistant",
                    "content": response.text,
                    "tool_calls": []
                }
            else:
                # 沒有工具,直接發送請求
                print(f"[Gemini] 沒有工具,直接呼叫 API")
                response = self.model.generate_content(prompt)
                
                return {
                    "role": "assistant",
                    "content": response.text,
                    "tool_calls": []
                }
            
        except Exception as e:
            print(f"[Gemini] API 錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Gemini API 錯誤: {str(e)}")

    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """將訊息列表轉換為 Gemini 提示詞"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        return "\n".join(prompt_parts)
    
    def _convert_tools_to_gemini_format(self, tools: List[Dict]) -> List[Dict]:
        """將 MCP 工具格式轉換為 Gemini 格式"""
        import google.generativeai as genai
        
        gemini_tools = []
        for tool in tools:
            # Gemini 使用 FunctionDeclaration
            gemini_tools.append(
                genai.protos.Tool(
                    function_declarations=[
                        genai.protos.FunctionDeclaration(
                            name=tool["name"],
                            description=tool["description"],
                            parameters=genai.protos.Schema(
                                type=genai.protos.Type.OBJECT,
                                properties={
                                    k: genai.protos.Schema(type=genai.protos.Type.STRING)
                                    for k in tool["inputSchema"].get("properties", {}).keys()
                                },
                                required=tool["inputSchema"].get("required", [])
                            )
                        )
                    ]
                )
            )
        return gemini_tools


class ClaudeClient(AIClient):
    """Anthropic Claude API Client"""
    
    def __init__(self, model_name: str = "claude-3-sonnet-20240229"):
        self.model_name = model_name
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY 環境變數未設定")
        
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("請安裝 anthropic 套件: pip install anthropic")
    
    def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """使用 Anthropic Claude API 進行對話"""
        try:
            # 準備請求參數
            params = {
                "model": self.model_name,
                "max_tokens": 4096,
                "messages": messages
            }
            
            # 如果有提供工具,加入 tools 參數
            if tools:
                params["tools"] = self._convert_tools_to_claude_format(tools)
            
            # 發送請求
            response = self.client.messages.create(**params)
            
            # 解析回應
            content = response.content[0]
            
            result = {
                "role": "assistant",
                "content": content.text if hasattr(content, 'text') else "",
                "tool_calls": []
            }
            
            # 處理工具調用
            if hasattr(content, 'tool_use'):
                result["tool_calls"] = [
                    {
                        "id": content.id,
                        "type": "function",
                        "function": {
                            "name": content.name,
                            "arguments": content.input
                        }
                    }
                ]
            
            return result
            
        except Exception as e:
            raise Exception(f"Claude API 錯誤: {str(e)}")
    
    def _convert_tools_to_claude_format(self, tools: List[Dict]) -> List[Dict]:
        """將 MCP 工具格式轉換為 Claude 格式"""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["inputSchema"]
            }
            for tool in tools
        ]


class AIClientFactory:
    """AI Client 工廠類別"""
    
    @staticmethod
    def create_client(provider: str, model_name: str) -> AIClient:
        """
        建立 AI Client
        
        Args:
            provider: 供應商名稱 (openai, google, anthropic)
            model_name: 模型名稱
        
        Returns:
            對應的 AI Client 實例
        """
        if provider == "openai":
            return OpenAIClient(model_name)
        elif provider == "google":
            return GeminiClient(model_name)
        elif provider == "anthropic":
            return ClaudeClient(model_name)
        else:
            raise ValueError(f"不支援的供應商: {provider}")
