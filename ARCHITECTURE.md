# Neo4j Graph RAG - Architecture

## System Overview

Neo4j Graph RAG is a production-ready Retrieval-Augmented Generation system that combines vector similarity search with graph-based context expansion to provide accurate, source-attributed answers to user questions.

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                          │
│  CLI (cli.py) │ Web UI (app.py) │ API (future)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     RAG ENGINE                               │
│  Query Processing → Retrieval → Generation → Response       │
└──┬──────────────────┬──────────────────┬───────────────────┘
   │                  │                  │
   │                  │                  │
   ▼                  ▼                  ▼
┌────────┐     ┌──────────┐      ┌─────────────┐
│Embedding│     │  Neo4j   │      │ LLM         │
│Service  │     │  Graph   │      │(OpenAI/     │
│         │     │  Database│      │ Ollama)     │
└────────┘     └──────────┘      └─────────────┘
```

## Core Components

### 1. Document Ingestion Pipeline

**Location**: `src/ingestion/`

**Components**:
- `DocumentLoader`: Multi-format document loading (PDF, TXT, MD, DOCX)
- `DocumentChunker`: Semantic text chunking with overlap

**Flow**:
```python
Documents → Load → Chunk → Embed → Store in Neo4j
```

**Key Features**:
- Recursive character splitting
- Token-aware chunking
- Metadata preservation
- Progress tracking

### 2. Knowledge Graph (Neo4j)

**Location**: `src/graph/`

**Node Types**:
```cypher
(:Document {id, filename, type, size, created_at})
(:Chunk {id, text, embedding[], token_count, created_at})
(:Entity {name, type, created_at})
```

**Relationship Types**:
```cypher
(Document)-[:HAS_CHUNK {position}]->(Chunk)
(Chunk)-[:NEXT]->(Chunk)
(Chunk)-[:SIMILAR_TO {similarity}]->(Chunk)
(Chunk)-[:MENTIONS]->(Entity)
```

**Indexes**:
- `chunk_id`: Fast chunk lookup
- `document_id`: Fast document lookup
- `chunk_text`: Full-text search
- `entity_name`: Entity lookups

### 3. Embeddings System

**Location**: `src/embeddings/`

**Supported Providers**:
- **OpenAI**: `text-embedding-ada-002` (1536 dim)
- **HuggingFace**: `all-MiniLM-L6-v2` (384 dim, local)
- **HuggingFace**: `all-mpnet-base-v2` (768 dim, better quality)

**Features**:
- Batch processing
- Progress tracking
- Provider abstraction
- Dimension detection

### 4. Hybrid Retrieval

**Location**: `src/rag/retriever.py`

**Two-Stage Retrieval**:

#### Stage 1: Vector Similarity Search
```cypher
MATCH (c:Chunk)
WHERE c.embedding IS NOT NULL
WITH c, gds.similarity.cosine(c.embedding, $query_embedding) AS similarity
WHERE similarity >= $threshold
RETURN c
ORDER BY similarity DESC
LIMIT $top_k
```

#### Stage 2: Graph Expansion
```cypher
MATCH (c:Chunk) WHERE c.id IN $initial_chunk_ids
MATCH path = (c)-[:SIMILAR_TO|NEXT*1..2]-(related:Chunk)
RETURN related
```

**Benefits**:
- Captures semantic similarity (vector search)
- Expands context (graph traversal)
- Finds related information (SIMILAR_TO)
- Maintains document flow (NEXT)

### 5. Answer Generation

**Location**: `src/rag/generator.py`

**LLM Providers**:
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Ollama**: Llama2, Mistral (local)
- **Anthropic**: Claude (future)

**Prompt Structure**:
```
You are a helpful assistant...

Context:
[Document 1] (Source: file.pdf, Relevance: 0.95)
{chunk text}

---

[Document 2] (Source: guide.md, Relevance: 0.87)
{chunk text}

Question: {user question}

Instructions:
1. Answer based ONLY on context
2. Cite document numbers
3. Be concise and accurate

Answer:
```

### 6. RAG Engine

**Location**: `src/rag/engine.py`

**Complete Query Flow**:
```python
def query(question):
    # 1. Embed question
    embedding = embedder.embed_text(question)

    # 2. Vector search (top-k chunks)
    vector_results = neo4j.vector_search(embedding, top_k=10)

    # 3. Graph expansion (related chunks)
    chunk_ids = [r.id for r in vector_results]
    expanded = neo4j.graph_search(chunk_ids, depth=2)

    # 4. Merge and rank
    all_chunks = merge(vector_results, expanded)
    ranked = rank_by_score(all_chunks)[:top_k]

    # 5. Generate answer
    context = build_context(ranked)
    answer = llm.generate(question, context)

    # 6. Return with sources
    return {
        "answer": answer,
        "sources": extract_sources(ranked),
        "chunks": len(ranked)
    }
