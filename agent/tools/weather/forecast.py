import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from agent.exceptions import WeatherAPIError
from agent.tools.weather.base import BaseWeatherTool

logger = logging.getLogger(__name__)

class ForecastTool(BaseWeatherTool):
    """Tool to fetch weather forecast for a given city."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        units: Optional[str] = None
    ):
        super().__init__(
            name="get_forecast",
            description="Fetches 5-day forecast for a city. Usage: get_forecast: [city name]",
            api_key=api_key,
            base_url=base_url,
            units=units
        )
    
    def execute(self, args: str) -> Dict[str, Any]:
        """
        Fetch 5-day forecast data for the specified city.
        """
        city = args.strip()
        
        try:
            data = self._make_weather_request("forecast", city)
            
            # Extract a simplified forecast (one entry per day)
            forecast_data = self._process_forecast_data(data["list"])
            
            return {
                "city": data["city"]["name"],
                "country": data["city"]["country"],
                "forecast": forecast_data
            }
            
        except KeyError as e:
            logger.error(f"Unexpected API response format: {str(e)}")
            raise WeatherAPIError(f"Unexpected API response format: {str(e)}")
    
    def _process_forecast_data(self, forecast_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process the raw forecast data to extract a simplified daily forecast.
        
        Args:
            forecast_list: Raw forecast data from the API
            
        Returns:
            List of daily forecasts (one entry per day, max 5 days)
        """
        forecast_data = []
        dates_processed = set()
        
        for item in forecast_list:
            # Convert timestamp to datetime
            dt = datetime.fromtimestamp(item["dt"])
            date_str = dt.strftime("%Y-%m-%d")
            
            # Take only one entry per day
            if date_str not in dates_processed:
                dates_processed.add(date_str)
                forecast_data.append({
                    "date": date_str,
                    "time": dt.strftime("%H:%M"),
                    "temperature": item["main"]["temp"],
                    "feels_like": item["main"]["feels_like"],
                    "humidity": item["main"]["humidity"],
                    "weather_condition": item["weather"][0]["main"],
                    "description": item["weather"][0]["description"]
                })
            
            # Limit to 5 days
            if len(forecast_data) >= 5:
                break
        
        return forecast_data