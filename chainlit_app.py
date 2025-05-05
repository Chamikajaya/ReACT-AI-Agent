import os
import json
import asyncio
import chainlit as cl
from typing import Dict

from agent.react_agent import Agent
from agent.tools.weather import WeatherTool, ForecastTool
from agent.tools.calculation import CalculationTool
from agent.tools.base import Tool
from utils.config import load_config

def create_tools() -> Dict[str, Tool]:
    """Create and return the tools needed by the agent."""
    weather_tool = WeatherTool()
    forecast_tool = ForecastTool()
    calculation_tool = CalculationTool()
    
    return {
        weather_tool.name: weather_tool,
        forecast_tool.name: forecast_tool,
        calculation_tool.name: calculation_tool
    }

# Initialize the agent outside the chat handler for persistence
config = load_config()
tools = create_tools()
model = config.get("model") or os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
api_key = os.environ.get("GROQ_API_KEY")

agent = Agent(
    tools=tools,
    model=model,
    api_key=api_key,
    temperature=0.0,
    max_iterations=10,
    debug=False
)

@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session."""
    await cl.Message(
        content="👋 Welcome to the Weather ReACT Agent! Ask me any weather-related question."
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Process user messages."""
    user_query = message.content
    
    # Store the complete ReACT process as it unfolds
    process_content = []
    final_answer = None
    
    # Create a task queue to manage async callbacks
    callback_queue = asyncio.Queue()
    
    # Create a thinking message that we'll remove later
    thinking_msg = await cl.Message(content="Thinking...").send()
    
    # Worker to process callbacks from the queue
    async def process_callbacks():
        nonlocal final_answer
        iteration = 1
        
        while True:
            try:
                content = await callback_queue.get()
                
                # Process different parts of the ReACT output
                if "Thought:" in content:
                    process_content.append(f"**Iteration {iteration} - Thought**: {content.split('Thought:', 1)[1].strip().split('Action:', 1)[0].strip()}")
                
                if "Action:" in content and "PAUSE" in content:
                    action_text = content.split('Action:', 1)[1].strip().split('PAUSE', 1)[0].strip()
                    process_content.append(f"**Action**: `{action_text}`")
                
                if "Observation:" in content:
                    obs_text = content.split('Observation:', 1)[1].strip()
                    try:
                        # Format JSON observations nicely but avoid code blocks
                        json_data = json.loads(obs_text)
                        # Convert to a simplified format to avoid lengthy JSON
                        if isinstance(json_data, dict):
                            # Create a more compact representation
                            formatted_text = ", ".join([f"{k}: {v}" for k, v in json_data.items() 
                                                    if k in ['city', 'temperature', 'weather_condition', 'description']])
                            if not formatted_text:  # If none of those keys were present
                                formatted_text = str(json_data)
                        else:
                            formatted_text = str(json_data)
                        process_content.append(f"**Observation**: {formatted_text}")
                    except:
                        # If not valid JSON, use plain text
                        process_content.append(f"**Observation**: {obs_text}")
                    iteration += 1
                
                if "Answer:" in content:
                    final_answer = content.split('Answer:', 1)[1].strip()
                
                callback_queue.task_done()
            except Exception as e:
                print(f"Error in callback processing: {e}")
                callback_queue.task_done()
    
    # Start the processing task
    processor_task = asyncio.create_task(process_callbacks())
    
    # Synchronous callback for the agent
    def sync_callback(content: str):
        try:
            asyncio.create_task(callback_queue.put(content))
        except Exception as e:
            print(f"Error creating callback task: {e}")
    
    try:
        # Run the ReACT loop
        result = agent.run_loop(
            query=user_query,
            callback=sync_callback,
            reset_conversation=False  # Preserve context between queries
        )
        
        # Wait for all callbacks to be processed
        await asyncio.sleep(0.5)  # Small delay to ensure all callbacks are processed
        await callback_queue.join()
        
        # Cancel the processor task
        processor_task.cancel()
        try:
            await processor_task
        except asyncio.CancelledError:
            pass
        
        # Remove the thinking message
        await thinking_msg.remove()
        
        # Send the final answer as a new message
        if final_answer:
            await cl.Message(content=final_answer).send()
            
            # Create a message with the reasoning process directly in the content
            if process_content:
                # Create a single dropdown message with HTML details tag
                process_text = "\n\n".join(process_content)
                details_content = f"""<details>
🤖  ReACT reasoning process

{process_text}
</details>"""
                
                await cl.Message(content=details_content).send()
        else:
            await cl.Message(content="I wasn't able to get a clear answer. Please try asking in a different way.").send()
            
    except Exception as e:
        error_message = f"Error: {str(e)}"
        print(f"Exception in run_loop: {str(e)}")
        
        # Remove the thinking message
        await thinking_msg.remove()
        
        # Send error as a new message
        await cl.Message(content=error_message).send()