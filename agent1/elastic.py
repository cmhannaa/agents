from elasticsearch import Elasticsearch
from datetime import datetime
import uuid


# Connect to Elasticsearch
es = Elasticsearch(
    "https://localhost:9200",              # ✅ use https
    basic_auth=("elastic", "w2Z2H1R7fda9DO0nm_If"),  # ✅ your actual password
    verify_certs=False                     # ✅ disable SSL cert verification for localhost
)




INDEX_QA = "agent_chats"
INDEX_CONVO = "agent_conversations"

# Create indices if they don't exist
# NEW: use keyword arguments
if not es.indices.exists(index=INDEX_QA):
    es.indices.create(index=INDEX_QA)

if not es.indices.exists(index=INDEX_CONVO):
    es.indices.create(index=INDEX_CONVO)

# -----------------------
# Helper functions
# -----------------------
def clean_messages(messages):
    """Remove empty messages."""
    return [m for m in messages if m.get("text") and m["text"].strip() != ""]

def get_embedding(text):
    """Generate embedding vector for semantic search."""
    # Example with OpenAI embeddings
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response['data'][0]['embedding']

# -----------------------
# Callback to log before sending to model
# -----------------------
def log_before_model(callback_context, llm_request):
    print("\n--- Prompt ABOUT TO BE SENT TO MODEL ---")
    for content in llm_request.contents:
        print(f"{content.role}: {content.parts[0].text}")

# -----------------------
# After model callback: save chats and conversation summaries
# -----------------------
def after_model_callback(callback_context, llm_request, llm_response):
    user_id = callback_context.metadata.get("user_id", "anonymous")
    conversation_id = callback_context.metadata.get("conversation_id", str(uuid.uuid4()))

    # -----------------------
    # Table 1: Q&A pairs
    # -----------------------
    user_messages = clean_messages([{"text": c.parts[0].text} for c in llm_request.contents])
    bot_messages = clean_messages([{"text": c.parts[0].text} for c in llm_response.contents])

    for u_msg, b_msg in zip(user_messages, bot_messages):
        # Generate embeddings for semantic search
        u_embedding = get_embedding(u_msg["text"])
        b_embedding = get_embedding(b_msg["text"])

        doc = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "user_message": u_msg["text"],
            "bot_message": b_msg["text"],
            "bot_rewritten_message": b_msg["text"],  # optional
            "user_embedding": u_embedding,
            "bot_embedding": b_embedding,
            "timestamp": datetime.utcnow()
        }
        es.index(index=INDEX_QA, document=doc)

    # -----------------------
    # Table 2: Conversation summary + full session
    # -----------------------
    resp = es.search(
        index=INDEX_CONVO,
        query={"term": {"conversation_id.keyword": conversation_id}}
    )

    if resp['hits']['hits']:
        convo_doc = resp['hits']['hits'][0]['_source']
        full_session = convo_doc.get("full_session", [])
    else:
        full_session = []

    # Append new messages
    for m in user_messages:
        full_session.append({"role": "user", "text": m["text"], "timestamp": datetime.utcnow()})
    for m in bot_messages:
        full_session.append({"role": "assistant", "text": m["text"], "timestamp": datetime.utcnow()})

    # Create rolling summary (last 10 messages)
    summary_text = " ".join([m["text"] for m in full_session[-10:]])

    # Upsert conversation doc
    es.index(
        index=INDEX_CONVO,
        id=conversation_id,
        document={
            "conversation_id": conversation_id,
            "user_id": user_id,
            "full_session": full_session,
            "summary": summary_text,
            "updated_at": datetime.utcnow()
        }
    )
