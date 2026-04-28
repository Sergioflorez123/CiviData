"""
Splitter - Divide documentos en chunks para embeddings.
"""

from typing import List, Dict


class TextSplitter:
    """Divide texto en chunks para embeddings."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents: List[Dict]) -> List[Dict]:
        """Divide documentos en chunks."""
        chunks = []

        for doc in documents:
            content = doc.get("content", "")
            sentences = content.split(" | ")
            current_chunk = []
            current_size = 0

            for sentence in sentences:
                sentence_size = len(sentence)

                if current_size + sentence_size > self.chunk_size and current_chunk:
                    chunks.append(
                        {
                            "content": " | ".join(current_chunk),
                            "metadata": doc.get("metadata", {}),
                        }
                    )

                    overlap_size = 0
                    overlap_chunk = []
                    for s in reversed(current_chunk):
                        if overlap_size + len(s) > self.chunk_overlap:
                            break
                        overlap_chunk.insert(0, s)
                        overlap_size += len(s)

                    current_chunk = overlap_chunk
                    current_size = overlap_size

                current_chunk.append(sentence)
                current_size += sentence_size

            if current_chunk:
                chunks.append(
                    {
                        "content": " | ".join(current_chunk),
                        "metadata": doc.get("metadata", {}),
                    }
                )

        return chunks
