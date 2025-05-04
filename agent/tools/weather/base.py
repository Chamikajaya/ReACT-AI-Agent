import logging
import os
from typing import Dict, Any, Optional

from agent.tools.base import Tool
from utils.api import make_request
from agent.exceptions import WeatherAPIError, ConfigurationError
from utils.config import load_config

logger = logging.getLogger(__name__)

api_config = load_config()
DEFAULT_BASE_URL = api_config["api"]["weather_base_url"]
DEFAULT_UNITS = api_config["api"]["units"]

class BaseWeatherTool(Tool):
    """Base class for weather-related tools."""
    
    def __init__(
        self,
        name: str,
        description: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        units: Optional[str] = None
    ):
        """
        Initialize the weather tool.
        
        Args:
            name: Name of the tool
            description: Description of the tool
            api_key: OpenWeatherMap API key (defaults to environment variable)
            base_url: Base URL for the OpenWeatherMap API
            units: Units to use for weather data (metric, imperial, standard)
        """
        super().__init__(name=name, description=description)
        
        self.api_key = api_key or os.getenv("OPENWEATHERMAP_API_KEY")
        if not self.api_key:
            logger.warning("No OpenWeatherMap API key provided. Set OPENWEATHERMAP_API_KEY environment variable.")
        
        self.base_url = base_url or DEFAULT_BASE_URL
        self.units = units or DEFAULT_UNITS
    
    def _make_weather_request(self, endpoint: str, city: str) -> Dict[str, Any]:
        """
        Make a request to the weather API with  error handling.
        """
        if not self.api_key:
            raise ConfigurationError("OpenWeatherMap API key is required")
        
        url = f"{self.base_url}/{endpoint}"
        
        params = {
            "q": city,
            "appid": self.api_key,
            "units": self.units
        }
        
        try:
            return make_request(url=url, params=params)
        except Exception as e:
            logger.error(f"Failed to fetch weather data: {str(e)}")
            raise WeatherAPIError(f"Failed to fetch weather data: {str(e)}")