from elasticsearch import Elasticsearch

# Connect to Elasticsearch
es = Elasticsearch(
    "https://localhost:9200",              # ✅ use https
    basic_auth=("elastic", "w2Z2H1R7fda9DO0nm_If"),  # ✅ your actual password
    verify_certs=False                     # ✅ disable SSL cert verification for localhost
)

# Test connection
print(es.info())
