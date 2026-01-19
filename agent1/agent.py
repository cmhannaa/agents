# agent1/agent.py
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from elastic import log_before_model, after_model_callback

root_agent = Agent(
    model="gemini-2.5-flash-lite",
    name='agent1',
    description="A helpful weather assistant that answers user questions. This agent can also retrieve weather, time, and geographic coordinate information using the attached MCP tools.",
    instruction='Answer user questions to the best of your knowledge. Use MCP tools for weather/time/coordinates.',
    tools=[
        McpToolset(connection_params=SseConnectionParams(url="http://127.0.0.1:8000/sse")),
        PreloadMemoryTool()  # <-- memory tool to use memory
    ],
    before_model_callback=log_before_model,
)
