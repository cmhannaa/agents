
import csv
from elasticsearch import Elasticsearch
import requests
# ----------------------------
#  CONFIGURE ES CONNECTION
# ----------------------------
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "Nd+RL7IsJq6aXnsS+-Ve"),  
    ca_certs=r"D:\OneDrive - Murex\Downloads\elasticsearch-9.2.4-windows-x86_64\elasticsearch-9.2.4\config\certs\http_ca.crt",
    ssl_show_warn=False  
)

index_name = "smartdb"
import json

# ----------------------------
#  OPTIONAL: CREATE INDEX WITH MAPPING
# ----------------------------
def create_index():
    if not es.indices.exists(index=index_name):
        mapping = {
            "mappings": {
                "properties": {
                    "session_id": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    "question": {"type": "text"},
                    "answer": {"type": "text"},
                    "embedding": {"type": "dense_vector", "dims": 1536},
                    "embedding_raw": {"type": "dense_vector", "dims": 1536}
                }
            }
        }
        es.indices.create(index=index_name, body=mapping)
        print("Index created:", index_name)
    else:
        print("Index already exists:", index_name)

# ----------------------------
#  PLACEHOLDER: YOUR EMBEDDING FUNCTIONS
# ----------------------------
GOOGLE_API_KEY = "AIzaSyBJj8Fuvj-TczD_aSUPuvCFqm0vlBL9yU4"

def embed_text(text: str):
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

# ----------------------------
#  LOAD CSV + PUSH TO ES
# ----------------------------
def push_csv_to_elasticsearch(csv_path):
    with open(csv_path, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            session_id, user_id, user_question, bot_reply = row

            # Compute embedding
            qa_text = user_question + " " + bot_reply
            qa_embedding = embed_text(qa_text)

            # Push to ES
            resp = es.index(
                index=index_name,
                document={
                    "session_id": session_id,
                    "user_id": user_id,
                    "question": user_question,
                    "answer": bot_reply,
                    "embedding": qa_embedding,
                    "embedding_raw": qa_embedding,
                }
            )

            print("Indexed:", resp["_id"])

# ----------------------------
#  RUN
# ----------------------------
if __name__ == "__main__":
    # create_index()
    push_csv_to_elasticsearch("qa_pairs.csv")
