from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from clean_data import faq_data  # Your external FAQ data

app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Connect to Elasticsearch
client = Elasticsearch("http://localhost:9200")
if client.ping():
    print("✅ Elasticsearch is connected.")
else:
    print("❌ Elasticsearch is not reachable.")

# Load the multilingual embedding model
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Get vector embedding for a given text
def get_embedding(text: str):
    return model.encode(text).tolist()

# Create index with dense_vector field if not exists
def create_index():
    if not client.indices.exists(index="faq_collection"):
        mappings = {
            "properties": {
                "question": {"type": "text"},
                "answer": {"type": "text"},
                "embedding": {"type": "dense_vector", "dims": 384}
            }
        }
        client.indices.create(index="faq_collection", body={"mappings": mappings}, ignore=400)

# Create index on startup
create_index()

# Insert FAQ data into Elasticsearch
def insert_sample_data(faq_data):
    for faq in faq_data:
        embedding = get_embedding(faq["question"])
        doc = {
            "question": faq["question"],
            "answer": faq["answer"],
            "embedding": embedding
        }
        client.index(index="faq_collection", id=faq["id"], body=doc)

insert_sample_data(faq_data)

# Home route
@app.get("/")
def home(request: Request):
    response = client.search(index="faq_collection", body={"query": {"match_all": {}}}, size=100)
    faqs = [{"question": hit["_source"]["question"], "answer": hit["_source"]["answer"]}
            for hit in response["hits"]["hits"]]
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "faqs": faqs,
        "question": None,
        "answer": None,
        "error": None
    })

# Search route using vector similarity
@app.get("/search")
def search_faq(request: Request, query: str):
    query_vector = get_embedding(query)

    response = client.search(
        index="faq_collection",
        body={
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": query_vector}
                    }
                }
            }
        }
    )

    # Fetch all FAQs to show in sidebar
    all_faqs = client.search(index="faq_collection", body={"query": {"match_all": {}}}, size=100)
    faqs = [{"question": hit["_source"]["question"], "answer": hit["_source"]["answer"]}
            for hit in all_faqs["hits"]["hits"]]

    # No matches
    if not response["hits"]["hits"]:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "faqs": faqs,
            "question": None,
            "answer": None,
            "error": "No relevant FAQ found."
        })

    # Best match (top hit)
    best_match = response["hits"]["hits"][0]["_source"]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "faqs": faqs,
        "question": best_match["question"],
        "answer": best_match["answer"],
        "error": None
    })

# Run app with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

