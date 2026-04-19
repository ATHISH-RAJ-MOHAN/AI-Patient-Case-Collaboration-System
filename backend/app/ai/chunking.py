from typing import List

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) ->List[str]:
    """
    Splits text into overlapping chunks.

    Args:
        text (str): full document text
        chunk_size (int): max size of each chunk
        overlap (int): overlapping characters between chunks

    Returns:
        List[str]: list of text chunks
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]

        chunks.append(chunk.strip())

        # move forward with overlap
        start += chunk_size - overlap
    
    return chunks