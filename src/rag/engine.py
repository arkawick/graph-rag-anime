"""Main RAG engine combining retrieval and generation."""

from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from .retriever import HybridRetriever
from .generator import AnswerGenerator

console = Console()


class RAGEngine:
    """Complete RAG engine for question answering."""

    def __init__(
        self,
        retriever: HybridRetriever,
        generator: AnswerGenerator
    ):
        self.retriever = retriever
        self.generator = generator

    def query(
        self,
        question: str,
        top_k: int = 5,
        use_graph: bool = True,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG.

        Args:
            question: User question
            top_k: Number of chunks to retrieve
            use_graph: Whether to use graph expansion
            verbose: Print detailed information

        Returns:
            Dictionary with answer, sources, and metadata
        """
        if verbose:
            console.print(Panel.fit(
                f"[bold cyan]{question}[/bold cyan]",
                title="Query"
            ))

        # Step 1: Retrieve relevant chunks
        retrieved_chunks = self.retriever.retrieve(
            query=question,
            top_k=top_k,
            use_graph_expansion=use_graph,
            verbose=verbose
        )

        if not retrieved_chunks:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": [],
                "chunks_retrieved": 0
            }

        # Convert to dict format for generator
        chunks_dict = [chunk.to_dict() for chunk in retrieved_chunks]

        # Step 2: Generate answer
        if verbose:
            console.print("[yellow]→ Generating answer...[/yellow]")

        result = self.generator.generate_answer(
            query=question,
            context_chunks=chunks_dict,
            include_sources=True
        )

        if verbose:
            console.print("\n" + "=" * 80 + "\n")
            console.print(Panel(
                Markdown(result["answer"]),
                title="[bold green]Answer[/bold green]",
                border_style="green"
            ))

            if result.get("sources"):
                console.print("\n[bold]Sources:[/bold]")
                for i, source in enumerate(result["sources"], 1):
                    console.print(f"  {i}. {source['source']} (relevance: {source['relevance']:.2f})")

            console.print(f"\n[dim]Retrieved {result['num_chunks']} chunks[/dim]")
            console.print("=" * 80 + "\n")

        return result

    def query_with_context(
        self,
        question: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Query and return answer with full context.

        Returns answer plus the actual chunk texts for inspection.
        """
        result = self.query(question, top_k=top_k, verbose=False)

        # Retrieve chunks again to get full text
        retrieved_chunks = self.retriever.retrieve(
            query=question,
            top_k=top_k,
            use_graph_expansion=True,
            verbose=False
        )

        result["context_chunks"] = [
            {
                "text": chunk.text,
                "source": chunk.source,
                "score": chunk.score
            }
            for chunk in retrieved_chunks
        ]

        return result
