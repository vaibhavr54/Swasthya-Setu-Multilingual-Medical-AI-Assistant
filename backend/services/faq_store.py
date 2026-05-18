"""
Medical FAQ Vector Store using ChromaDB + Mistral Embeddings API
Replaces local sentence-transformers with Mistral API — faster cold start,
smaller Docker image, no PyTorch dependency.
"""

import json
import os
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
import requests

# ─── Paths ─────────────────────────────────────────────────────────────────
FAQ_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'medical_faqs.json')
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'chroma_db')

_client = None
_collection = None
_init_error = None


# ─── Mistral Embedding Function for ChromaDB ───────────────────────────────

class MistralEmbeddingFunction(EmbeddingFunction):
    """
    Custom ChromaDB embedding function using Mistral Embeddings API.
    Model: mistral-embed — multilingual, 1024 dimensions.
    """

    def __init__(self):
        from config import MISTRAL_API_KEY
        self.api_key = MISTRAL_API_KEY
        self.url = "https://api.mistral.ai/v1/embeddings"
        self.model = "mistral-embed"

    def __call__(self, input: Documents) -> Embeddings:
        """Embed a list of documents using Mistral API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "inputs": input,          # list of strings
            "encoding_format": "float"
        }
        response = requests.post(self.url, headers=headers, json=payload, timeout=30)

        if not response.ok:
            raise Exception(f"Mistral embed error {response.status_code}: {response.text}")

        data = response.json()
        # Mistral returns: {"data": [{"embedding": [...], "index": 0}, ...]}
        embeddings = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
        return embeddings


# ─── Collection init ───────────────────────────────────────────────────────

def get_collection():
    """Get or create ChromaDB collection with Mistral embeddings."""
    global _client, _collection, _init_error

    if _init_error:
        raise _init_error
    if _collection is not None:
        return _collection

    try:
        os.makedirs(os.path.dirname(CHROMA_DB_PATH), exist_ok=True)

        if not os.path.exists(FAQ_DATA_PATH):
            raise FileNotFoundError(
                f"FAQ data not found at {FAQ_DATA_PATH}. "
                f"Please ensure medical_faqs.json is in backend/data/"
            )

        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        ef = MistralEmbeddingFunction()

        _collection = _client.get_or_create_collection(
            name="medical_faqs_mistral",   # new name — avoids conflict with old ST collection
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"}
        )

        if _collection.count() == 0:
            _seed_faqs(_collection)

        return _collection

    except Exception as e:
        _init_error = e
        print(f"❌ ChromaDB initialization failed: {e}")
        raise


def _seed_faqs(collection):
    """Load FAQs from JSON and embed via Mistral API into ChromaDB."""
    print("🔄 Seeding medical FAQ embeddings via Mistral API...")

    with open(FAQ_DATA_PATH, 'r', encoding='utf-8') as f:
        faqs = json.load(f)

    ids = []
    documents = []
    metadatas = []

    for faq in faqs:
        doc_text = f"{faq['question']} {faq['answer']}"
        ids.append(faq['id'])
        documents.append(doc_text)
        metadatas.append({
            "question": faq['question'],
            "answer": faq['answer'],
            "category": faq['category'],
            "tags": ", ".join(faq['tags'])
        })

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"✅ Seeded {len(faqs)} medical FAQs into ChromaDB via Mistral embed")


def semantic_search(query: str, n_results: int = 3) -> list:
    """Search FAQs semantically using Mistral embeddings."""
    collection = get_collection()

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count())
    )

    faqs = []
    if results and results['metadatas']:
        for i, metadata in enumerate(results['metadatas'][0]):
            distance = results['distances'][0][i] if results.get('distances') else 1.0
            similarity = round(1 - distance, 4)
            faqs.append({
                "id": results['ids'][0][i],
                "question": metadata['question'],
                "answer": metadata['answer'],
                "category": metadata['category'],
                "similarity": similarity
            })

    return faqs


def get_faq_count() -> int:
    """Return number of FAQs in the store."""
    return get_collection().count()


def reset_faq_store():
    """Reset and re-seed — useful when FAQ data is updated."""
    global _client, _collection, _init_error
    _init_error = None
    if _client:
        try:
            _client.delete_collection("medical_faqs_mistral")
        except Exception:
            pass
        _collection = None
    get_collection()