"""Command-line interface for Neo4j Graph RAG."""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from src.ingestion import DocumentLoader, DocumentChunker
from src.ingestion.anime_fetcher import AnimeDataFetcher
from src.embeddings import Embedder
from src.graph import Neo4jClient, GraphBuilder
from src.graph.anime_graph_builder import AnimeGraphBuilder
from src.rag import HybridRetriever, AnswerGenerator, RAGEngine

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Neo4j Graph RAG - Production-ready RAG system with knowledge graph."""
    pass


@cli.command()
@click.option(
    "--source",
    "-s",
    type=click.Path(exists=True),
    required=True,
    help="Source directory or file to ingest"
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Recursively scan directories"
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear existing database before ingesting"
)
def ingest(source: str, recursive: bool, clear: bool):
    """Ingest documents into the knowledge graph."""
    console.print("\n[bold cyan]═══ Document Ingestion ═══[/bold cyan]\n")

    try:
        # Initialize components
        loader = DocumentLoader()
        chunker = DocumentChunker()
        embedder = Embedder()
        neo4j = Neo4jClient()
        builder = GraphBuilder(neo4j)

        # Clear database if requested
        if clear:
            console.print("[yellow]Clearing existing database...[/yellow]")
            neo4j.clear_database()

        # Create indexes
        neo4j.create_indexes()

        # Load documents
        console.print(f"[yellow]Loading documents from: {source}[/yellow]")
        source_path = Path(source)

        if source_path.is_file():
            documents = [loader.load_file(source_path)]
        else:
            documents = loader.load_directory(source_path, recursive=recursive)

        if not documents:
            console.print("[red]No documents found![/red]")
            return

        # Chunk documents
        console.print(f"\n[yellow]Chunking {len(documents)} documents...[/yellow]")
        chunks = chunker.chunk_documents(documents)
        console.print(f"[green]✓ Created {len(chunks)} chunks[/green]")

        # Generate embeddings
        console.print(f"\n[yellow]Generating embeddings...[/yellow]")
        embeddings = embedder.embed_chunks(chunks)

        # Build knowledge graph
        builder.build_from_documents(documents, chunks, embeddings)

        console.print("\n[bold green]✓ Ingestion complete![/bold green]\n")

        neo4j.close()

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        raise


@cli.command()
@click.argument("question")
@click.option(
    "--top-k",
    "-k",
    type=int,
    default=5,
    help="Number of chunks to retrieve"
)
@click.option(
    "--no-graph",
    is_flag=True,
    help="Disable graph expansion"
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Minimal output (answer only)"
)
def query(question: str, top_k: int, no_graph: bool, quiet: bool):
    """Query the knowledge graph."""
    try:
        # Initialize components
        neo4j = Neo4jClient()
        embedder = Embedder()
        retriever = HybridRetriever(neo4j, embedder, top_k=top_k)
        generator = AnswerGenerator()
        engine = RAGEngine(retriever, generator)

        # Query
        result = engine.query(
            question=question,
            top_k=top_k,
            use_graph=not no_graph,
            verbose=not quiet
        )

        if quiet:
            console.print(result["answer"])

        neo4j.close()

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        raise


@cli.command()
def stats():
    """Show knowledge graph statistics."""
    try:
        neo4j = Neo4jClient()
        stats = neo4j.get_statistics()

        table = Table(title="Knowledge Graph Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green", justify="right")

        table.add_row("Documents", str(stats["document_count"]))
        table.add_row("Chunks", str(stats["chunk_count"]))
        table.add_row("Entities", str(stats["entity_count"]))
        table.add_row("Relationships", str(stats["relationship_count"]))

        console.print()
        console.print(table)
        console.print()

        neo4j.close()

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        raise


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to clear the database?")
def clear():
    """Clear all data from the knowledge graph."""
    try:
        neo4j = Neo4jClient()
        neo4j.clear_database()
        console.print("\n[green]✓ Database cleared[/green]\n")
        neo4j.close()

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        raise


@cli.command()
@click.option(
    "--port",
    "-p",
    type=int,
    default=8501,
    help="Port to run Streamlit on"
)
def serve(port: int):
    """Launch the web UI."""
    import subprocess
    import sys

    console.print(f"\n[cyan]Starting web UI on port {port}...[/cyan]\n")

    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(port)],
            check=True
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]\n")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")


@cli.command()
def test():
    """Test the RAG system with example queries."""
    console.print("\n[bold cyan]═══ Testing RAG System ═══[/bold cyan]\n")

    test_queries = [
        "What is this document about?",
        "Summarize the main points",
        "What are the key concepts discussed?"
    ]

    try:
        neo4j = Neo4jClient()
        embedder = Embedder()
        retriever = HybridRetriever(neo4j, embedder)
        generator = AnswerGenerator()
        engine = RAGEngine(retriever, generator)

        for question in test_queries:
            console.print(f"\n[bold]Q: {question}[/bold]")
            result = engine.query(question, verbose=False)
            console.print(f"[green]A: {result['answer'][:200]}...[/green]\n")

        neo4j.close()
        console.print("[bold green]✓ Tests complete![/bold green]\n")

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")


@cli.command()
@click.option(
    "--source",
    "-s",
    type=click.Choice(["jikan", "anilist"]),
    default="jikan",
    help="API source to fetch from"
)
@click.option(
    "--count",
    "-c",
    type=int,
    default=100,
    help="Number of anime to fetch"
)
@click.option(
    "--min-score",
    type=float,
    default=7.0,
    help="Minimum score filter"
)
@click.option(
    "--output",
    "-o",
    type=str,
    default="anime_data.json",
    help="Output JSON filename"
)
def fetch_anime(source: str, count: int, min_score: float, output: str):
    """Fetch anime data from AniList or Jikan API."""
    console.print("\n[bold cyan]═══ Fetching Anime Data ═══[/bold cyan]\n")

    try:
        fetcher = AnimeDataFetcher()

        if source == "jikan":
            anime_list = fetcher.fetch_from_jikan(max_anime=count, min_score=min_score)
        elif source == "anilist":
            # AniList uses 0-100 score, so convert
            min_score_anilist = int(min_score * 10)
            anime_list = fetcher.fetch_from_anilist(max_anime=count, min_score=min_score_anilist)

        if anime_list:
            fetcher.save_to_json(anime_list, output)
            console.print(f"\n[bold green]✓ Fetched {len(anime_list)} anime![/bold green]\n")
        else:
            console.print("[red]No anime data fetched![/red]")

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        raise


@cli.command()
@click.option(
    "--json-file",
    "-j",
    type=click.Path(exists=True),
    default="data/anime/anime_data.json",
    help="JSON file with anime data"
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear existing database before ingesting"
)
@click.option(
    "--embeddings/--no-embeddings",
    default=True,
    help="Generate embeddings from synopsis"
)
def ingest_anime(json_file: str, clear: bool, embeddings: bool):
    """Ingest anime data from JSON into the knowledge graph."""
    console.print("\n[bold cyan]═══ Anime Data Ingestion ═══[/bold cyan]\n")

    try:
        # Load anime data
        fetcher = AnimeDataFetcher()
        anime_list = fetcher.load_from_json(Path(json_file).name)

        if not anime_list:
            console.print("[red]No anime data found in JSON file![/red]")
            return

        # Initialize components
        neo4j = Neo4jClient()
        builder = AnimeGraphBuilder(neo4j)

        # Clear database if requested
        if clear:
            console.print("[yellow]Clearing existing database...[/yellow]")
            neo4j.clear_database()

        # Create indexes
        neo4j.create_indexes()

        # Generate embeddings from synopsis if requested
        embedding_vectors = None
        if embeddings:
            console.print(f"\n[yellow]Generating embeddings from anime synopsis...[/yellow]")
            embedder = Embedder()

            # Extract synopsis texts
            synopsis_texts = [anime.get("synopsis", "") for anime in anime_list]

            # Generate embeddings
            embedding_vectors = embedder.embed_texts(synopsis_texts)
            console.print(f"[green]✓ Generated {len(embedding_vectors)} embeddings[/green]")

        # Build anime knowledge graph
        builder.build_from_anime_data(anime_list, embedding_vectors)

        console.print("\n[bold green]✓ Anime ingestion complete![/bold green]\n")

        neo4j.close()

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        raise


@cli.command()
@click.argument("question")
@click.option(
    "--top-k",
    "-k",
    type=int,
    default=5,
    help="Number of anime to retrieve"
)
def query_anime(question: str, top_k: int):
    """Query the anime knowledge graph."""
    console.print(f"\n[bold cyan]Question:[/bold cyan] {question}\n")

    try:
        neo4j = Neo4jClient()
        embedder = Embedder()

        # Generate query embedding
        query_embedding = embedder.embed_texts([question])[0]

        # Vector search on anime
        query = """
        MATCH (a:Anime)
        WHERE a.embedding IS NOT NULL
        WITH a, gds.similarity.cosine(a.embedding, $query_embedding) AS similarity
        WHERE similarity >= 0.5
        RETURN a.title as title,
               a.synopsis as synopsis,
               a.score as score,
               a.episodes as episodes,
               similarity
        ORDER BY similarity DESC
        LIMIT $top_k
        """

        results = neo4j.execute_query(query, {
            "query_embedding": query_embedding,
            "top_k": top_k
        })

        if results:
            console.print("[bold green]Top matching anime:[/bold green]\n")

            for idx, result in enumerate(results, 1):
                console.print(f"[bold]{idx}. {result['title']}[/bold]")
                console.print(f"   Score: {result['score']} | Episodes: {result['episodes']}")
                console.print(f"   Similarity: {result['similarity']:.3f}")
                console.print(f"   Synopsis: {result['synopsis'][:150]}...\n")
        else:
            console.print("[yellow]No matching anime found![/yellow]")

        neo4j.close()

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        raise


if __name__ == "__main__":
    cli()
