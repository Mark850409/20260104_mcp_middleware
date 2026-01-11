"""
LINE Messaging API 客戶端服務
處理 LINE BOT 的訊息發送、接收和驗證
"""
import hashlib
import hmac
import base64
import json
from typing import Dict, List, Optional, Any
import requests


class LineClient:
    """LINE Messaging API 客戶端"""
    
    LINE_API_BASE = "https://api.line.me/v2/bot"
    
    def __init__(self, channel_access_token: str, channel_secret: str):
        """
        初始化 LINE 客戶端
        
        Args:
            channel_access_token: LINE Channel Access Token
            channel_secret: LINE Channel Secret
        """
        # 移除 Token 前後的空格
        self.channel_access_token = channel_access_token.strip() if channel_access_token else ""
        self.channel_secret = channel_secret.strip() if channel_secret else ""
        
        # 調試日誌
        print(f"[LINE Client] Token 長度: {len(self.channel_access_token)}")
        print(f"[LINE Client] Token 前10字: {self.channel_access_token[:10] if len(self.channel_access_token) >= 10 else 'TOO_SHORT'}")
        print(f"[LINE Client] Secret 長度: {len(self.channel_secret)}")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}"
        }
    
    def verify_signature(self, body: str, signature: str) -> bool:
        """
        驗證 LINE Webhook 請求的簽章
        
        Args:
            body: 請求的原始 body (字串格式)
            signature: X-Line-Signature header 的值
            
        Returns:
            簽章是否有效
        """
        hash_value = hmac.new(
            self.channel_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        expected_signature = base64.b64encode(hash_value).decode('utf-8')
        return hmac.compare_digest(signature, expected_signature)
    
    def send_text_message(self, user_id: str, text: str) -> Dict[str, Any]:
        """
        發送文字訊息
        
        Args:
            user_id: LINE 使用者 ID
            text: 訊息內容
            
        Returns:
            API 回應
        """
        url = f"{self.LINE_API_BASE}/message/push"
        payload = {
            "to": user_id,
            "messages": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return {
                "success": True,
                "message": "訊息發送成功"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_messages(self, user_id: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        發送多則訊息
        
        Args:
            user_id: LINE 使用者 ID
            messages: 訊息列表 (最多 5 則)
            
        Returns:
            API 回應
        """
        if len(messages) > 5:
            return {
                "success": False,
                "error": "一次最多只能發送 5 則訊息"
            }
        
        url = f"{self.LINE_API_BASE}/message/push"
        payload = {
            "to": user_id,
            "messages": messages
        }
        
        try:
            print(f"[LINE API] 發送訊息到: {user_id}")
            print(f"[LINE API] 訊息數量: {len(messages)}")
            print(f"[LINE API] URL: {url}")
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            
            # 記錄響應狀態
            print(f"[LINE API] 響應狀態碼: {response.status_code}")
            
            # 如果失敗，記錄詳細錯誤
            if response.status_code != 200:
                print(f"[LINE API] 錯誤響應: {response.text}")
                print(f"[LINE API] 請求 Headers: {self.headers}")
                print(f"[LINE API] 請求 Payload: {json.dumps(payload, ensure_ascii=False)}")
            
            response.raise_for_status()
            return {
                "success": True,
                "message": "訊息發送成功"
            }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"[LINE API] 發送失敗: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def reply_message(self, reply_token: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        回覆訊息 (使用 reply token)
        
        Args:
            reply_token: LINE 提供的 reply token
            messages: 訊息列表 (最多 5 則)
            
        Returns:
            API 回應
        """
        if len(messages) > 5:
            return {
                "success": False,
                "error": "一次最多只能回覆 5 則訊息"
            }
        
        url = f"{self.LINE_API_BASE}/message/reply"
        payload = {
            "replyToken": reply_token,
            "messages": messages
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return {
                "success": True,
                "message": "訊息回覆成功"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        取得使用者資料
        
        Args:
            user_id: LINE 使用者 ID
            
        Returns:
            使用者資料或 None
        """
        url = f"{self.LINE_API_BASE}/profile/{user_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"取得使用者資料失敗: {str(e)}")
            return None
    
    def send_flex_message(self, user_id: str, alt_text: str, contents: Dict[str, Any]) -> Dict[str, Any]:
        """
        發送 Flex Message
        
        Args:
            user_id: LINE 使用者 ID
            alt_text: 替代文字 (在不支援 Flex Message 的環境顯示)
            contents: Flex Message 內容
            
        Returns:
            API 回應
        """
        url = f"{self.LINE_API_BASE}/message/push"
        payload = {
            "to": user_id,
            "messages": [
                {
                    "type": "flex",
                    "altText": alt_text,
                    "contents": contents
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return {
                "success": True,
                "message": "Flex Message 發送成功"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }


def create_line_client(channel_access_token: str, channel_secret: str) -> LineClient:
    """
    建立 LINE 客戶端實例
    
    Args:
        channel_access_token: LINE Channel Access Token
        channel_secret: LINE Channel Secret
        
    Returns:
        LineClient 實例
    """
    return LineClient(channel_access_token, channel_secret)
