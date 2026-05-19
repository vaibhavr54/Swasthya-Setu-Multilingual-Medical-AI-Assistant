"""
Medical FAQ Vector Store using ChromaDB + Mistral Embeddings API
Replaces local sentence-transformers with Mistral API — faster cold start,
smaller Docker image, no PyTorch dependency.

Now with smart sync: auto-detects new, updated, and deleted FAQs.
"""

import json
import os
import hashlib
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
            "input": input,
            "encoding_format": "float"
        }
        response = requests.post(self.url, headers=headers, json=payload, timeout=30)

        if not response.ok:
            raise Exception(f"Mistral embed error {response.status_code}: {response.text}")

        data = response.json()
        embeddings = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
        return embeddings


# ─── Content Hashing ───────────────────────────────────────────────────────

def _get_content_hash(faq: dict) -> str:
    """Hash FAQ content to detect changes without re-embedding everything."""
    content = f"{faq['question']}|{faq['answer']}|{faq['category']}|{','.join(sorted(faq.get('tags', [])))}"
    return hashlib.md5(content.encode()).hexdigest()


# ─── Collection init with Smart Sync ───────────────────────────────────────

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
            name="medical_faqs_mistral",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"}
        )

        # Smart sync: handles new, updated, deleted FAQs
        sync_faqs()

        return _collection

    except Exception as e:
        _init_error = e
        print(f"ChromaDB initialization failed: {e}")
        raise


# ─── Smart FAQ Sync ────────────────────────────────────────────────────────

def sync_faqs() -> dict:
    global _collection
    collection = _collection
    if collection is None:
        raise RuntimeError("Collection not initialized")

    # Load current JSON
    with open(FAQ_DATA_PATH, 'r', encoding='utf-8') as f:
        json_faqs_raw = json.load(f)

    # Handle both flat list and nested {"faqs": [...]} formats
    if isinstance(json_faqs_raw, dict) and "faqs" in json_faqs_raw:
        json_faqs = {faq['id']: faq for faq in json_faqs_raw['faqs']}
    else:
        json_faqs = {faq['id']: faq for faq in json_faqs_raw}

    # Get existing IDs from ChromaDB
    try:
        existing = collection.get()
        existing_ids = set(existing['ids']) if existing and existing['ids'] else set()
    except Exception:
        existing_ids = set()

    json_ids = set(json_faqs.keys())

    # Determine actions
    to_add = json_ids - existing_ids
    to_delete = existing_ids - json_ids
    to_update = set()

    # Check for content changes in existing FAQs
    common_ids = json_ids & existing_ids
    if common_ids:
        try:
            existing_data = collection.get(ids=list(common_ids))
            existing_meta_map = {
                id_: meta for id_, meta in zip(existing_data['ids'], existing_data['metadatas'])
            }
            for fid in common_ids:
                old_hash = existing_meta_map.get(fid, {}).get('content_hash', '')
                new_hash = _get_content_hash(json_faqs[fid])
                if new_hash != old_hash:
                    to_update.add(fid)
        except Exception as e:
            print(f"⚠️ Could not check for updates: {e}")
            # Fallback: re-embed all common IDs to be safe
            to_update = common_ids

    # Execute deletions
    if to_delete:
        collection.delete(ids=list(to_delete))
        print(f"🗑️ Deleted {len(to_delete)} FAQs")

    # Execute updates (delete old, will re-add below)
    if to_update:
        collection.delete(ids=list(to_update))
        to_add = to_add | to_update  # Add to the add batch
        print(f"🔄 Updating {len(to_update)} changed FAQs")

    # Execute additions
    if to_add:
        faqs_to_add = [json_faqs[fid] for fid in sorted(to_add)]
        ids = []
        documents = []
        metadatas = []

        for faq in faqs_to_add:
            doc_text = f"{faq['question']} {faq['answer']}"
            ids.append(faq['id'])
            documents.append(doc_text)
            metadatas.append({
                "question": faq['question'],
                "answer": faq['answer'],
                "category": faq['category'],
                "tags": ", ".join(faq.get('tags', [])),
                "content_hash": _get_content_hash(faq)
            })

        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        added_count = len([f for f in faqs_to_add if f['id'] in (to_add - to_update)])
        updated_count = len([f for f in faqs_to_add if f['id'] in to_update])
        if added_count:
            print(f"✅ Added {added_count} new FAQs")
        if updated_count:
            print(f"✅ Re-embedded {updated_count} updated FAQs")

    unchanged = len(common_ids - to_update)
    if not any([to_add, to_delete, to_update]):
        print(f"ℹ️ No changes detected ({unchanged} FAQs unchanged)")

    total = collection.count()
    print(f"📊 Total FAQs in store: {total}")

    return {
        "added": len(to_add - to_update),
        "updated": len(to_update),
        "deleted": len(to_delete),
        "unchanged": unchanged,
        "total": total
    }


# ─── Legacy seed (kept for compatibility) ──────────────────────────────────

def _seed_faqs(collection):
    """Legacy: seed all FAQs. Use sync_faqs() instead."""
    print("🔄 Seeding medical FAQ embeddings via Mistral API...")
    sync_faqs()


# ─── Search ────────────────────────────────────────────────────────────────

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
    """Hard reset: delete collection and re-sync from scratch."""
    global _client, _collection, _init_error
    _init_error = None
    if _client:
        try:
            _client.delete_collection("medical_faqs_mistral")
        except Exception:
            pass
        _collection = None
    get_collection()