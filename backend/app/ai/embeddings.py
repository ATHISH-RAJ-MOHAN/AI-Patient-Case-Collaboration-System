import os
from typing import List

from app.ai.openai_client import create_openai_client


def get_embedding(text: str) -> List[float]:
    try:
        client = create_openai_client()
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"[EMBEDDING ERROR] {e}")
        return []


def get_embedding_batch(texts: list[str]) -> list[list[float]]:
    try:
        client = create_openai_client()
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"[BATCH EMBEDDING ERROR] {e}")
        return []
