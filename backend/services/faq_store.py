"""
Medical FAQ Vector Store using ChromaDB + Sentence Transformers
"""

import json
import os
import chromadb
from chromadb.utils import embedding_functions

# ─── Paths ─────────────────────────────────────────────────────────────────
FAQ_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'medical_faqs.json')
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'chroma_db')

# ─── Embedding model ───────────────────────────────────────────────────────
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

_client = None
_collection = None
_init_error = None


def get_collection():
    """Get or create ChromaDB collection with FAQ embeddings."""
    global _client, _collection, _init_error

    if _init_error:
        raise _init_error
    if _collection is not None:
        return _collection

    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(CHROMA_DB_PATH), exist_ok=True)

        # Ensure FAQ JSON exists
        if not os.path.exists(FAQ_DATA_PATH):
            raise FileNotFoundError(
                f"FAQ data not found at {FAQ_DATA_PATH}. "
                f"Please ensure medical_faqs.json is in backend/data/"
            )

        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )

        _collection = _client.get_or_create_collection(
            name="medical_faqs",
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
    """Load FAQs from JSON and embed them into ChromaDB."""
    print("🔄 Seeding medical FAQ embeddings into ChromaDB...")

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
    print(f"✅ Seeded {len(faqs)} medical FAQs into ChromaDB")


def semantic_search(query: str, n_results: int = 3) -> list:
    """Search FAQs semantically."""
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