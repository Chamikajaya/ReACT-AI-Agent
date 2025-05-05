import os
import logging
import re
import json
from typing import Dict, Optional, Callable
from groq import Groq

from agent.tools.base import Tool
from agent.exceptions import LLMAPIError

logger = logging.getLogger(__name__)

class Agent:
    """
    An agent that implements the ReACT (Reasoning and Acting) pattern.
    
    The agent can use various tools to solve problems, thinking through
    each step before acting. It follows the loop:
    
    Thought -> Action -> Observation -> Thought -> ...
    """
    
    def __init__(
        self,
        tools: Optional[Dict[str, Tool]] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_iterations: int = 10,
        debug: bool = False
    ):
        """
        Initialize the agent with LLM settings and available tools.
        
        Args:
            tools: Dictionary of available tools
            model: LLM model name - I am using LLAMA model
            api_key: API key for the LLM provider
            temperature: Temperature parameter for the LLM
            max_iterations: Maximum iterations for the ReACT loop
            debug: Whether to print debug information
        """
        # Set up tools
        self.tools = tools or {}
        
        # LLM settings
        self.model = model or self._get_default_model()
        self.api_key = api_key
        self.temperature = temperature
        
        # ReACT loop settings
        self.max_iterations = max_iterations
        self.debug = debug
        
        # Initialize conversation history
        self.messages = []
        
        # Configure the LLM client
        self._configure_llm_client()
        
        # Create system prompt
        self.system_prompt = self._create_system_prompt()
    
    def _configure_llm_client(self) -> None:
        """
        Configure the Groq client.
        """
        api_key = self.api_key or os.environ.get("GROQ_API_KEY")
        
        if not api_key:
            raise ValueError("Groq API key not provided.")
        
        self.groq_client = Groq(api_key=api_key)
    
    def _get_default_model(self) -> str:
        """Get the default model name."""
        return os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        
    
    def add_tool(self, tool: Tool) -> None:
        """
        Add a tool to the agent's available tools.
        
        Args:
            tool: Tool instance to add
        """
        self.tools[tool.name] = tool
        # Update system prompt when tools change
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """
        Create the system prompt that defines the ReACT loop and available tools.
        
        Returns:
            System prompt string
        """
        # Create the tool descriptions section
        tools_description = ""
        for name, tool in self.tools.items():
            tools_description += f"{name}:\n{tool.description}\n\n"
        
        # Create the full system prompt
        system_prompt = f"""
        You run in a loop of Thought, Action, PAUSE, Observation.
        At the end of the loop you output an Answer.
        
        Use Thought to describe your thoughts about the question you have been asked.
        Use Action to run one of the actions available to you - then return PAUSE.
        Observation will be the result of running those actions.
        
        IMPORTANT: If you receive a greeting or non-weather query like "hello", "what's up", "how are you", simply respond with a friendly greeting and do not use any tools.
        
        IMPORTANT: If the user doesn't specify a location but has mentioned a location in a previous question, use that location.

        
        Your available actions are:
        
        {tools_description}
        
        Example session:
        
        Question: What's the weather in London and what will it be like in 3 days?
        Thought: I need to check the current weather in London.
        Action: get_weather: London
        PAUSE
        
        You will be called again with this:
        
        Observation: {{"city": "London", "country": "GB", "temperature": 18.5, "weather_condition": "Clouds", "humidity": 75, "wind_speed": 5.2, "description": "scattered clouds", "timestamp": "2025-05-05 13:45:22"}}
        
        Thought: I now have the current weather. To see what it will be like in 3 days, I need the forecast.
        Action: get_forecast: London
        PAUSE
        
        You will be called again with this:
        
        Observation: {{"city": "London", "country": "GB", "forecast": [{{"date": "2025-05-05", "temperature": 18.5, "weather_condition": "Clouds"}}, {{"date": "2025-05-06", "temperature": 19.2, "weather_condition": "Clear"}}, {{"date": "2025-05-07", "temperature": 17.8, "weather_condition": "Rain"}}, {{"date": "2025-05-08", "temperature": 16.5, "weather_condition": "Rain"}}, {{"date": "2025-05-09", "temperature": 18.0, "weather_condition": "Clouds"}}]}}
        
        Thought: Let me calculate the temperature difference between today and in 3 days.
        Action: calculate: 17.8 - 18.5
        PAUSE
        
        You will be called again with this:
        
        Observation: {{"result": -0.7}}
        
        Answer: The current weather in London is 18.5°C with scattered clouds. In 3 days (on May 7), it will be 17.8°C and rainy, which is 0.7°C cooler than today. You should plan for rainy conditions if you're going to be in London in 3 days.
        
        Now it's your turn. I'll give you a question, and you start the loop with your Thought.
        """
        
        return system_prompt.strip()
       
    
    def reset(self) -> None:
        """Reset the conversation history."""
        self.messages = [{"role": "system", "content": self.system_prompt}]
    
    def _call_llm(self) -> str:
        """
        Call the Groq API with the current conversation history.
        
        Returns:
            Model response text
            
        Raises:
            LLMAPIError: If the API call fails
        """
        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"Error calling Groq API: {str(e)}"
            logger.error(error_msg)
            raise LLMAPIError(error_msg)
    
    def _parse_action(self, response: str) -> Optional[Dict[str, str]]:
        """
        Parse an action from the model's response.
        
        Args:
            response: Model response text
        
        Uses regex to extract tool name and arguments from the LLM's response
      
        """
        # Look for Action: [tool_name]: [args] pattern
        action_match = re.search(r"Action: ([a-z_]+): (.+?)(?:\n|$)", response, re.IGNORECASE)
        
        if action_match:
            return {
                "tool": action_match.group(1),
                "args": action_match.group(2)
            }
        
        return None
    
    def run_loop(
        self, 
        query: str, 
        callback: Optional[Callable[[str], None]] = None,
        max_iterations: Optional[int] = None,
        reset_conversation=False
    ) -> str:
        """
        Run the ReACT loop until an answer is reached or max iterations exceeded.
        
        Args:
            query: The user's query
            callback: Optional callback function to receive intermediate results
            max_iterations: Override the default max iterations
            
        Returns:
            The final answer from the agent
        
        """
        # Use override max_iterations if provided
        max_iterations = max_iterations or self.max_iterations
        
        # Only reset if explicitly requested or this is the first query
        if reset_conversation or not self.messages:
            self.reset()
        
        # Add the user's query
        self.messages.append({"role": "user", "content": f"Question: {query}"})
        
        iteration = 0
        full_response = []
        
        while iteration < max_iterations:
            iteration += 1
            
            # Get response from LLM
            response = self._call_llm()
            self.messages.append({"role": "assistant", "content": response})
            full_response.append(response)
            
            # Call the callback if provided
            if callback:
                callback(response)
            
            # Print debug information if enabled
            if self.debug:
                print(f"\n--- Iteration {iteration} ---")
                print(response)
            
            # Check if we've reached an answer
            if "Answer:" in response:
                return "\n".join(full_response)
            
            # Check for PAUSE (indicating an action to execute)
            if "PAUSE" in response:
                action = self._parse_action(response)
                
                if action:
                    tool_name = action["tool"]
                    args = action["args"]
                    
                    # Execute the tool if it exists
                    if tool_name in self.tools:
                        try:
                            result = self.tools[tool_name].safe_execute(args)
                            observation = f"Observation: {json.dumps(result, indent=2)}"
                        except Exception as e:
                            observation = f"Observation: Error executing tool '{tool_name}': {str(e)}"
                    else:
                        available_tools = ", ".join(self.tools.keys())
                        observation = f"Observation: Tool '{tool_name}' not found. Available tools: {available_tools}"
                    
                    # Add the observation to the conversation
                    self.messages.append({"role": "user", "content": observation})
                    
                    # Call the callback if provided
                    if callback:
                        callback(observation)
                    
                    # Print debug information if enabled
                    if self.debug:
                        print(observation)
                else:
                    # No valid action found
                    observation = "Observation: Could not parse action. Please use the format 'Action: tool_name: arguments'"
                    self.messages.append({"role": "user", "content": observation})
                    
                    # Call the callback if provided
                    if callback:
                        callback(observation)
                    
                    # Print debug information if enabled
                    if self.debug:
                        print(observation)
            else:
                # No PAUSE or Action found
                observation = "Observation: Expected 'Action: tool_name: arguments' followed by 'PAUSE'. Please follow the format."
                self.messages.append({"role": "user", "content": observation})
                
                # Call the callback if provided
                if callback:
                    callback(observation)
                
                # Print debug information if enabled
                if self.debug:
                    print(observation)
        
        # If we reach here, we've exceeded the maximum iterations
        return "\n".join(full_response) + "\nExceeded maximum iterations without reaching an answer."