"""Neo4j database client."""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from rich.console import Console
from ..config import config

console = Console()


class Neo4jClient:
    """Neo4j database client for graph operations."""

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """Initialize Neo4j client."""
        self.uri = uri or config.neo4j.uri
        self.user = user or config.neo4j.user
        self.password = password or config.neo4j.password

        self.driver = None
        self._connect()

    def _connect(self):
        """Connect to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")

            console.print(f"[green]✓ Connected to Neo4j at {self.uri}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to connect to Neo4j: {e}[/red]")
            raise

    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            console.print("[yellow]Neo4j connection closed[/yellow]")

    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        """Execute a Cypher query and return results."""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def create_document_node(self, doc_id: str, metadata: Dict[str, Any]) -> None:
        """Create a Document node."""
        query = """
        MERGE (d:Document {id: $doc_id})
        SET d += $metadata
        SET d.created_at = datetime()
        RETURN d
        """
        self.execute_query(query, {"doc_id": doc_id, "metadata": metadata})

    def create_chunk_node(
        self,
        chunk_id: str,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """Create a Chunk node with embedding."""
        query = """
        MERGE (c:Chunk {id: $chunk_id})
        SET c.text = $text
        SET c.embedding = $embedding
        SET c += $metadata
        SET c.created_at = datetime()
        RETURN c
        """
        self.execute_query(query, {
            "chunk_id": chunk_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata
        })

    def create_entity_node(self, entity: str, entity_type: str, metadata: Dict[str, Any] = None) -> None:
        """Create an Entity node."""
        query = """
        MERGE (e:Entity {name: $entity, type: $entity_type})
        SET e += $metadata
        SET e.created_at = datetime()
        RETURN e
        """
        self.execute_query(query, {
            "entity": entity,
            "entity_type": entity_type,
            "metadata": metadata or {}
        })

    def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        from_label: str = "Chunk",
        to_label: str = "Chunk",
        properties: Dict[str, Any] = None
    ) -> None:
        """Create a relationship between two nodes."""
        query = f"""
        MATCH (a:{from_label} {{id: $from_id}})
        MATCH (b:{to_label} {{id: $to_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $properties
        RETURN r
        """
        self.execute_query(query, {
            "from_id": from_id,
            "to_id": to_id,
            "properties": properties or {}
        })

    def vector_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """Perform vector similarity search on chunk embeddings."""
        query = """
        MATCH (c:Chunk)
        WHERE c.embedding IS NOT NULL
        WITH c,
             gds.similarity.cosine(c.embedding, $query_embedding) AS similarity
        WHERE similarity >= $threshold
        RETURN c.id AS chunk_id,
               c.text AS text,
               c AS chunk,
               similarity
        ORDER BY similarity DESC
        LIMIT $top_k
        """
        return self.execute_query(query, {
            "query_embedding": query_embedding,
            "top_k": top_k,
            "threshold": similarity_threshold
        })

    def graph_search(
        self,
        chunk_ids: List[str],
        depth: int = 2
    ) -> List[Dict]:
        """Expand search results using graph traversal."""
        query = """
        MATCH (c:Chunk)
        WHERE c.id IN $chunk_ids
        CALL apoc.path.subgraphAll(c, {
            maxLevel: $depth,
            relationshipFilter: "SIMILAR_TO|MENTIONS|NEXT"
        })
        YIELD nodes, relationships
        RETURN nodes, relationships
        """
        return self.execute_query(query, {
            "chunk_ids": chunk_ids,
            "depth": depth
        })

    def create_indexes(self):
        """Create necessary indexes for performance."""
        indexes = [
            "CREATE INDEX chunk_id IF NOT EXISTS FOR (c:Chunk) ON (c.id)",
            "CREATE INDEX document_id IF NOT EXISTS FOR (d:Document) ON (d.id)",
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE TEXT INDEX chunk_text IF NOT EXISTS FOR (c:Chunk) ON (c.text)"
        ]

        for index_query in indexes:
            try:
                self.execute_query(index_query)
            except Exception as e:
                console.print(f"[yellow]Index creation info: {e}[/yellow]")

        console.print("[green]✓ Indexes created/verified[/green]")

    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)."""
        query = "MATCH (n) DETACH DELETE n"
        self.execute_query(query)
        console.print("[yellow]⚠ Database cleared[/yellow]")

    def get_statistics(self) -> Dict[str, int]:
        """Get database statistics."""
        stats = {}

        # Count nodes
        for label in ["Document", "Chunk", "Entity"]:
            result = self.execute_query(f"MATCH (n:{label}) RETURN count(n) as count")
            stats[f"{label.lower()}_count"] = result[0]["count"] if result else 0

        # Count relationships
        result = self.execute_query("MATCH ()-[r]->() RETURN count(r) as count")
        stats["relationship_count"] = result[0]["count"] if result else 0

        return stats

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
