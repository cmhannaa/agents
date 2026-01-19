from elasticsearch import Elasticsearch
from datetime import datetime

# Connect to Elasticsearch
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "w2Z2H1R7fda9DO0nm_If"),
    verify_certs=False
)

INDEX_QA = "agent_chats"
INDEX_CONVO = "agent_conversations"

def clean_ts(ts):
    """Convert timestamp to readable string if exists."""
    if not ts:
        return "N/A"
    try:
        return datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(ts)

def read_qas():
    print("\n=== Q&A Pairs ===\n")
    resp = es.search(index=INDEX_QA, query={"match_all": {}}, size=1000)
    hits = resp['hits']['hits']
    if not hits:
        print("No Q&A found.")
        return
    for doc in hits:
        src = doc['_source']
        ts = clean_ts(src.get("timestamp"))
        print(f"[{ts}] User: {src.get('user_message')}")
        print(f"[{ts}] Bot:  {src.get('bot_message')}\n")

def read_conversations():
    print("\n=== Full Conversations ===\n")
    resp = es.search(index=INDEX_CONVO, query={"match_all": {}}, size=1000)
    hits = resp['hits']['hits']
    if not hits:
        print("No conversations found.")
        return
    for doc in hits:
        src = doc['_source']
        print(f"Conversation ID: {src.get('conversation_id')}")
        print(f"User ID: {src.get('user_id')}")
        print("Full session:")
        for msg in src.get("full_session", []):
            ts = clean_ts(msg.get("timestamp"))
            print(f"  [{ts}] {msg['role'].capitalize()}: {msg['text']}")
        print(f"Summary: {src.get('summary')}")
        print("-"*50 + "\n")

# Run the readers
read_qas()
read_conversations()
