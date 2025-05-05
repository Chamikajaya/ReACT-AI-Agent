import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

def load_config(default_values: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Load configuration from config.json in the project root.
    
    Args:
        default_values: Dictionary of default values to use if config file is not found
        
    Returns:
        Dictionary containing configuration values
    """
    try:
        # Get the project root directory (parent of the utils directory)
        root_dir = Path(__file__).parent.parent
        config_path = root_dir / "config.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        logger.debug(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.warning(f"Failed to load config.json: {str(e)}. Using default values.")
        return default_values or {}