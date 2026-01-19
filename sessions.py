
from google.adk.sessions import InMemorySessionService, Session
import asyncio

# Create an in-memory session service.
# This manages all sessions but stores them only in RAM (not persisted).
temp_service = InMemorySessionService()

# Create a new session for a specific user interacting with a specific app.
# Each session = one conversation thread.
example_session = await temp_service.create_session(
    app_name="my_app",               # Which agent application this belongs to
    user_id="example_user",          # Which user this session is for
    state={"initial_key": "initial_value"}  # Optional initial session state (short-term memory)
)

# ---- Inspecting the session ----
print(f"ID (`id`): {example_session.id}")  
# Unique identifier for this specific chat thread.

print(f"App Name (`app_name`): {example_session.app_name}")
# Tells which application created this session.

print(f"User ID (`user_id`): {example_session.user_id}")
# Identifies the user owning this session.

print(f"State (`state`): {example_session.state}")
# The session's short-term memory.
# Only the initial state is shown here (no updates have happened yet).

print(f"Events (`events`): {example_session.events}")
# List of all messages, agent actions, and responses.
# Empty now because nothing has happened yet.

print(f"Last Update (`last_update_time`): {example_session.last_update_time:.2f}")
# Timestamp marking when the session was last modified (creation time for now).

# ---- Cleaning up ----
# Delete the session we created.
# Usually done when a conversation ends or expires.
temp_service = await temp_service.delete_session(
    app_name=example_session.app_name,
    user_id=example_session.user_id,
    session_id=example_session.id
)

print("The final status of temp_service - ", temp_service)
# Shows the session service after deletion (session removed).
