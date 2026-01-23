
from elasticsearch import Elasticsearch, helpers
import json

es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "Nd+RL7IsJq6aXnsS+-Ve"),
    ca_certs=r"D:\OneDrive - Murex\Downloads\elasticsearch-9.2.4-windows-x86_64\elasticsearch-9.2.4\config\certs\http_ca.crt",
    ssl_show_warn=False,
)

index_name = "smartdb"

print(f"\nReading index: {index_name}\n")

# Use a scroll/scan to fetch all documents safely
results = helpers.scan(
    es,
    index=index_name,
    query={"query": {"match_all": {}}},
    preserve_order=False
)

count = 0
for doc in results:
    count += 1
    src = doc["_source"]

    print(f" Document ID: {doc['_id']}")
    print(f" Session ID : {src.get('session_id')}")
    print(f" User ID    : {src.get('user_id')}")
    print()
    print(f" Question   : {src.get('question')}")
    print(f" Answer     : {src.get('answer')}")
    print()

    # embedding_raw is stored — print first 8 dims only
    print("──────────────────────────────────────────────")
    print()

print(f"Total documents read: {count}")
