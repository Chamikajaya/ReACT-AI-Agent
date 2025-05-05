import argparse
import logging
import os
from typing import Dict

from agent.react_agent import Agent
from agent.tools.weather import WeatherTool, ForecastTool
from agent.tools.base import Tool  
from agent.tools.calculation import CalculationTool
from utils.config import load_config


logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Weather Agent - ReACT pattern implementation")
    
    parser.add_argument(
        "--model", 
        type=str,
        help="LLM model name"
    )
    
    parser.add_argument(
        "--api-key", 
        type=str,
        help="API key for Groq"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug output"
    )
    
    parser.add_argument(
        "--query", 
        type=str,
        help="Query to process (non-interactive mode)"
    )
    
    return parser.parse_args()

def create_tools() -> Dict[str, Tool]:
    """Create and return the tools needed by the agent."""
    # Weather tools need API key from environment
    weather_tool = WeatherTool()
    forecast_tool = ForecastTool()
    calculation_tool = CalculationTool()
    
    return {
        weather_tool.name: weather_tool,
        forecast_tool.name: forecast_tool,
        calculation_tool.name: calculation_tool
    }

def main():
    """Main entry point for the application."""
    args = parse_args()
    
    try:
        # Load configuration
        config = load_config()
        
        # Create tools
        tools = create_tools()
        
        # Get model from args, config, or environment
        model = args.model or config.get("model") or os.environ.get("GROQ_MODEL")
        
        # Get API key from args or environment
        api_key = args.api_key or os.environ.get("GROQ_API_KEY")
        
        # Create agent
        logger.info(f"Initializing agent with model={model}")
        agent = Agent(
            tools=tools,
            model=model,
            api_key=api_key,
            temperature=0.0,  # Default temperature
            max_iterations=10,  # Default max iterations
            debug=args.debug
        )
        
        # Define callback for interactive output
        def print_callback(message):
            print(message)
            print("-" * 40)
        
        
        print("\n" + "=" * 60)
        print("Weather Agent - ReACT Pattern Implementation")
        print("=" * 60 + "\n")
        print("Weather Agent initialized and ready for queries!")
        
        while True:
            try:
                user_query = input("\nEnter your weather query (or 'quit' to exit): ")
                
                if user_query.lower() in ['quit', 'exit', 'q']:
                    print("\nExiting Weather Agent. Goodbye!")
                    break
                
                print("\nRunning ReACT loop...\n")
                print("-" * 40)
                
                agent.run_loop(user_query, callback=print_callback)
                
                print("\nProcess complete!")
                
            except KeyboardInterrupt:
                print("\n\nExiting Weather Agent. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {str(e)}", exc_info=True)
                print(f"\nError: {str(e)}")
                print("Please try again.")
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())