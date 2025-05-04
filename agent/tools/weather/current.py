import logging
from datetime import datetime
from typing import Dict, Any, Optional

from agent.exceptions import WeatherAPIError
from agent.tools.weather.base import BaseWeatherTool

logger = logging.getLogger(__name__)

class WeatherTool(BaseWeatherTool):
    """Tool to fetch current weather data for a given city."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        units: Optional[str] = None
    ):
        super().__init__(
            name="get_weather",
            description="Fetches current weather for a city. Usage: get_weather: [city name]",
            api_key=api_key,
            base_url=base_url,
            units=units
        )
    
    def execute(self, args: str) -> Dict[str, Any]:
        """
        Fetch current weather data for the specified city.
        """
        city = args.strip()
        
        try:
            data = self._make_weather_request("weather", city)
            
            return {
                "city": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "weather_condition": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except KeyError as e:
            logger.error(f"Unexpected API response format: {str(e)}")
            raise WeatherAPIError(f"Unexpected API response format: {str(e)}")