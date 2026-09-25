import os
import glob

from sentence_transformers import SentenceTransformer
import chromadb

BASE_DIR = os.path.dirname(__file__)
DOCS_DIR = os.path.join(BASE_DIR, "docs")
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "zepto_policies"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def load_documents() -> list[dict]:
    """Return one chunk per document: {id, text, source_file}."""
    chunks = []
    for path in sorted(glob.glob(os.path.join(DOCS_DIR, "doc_*.txt"))):
        doc_id = os.path.splitext(os.path.basename(path))[0]  # e.g. "doc_01"
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        chunks.append({"id": doc_id, "text": text, "source_file": os.path.basename(path)})
    return chunks


def get_collection(client: chromadb.ClientAPI | None = None):
    if client is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_index(force: bool = False) -> chromadb.Collection:
    """Embed all 8 documents and repopulate the ChromaDB collection."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    if force:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    collection = get_collection(client)

    if collection.count() >= len(load_documents()) and not force:
        return collection

    chunks = load_documents()
    model = get_embedding_model()
    embeddings = model.encode([c["text"] for c in chunks]).tolist()

    collection.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[{"source_file": c["source_file"]} for c in chunks],
    )
    return collection


def retrieve_top_k(query: str, k: int = 3) -> list[dict]:
    """Embed the query and retrieve the top-k most similar chunks (cosine similarity)."""
    collection = get_collection()
    model = get_embedding_model()
    query_embedding = model.encode([query]).tolist()

    results = collection.query(query_embeddings=query_embedding, n_results=k)

    retrieved = []
    for doc_id, text, distance in zip(
        results["ids"][0], results["documents"][0], results["distances"][0]
    ):
        retrieved.append({"id": doc_id, "text": text, "similarity": 1 - distance})
    return retrieved


if __name__ == "__main__":
    col = build_index(force=True)
    print(f"Indexed {col.count()} document chunks into ChromaDB collection '{COLLECTION_NAME}'")

    for q in ["How fast is delivery?", "What is the weather like today?"]:
        print(f"\nQuery: {q!r}")
        for r in retrieve_top_k(q, k=3):
            print(f"  [{r['id']}] similarity={r['similarity']:.3f}  {r['text'][:80]!r}")
