from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Connect to Elasticsearch
client = Elasticsearch("http://localhost:9200")  # Adjust the host if necessary

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


# Function to get embeddings
def get_embedding(text: str):
    return model.encode(text).tolist()


# Function to create the index (if not created)
def create_index():
    if not client.indices.exists(index="faq_collection"):
        mappings = {
            "properties": {
                "question": {"type": "text"},
                "answer": {"type": "text"},
                "embedding": {"type": "dense_vector", "dims": 384}  # Dimensions should match embedding size
            }
        }
        client.indices.create(index="faq_collection", body={"mappings": mappings}, ignore=400)


# Call this function to create the index when the app starts
create_index()


@app.get("/")
def home(request: Request):
    # Retrieve all stored FAQs from Elasticsearch
    response = client.search(index="faq_collection", body={"query": {"match_all": {}}}, size=100)
    
    faqs = [{"question": hit["_source"]["question"], "answer": hit["_source"]["answer"]} for hit in response["hits"]["hits"]]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "faqs": faqs,
        "question": None,
        "answer": None,
        "error": None
    })


@app.get("/search")
def search_faq(request: Request, query: str):
    query_vector = get_embedding(query)  # Get the embedding of the query

    # Perform a vector search in Elasticsearch using script_score for cosine similarity
    response = client.search(
        index="faq_collection",
        body={
            "query": {
                "script_score": {
                    "query": {"match_all": {}},  # Match all documents
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": query_vector}
                    }
                }
            }
        }
    )

    # Retrieve all stored FAQs for display
    all_faqs_response = client.search(index="faq_collection", body={"query": {"match_all": {}}}, size=100)
    faqs = [{"question": hit["_source"]["question"], "answer": hit["_source"]["answer"]} for hit in all_faqs_response["hits"]["hits"]]

    if not response["hits"]["hits"]:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "faqs": faqs,
            "question": None,
            "answer": None,
            "error": "No relevant FAQ found."
        })

    best_match = response["hits"]["hits"][0]["_source"]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "faqs": faqs,
        "question": best_match["question"],
        "answer": best_match["answer"],
        "error": None
    })


# Function to insert sample data (usually you'd run this once to populate the index)
def insert_sample_data():
    faq_data = [
        {"id": 1, "question": "How do I reset my password?", "answer": "Go to settings and click 'Reset Password'."},
        {"id": 2, "question": "What are your support hours?", "answer": "We are available 24/7."},
        {"id": 3, "question": "How can I contact customer support?", "answer": "You can reach us via email at support@example.com or call our 24/7 hotline at +1-800-123-4567."},
        {"id": 4, "question": "How do I create an account?", "answer": "Click on 'Sign Up', fill in your details, verify your email, and you're good to go!"},
        {"id": 5, "question": "How do I delete my account?", "answer": "Go to account settings, scroll down, and click 'Delete Account'. Be aware that this action is irreversible."},
        {"id": 6, "question": "Can I recover a deleted account?", "answer": "Unfortunately, once an account is deleted, it cannot be recovered. You will need to create a new one."},
        {"id": 7, "question": "Do you have a mobile app?", "answer": "Yes, we have both iOS and Android apps available on the App Store and Google Play."},
        {"id": 8, "question": "What payment methods do you accept?", "answer": "We accept credit cards, PayPal, and bank transfers. Some regions may have additional local payment options."},
        {"id": 9, "question": "How can I update my billing information?", "answer": "Go to the 'Billing' section in your account settings and update your payment details."},
        {"id": 10, "question": "Is my personal information secure?", "answer": "Yes! We use industry-standard encryption and security measures to protect your data."},
    ]

    for faq in faq_data:
        embedding = get_embedding(faq["question"])  # Get embedding for the question
        doc = {
            "question": faq["question"],
            "answer": faq["answer"],
            "embedding": embedding
        }
        client.index(index="faq_collection", id=faq["id"], body=doc)


