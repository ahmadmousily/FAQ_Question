from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from clean_data import faq_data  
from collections import defaultdict
app = FastAPI()


templates = Jinja2Templates(directory="templates")

client = Elasticsearch("http://localhost:9200")
if client.ping():
    print("✅ Elasticsearch is connected.")
else:
    print("❌ Elasticsearch is not reachable.")


model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def get_embedding(text: str):
    return model.encode(text).tolist()


def create_index():
    if not client.indices.exists(index="faq_collection"):
        mappings = {
            "properties": {
                "question": {"type": "text"},
                "answer": {"type": "text"},
                "department": {"type": "keyword"},
                "embedding": {"type": "dense_vector", "dims": 384}
            }
        }
        client.indices.create(index="faq_collection", body={"mappings": mappings}, ignore=400)

client.indices.delete(index="faq_collection", ignore=[400, 404])
create_index()


def insert_sample_data(faq_data):
    for faq in faq_data:
        department = str(faq.get("department", "General")).strip()
        embedding = [float(x) for x in get_embedding(faq["question"])]
        doc = {
            "question": faq["question"],
            "answer": faq["answer"],
            "department": department,
            "embedding": embedding
        }
        client.index(index="faq_collection", id=faq["id"], body=doc)

insert_sample_data(faq_data)

def group_by_department(faq_hits):
    grouped = defaultdict(list)
    for hit in faq_hits:
        source = hit["_source"]
        grouped[source["department"]].append({
            "question": source["question"],
            "answer": source["answer"]
        })
    return dict(grouped)


@app.get("/")
def home(request: Request):
    response = client.search(index="faq_collection", body={"query": {"match_all": {}}}, size=100)
    grouped_faqs = group_by_department(response["hits"]["hits"])

    return templates.TemplateResponse("index.html", {
        "request": request,
        "faqs_by_dept": grouped_faqs,
        "question": None,
        "answer": None,
        "error": None
    })


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


    all_faqs = client.search(index="faq_collection", body={"query": {"match_all": {}}}, size=100)
    grouped_faqs = group_by_department(all_faqs["hits"]["hits"])


    if not response["hits"]["hits"]:
        if not response["hits"]["hits"]:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "faqs_by_dept": grouped_faqs,
                "question": None,
                "answer": None,
                "error": "No relevant FAQ found.",
                "ranked_matches": None
            })


    ranked_matches = [
    {
        "question": hit["_source"]["question"],
        "answer": hit["_source"]["answer"],
        "score": hit["_score"]
    }
    for hit in response["hits"]["hits"]
        ]

    return templates.TemplateResponse("index.html", {
    "request": request,
    "faqs_by_dept": grouped_faqs,
    "ranked_matches": ranked_matches,
    "question": None,
    "answer": None,
    "error": None
})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

