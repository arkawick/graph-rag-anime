"""Generate embeddings for text chunks."""

from typing import List, Union
import os
from rich.console import Console
from ..config import config

console = Console()


class Embedder:
    """Generate embeddings using various providers."""

    def __init__(
        self,
        provider: str = None,
        model: str = None
    ):
        self.provider = provider or config.embedding.provider
        self.model = model or config.embedding.model

        self._initialize_model()

    def _initialize_model(self):
        """Initialize the embedding model based on provider."""
        console.print(f"[yellow]Initializing embeddings ({self.provider}/{self.model})...[/yellow]")

        if self.provider == "openai":
            from langchain_openai import OpenAIEmbeddings
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")

            self.embedder = OpenAIEmbeddings(
                model=self.model or "text-embedding-ada-002",
                openai_api_key=api_key
            )

        elif self.provider == "huggingface":
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer(self.model)

        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

        console.print(f"[green]✓ Embeddings initialized[/green]")

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text."""
        if self.provider == "openai":
            return self.embedder.embed_query(text)
        elif self.provider == "huggingface":
            return self.embedder.encode(text, convert_to_tensor=False).tolist()

    def embed_texts(self, texts: List[str], show_progress: bool = True) -> List[List[float]]:
        """Embed multiple texts."""
        if show_progress:
            console.print(f"[yellow]Embedding {len(texts)} texts...[/yellow]")

        if self.provider == "openai":
            embeddings = self.embedder.embed_documents(texts)
        elif self.provider == "huggingface":
            if show_progress:
                embeddings = self.embedder.encode(
                    texts,
                    show_progress_bar=True,
                    convert_to_tensor=False
                ).tolist()
            else:
                embeddings = self.embedder.encode(
                    texts,
                    convert_to_tensor=False
                ).tolist()

        if show_progress:
            console.print(f"[green]✓ {len(embeddings)} embeddings generated[/green]")

        return embeddings

    def embed_chunks(self, chunks: List, show_progress: bool = True) -> List[List[float]]:
        """Embed a list of Chunk objects."""
        texts = [chunk.text for chunk in chunks]
        return self.embed_texts(texts, show_progress=show_progress)

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self.provider == "openai":
            if "ada-002" in self.model:
                return 1536
            return 1536  # Default
        elif self.provider == "huggingface":
            # Get dimension from model
            return self.embedder.get_sentence_embedding_dimension()
        return 384  # Default
