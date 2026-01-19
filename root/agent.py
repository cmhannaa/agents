
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents.llm_agent import Agent

# Correct mapping:
# agent1 = greeting agent
# agent2 = weather/time/coordinates agent
from agent1.agent import root_agent as agent1
from agent2.agent import root_agent as agent2

root_agent = Agent(
    model="openai/llama3-8b",
    name="root_agent",
    description=(
        "The ROOT agent orchestrates a fixed pipeline: "
        "Agent2 → Agent1 → Final refinement."
    ),

    instruction="""
You are the ROOT agent.

You MUST ALWAYS follow this exact pipeline for every user message:

------------------------------------------------------------
STEP 1 — ALWAYS call Agent1 first.
Use exactly: transfer_to_agent("agent2")

STEP 2 — AFTER Agent2 returns, ALWAYS call Agent1.
Use exactly: transfer_to_agent("agent1")

STEP 3 — After BOTH agent results are available:
- Combine their outputs.
- If any result is empty, compensate and still answer.
- Provide the BEST refined final answer in your own voice.

------------------------------------------------------------

RULES:
- NEVER skip Agent1 or Agent2.
- NEVER invent tools or functions.
- The ONLY allowed action is transfer_to_agent().
- After both calls, ALWAYS respond with a final combined answer.
""",

    sub_agents=[agent1, agent2],
)

root_agent = root_agent
