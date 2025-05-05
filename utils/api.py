import logging
import time
from typing import Dict, Any, Optional

import requests
from requests.exceptions import RequestException

from agent.exceptions import APIError
from utils.config import load_config

logger = logging.getLogger(__name__)

api_config = load_config()
DEFAULT_TIMEOUT = api_config.get("api", {}).get("default_timeout", 15)
MAX_RETRIES = api_config.get("api", {}).get("max_retries", 3)
RETRY_DELAY = api_config.get("api", {}).get("retry_delay", 1)


def make_request(
    url: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = MAX_RETRIES,
    retry_delay: int = RETRY_DELAY,
) -> Dict[str, Any]:
    """
    Make an HTTP request with retry logic and error handling.
    """
    method = method.upper()
    attempts = 0
    
    # Initialize default parameters if None
    if params is None:
        params = {}
    if headers is None:
        headers = {}
    
    while attempts < retries:
        attempts += 1
        try:
            logger.debug(f"Making {method} request to {url}")
            
            response = requests.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                json=json_data,
                timeout=timeout
            )
            
            logger.debug(f"Request {method} {url}: status={response.status_code}")
            
            # Raise an exception for 4XX/5XX status codes
            response.raise_for_status()
            
            # Parse and return JSON response
            try:
                return response.json()
            except ValueError:
                # If the response is not JSON, return the text
                return {"text": response.text}
                
        except RequestException as e:
            # Log the error
            logger.warning(f"Request failed (attempt {attempts}/{retries}): {str(e)}")
            
            # If we've used all our retries, raise an exception
            if attempts >= retries:
                raise APIError(f"Request failed after {retries} attempts: {str(e)}") from e
            
            # Wait before retrying
            time.sleep(retry_delay)