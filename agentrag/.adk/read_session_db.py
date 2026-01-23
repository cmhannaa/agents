
import sqlite3
import json
import time
import csv
from collections import defaultdict
from elasticsearch import Elasticsearch
import os

DB_PATH = "session.db"
CSV_PATH = "qa_pairs.csv"
POLL_INTERVAL = 1  # check every 1 second


# ---------------------------
# Extract Q/A Pairs From Events (now includes user_id)
# ---------------------------
def extract_qa_pairs(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT session_id, event_data FROM events")
    rows = cur.fetchall()

    sessions = defaultdict(list)

    for row in rows:
        session_id = row["session_id"]

        try:
            data = json.loads(row["event_data"])
        except:
            continue

        timestamp = data.get("timestamp", 0)
        role = data.get("content", {}).get("role", "")
        user_id = data.get("author", None)  # <-- extract user_id here

        parts = data.get("content", {}).get("parts", [])
        text = None
        if parts and isinstance(parts[0], dict) and "text" in parts[0]:
            text = parts[0]["text"]

        sessions[session_id].append({
            "timestamp": timestamp,
            "role": role,
            "text": text,
            "user_id": user_id
        })

    conn.close()

    # Build Q/A pairs
    qa_pairs = []

    for session_id, events in sessions.items():
        events.sort(key=lambda x: x["timestamp"])

        last_user_msg = None
        last_user_id = None

        for ev in events:
            if ev["role"] == "user" and ev["text"]:
                last_user_msg = ev["text"].strip()
                last_user_id = ev["user_id"]

            elif ev["role"] == "model" and ev["text"]:
                if last_user_msg:
                    qa_pairs.append({
                        "session_id": session_id,
                        "user_id": last_user_id,
                        "question": last_user_msg,
                        "answer": ev["text"].strip()
                    })
                    last_user_msg = None
                    last_user_id = None

    return qa_pairs


# ---------------------------
# Load existing CSV entries so we don't duplicate
# ---------------------------
def load_existing_csv(csv_path=CSV_PATH):
    existing = set()

    if not os.path.exists(csv_path):
        return existing

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header

        for row in reader:
            if len(row) >= 4:
                session_id, user_id, question, answer = row
                key = (session_id, user_id, question, answer)
                existing.add(key)

    return existing

GOOGLE_API_KEY = "AIzaSyBJj8Fuvj-TczD_aSUPuvCFqm0vlBL9yU4"
import requests 
import json
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

# ---------------------------
# Append new Q/A pairs to CSV
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "Nd+RL7IsJq6aXnsS+-Ve"),  
    ca_certs=r"D:\OneDrive - Murex\Downloads\elasticsearch-9.2.4-windows-x86_64\elasticsearch-9.2.4\config\certs\http_ca.crt",
    ssl_show_warn=False  
)

index_name = "smartdb"
# ---------------------------
def append_new_to_csv(new_pairs, existing, csv_path=CSV_PATH):
    write_header = not os.path.exists(csv_path)

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if write_header:
            writer.writerow(["session_id", "user_id", "question", "answer"])

        for item in new_pairs:
            key = (item["session_id"], item["user_id"], item["question"], item["answer"])

            if key not in existing:
                writer.writerow([
                    item["session_id"],
                    item["user_id"],
                    item["question"],
                    item["answer"]
                ])
            

                print(f"✔ NEW Q/A SAVED: {item['question']}")
                
                session_id = item["session_id"]
                user_id = item["user_id"]
                question = item["question"]
                bot_reply = item["answer"]

                qa_embedding = embed_text(question + "\n" + bot_reply)

                    # Push to ES
                resp = es.index(
                    index=index_name,
                    document={
                        "session_id": session_id,
                        "user_id": user_id,
                        "question": question,
                        "answer": bot_reply,
                        "embedding": qa_embedding,
                        "embedding_raw": qa_embedding,
                    }
                )

                print("Indexed:", resp["_id"])

                existing.add(key)


# ---------------------------
# Watcher Loop
# ---------------------------
def watch_database():
    print("🔍 Watching session.db for new events...")

    existing_pairs = load_existing_csv()

    last_count = 0

    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM events")
            count = cur.fetchone()[0]
            conn.close()

            if count > last_count:
                print(f"\n📥 Detected {count - last_count} new event(s). Processing...")
                last_count = count

                qa_pairs = extract_qa_pairs()

                append_new_to_csv(qa_pairs, existing_pairs)

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\n🛑 Stopped by user.")
            break


if __name__ == "__main__":
    watch_database()
