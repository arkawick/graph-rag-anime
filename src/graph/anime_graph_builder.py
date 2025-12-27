"""Build anime knowledge graph from API data."""

from typing import List, Dict, Any
import hashlib
from rich.console import Console
from rich.progress import track
from .neo4j_client import Neo4jClient

console = Console()


class AnimeGraphBuilder:
    """Build anime knowledge graph in Neo4j."""

    def __init__(self, neo4j_client: Neo4jClient):
        self.client = neo4j_client

    def build_from_anime_data(
        self,
        anime_list: List[Dict[str, Any]],
        embeddings: List[List[float]] = None
    ):
        """
        Build complete anime knowledge graph.

        Args:
            anime_list: List of anime dictionaries from API
            embeddings: Optional embeddings for anime (from synopsis)
        """
        console.print("\n[bold cyan]Building Anime Knowledge Graph...[/bold cyan]")

        # Create anime nodes
        console.print("[yellow]Creating anime nodes...[/yellow]")
        anime_ids = []

        for idx, anime in track(enumerate(anime_list), total=len(anime_list), description="Anime"):
            anime_id = str(anime["id"])
            anime_ids.append(anime_id)

            # Prepare embedding if available
            embedding = embeddings[idx] if embeddings and idx < len(embeddings) else None

            self._create_anime_node(anime, embedding)

        # Create genre nodes and relationships
        console.print("[yellow]Creating genres...[/yellow]")
        genres_created = set()

        for anime in track(anime_list, description="Genres"):
            anime_id = str(anime["id"])

            for genre in anime.get("genres", []):
                if genre not in genres_created:
                    self._create_genre_node(genre)
                    genres_created.add(genre)

                self._link_anime_to_genre(anime_id, genre)

        # Create studio nodes and relationships
        console.print("[yellow]Creating studios...[/yellow]")
        studios_created = set()

        for anime in track(anime_list, description="Studios"):
            anime_id = str(anime["id"])

            for studio in anime.get("studios", []):
                if studio not in studios_created:
                    self._create_studio_node(studio)
                    studios_created.add(studio)

                self._link_anime_to_studio(anime_id, studio)

        # Create character nodes and relationships (if available)
        console.print("[yellow]Creating characters...[/yellow]")
        characters_created = set()

        for anime in track(anime_list, description="Characters"):
            anime_id = str(anime["id"])

            for char in anime.get("characters", []):
                char_id = str(char["id"])

                if char_id not in characters_created:
                    self._create_character_node(char)
                    characters_created.add(char_id)

                role = char.get("role", "UNKNOWN")
                self._link_anime_to_character(anime_id, char_id, role)

                # Voice actors (if available)
                for va in char.get("voice_actors", []):
                    va_id = str(va["id"])
                    self._create_voice_actor_node(va)
                    self._link_character_to_voice_actor(char_id, va_id, va.get("language"))

        # Create recommendation relationships
        console.print("[yellow]Creating recommendations...[/yellow]")
        for anime in track(anime_list, description="Recommendations"):
            anime_id = str(anime["id"])

            for rec in anime.get("recommendations", []):
                rec_id = str(rec["id"])

                # Only create relationship if recommended anime exists in our dataset
                if rec_id in [str(a["id"]) for a in anime_list]:
                    votes = rec.get("votes", rec.get("rating", 0))
                    self._create_recommendation_relationship(anime_id, rec_id, votes)

        # Create relation relationships (sequel, prequel, etc.)
        console.print("[yellow]Creating anime relations...[/yellow]")
        for anime in track(anime_list, description="Relations"):
            anime_id = str(anime["id"])

            for rel in anime.get("relations", []):
                rel_id = str(rel["id"])
                rel_type = rel.get("type", "RELATED")

                # Only create relationship if related anime exists in our dataset
                if rel_id in [str(a["id"]) for a in anime_list]:
                    self._create_anime_relationship(anime_id, rel_id, rel_type)

        # Compute similarity based on embeddings (if provided)
        if embeddings:
            console.print("[yellow]Computing anime similarities from embeddings...[/yellow]")
            self._create_similarity_relationships(anime_ids, embeddings)

        # Print statistics
        stats = self.client.get_statistics()
        console.print("\n[bold green]✓ Anime Knowledge Graph Built![/bold green]")
        console.print(f"  Anime: {self._count_nodes('Anime')}")
        console.print(f"  Genres: {self._count_nodes('Genre')}")
        console.print(f"  Studios: {self._count_nodes('Studio')}")
        console.print(f"  Characters: {self._count_nodes('Character')}")
        console.print(f"  Total Relationships: {stats['relationship_count']}\n")

    def _create_anime_node(self, anime: Dict, embedding: List[float] = None):
        """Create an Anime node."""
        query = """
        MERGE (a:Anime {id: $id})
        SET a.title = $title
        SET a.title_english = $title_english
        SET a.title_japanese = $title_japanese
        SET a.synopsis = $synopsis
        SET a.episodes = $episodes
        SET a.score = $score
        SET a.popularity = $popularity
        SET a.type = $type
        SET a.status = $status
        SET a.year = $year
        SET a.season = $season
        SET a.image_url = $image_url
        SET a.url = $url
        """

        if embedding:
            query += "SET a.embedding = $embedding\n"

        query += "SET a.updated_at = datetime()\nRETURN a"

        params = {
            "id": str(anime["id"]),
            "title": anime.get("title", "Unknown"),
            "title_english": anime.get("title_english"),
            "title_japanese": anime.get("title_japanese"),
            "synopsis": anime.get("synopsis", ""),
            "episodes": anime.get("episodes"),
            "score": anime.get("score"),
            "popularity": anime.get("popularity"),
            "type": anime.get("type"),
            "status": anime.get("status"),
            "year": anime.get("year"),
            "season": anime.get("season"),
            "image_url": anime.get("image_url"),
            "url": anime.get("url"),
        }

        if embedding:
            params["embedding"] = embedding

        self.client.execute_query(query, params)

    def _create_genre_node(self, genre: str):
        """Create a Genre node."""
        query = """
        MERGE (g:Genre {name: $name})
        SET g.updated_at = datetime()
        RETURN g
        """
        self.client.execute_query(query, {"name": genre})

    def _create_studio_node(self, studio: str):
        """Create a Studio node."""
        query = """
        MERGE (s:Studio {name: $name})
        SET s.updated_at = datetime()
        RETURN s
        """
        self.client.execute_query(query, {"name": studio})

    def _create_character_node(self, character: Dict):
        """Create a Character node."""
        query = """
        MERGE (c:Character {id: $id})
        SET c.name = $name
        SET c.role = $role
        SET c.image_url = $image_url
        SET c.updated_at = datetime()
        RETURN c
        """
        self.client.execute_query(query, {
            "id": str(character["id"]),
            "name": character.get("name", "Unknown"),
            "role": character.get("role", "UNKNOWN"),
            "image_url": character.get("image_url")
        })

    def _create_voice_actor_node(self, voice_actor: Dict):
        """Create a VoiceActor node."""
        query = """
        MERGE (v:VoiceActor {id: $id})
        SET v.name = $name
        SET v.updated_at = datetime()
        RETURN v
        """
        self.client.execute_query(query, {
            "id": str(voice_actor["id"]),
            "name": voice_actor.get("name", "Unknown")
        })

    def _link_anime_to_genre(self, anime_id: str, genre: str):
        """Create HAS_GENRE relationship."""
        query = """
        MATCH (a:Anime {id: $anime_id})
        MATCH (g:Genre {name: $genre})
        MERGE (a)-[:HAS_GENRE]->(g)
        """
        self.client.execute_query(query, {"anime_id": anime_id, "genre": genre})

    def _link_anime_to_studio(self, anime_id: str, studio: str):
        """Create PRODUCED_BY relationship."""
        query = """
        MATCH (a:Anime {id: $anime_id})
        MATCH (s:Studio {name: $studio})
        MERGE (a)-[:PRODUCED_BY]->(s)
        """
        self.client.execute_query(query, {"anime_id": anime_id, "studio": studio})

    def _link_anime_to_character(self, anime_id: str, character_id: str, role: str):
        """Create FEATURES relationship."""
        query = """
        MATCH (a:Anime {id: $anime_id})
        MATCH (c:Character {id: $character_id})
        MERGE (a)-[r:FEATURES]->(c)
        SET r.role = $role
        """
        self.client.execute_query(query, {
            "anime_id": anime_id,
            "character_id": character_id,
            "role": role
        })

    def _link_character_to_voice_actor(self, character_id: str, va_id: str, language: str):
        """Create VOICED_BY relationship."""
        query = """
        MATCH (c:Character {id: $character_id})
        MATCH (v:VoiceActor {id: $va_id})
        MERGE (c)-[r:VOICED_BY]->(v)
        SET r.language = $language
        """
        self.client.execute_query(query, {
            "character_id": character_id,
            "va_id": va_id,
            "language": language or "Japanese"
        })

    def _create_recommendation_relationship(self, anime_id: str, rec_id: str, votes: int):
        """Create RECOMMENDED relationship."""
        query = """
        MATCH (a1:Anime {id: $anime_id})
        MATCH (a2:Anime {id: $rec_id})
        MERGE (a1)-[r:RECOMMENDED]->(a2)
        SET r.votes = $votes
        """
        self.client.execute_query(query, {
            "anime_id": anime_id,
            "rec_id": rec_id,
            "votes": votes
        })

    def _create_anime_relationship(self, anime_id: str, related_id: str, rel_type: str):
        """Create typed relationship between anime (SEQUEL, PREQUEL, etc.)."""
        # Map relation types to valid Cypher relationship types
        rel_type_map = {
            "SEQUEL": "SEQUEL_OF",
            "PREQUEL": "PREQUEL_OF",
            "ALTERNATIVE": "ALTERNATIVE_VERSION",
            "SIDE_STORY": "SIDE_STORY_OF",
            "PARENT": "PARENT_STORY",
            "SUMMARY": "SUMMARY_OF",
            "ADAPTATION": "ADAPTED_FROM"
        }

        cypher_rel_type = rel_type_map.get(rel_type, "RELATED_TO")

        query = f"""
        MATCH (a1:Anime {{id: $anime_id}})
        MATCH (a2:Anime {{id: $related_id}})
        MERGE (a1)-[r:{cypher_rel_type}]->(a2)
        """
        self.client.execute_query(query, {
            "anime_id": anime_id,
            "related_id": related_id
        })

    def _create_similarity_relationships(
        self,
        anime_ids: List[str],
        embeddings: List[List[float]],
        threshold: float = 0.75,
        max_connections: int = 10
    ):
        """Create SIMILAR_TO relationships based on embeddings."""
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        embeddings_array = np.array(embeddings)
        similarities = cosine_similarity(embeddings_array)

        for i in range(len(anime_ids)):
            sims = similarities[i]
            similar_indices = np.argsort(sims)[::-1][1:max_connections + 1]

            for j in similar_indices:
                similarity = float(sims[j])

                if similarity >= threshold:
                    query = """
                    MATCH (a1:Anime {id: $anime_id1})
                    MATCH (a2:Anime {id: $anime_id2})
                    MERGE (a1)-[r:SIMILAR_TO]->(a2)
                    SET r.similarity = $similarity
                    """
                    self.client.execute_query(query, {
                        "anime_id1": anime_ids[i],
                        "anime_id2": anime_ids[j],
                        "similarity": similarity
                    })

    def _count_nodes(self, label: str) -> int:
        """Count nodes with specific label."""
        query = f"MATCH (n:{label}) RETURN count(n) as count"
        result = self.client.execute_query(query)
        return result[0]["count"] if result else 0
