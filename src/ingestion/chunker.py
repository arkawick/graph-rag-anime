"""Document chunking utilities."""

from typing import List
from dataclasses import dataclass
import tiktoken
from ..config import config


@dataclass
class Chunk:
    """Text chunk with metadata."""
    text: str
    metadata: dict
    chunk_id: int

    def __post_init__(self):
        """Add token count to metadata."""
        encoding = tiktoken.get_encoding("cl100k_base")
        self.metadata["token_count"] = len(encoding.encode(self.text))


class DocumentChunker:
    """Chunk documents into smaller pieces for embedding."""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size or config.chunking.chunk_size
        self.chunk_overlap = chunk_overlap or config.chunking.chunk_overlap
        self.separators = separators or config.chunking.separators

    def chunk_document(self, document) -> List[Chunk]:
        """
        Chunk a document using recursive character splitting.

        Args:
            document: Document object with content and metadata

        Returns:
            List of Chunk objects
        """
        text = document.content
        metadata = document.metadata.copy()

        chunks = self._split_text_recursive(text)

        # Create Chunk objects with metadata
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk_text)
            })

            chunk_objects.append(
                Chunk(text=chunk_text, metadata=chunk_metadata, chunk_id=i)
            )

        return chunk_objects

    def _split_text_recursive(
        self,
        text: str,
        separators: List[str] = None
    ) -> List[str]:
        """
        Recursively split text using different separators.

        Tries to split on paragraphs first, then sentences, then words.
        """
        separators = separators or self.separators
        final_chunks = []

        # Base case: text is small enough
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        # Try each separator
        for separator in separators:
            if separator in text:
                splits = text.split(separator)
                current_chunk = ""
                current_size = 0

                for split in splits:
                    split_size = len(split)

                    # If adding this split would exceed chunk size
                    if current_size + split_size > self.chunk_size and current_chunk:
                        final_chunks.append(current_chunk.strip())

                        # Add overlap from previous chunk
                        overlap_text = current_chunk[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                        current_chunk = overlap_text + split + separator
                        current_size = len(current_chunk)
                    else:
                        current_chunk += split + separator
                        current_size += split_size + len(separator)

                # Add remaining chunk
                if current_chunk.strip():
                    final_chunks.append(current_chunk.strip())

                return final_chunks

        # If no separator worked, split by character count
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            if chunk.strip():
                chunks.append(chunk)

        return chunks

    def chunk_documents(self, documents: List) -> List[Chunk]:
        """Chunk multiple documents."""
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)

        return all_chunks
