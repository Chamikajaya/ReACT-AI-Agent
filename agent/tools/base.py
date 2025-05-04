import logging
from typing import Dict, Any, Optional

from agent.exceptions import ToolExecutionError

logger = logging.getLogger(__name__)

class Tool:
    
    def __init__(self, name: str, description:str, required_args:bool = True):
        self.name = name
        self.description = description
        self.required_args = required_args
        
    
    def execute(self, args:str) -> Dict[str, Any]:  # args => string args for the tool and will return the results of the tool execution as a dictionary
        raise NotImplementedError("Subclass must implement execute method.")
    
    
    def safe_execute(self, args:str) -> Dict[str, Any]:
        try:
            logger.debug(f"Executing the tool {self.name} with args - {args}")
            return self.execute(args)
        except Exception as e:
            err_message = f"Error executing the tool {self.name} with args {args}"
            logger.error(err_message, exc_info=True)
            return {"error" : err_message}
    
    
    def __str__(self) -> str:
        return f"{self.name}:{self.description}"
            
    