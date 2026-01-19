from dotenv import load_dotenv
load_dotenv()
from google.adk.agents.llm_agent import Agent
from fastmcp import Client
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.genai import types as genai_types


from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.genai import types as genai_types
import json



def log_before_model(callback_context: CallbackContext,
                     llm_request: LlmRequest) -> Optional[genai_types.Content]:

    key = f"__logged_invocation__:{callback_context.invocation_id}"
    if callback_context.state.get(key):
        return None
    callback_context.state[key] = True

    print("\n==================== FINAL LLM REQUEST ====================\n")
    print(json.dumps({
        "model": llm_request.model,
        "messages": [
            {
                "role": c.role,
                "parts": [
                    p.text if hasattr(p, "text") else p.__class__.__name__
                    for p in (c.parts or [])
                ]
            }
            for c in (llm_request.contents or [])
        ]
    }, indent=2, ensure_ascii=False))
    print("\n===========================================================\n")

    return None


root_agent = Agent(
    model="openai/llama3-8b",
    name='agent1',
    description="A helpful weather assistant that answers user questions. This agent can also retrieve weather, time, and geographic coordinate information using the attached MCP tools.",
    instruction='Answer user questions to the best of your knowledge. Start by identifying the user intent if they request weather, time or city coordinated information use the attched MCP tools and answer their question accordingly. Otherwise specify that you are only a weather, time and coordinates assistant. While checking the chat history ignore empty messages and focus only on written ones as they are sent because of the stream activated act as if they do not exist.',
    tools=[McpToolset(
        connection_params=SseConnectionParams(
            url="http://127.0.0.1:8000/sse",
        )
    )],
    
generate_content_config=genai_types.GenerateContentConfig(
        # --- sampling controls ---
        temperature=0.7,      # lower = more deterministic between 0 and 2 
        top_p=0.95,
        max_output_tokens=1024,
    ),

    before_model_callback=log_before_model,
)





