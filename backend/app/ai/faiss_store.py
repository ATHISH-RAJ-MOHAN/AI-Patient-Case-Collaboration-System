import os
import faiss
import numpy as np
from typing import List, Tuple
import pickle

# Folder to store FAISS indexes
FAISS_DIR = "faiss_indexes"
os.makedirs(FAISS_DIR, exist_ok=True)

# Helper: get file paths
def get_index_path(case_id: int) -> str:
    return os.path.join(FAISS_DIR, f"case_{case_id}.index")


def get_meta_path(case_id: int) -> str:
    return os.path.join(FAISS_DIR, f"case_{case_id}.pkl")


# Create or load index
def load_or_create_index(case_id: int, dim: int):
    index_path = get_index_path(case_id)

    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
    else:
        index = faiss.IndexFlatL2(dim)

    return index

# Load metadata (chunks)
def load_metadata(case_id: int) -> List[str]:
    meta_path = get_meta_path(case_id)

    if os.path.exists(meta_path):
        with open(meta_path, "rb") as f:
            return pickle.load(f)
    return []


def save_metadata(case_id: int, data: List[str]):
    meta_path = get_meta_path(case_id)

    with open(meta_path, "wb") as f:
        pickle.dump(data, f)

# Add embeddings to FAISS
def add_embeddings(
    case_id: int,
    embeddings: List[List[float]],
    chunks: List[str]
):
    if not embeddings:
        return

    vectors = np.array(embeddings).astype("float32")
    dim = vectors.shape[1]

    index = load_or_create_index(case_id, dim)
    metadata = load_metadata(case_id)

    # Add vectors
    index.add(vectors)

    # Save updated index
    faiss.write_index(index, get_index_path(case_id))

    # Store corresponding text chunks
    metadata.extend(chunks)
    save_metadata(case_id, metadata)

# Search similar chunks
def search(
    case_id: int,
    query_embedding: List[float],
    top_k: int = 5
) -> List[Tuple[str, float]]:
    index_path = get_index_path(case_id)

    if not os.path.exists(index_path):
        return []

    index = faiss.read_index(index_path)
    metadata = load_metadata(case_id)

    query_vector = np.array([query_embedding]).astype("float32")

    distances, indices = index.search(query_vector, top_k)

    results = []

    for i, idx in enumerate(indices[0]):
        if idx < len(metadata):
            results.append((metadata[idx], float(distances[0][i])))

    return results