```

## Data Flow

### Ingestion Flow

```
1. User provides documents directory
   │
2. DocumentLoader scans and loads files
   ├─→ PDF: pypdf extraction
   ├─→ DOCX: python-docx parsing
   ├─→ TXT: direct read
   └─→ MD: markdown conversion
   │
3. DocumentChunker splits into chunks
   ├─→ Recursive character splitting
   ├─→ Maintains overlap for context
   └─→ Tracks metadata (position, source)
   │
4. Embedder generates vectors
   ├─→ Batch processing for efficiency
   └─→ Provider-specific encoding
   │
5. GraphBuilder constructs Neo4j graph
   ├─→ Create Document nodes
   ├─→ Create Chunk nodes with embeddings
   ├─→ Link chunks to documents (HAS_CHUNK)
   ├─→ Link sequential chunks (NEXT)
   └─→ Compute and link similar chunks (SIMILAR_TO)
```

### Query Flow

```
1. User asks question
   │
2. Embedder encodes question
   │
3. Neo4j vector search
   ├─→ Cosine similarity with all chunks
   └─→ Filter by threshold, return top-k
   │
4. Graph expansion (optional)
   ├─→ Traverse SIMILAR_TO relationships
   ├─→ Traverse NEXT relationships
   └─→ Aggregate related chunks
   │
5. Merge and rank results
   ├─→ Deduplicate chunks
   ├─→ Score by relevance
   └─→ Select final top-k
   │
6. Generate answer
   ├─→ Build context from chunks
   ├─→ Create prompt
   ├─→ Call LLM
   └─→ Parse response
   │
7. Return answer + sources
   └─→ Display to user
```

## Configuration

**Location**: `src/config.py`

**Pydantic Models**:
- `Neo4jConfig`: Database connection
- `EmbeddingConfig`: Embedding provider and model
- `LLMConfig`: LLM provider and parameters
- `ChunkingConfig`: Chunk size and overlap
- `SearchConfig`: Retrieval parameters

**Environment Variables** (`.env`):
```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# OpenAI (optional)
OPENAI_API_KEY=sk-...

# Embedding
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# LLM
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# Chunking
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Search
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.7
```

## Performance Considerations

### Scalability

**Current Limits**:
- Documents: 10,000+
- Chunks: 100,000+
- Queries: <1s response time

**Bottlenecks**:
1. **Embedding Generation**: Batch processing, use GPU
2. **Vector Search**: Neo4j GDS optimized
3. **Graph Traversal**: Limited depth (2 hops)
4. **LLM Generation**: Depends on provider

**Optimizations**:
- Batch embedding generation
- Indexed vector search
- Cached embeddings
- Parallel processing

### Memory Usage

**Embeddings**:
- `all-MiniLM-L6-v2`: 384 dims → ~1.5 KB per chunk
- 100K chunks ≈ 150 MB

**Neo4j**:
- Configure heap size: `NEO4J_dbms_memory_heap_max__size=2G`
- Page cache: `NEO4J_dbms_memory_pagecache_size=1G`

**Python Process**:
- Typical: 200-500 MB
- With large models: 1-2 GB

## Security

**Neo4j**:
- Change default password
- Enable auth
- Use encrypted connections (bolt+s)

**API Keys**:
- Store in `.env`
- Never commit to git
- Use key rotation

**Data Privacy**:
- All data stays local (except OpenAI API calls)
- Use Ollama for fully local deployment

## Deployment

### Local Development
```bash
docker-compose up -d
python cli.py ingest --source docs/
python cli.py query "What is X?"
```

### Production

**Option 1: Docker**
```bash
docker build -t graph-rag .
docker run -p 8501:8501 graph-rag
```

**Option 2: Cloud**
- Deploy Neo4j AuraDB (managed)
- Deploy app to Cloud Run / Lambda
- Use vector index for scale

## Monitoring

**Metrics to Track**:
- Query latency
- Retrieval accuracy
- LLM token usage
- Database performance
- Error rates

**Logging**:
- Rich console output
- File logging (configurable)
- Structured logs for production

## Future Enhancements

1. **Multi-modal**: Images, tables, code
2. **Real-time**: Stream processing
3. **Multi-tenant**: User isolation
4. **Advanced NER**: Entity extraction
5. **Graph algorithms**: PageRank, community detection
6. **Caching**: Redis for frequent queries
7. **API**: REST/GraphQL endpoints
8. **Analytics**: Query insights dashboard

## Troubleshooting

**Common Issues**:

1. **Connection failed**: Check Neo4j is running
2. **Out of memory**: Reduce batch size
3. **Slow queries**: Add indexes, reduce top_k
4. **Poor answers**: Adjust chunk size, improve retrieval

**Debug Mode**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## References

- [Neo4j](https://neo4j.com/)
- [LangChain](https://python.langchain.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [RAG Paper](https://arxiv.org/abs/2005.11401)
