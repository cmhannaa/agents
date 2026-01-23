from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm # For multimodel support
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts
from typing import Optional
from dotenv import load_dotenv
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.mcp_tool import McpToolset
from elastic import after_model_callback,before_model_callback
MODEL_GEMINI_2_0_FLASH = "gemini-2.5-flash"



import json

def clear_convo_json(path="conversation.json"):
    """Clears the contents of convo.json by writing an empty JSON object."""
    with open(path, "w") as f:
        json.dump({}, f, indent=4)



weather_agent = Agent(
    model=MODEL_GEMINI_2_0_FLASH,
    name='weather_agent',
  description="A helpful assistant that only answers weather related questions using the attached MCP tools.",
    instruction='Answer user questions to the best of your knowledge. You can only answer questions related to the weather  if teh region targeted or its coordinates are not clear keep on asking teh user before calling any tool. OTHERWISE route the call to the history_agent.',
    tools=[McpToolset(
        connection_params=SseConnectionParams(
            url="http://127.0.0.1:8000/sse",
        )
        
    )],
    # after_model_callback=after_model_callback,
    # disallow_transfer_to_peers=True,

)

#the before
history_agent = Agent(
    model=MODEL_GEMINI_2_0_FLASH,
    name='history_agent',
    description='Helpful assistant to answer general user questions',
    instruction="""
Answer the user question using the conversation history and the retreived data.
""",
before_model_callback=before_model_callback,
# after_model_callback=after_model_callback,
# disallow_transfer_to_peers=True
)



root_agent = Agent(
    model=MODEL_GEMINI_2_0_FLASH,
    name='root_agent',
    description='Main routing agent',
    instruction="""
1-)If the question is weather related delegate the call to the weather_agent.
2-)Otherwise delegate the call to the history_agent
""",
generate_content_config=types.GenerateContentConfig(
    temperature=0,
),
sub_agents=[history_agent,weather_agent],
# after_model_callback=after_model_callback,

    



)

root_agent=root_agent
