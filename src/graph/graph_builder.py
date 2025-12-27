"""Build knowledge graph from documents and chunks."""

from typing import List
import hashlib
from rich.console import Console
from rich.progress import track
from .neo4j_client import Neo4jClient
from ..ingestion.loader import Document
from ..ingestion.chunker import Chunk

console = Console()


class GraphBuilder:
    """Build knowledge graph in Neo4j from documents and chunks."""

    def __init__(self, neo4j_client: Neo4jClient):
        self.client = neo4j_client

    def build_from_documents(
        self,
        documents: List[Document],
        chunks: List[Chunk],
        embeddings: List[List[float]]
    ):
        """
        Build complete knowledge graph from documents.

        Args:
            documents: List of Document objects
            chunks: List of Chunk objects
            embeddings: List of embedding vectors (same length as chunks)
        """
        console.print("\n[bold cyan]Building Knowledge Graph...[/bold cyan]")

        # Create document nodes
        console.print("[yellow]Creating document nodes...[/yellow]")
        doc_map = {}
        for doc in track(documents, description="Documents"):
            doc_id = self._generate_id(doc.metadata["source"])
            doc_map[doc.metadata["source"]] = doc_id

            self.client.create_document_node(doc_id, {
                "filename": doc.metadata.get("filename", "unknown"),
                "type": doc.metadata.get("type", "text"),
                "size": doc.metadata.get("size", 0)
            })

        # Create chunk nodes with embeddings
        console.print("[yellow]Creating chunk nodes with embeddings...[/yellow]")
        chunk_ids = []
        for chunk, embedding in track(
            zip(chunks, embeddings),
            total=len(chunks),
            description="Chunks"
        ):
            chunk_id = self._generate_id(
                f"{chunk.metadata['source']}_{chunk.chunk_id}"
            )
            chunk_ids.append(chunk_id)

            self.client.create_chunk_node(
                chunk_id=chunk_id,
                text=chunk.text,
                embedding=embedding,
                metadata={
                    "chunk_index": chunk.metadata.get("chunk_index", 0),
                    "token_count": chunk.metadata.get("token_count", 0)
                }
            )

            # Link chunk to document
            doc_id = doc_map[chunk.metadata["source"]]
            self.client.create_relationship(
                from_id=doc_id,
                to_id=chunk_id,
                rel_type="HAS_CHUNK",
                from_label="Document",
                to_label="Chunk",
                properties={"position": chunk.metadata.get("chunk_index", 0)}
            )

        # Create sequential relationships between chunks from same document
        console.print("[yellow]Creating sequential chunk relationships...[/yellow]")
        doc_chunks = {}
        for chunk, chunk_id in zip(chunks, chunk_ids):
            source = chunk.metadata["source"]
            if source not in doc_chunks:
                doc_chunks[source] = []
            doc_chunks[source].append((chunk_id, chunk.metadata.get("chunk_index", 0)))

        for source, chunk_list in doc_chunks.items():
            # Sort by chunk index
            chunk_list.sort(key=lambda x: x[1])

            # Create NEXT relationships
            for i in range(len(chunk_list) - 1):
                self.client.create_relationship(
                    from_id=chunk_list[i][0],
                    to_id=chunk_list[i + 1][0],
                    rel_type="NEXT",
                    from_label="Chunk",
                    to_label="Chunk"
                )

        # Create similarity relationships based on embeddings
        console.print("[yellow]Computing chunk similarities...[/yellow]")
        self._create_similarity_relationships(chunk_ids, embeddings)

        # Print statistics
        stats = self.client.get_statistics()
        console.print("\n[bold green]✓ Knowledge Graph Built![/bold green]")
        console.print(f"  Documents: {stats['document_count']}")
        console.print(f"  Chunks: {stats['chunk_count']}")
        console.print(f"  Entities: {stats['entity_count']}")
        console.print(f"  Relationships: {stats['relationship_count']}\n")

    def _create_similarity_relationships(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        threshold: float = 0.75,
        max_connections: int = 5
    ):
        """Create SIMILAR_TO relationships between similar chunks."""
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        # Compute pairwise similarities
        embeddings_array = np.array(embeddings)
        similarities = cosine_similarity(embeddings_array)

        # Create relationships for top-k similar chunks
        for i in range(len(chunk_ids)):
            # Get similarities for this chunk
            sims = similarities[i]

            # Get top-k similar chunks (excluding self)
            similar_indices = np.argsort(sims)[::-1][1:max_connections + 1]

            for j in similar_indices:
                similarity = float(sims[j])

                if similarity >= threshold:
                    self.client.create_relationship(
                        from_id=chunk_ids[i],
                        to_id=chunk_ids[j],
                        rel_type="SIMILAR_TO",
                        properties={"similarity": similarity}
                    )

    def _generate_id(self, text: str) -> str:
        """Generate unique ID from text."""
        return hashlib.md5(text.encode()).hexdigest()
