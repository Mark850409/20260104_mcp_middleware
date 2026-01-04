import os
import httpx
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()


# ============================================
# 純函數版本 (供 server.py 使用)
# ============================================

async def get_weather_func(city: str, api_key: Optional[str] = None) -> str:
    """
    獲取指定城市的天氣信息 (純函數版本)
    
    Args:
        city (str): 城市名稱
        api_key (str, optional): API 金鑰,如果不提供則從環境變數讀取
        
    Returns:
        str: 天氣信息
    """
    try:
        # 檢查 API KEY
        weather_api_key = api_key or os.getenv("WEATHER_API_KEY")
        if not weather_api_key:
            return "錯誤:未設置 WEATHER_API_KEY 環境變數"

        # 設定 API URL
        api_url = "https://api.weatherapi.com/v1/current.json"
        
        # 設定請求頭和參數
        headers = {
            "accept": "application/json"
        }
        
        params = {
            "key": weather_api_key,
            "q": city
        }
        
        logger.info(f"正在查詢 {city} 的天氣信息...")
        
        # 發送請求
        async with httpx.AsyncClient() as client:
            response = await client.get(
                api_url, 
                headers=headers, 
                params=params, 
                timeout=10
            )
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"API 請求錯誤:狀態碼 {response.status_code}, 回應: {error_text}")
                return f"API 請求錯誤:無法獲取 {city} 的天氣信息"
            
            data = response.json()
        
        # 解析回應
        weather_text = data['current']['condition']['text']
        temperature = data['current']['temp_c']
        feels_like = data['current']['feelslike_c']
        humidity = data['current']['humidity']
        wind_kph = data['current']['wind_kph']
        wind_dir = data['current']['wind_dir']
        
        # 格式化回應
        weather_info = f"""
【{city} 天氣信息】

天氣狀況:{weather_text}
溫度:{temperature}°C (體感溫度:{feels_like}°C)
濕度:{humidity}%
風速:{wind_kph} km/h ({wind_dir})

資料來源:WeatherAPI.com
查詢時間:{data['current']['last_updated']}
"""
        
        logger.info(f"成功獲取 {city} 的天氣信息")
        return weather_info

    except httpx.RequestError as e:
        logger.error(f"請求錯誤: {e}")
        return f"請求錯誤:無法連接到天氣 API ({str(e)})"
    except KeyError as e:
        logger.error(f"數據解析錯誤: {e}")
        return f"數據解析錯誤:API 返回的數據格式不符合預期 ({str(e)})"
    except Exception as e:
        logger.error(f"發生未知錯誤: {e}")
        return f"發生錯誤:{str(e)}"


async def get_forecast_func(city: str, days: int = 3, api_key: Optional[str] = None) -> str:
    """
    獲取指定城市的天氣預報 (純函數版本)
    
    Args:
        city (str): 城市名稱
        days (int): 預報天數 (1-7)
        api_key (str, optional): API 金鑰,如果不提供則從環境變數讀取
        
    Returns:
        str: 天氣預報信息
    """
    try:
        # 檢查 API KEY
        weather_api_key = api_key or os.getenv("WEATHER_API_KEY")
        if not weather_api_key:
            return "錯誤:未設置 WEATHER_API_KEY 環境變數"

        # 驗證天數參數
        if days < 1 or days > 7:
            return "錯誤:預報天數必須在 1-7 之間"

        # 設定 API URL
        api_url = "https://api.weatherapi.com/v1/forecast.json"
        
        # 設定請求頭和參數
        headers = {
            "accept": "application/json"
        }
        
        params = {
            "key": weather_api_key,
            "q": city,
            "days": days
        }
        
        logger.info(f"正在查詢 {city} 的 {days} 天天氣預報...")
        
        # 發送請求
        async with httpx.AsyncClient() as client:
            response = await client.get(
                api_url, 
                headers=headers, 
                params=params, 
                timeout=10
            )
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"API 請求錯誤:狀態碼 {response.status_code}, 回應: {error_text}")
                return f"API 請求錯誤:無法獲取 {city} 的天氣預報"
            
            data = response.json()
        
        # 解析回應
        forecast_days = data['forecast']['forecastday']
        
        # 格式化回應
        forecast_info = f"【{city} {days} 天天氣預報】\n\n"
        
        for day in forecast_days:
            date = day['date']
            condition = day['day']['condition']['text']
            max_temp = day['day']['maxtemp_c']
            min_temp = day['day']['mintemp_c']
            
            forecast_info += f"日期:{date}\n"
            forecast_info += f"天氣狀況:{condition}\n"
            forecast_info += f"最高溫度:{max_temp}°C\n"
            forecast_info += f"最低溫度:{min_temp}°C\n\n"
        
        forecast_info += "資料來源:WeatherAPI.com"
        
        logger.info(f"成功獲取 {city} 的天氣預報")
        return forecast_info

    except httpx.RequestError as e:
        logger.error(f"請求錯誤: {e}")
        return f"請求錯誤:無法連接到天氣 API ({str(e)})"
    except KeyError as e:
        logger.error(f"數據解析錯誤: {e}")
        return f"數據解析錯誤:API 返回的數據格式不符合預期 ({str(e)})"
    except Exception as e:
        logger.error(f"發生未知錯誤: {e}")
        return f"發生錯誤:{str(e)}"


