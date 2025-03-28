from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Connect to Qdrant
client = QdrantClient("localhost", port=6333)

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


# Function to get embeddings
def get_embedding(text: str):
    return model.encode(text).tolist()


@app.get("/")
def home(request: Request):
    # Retrieve all stored FAQs from Qdrant
    all_faqs = client.scroll(collection_name="faq_collection", limit=100)[0]  # Get up to 100 FAQs

    faqs = [{"question": item.payload["question"], "answer": item.payload["answer"]} for item in all_faqs]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "faqs": faqs,
        "question": None,
        "answer": None,
        "error": None
    })


@app.get("/search")
def search_faq(request: Request, query: str):
    query_vector = get_embedding(query)

    search_results = client.search(
        collection_name="faq_collection",
        query_vector=query_vector,
        limit=1
    )

    # Retrieve all stored FAQs for display
    all_faqs = client.scroll(collection_name="faq_collection", limit=100)[0]
    faqs = [{"question": item.payload["question"], "answer": item.payload["answer"]} for item in all_faqs]

    if not search_results:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "faqs": faqs,
            "question": None,
            "answer": None,
            "error": "No relevant FAQ found."
        })

    return templates.TemplateResponse("index.html", {
        "request": request,
        "faqs": faqs,
        "question": search_results[0].payload["question"],
        "answer": search_results[0].payload["answer"],
        "error": None
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
