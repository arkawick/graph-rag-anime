"""Configuration management for Graph RAG."""

import os
from typing import Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Neo4jConfig(BaseModel):
    """Neo4j database configuration."""
    uri: str = Field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    user: str = Field(default_factory=lambda: os.getenv("NEO4J_USER", "neo4j"))
    password: str = Field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", "password123"))


class EmbeddingConfig(BaseModel):
    """Embedding model configuration."""
    provider: Literal["openai", "huggingface"] = Field(
        default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "huggingface")
    )
    model: str = Field(
        default_factory=lambda: os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2"
        )
    )
    dimension: int = 384  # Default for all-MiniLM-L6-v2


class LLMConfig(BaseModel):
    """LLM configuration."""
    provider: Literal["openai", "ollama", "anthropic"] = Field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "openai")
    )
    model: str = Field(default="gpt-4")
    temperature: float = 0.0
    max_tokens: int = 1000


class ChunkingConfig(BaseModel):
    """Document chunking configuration."""
    chunk_size: int = Field(
        default_factory=lambda: int(os.getenv("CHUNK_SIZE", "500"))
    )
    chunk_overlap: int = Field(
        default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "50"))
    )
    separators: list[str] = ["\n\n", "\n", ". ", " ", ""]


class SearchConfig(BaseModel):
    """Search configuration."""
    top_k: int = Field(
        default_factory=lambda: int(os.getenv("TOP_K_RESULTS", "5"))
    )
    similarity_threshold: float = Field(
        default_factory=lambda: float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    )
    graph_depth: int = 2  # How many hops to traverse in graph
    include_entities: bool = True  # Include entity relationships


class Config(BaseModel):
    """Main configuration."""
    neo4j: Neo4jConfig = Field(default_factory=Neo4jConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)


# Global config instance
config = Config()
