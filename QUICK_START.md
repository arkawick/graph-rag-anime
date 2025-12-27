# Quick Start Guide

Get your Neo4j Graph RAG system running in 5 minutes!

## Prerequisites

- Python 3.10+
- Docker (for Neo4j)
- OpenAI API key (or use local models)

## Installation

```bash
# 1. Clone and navigate to project
cd neo4j-graph-rag

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download spaCy model
python -m spacy download en_core_web_sm

# 4. Set up environment
cp .env.example .env
# Edit .env and add your API keys
```

## Start Neo4j

### Option A: Using Docker

```bash
# Start Neo4j with Docker
docker-compose up -d

# Wait for Neo4j to be ready (30 seconds)
# Access Neo4j Browser at: http://localhost:7474
# Login: neo4j/password123
```

### Option B: Using Existing Neo4j Desktop ✅

**Already have Neo4j Desktop installed?**

1. Start your database in Neo4j Desktop (click Start)
2. Install plugins: APOC + Graph Data Science
3. Configure `.env` with your connection details:
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-actual-password
   ```
4. Skip the docker-compose step!

See **[NEO4J_DESKTOP_SETUP.md](NEO4J_DESKTOP_SETUP.md)** for detailed instructions.

## Ingest Your First Documents

```bash
# Create a test document
mkdir -p data/documents
echo "Artificial Intelligence is transforming technology." > data/documents/test.txt

# Ingest documents
python cli.py ingest --source data/documents

# Check statistics
python cli.py stats
```

## Query the System

```bash
# Ask a question
python cli.py query "What is AI?"

# More verbose output
python cli.py query "What is AI?" --top-k 10

# Quiet mode (answer only)
python cli.py query "What is AI?" --quiet
```

## Launch Web UI

```bash
python cli.py serve
```

Open http://localhost:8501 in your browser!

## Common Commands

```bash
# Ingest documents
python cli.py ingest --source /path/to/docs

# Clear and re-ingest
python cli.py ingest --source /path/to/docs --clear

# View statistics
python cli.py stats

# Clear database
python cli.py clear

# Test system
python cli.py test
```

## Using Different Models

### Local Embeddings (Free, no API key needed)

Edit `.env`:
```env
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Local LLM with Ollama (Free)

```bash
# Install Ollama: https://ollama.ai
ollama pull llama2

# Edit .env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama2
```

### OpenAI (Best quality)

Edit `.env`:
```env
OPENAI_API_KEY=sk-your-key-here
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
```

## Troubleshooting

### Neo4j connection failed
```bash
# Check if Neo4j is running
docker ps

# Restart Neo4j
docker-compose restart
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Out of memory
Edit `docker-compose.yml` and reduce memory:
```yaml
NEO4J_dbms_memory_heap_max__size=1G
```

## Next Steps

- Read [Architecture Guide](docs/ARCHITECTURE.md)
- Check [API Documentation](docs/API.md)
- See [Example Notebooks](docs/examples/)

## Support

- Issues: https://github.com/your-repo/issues
- Docs: https://your-docs-url
