"""Hybrid retriever combining vector search and graph traversal."""

from typing import List, Dict, Any
from dataclasses import dataclass
from rich.console import Console
from ..graph.neo4j_client import Neo4jClient
from ..embeddings.embedder import Embedder
from ..config import config

console = Console()


@dataclass
class RetrievedChunk:
    """Retrieved chunk with metadata and score."""
    chunk_id: str
    text: str
    score: float
    source: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "score": self.score,
            "source": self.source,
            "metadata": self.metadata
        }


class HybridRetriever:
    """
    Hybrid retrieval combining:
    1. Vector similarity search
    2. Graph-based context expansion
    """

    def __init__(
        self,
        neo4j_client: Neo4jClient,
        embedder: Embedder,
        top_k: int = None,
        graph_depth: int = None
    ):
        self.client = neo4j_client
        self.embedder = embedder
        self.top_k = top_k or config.search.top_k
        self.graph_depth = graph_depth or config.search.graph_depth

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        use_graph_expansion: bool = True,
        verbose: bool = False
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: User query string
            top_k: Number of results to return
            use_graph_expansion: Whether to expand results using graph
            verbose: Print retrieval details

        Returns:
            List of RetrievedChunk objects
        """
        top_k = top_k or self.top_k

        if verbose:
            console.print(f"\n[cyan]Query:[/cyan] {query}")

        # Step 1: Vector similarity search
        if verbose:
            console.print("[yellow]→ Performing vector search...[/yellow]")

        query_embedding = self.embedder.embed_text(query)
        vector_results = self.client.vector_search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Get more for graph expansion
            similarity_threshold=config.search.similarity_threshold
        )

        if verbose:
            console.print(f"  Found {len(vector_results)} similar chunks")

        # Convert to RetrievedChunk objects
        retrieved_chunks = []
        for result in vector_results:
            chunk = result["chunk"]
            retrieved_chunks.append(RetrievedChunk(
                chunk_id=result["chunk_id"],
                text=result["text"],
                score=result["similarity"],
                source=chunk.get("metadata", {}).get("source", "unknown"),
                metadata=chunk.get("metadata", {})
            ))

        # Step 2: Graph-based expansion (optional)
        if use_graph_expansion and len(retrieved_chunks) > 0:
            if verbose:
                console.print(f"[yellow]→ Expanding with graph traversal (depth={self.graph_depth})...[/yellow]")

            chunk_ids = [chunk.chunk_id for chunk in retrieved_chunks[:top_k]]
            expanded_results = self._expand_with_graph(chunk_ids)

            if verbose:
                console.print(f"  Found {len(expanded_results)} total chunks after expansion")

            # Merge and deduplicate
            retrieved_chunks = self._merge_results(retrieved_chunks, expanded_results)

        # Step 3: Rank and filter
        retrieved_chunks = self._rank_results(retrieved_chunks)[:top_k]

        if verbose:
            console.print(f"[green]✓ Retrieved {len(retrieved_chunks)} final chunks[/green]\n")

        return retrieved_chunks

    def _expand_with_graph(self, chunk_ids: List[str]) -> List[RetrievedChunk]:
        """Expand results using graph relationships."""
        expanded = []

        # Traverse graph to find related chunks
        query = """
        MATCH (c:Chunk)
        WHERE c.id IN $chunk_ids
        MATCH path = (c)-[:SIMILAR_TO|NEXT*1..2]-(related:Chunk)
        RETURN DISTINCT related.id AS chunk_id,
               related.text AS text,
               related AS chunk,
               length(path) AS distance
        """

        results = self.client.execute_query(query, {"chunk_ids": chunk_ids})

        for result in results:
            chunk = result["chunk"]
            # Score based on graph distance (closer = higher score)
            score = 1.0 / (result["distance"] + 1)

            expanded.append(RetrievedChunk(
                chunk_id=result["chunk_id"],
                text=result["text"],
                score=score,
                source=chunk.get("metadata", {}).get("source", "unknown"),
                metadata=chunk.get("metadata", {})
            ))

        return expanded

    def _merge_results(
        self,
        vector_results: List[RetrievedChunk],
        graph_results: List[RetrievedChunk]
    ) -> List[RetrievedChunk]:
        """Merge and deduplicate results from vector and graph search."""
        seen_ids = set()
        merged = []

        # Add vector results first (they have higher priority)
        for chunk in vector_results:
            if chunk.chunk_id not in seen_ids:
                merged.append(chunk)
                seen_ids.add(chunk.chunk_id)

        # Add graph results
        for chunk in graph_results:
            if chunk.chunk_id not in seen_ids:
                merged.append(chunk)
                seen_ids.add(chunk.chunk_id)

        return merged

    def _rank_results(self, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """Re-rank results by score."""
        return sorted(chunks, key=lambda x: x.score, reverse=True)
