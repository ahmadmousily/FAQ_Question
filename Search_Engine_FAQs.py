from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from qdrant_client.models import PointStruct

client = QdrantClient("localhost", port=6333)

model = SentenceTransformer("all-MiniLM-L6-v2")  # Fast & accurate

def get_embedding(text):
    return model.encode(text).tolist()

client.recreate_collection(
    collection_name="faq_collection",
    vectors_config={
        "size": 384,  # Size of the embeddings produced by the model (all-MiniLM-L6-v2)
        "distance": "Cosine"  # Cosine similarity
    }
)
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
    {"id": 11, "question": "How do I change my subscription plan?", "answer": "Navigate to 'Subscription' in settings and choose the plan that fits your needs. Your changes will take effect on the next billing cycle."},
    {"id": 12, "question": "Can I get a refund?", "answer": "Refunds are available within 14 days of purchase. Contact support for assistance."},
    {"id": 13, "question": "How do I enable two-factor authentication (2FA)?", "answer": "Go to 'Security Settings', select 'Enable 2FA', and follow the on-screen instructions to link your authenticator app."},
    {"id": 14, "question": "Why was my payment declined?", "answer": "There could be several reasons: insufficient funds, incorrect details, or bank restrictions. Try another payment method or contact your bank."},
    {"id": 15, "question": "How do I report a bug?", "answer": "Submit a bug report through our support portal with a description and screenshots, if possible."},
    {"id": 16, "question": "What happens if I forget my username?", "answer": "You can use your registered email to log in or retrieve your username from the 'Forgot Username' section."},
    {"id": 17, "question": "How do I update my profile information?", "answer": "Go to your profile page, click 'Edit', update the necessary fields, and save changes."},
    {"id": 18, "question": "What should I do if I suspect unauthorized access to my account?", "answer": "Immediately change your password and enable two-factor authentication. If you still have concerns, contact support."},
    {"id": 19, "question": "How can I improve my account security?", "answer": "Use a strong password, enable 2FA, avoid sharing credentials, and regularly update your account details."},
    {"id": 20, "question": "Where can I find the terms and conditions?", "answer": "Our terms and conditions are available on our website under the 'Legal' section or at www.example.com/terms."}
]

points = [
    PointStruct(
        id=faq["id"],   # Assign a unique ID
        vector=get_embedding(faq["question"]),  # Convert question text into an embedding
        payload={"question": faq["question"], "answer": faq["answer"]}
    )
    for faq in faq_data
]

client.upsert(collection_name="faq_collection", points=points)


def search_faq(query, top_k=1):
    query_vector = get_embedding(query)  # Convert user input to an embedding

    search_results = client.search(
        collection_name="faq_collection",
        query_vector=query_vector,
        limit=top_k
    )

    if search_results:
        return search_results[0].payload["answer"]  # Return the best matching answer
    else:
        return "Sorry, I couldn't find an answer to your question."


# Example usage
user_query = "How to update password?"
answer = search_faq(user_query)
print("Answer:", answer)