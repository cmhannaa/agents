from elasticsearch import Elasticsearch
from datetime import datetime
import requests
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
import json
import uuid
from gemini import rewrite_query
from google.genai import types
import json
import os


import numpy as np

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def extract_contents_list(contents):
    """
    Converts a list of Content(role, parts=[Part(text)]) 
    into a simple list of dicts: [{"role": "...", "text": "..."}].
    """
    extracted = []

    for msg in contents:
        role = msg.role
        text = msg.parts[0].text if msg.parts else ""
        extracted.append({"role": role, "text": text})

    return extracted

es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "Nd+RL7IsJq6aXnsS+-Ve"),  
    ca_certs=r"D:\OneDrive - Murex\Downloads\elasticsearch-9.2.4-windows-x86_64\elasticsearch-9.2.4\config\certs\http_ca.crt",
    ssl_show_warn=False  
)

GOOGLE_API_KEY = "AIzaSyBJj8Fuvj-TczD_aSUPuvCFqm0vlBL9yU4"

def get_embedding(text: str):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"text-embedding-004:embedContent?key={GOOGLE_API_KEY}"
    )
    payload = {
        "content": {
            "parts": [{"text": text}]
        }
    }
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    data = resp.json()
    embedding = data.get("embedding", {}).get("values")
    # print(f"Length: {len(embedding)}")
    return embedding



index_name = "smartdb"

# Delete old index if exists
# es.indices.delete(index=index_name, ignore=[400, 404])
# print("Deleted old index")


mapping = {
    "mappings": {
        "properties": {
            "session_id": {"type": "keyword"},
            "user_id": {"type": "keyword"},
            "question": {"type": "text"},
            "answer": {"type": "text"},
            # Used for vector search (HNSW). Not retrievable.
            "embedding": {
                "type": "dense_vector",
                "dims": 768,
                "index": True,
                "similarity": "cosine"
            },
            "embedding_raw": {"type": "float"}
        }
    }
}


# es.indices.create(index=index_name, body=mapping)
# print("Created new k‑NN index:", index_name)







def append_user_and_model_to_json(file_path, user_msg, model_msg):
    """
    Appends a user message and a model response to a JSON list.
    Creates file if it does not exist.
    """

    # Structure entries
    user_entry = {
        "role": "user",
        "text": user_msg
    }

    model_entry = {
        "role": "model",
        "text": model_msg
    }

    # Load existing history
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    # Append both messages
    data.append(user_entry)
    data.append(model_entry)

    # Save back (append mode in JSON = rewrite whole list)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def inspect(callback_context, llm_response):
    print("llm response")
    print(llm_response)
    print()
    print("callback_context")
    print(callback_context)
    print()




def after_model_callback(callback_context, llm_response):
    # print("llm response")
    # print(llm_response)
    #print("end of llm response")
    try:
        session_id = callback_context.session.id
        user_id = callback_context.session.user_id

        # ---- USER QUESTION ----
        user_question = ""
        if callback_context.user_content and callback_context.user_content.parts:
            user_question = callback_context.user_content.parts[0].text.strip()

        # ---- BOT REPLY OR TOOL CALL ----
        parts = llm_response.content.parts
        bot_reply = ""

        for p in parts:
            if getattr(p, "text", None):
                bot_reply = p.text.strip()
                break

        if not bot_reply:
            for p in parts:
                if getattr(p, "function_call", None):
                    fc = p.function_call
                    bot_reply = f"[TOOL CALL] {fc.name}({fc.args})"
                    break

        if not user_question or not bot_reply:
            print("No valid QA pair to save.")
            return
        
        #hallucinations
        if bot_reply.startswith("[TOOL CALL]"):
            return

        
        append_user_and_model_to_json("conversation.json", user_question,bot_reply)

        # -------------------------------
        # NEW: Combined QA embedding
        # -------------------------------
        combined_text = f"Q: {user_question}\nA: {bot_reply}"
        qa_embedding = get_embedding(combined_text)
        # print(f"qa embedding {qa_embedding[:8]}")

        # ---- Save to Elasticsearch ----
        resp=es.index(
            index=index_name,
            document={
            "session_id": session_id,
            "user_id": user_id,
            "question": user_question,
            "answer": bot_reply,
            "embedding": qa_embedding,
            "embedding_raw":qa_embedding,
        },
        refresh="wait_for",
        )
        doc_id = resp["_id"]
        # print("Saved with ID:", doc_id)

        doc = es.get(index=index_name, id=doc_id)
        # print("Question:", doc["_source"]["question"])
        # print("Answer:", doc["_source"]["answer"])
        # print("Embedding copy (first 8 dims):", doc["_source"]["embedding_raw"][:8])
 

        print("✓ Saved QA pair to Elasticsearch (with combined QA embedding).", index_name)
    except Exception as e:
        print("after_model_callback ERROR:", e)






def before_model_callback(callback_context, llm_request):
    llm_request.contents = llm_request.contents[-6:]
    # print("start")
    # print(llm_request.contents)
    # print("end")
    clean_list = extract_contents_list(llm_request.contents)
    session_id = callback_context.session.id
    # user_id = callback_context.session.user_id
    user_id="user"
    # print(clean_list)
    # events = callback_context.session.events
    # print()
    # print()
    # print("Start of events")
    # print(events)
    # print("End of events")
    # print()
    # print()
    # print()
    # print("llm request")
    # print(llm_request)
    # print("end of llm request")
    # print()
    # print()
    user_question = ""
    if callback_context.user_content:
        parts = callback_context.user_content.parts
        if parts and hasattr(parts[0], "text"):
            user_question = parts[0].text.strip()

    print(f"user question before {user_question}")

    # rewritten_query=rewrite_query(user_question,clean_list)
    # print(f"rewritten query: {rewritten_query}")

    request_embedding=get_embedding(user_question)

    k=10


        
    # 1) Fetch ALL docs for this session
    session_docs = es.search(
        index=index_name,
        body={
            "query": {
                "term": {"user_id": user_id}
            },
            "_source": ["question", "answer", "embedding"],
            "size": 10000
        }
    )["hits"]["hits"]

    print(f"Fetched {len(session_docs)} docs for this session.")

    # 2) Compute cosine similarity in Python
    ranked_docs = []
    for d in session_docs:
        src = d["_source"]
        embedding = src.get("embedding")
        if embedding:
            score = cosine_similarity(request_embedding, embedding)
            ranked_docs.append({
                "question": src.get("question", ""),
                "answer": src.get("answer", ""),
                "score": score
            })

    # 3) Sort descending by similarity
    ranked_docs.sort(key=lambda x: x["score"], reverse=True)

    # 4) Keep top‑K
    top_k_docs = ranked_docs[:10]

    # 5) Format for insertion into system prompt
    similar_docs = "\n\n".join(
        f"Q: {doc['question']}\nA: {doc['answer']}"
        for doc in top_k_docs
    )

    llm_request.contents.insert(
        0,
        types.Content(
            role="model",
            parts=[
                types.Part(
                    text=(
                        "You are a personal assistant, responsible to answer teh user's requests. Use the following fetched information to answer the questions.\n\n"
                        f"{similar_docs}\n\n"
                        "If info is missing in the context, say you are unsure. Follows is the recent convo history"
                    )
                )
            ],
        ),
    )
    # print()
    # print("similar docs")
    # print(similar_docs)
    print("After llm request")
    print(llm_request)
    print("end of After llm request")
    print()
    print()
    # print("llm requests")
    # print(llm_request)
    # print("end")