def get_service_info_func() -> str:
    """獲取天氣服務的基本信息 (純函數版本)"""
    return """
【天氣查詢服務信息】

此服務提供以下功能:
1. 獲取指定城市的當前天氣信息
2. 獲取指定城市的天氣預報 (1-7 天)
3. 自動處理錯誤和異常情況

使用方法:
- 使用 get_weather 工具獲取當前天氣
- 使用 get_forecast 工具獲取天氣預報
- 使用 get_service_info 工具獲取服務信息

參數說明:
- city: 城市名稱 (例如:Taipei, Tokyo, New York)
- days: 預報天數 (1-7)

環境配置:
- WEATHER_API_KEY: WeatherAPI.com 的 API 金鑰

資料來源:WeatherAPI.com
"""


# ============================================
# FastMCP 版本 (可作為獨立 MCP 服務運行)
# ============================================

try:
    from mcp.server import FastMCP
    
    # 創建一個 MCP 服務器
    mcp = FastMCP("天氣查詢服務")
    
    @mcp.tool()
    async def get_weather(city: str) -> str:
        """
        獲取指定城市的天氣信息
        
        Args:
            city (str): 城市名稱
            
        Returns:
            str: 天氣信息
        """
        return await get_weather_func(city)
    
    @mcp.tool()
    async def get_forecast(city: str, days: int = 3) -> str:
        """
        獲取指定城市的天氣預報
        
        Args:
            city (str): 城市名稱
            days (int): 預報天數 (1-7)
            
        Returns:
            str: 天氣預報信息
        """
        return await get_forecast_func(city, days)
    
    @mcp.tool()
    def get_service_info() -> str:
        """獲取天氣服務的基本信息"""
        return get_service_info_func()
    
    def check_environment() -> bool:
        """檢查必要的環境變數"""
        required_vars = ["WEATHER_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"缺少必要的環境變數: {', '.join(missing_vars)}")
            return False
        return True
    
    if __name__ == "__main__":
        if not check_environment():
            logger.warning("環境變數設置不完整,部分功能可能無法正常使用")
        
        logger.info("啟動天氣查詢 MCP 服務...")
        mcp.run()

except ImportError:
    logger.warning("FastMCP 未安裝,僅提供純函數版本")
    mcp = None


# ============================================
# 插件註冊函數 (供 plugin_loader 使用)
# ============================================

def register_plugin():
    """
    註冊天氣工具插件
    
    Returns:
        dict: 工具註冊資訊
    """
    # 建立非同步包裝函數
    async def get_weather_wrapper(city: str) -> str:
        """天氣查詢工具包裝器"""
        api_key = os.getenv('WEATHER_API_KEY')
        return await get_weather_func(city, api_key)
    
    async def get_forecast_wrapper(city: str, days: int = 3) -> str:
        """天氣預報工具包裝器"""
        api_key = os.getenv('WEATHER_API_KEY')
        return await get_forecast_func(city, days, api_key)
    
    return {
        "get_weather": {
            "function": get_weather_wrapper,
            "is_async": True,
            "schema": {
                "name": "get_weather",
                "description": "獲取指定城市的當前天氣信息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名稱 (例如: Taipei, Tokyo, New York)"
                        }
                    },
                    "required": ["city"]
                }
            }
        },
        "get_forecast": {
            "function": get_forecast_wrapper,
            "is_async": True,
            "schema": {
                "name": "get_forecast",
                "description": "獲取指定城市的天氣預報",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名稱"
                        },
                        "days": {
                            "type": "integer",
                            "description": "預報天數 (1-7)",
                            "default": 3
                        }
                    },
                    "required": ["city"]
                }
            }
        },
        "get_weather_info": {
            "function": get_service_info_func,
            "is_async": False,
            "schema": {
                "name": "get_weather_info",
                "description": "獲取天氣服務的基本信息",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    }
