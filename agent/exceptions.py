"""
WeatherAgentError (base class)
├── ConfigurationError
├── APIError
│   ├── WeatherAPIError
│   └── LLMAPIError
├── ToolExecutionError
└── ToolNotFoundError
"""



class WeatherAgentError(Exception):
    """Base exception for all Weather Agent errors."""
    pass


class ConfigurationError(WeatherAgentError):
    """Error in the configuration of the Weather Agent."""
    pass


class APIError(WeatherAgentError):
    """Error when interacting with external APIs."""
    pass


class WeatherAPIError(APIError):
    """Error when interacting with the Weather API."""
    pass


class LLMAPIError(APIError):
    """Error when interacting with the LLM API."""
    pass


class ToolExecutionError(WeatherAgentError):
    """Error when executing a tool."""
    pass


class ToolNotFoundError(WeatherAgentError):
    """Error when a tool is not found."""
    pass