# Insert sample data (run only once to populate the Elasticsearch index)
insert_sample_data()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Connect to Elasticsearch
client = Elasticsearch("http://localhost:9200")  # Adjust the host if necessary

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


# Function to get embeddings
def get_embedding(text: str):
    return model.encode(text).tolist()


# Function to create the index (if not created)
def create_index():
    if not client.indices.exists(index="faq_collection"):
        mappings = {
            "properties": {
                "question": {"type": "text"},
                "answer": {"type": "text"},
                "embedding": {"type": "dense_vector", "dims": 384}  # Dimensions should match embedding size
            }
        }
        client.indices.create(index="faq_collection", body={"mappings": mappings}, ignore=400)


# Call this function to create the index when the app starts
create_index()


@app.get("/")
def home(request: Request):
    # Retrieve all stored FAQs from Elasticsearch
    response = client.search(index="faq_collection", body={"query": {"match_all": {}}}, size=100)
    
    faqs = [{"question": hit["_source"]["question"], "answer": hit["_source"]["answer"]} for hit in response["hits"]["hits"]]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "faqs": faqs,
        "question": None,
        "answer": None,
        "error": None
    })


@app.get("/search")
def search_faq(request: Request, query: str):
    query_vector = get_embedding(query)  # Get the embedding of the query

    # Perform a vector search in Elasticsearch using script_score for cosine similarity
    response = client.search(
        index="faq_collection",
        body={
            "query": {
                "script_score": {
                    "query": {"match_all": {}},  # Match all documents
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": query_vector}
                    }
                }
            }
        }
    )

    # Retrieve all stored FAQs for display
    all_faqs_response = client.search(index="faq_collection", body={"query": {"match_all": {}}}, size=100)
    faqs = [{"question": hit["_source"]["question"], "answer": hit["_source"]["answer"]} for hit in all_faqs_response["hits"]["hits"]]

    if not response["hits"]["hits"]:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "faqs": faqs,
            "question": None,
            "answer": None,
            "error": "No relevant FAQ found."
        })

    best_match = response["hits"]["hits"][0]["_source"]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "faqs": faqs,
        "question": best_match["question"],
        "answer": best_match["answer"],
        "error": None
    })


# Function to insert sample data (usually you'd run this once to populate the index)
def insert_sample_data():
    faq_data = [
        {"id": 1, "question": "How do I reset my password?", "answer": "Go to settings and click 'Reset Password'."},
        {"id": 2, "question": "What are your support hours?", "answer": "We are available 24/7."},
        {"id": 3, "question": "How can I contact customer support?", "answer": "You can reach us via email at support@example.com or call our 24/7 hotline at +1-800-123-4567."},
        {"id": 4, "question": "How do I create an account?", "answer": "Click on 'Sign Up', fill in your details, verify your email, and you're good to go!"},
        {"id": 5, "question": "How do I delete my account?", "answer": "Go to account settings, scroll down, and click 'Delete Account'. Be aware that this action is irreversible."},
        {"id": 6, "question": "Can I recover a deleted account?", "answer": "Unfortunately, once an account is deleted, it cannot be recovered. You will need to create a new one."},
        {"id": 7, "question": "Do you have a mobile app?", "answer": "Yes, we have both iOS and Android apps available on the App Store and Google Play."},
        {"id": 8, "question": "What payment methods do you accept?", "answer": "We accept credit cards, PayPal, and bank transfers. Some regions may have additional local payment options."},
        {"id": 9, "question": "How can I update my billing information?", "answer": "Go to the 'Billing' section in your account settings and update your payment details."},
        {"id": 10, "question": "Is my personal information secure?", "answer": "Yes! We use industry-standard encryption and security measures to protect your data."},
    ]

    for faq in faq_data:
        embedding = get_embedding(faq["question"])  # Get embedding for the question
        doc = {
            "question": faq["question"],
            "answer": faq["answer"],
            "embedding": embedding
        }
        client.index(index="faq_collection", id=faq["id"], body=doc)


# Insert sample data (run only once to populate the Elasticsearch index)
insert_sample_data()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
