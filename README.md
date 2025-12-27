# Anime Knowledge Graph RAG System 🎌

A production-ready Neo4j-powered knowledge graph system for anime data with semantic search and graph-based recommendations. Built with vector embeddings, hybrid retrieval, and support for both anime APIs and document ingestion.

![Graph Visualization](docs/images/visualization.png)
*Interactive anime knowledge graph in Neo4j Browser*

---

## 🌟 Features

### Anime RAG System
- 🎌 **Multi-source Data Fetching**: AniList GraphQL API & Jikan REST API (MyAnimeList)
- 📊 **Rich Knowledge Graph**: Anime, Genres, Studios, Characters, Voice Actors
- 🔗 **Semantic Relationships**: SIMILAR_TO (embedding-based), RECOMMENDED, SEQUEL_OF, HAS_GENRE
- 🧠 **Vector Search**: Find anime by natural language queries ("dark fantasy with great animation")
- 🎯 **Hybrid Retrieval**: Combines embedding similarity with graph traversal
- 🎨 **Interactive Visualization**: Explore anime networks in Neo4j Browser
- 📈 **Recommendation Engine**: Discover similar anime and hidden gems

### Document RAG System (Bonus)
- 📄 **Multi-format Ingestion**: PDF, TXT, Markdown, DOCX
- 🧠 **Smart Chunking**: Semantic and recursive text splitting
- 🤖 **RAG Engine**: Context-aware answer generation with LLM
- 🔍 **Source Attribution**: Cite specific chunks and documents

---

## 📊 Graph Architecture

### Anime Knowledge Graph

```
API Data → JSON Storage → Embeddings → Neo4j Graph → Semantic Search
```

**Node Types:**
```
(:Anime)       - Title, synopsis, score, episodes, embeddings
(:Genre)       - Action, Fantasy, Romance, etc.
(:Studio)      - Production companies
(:Character)   - Main/supporting characters
(:VoiceActor)  - Japanese/English voice actors
```

**Relationships:**
```
(Anime)-[:HAS_GENRE]->(Genre)
(Anime)-[:PRODUCED_BY]->(Studio)
(Anime)-[:FEATURES {role}]->(Character)
(Character)-[:VOICED_BY {language}]->(VoiceActor)
(Anime)-[:SIMILAR_TO {similarity: 0.85}]->(Anime)    ← Computed from embeddings
(Anime)-[:RECOMMENDED {votes}]->(Anime)              ← From API
(Anime)-[:SEQUEL_OF]->(Anime)                        ← From API
(Anime)-[:PREQUEL_OF]->(Anime)                       ← From API
```

### Visual Structure

![Graph Schema](docs/images/schema.png)
*Neo4j graph schema showing node types and relationships*

```
        ┌─────────┐
        │ Action  │ (Genre)
        └────┬────┘
             │ HAS_GENRE
    ┌────────┴────────┐
    │  Attack on      │
    │  Titan          │ (Anime)
    │  score: 8.5     │
    │  embedding: [...]
    └─┬──────┬────┬───┘
      │      │    │
      │      │    └──PRODUCED_BY──→ [WIT Studio]
      │      │
      │      └──FEATURES──→ [Eren Yeager] ──VOICED_BY──→ [Yuki Kaji]
      │
      └──SIMILAR_TO (0.82)──→ [Code Geass]
      └──RECOMMENDED (250)───→ [Fullmetal Alchemist]
```

---

## 🚀 Quick Start

### Prerequisites

1. **Neo4j Desktop** or **Docker** with Neo4j
2. **Python 3.10+**
3. **API Access** (no auth needed for Jikan/AniList)

### Step 1: Installation

```bash
# Clone repository
cd map-of-anime

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Configure environment
cp .env.example .env
# Edit .env with your Neo4j credentials
```

### Step 2: Neo4j Setup

#### Option A: Using Neo4j Desktop (Recommended)

1. **Start Neo4j Desktop**
2. **Create/Start a database**
3. **Install required plugins:**
   - APOC (Awesome Procedures on Cypher)
   - Graph Data Science
4. **Configure `.env`:**
   ```env
   NEO4J_URI=neo4j://127.0.0.1:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-password
   ```

See **[NEO4J_DESKTOP_SETUP.md](NEO4J_DESKTOP_SETUP.md)** for detailed setup guide.

#### Option B: Using Docker

```bash
# Start Neo4j container
docker-compose up -d

# Wait 30 seconds for initialization
# Access Neo4j Browser at: http://localhost:7474
# Login: neo4j/password123
```

### Step 3: Verify Connection

```bash
# Test connection
python cli.py stats
```

**Expected output:**
```
┌──────────────────┬───────┐
│ Metric           │ Count │
├──────────────────┼───────┤
│ Documents        │ 0     │
│ Chunks           │ 0     │
│ Entities         │ 0     │
│ Relationships    │ 0     │
└──────────────────┴───────┘
```

---

## 🎌 Building Your Anime Knowledge Graph

### Workflow: Fetch → Store → Ingest → Query

#### 1. Fetch Anime Data

```bash
# Fetch top 100 anime from Jikan (MyAnimeList data)
python cli.py fetch-anime --source jikan --count 100 --min-score 7.5

# Or fetch from AniList
python cli.py fetch-anime --source anilist --count 100 --min-score 75

# Fetch more for comprehensive database
python cli.py fetch-anime --source jikan --count 500 --min-score 6.0 --output comprehensive.json
```

**What you get (saved to `data/anime/anime_data.json`):**
- ✅ Anime metadata (title, synopsis, score, episodes, year, season)
- ✅ Genres and themes
- ✅ Studios
- ✅ Characters and voice actors (Jikan only)
- ✅ User recommendations (vote counts)
- ✅ Related anime (sequels, prequels, spin-offs)

**API Sources:**

| Source | Pros | Cons | Data Quality |
|--------|------|------|--------------|
| **Jikan** | Free, no auth, includes characters/VAs | 3 req/s limit | ⭐⭐⭐⭐⭐ |
| **AniList** | GraphQL, faster, relations | No voice actors | ⭐⭐⭐⭐ |

#### 2. Ingest into Neo4j Graph

```bash
# Full ingestion with embeddings (recommended)
python cli.py ingest-anime --clear

# This process:
# ✓ Loads JSON data
# ✓ Generates 384D embeddings from synopsis (using sentence-transformers)
# ✓ Creates Anime, Genre, Studio, Character, VoiceActor nodes
# ✓ Links nodes with typed relationships
# ✓ Computes cosine similarity between anime (threshold: 0.75)
# ✓ Creates indexes for fast lookups
```

**Ingestion options:**

```bash
# Without embeddings (faster, but no similarity search)
python cli.py ingest-anime --no-embeddings

# From custom JSON file
python cli.py ingest-anime --json-file data/anime/my_custom.json

# Add to existing graph (don't clear)
python cli.py ingest-anime
```

**Progress output:**
```
Building Anime Knowledge Graph...
Creating anime nodes...       ████████████████████ 100/100
Creating genres...            ████████████████████ 45/45
Creating studios...           ████████████████████ 78/78
Creating characters...        ████████████████████ 250/250
Computing similarities...     ████████████████████ 100/100

✓ Anime Knowledge Graph Built!
  Anime: 100
  Genres: 45
  Studios: 78
  Characters: 250
  Total Relationships: 1,234
```

#### 3. Query the Graph

**Command-line queries:**

```bash
# Semantic search
python cli.py query-anime "dark fantasy anime with complex plot"

# Find similar anime
python cli.py query-anime "anime similar to Steins Gate"

# Genre-based
python cli.py query-anime "wholesome slice of life comedy"

# Get more results
python cli.py query-anime "mecha anime" --top-k 10
```

**Example output:**
```
Question: dark fantasy anime with complex plot

Top matching anime:

1. Attack on Titan
   Score: 8.55 | Episodes: 87
   Similarity: 0.873
   Synopsis: Eren Yeager and others of the 107th Training Corps...

2. Death Note
   Score: 8.62 | Episodes: 37
   Similarity: 0.845
   Synopsis: Light Yagami finds the "Death Note," a notebook...

3. Fate/Zero
   Score: 8.27 | Episodes: 25
   Similarity: 0.821
   Synopsis: War of the Holy Grail - Pursuing the power to grant...
```

---

## 🎨 Graph Visualization

### Access Neo4j Browser

```
Open: http://localhost:7474
Login: neo4j / your-password
```

![Neo4j Browser](docs/images/browser.png)
*Neo4j Browser interface for graph exploration*

### Essential Visualization Queries

#### View 50-200 Nodes (Recommended Starting Point)

```cypher
// View 50 nodes and relationships
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 50
```

```cypher
// View 100 nodes
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 100
```

```cypher
// View 200 nodes
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 200
```

⚠️ **Warning:** Viewing entire graph without LIMIT may freeze browser on large datasets!

#### Best Visualization Queries

**Top-rated anime ecosystem (most visually appealing):**
```cypher
MATCH (a:Anime)-[r]->(n)
WHERE a.score >= 8.5
RETURN a, r, n
LIMIT 200
```

**Complete anime ecosystem with genres and studios:**
```cypher
MATCH (a:Anime)-[r1:HAS_GENRE]->(g:Genre)
OPTIONAL MATCH (a)-[r2:PRODUCED_BY]->(s:Studio)
RETURN a, r1, g, r2, s
LIMIT 50
```

**Similarity network (shows clustering):**
```cypher
MATCH (a1:Anime)-[r:SIMILAR_TO]->(a2:Anime)
WHERE r.similarity >= 0.75
RETURN a1, r, a2
LIMIT 100
```

**Recommendation network:**
```cypher
MATCH (a1:Anime)-[r:RECOMMENDED]->(a2:Anime)
WHERE r.votes >= 50
RETURN a1, r, a2
LIMIT 100
```

**Explore specific anime neighborhood:**
```cypher
MATCH (a:Anime {title: "Attack on Titan"})-[r]-(n)
RETURN a, r, n
```

**Studio-centric view:**
```cypher
MATCH (s:Studio {name: "Kyoto Animation"})<-[r1:PRODUCED_BY]-(a:Anime)-[r2]->(n)
RETURN s, r1, a, r2, n
LIMIT 200
```

![Similarity Network](docs/images/similarity_network.png)
*Anime similarity network based on synopsis embeddings*

### Visualization Styling Tips

**In Neo4j Browser, customize node appearance:**

1. **Click node type** (e.g., "Anime") at top of results
2. **Set caption** to display on nodes:
   - Anime: `title`, `score`
   - Genre: `name`
   - Studio: `name`
3. **Size by property**: Set size by `score` for Anime nodes
4. **Color**: Choose distinct colors for each node type
5. **Download**: Export as PNG or SVG

![Styled Graph](docs/images/styled_graph.png)
*Custom-styled graph with sized nodes and colored types*

---

## 🔍 Advanced Cypher Queries

### Recommendation & Discovery

**Find anime by genre:**
```cypher
MATCH (a:Anime)-[:HAS_GENRE]->(g:Genre {name: "Action"})
WHERE a.score >= 8.0
RETURN a.title, a.score, a.synopsis
ORDER BY a.score DESC
LIMIT 10
```

**Discover hidden gems (high score, low popularity):**
```cypher
MATCH (a:Anime)
WHERE a.score >= 8.0 AND a.popularity < 10000
RETURN a.title, a.score, a.synopsis, a.popularity
ORDER BY a.score DESC
LIMIT 10
```

**Find similar anime to a specific title:**
```cypher
MATCH (a1:Anime {title: "Steins;Gate"})-[s:SIMILAR_TO]->(a2:Anime)
RETURN a2.title, s.similarity, a2.score, a2.synopsis
ORDER BY s.similarity DESC
LIMIT 5
```

**Shortest path between two anime:**
```cypher
MATCH path = shortestPath(
  (a1:Anime {title: "Death Note"})-[*..5]-(a2:Anime {title: "Code Geass"})
)
RETURN path
```

### Studio & Production Analysis

**Top studios by anime count:**
```cypher
MATCH (s:Studio)<-[:PRODUCED_BY]-(a:Anime)
RETURN s.name,
       count(a) as anime_count,
       avg(a.score) as avg_score,
       max(a.score) as best_score
ORDER BY anime_count DESC
LIMIT 10
```

**Studio's complete portfolio:**
```cypher
MATCH (s:Studio {name: "Kyoto Animation"})<-[:PRODUCED_BY]-(a:Anime)
RETURN a.title, a.year, a.score, a.episodes
ORDER BY a.year DESC
```

### Character & Voice Actor Networks

**Voice actor's anime roles:**
```cypher
MATCH (va:VoiceActor {name: "Kana Hanazawa"})<-[:VOICED_BY]-(c:Character)<-[:FEATURES]-(a:Anime)
RETURN DISTINCT a.title, c.name as character, c.role
ORDER BY a.score DESC
```

**Characters appearing in multiple anime (shared universe):**
```cypher
MATCH (c:Character)<-[:FEATURES]-(a:Anime)
WITH c, collect(a.title) as anime_list, count(a) as anime_count
WHERE anime_count > 1
RETURN c.name, anime_list, anime_count
ORDER BY anime_count DESC
```

### Graph Statistics

**Node type distribution:**
```cypher
MATCH (n)
RETURN DISTINCT labels(n) AS NodeType, count(n) AS Count
ORDER BY Count DESC
```

**Relationship type distribution:**
```cypher
MATCH ()-[r]->()
RETURN DISTINCT type(r) AS RelationshipType, count(r) AS Count
ORDER BY Count DESC
```

**Graph schema:**
```cypher
CALL db.schema.visualization()
```

**Anime with most connections:**
```cypher
MATCH (a:Anime)-[r]-()
RETURN a.title, a.score, count(r) as connection_count
ORDER BY connection_count DESC
LIMIT 10
```

---

## 🛠️ CLI Commands Reference

### Anime Commands

```bash
# Fetch anime data
python cli.py fetch-anime --source jikan --count 100 --min-score 7.0
python cli.py fetch-anime --source anilist --count 100 --min-score 70
python cli.py fetch-anime --output my_anime.json

# Ingest anime data
python cli.py ingest-anime --clear
python cli.py ingest-anime --no-embeddings
python cli.py ingest-anime --json-file data/anime/custom.json

# Query anime
python cli.py query-anime "dark fantasy anime"
python cli.py query-anime "slice of life" --top-k 10

# View statistics
python cli.py stats
```

### Document RAG Commands (Bonus)

```bash
# Ingest documents
python cli.py ingest --source data/documents
python cli.py ingest --source data/documents --clear

# Query documents
python cli.py query "What is machine learning?"
python cli.py query "Explain the concept" --top-k 10 --quiet

# Clear database
python cli.py clear

# Launch web UI
python cli.py serve --port 8501

# Run tests
python cli.py test
```

---

## 💡 Example Workflows

### Workflow 1: Complete Anime Database

```bash
# 1. Fetch comprehensive data (~5 mins for 500 anime)
python cli.py fetch-anime --source jikan --count 500 --min-score 6.0

# 2. Ingest into graph (~3 mins with embeddings)
python cli.py ingest-anime --clear

# 3. Open Neo4j Browser
# http://localhost:7474

# 4. Run visualization query
MATCH (a:Anime)-[r]->(n)
WHERE a.score >= 8.0
RETURN a, r, n
LIMIT 200

# 5. Query from CLI
python cli.py query-anime "psychological thriller with time travel"
```

### Workflow 2: Seasonal Anime Update

```bash
# Fetch current season's top anime
python cli.py fetch-anime --count 50 --min-score 8.0 --output seasonal_2025.json

# Add to existing graph (don't clear)
python cli.py ingest-anime --json-file data/anime/seasonal_2025.json

# Find similar to trending anime
python cli.py query-anime "anime like Frieren"
```

### Workflow 3: Genre-Specific Analysis

```bash
# Fetch broad dataset
python cli.py fetch-anime --count 300

# Ingest
python cli.py ingest-anime --clear

# Analyze in Neo4j Browser
MATCH (g:Genre)<-[:HAS_GENRE]-(a:Anime)
WITH g, count(a) as anime_count, avg(a.score) as avg_score
RETURN g.name, anime_count, round(avg_score, 2) as avg_score
ORDER BY anime_count DESC
```

### Workflow 4: Studio Comparison

```cypher
// Compare top studios
MATCH (s:Studio)<-[:PRODUCED_BY]-(a:Anime)
WITH s, collect({title: a.title, score: a.score}) as anime_list,
     avg(a.score) as avg_score, count(a) as anime_count
WHERE anime_count >= 5
RETURN s.name, anime_count, round(avg_score, 2) as avg_score
ORDER BY avg_score DESC
LIMIT 10
```

---

## 🎯 Use Cases

### 1. Anime Recommendation System
```bash
python cli.py query-anime "anime similar to Your Name with romance and beautiful visuals"
```

### 2. Content Discovery
```cypher
// Find underrated anime
MATCH (a:Anime)
WHERE a.score >= 8.0 AND a.popularity > 1000
RETURN a.title, a.score, a.synopsis
ORDER BY a.popularity DESC
LIMIT 20
```

### 3. Studio Portfolio Analysis
```cypher
MATCH (s:Studio)<-[:PRODUCED_BY]-(a:Anime)
RETURN s.name, count(a) as total, avg(a.score) as avg_score
ORDER BY total DESC
```

### 4. Voice Actor Tracking
```cypher
MATCH (va:VoiceActor)<-[:VOICED_BY]-(c:Character)<-[:FEATURES]-(a:Anime)
WHERE va.name = "Hiroshi Kamiya"
RETURN a.title, c.name, c.role
ORDER BY a.score DESC
```

### 5. Franchise Mapping
```cypher
MATCH path = (a:Anime)-[:SEQUEL_OF*]->(origin:Anime)
WHERE NOT (origin)-[:PREQUEL_OF]->()
RETURN path
```

---

## 🔧 Customization & Extension

### Add Custom Node Types

Edit `src/graph/anime_graph_builder.py`:

```python
def _create_theme_node(self, theme: str):
    """Create a Theme node (different from Genre)."""
    query = """
    MERGE (t:Theme {name: $name})
    SET t.updated_at = datetime()
    RETURN t
    """
    self.client.execute_query(query, {"name": theme})

def _link_anime_to_theme(self, anime_id: str, theme: str):
    query = """
    MATCH (a:Anime {id: $anime_id})
    MATCH (t:Theme {name: $theme})
    MERGE (a)-[:HAS_THEME]->(t)
    """
    self.client.execute_query(query, {"anime_id": anime_id, "theme": theme})
```

### Add New Data Sources

Edit `src/ingestion/anime_fetcher.py`:

```python
def fetch_from_kitsu(self, max_anime: int = 100):
    """Fetch from Kitsu API."""
    url = "https://kitsu.io/api/edge/anime"
    # Implementation...
```

### Modify Similarity Threshold

In `src/graph/anime_graph_builder.py`:

```python
self._create_similarity_relationships(
    anime_ids,
    embeddings,
    threshold=0.70,  # Lower = more connections (default: 0.75)
    max_connections=10  # More similar anime per node (default: 10)
)
```

---

## 📈 Performance Optimization

### Indexing (Automatic)

```cypher
CREATE INDEX anime_id FOR (a:Anime) ON (a.id);
CREATE INDEX anime_title FOR (a:Anime) ON (a.title);
CREATE INDEX genre_name FOR (g:Genre) ON (g.name);
CREATE INDEX studio_name FOR (s:Studio) ON (s.name);
CREATE INDEX character_id FOR (c:Character) ON (c.id);
```

### Batch Processing

```bash
# Process large datasets in batches
for i in {1..5}; do
  python cli.py fetch-anime --count 100 --output batch_$i.json
  python cli.py ingest-anime --json-file data/anime/batch_$i.json
done
```

### Skip Embeddings for Speed

```bash
# 3-5x faster ingestion without embeddings
python cli.py ingest-anime --no-embeddings

# Add embeddings later if needed
# (requires custom script)
```

### Query Optimization

```cypher
// Use LIMIT to prevent long execution times
MATCH (a:Anime)-[r]->(n)
WHERE a.score >= 8.0
RETURN a, r, n
LIMIT 100  // Always add LIMIT for visualization queries
```

---

## 🐛 Troubleshooting

### Neo4j Connection Issues

```bash
# Test connection
python cli.py stats

# Check .env configuration
cat .env | grep NEO4J

# Verify Neo4j is running
# Neo4j Desktop → Database → Start
# Or: docker ps | grep neo4j
```

**Common fixes:**
- Update `NEO4J_PASSWORD` in `.env`
- Ensure APOC and GDS plugins are installed
- Restart Neo4j after plugin installation
- Check URI format: `neo4j://` or `bolt://`

### API Rate Limiting

**Jikan API (3 req/s):**
- Automatic delays implemented in `anime_fetcher.py`
- Reduce `--count` if seeing 429 errors

**AniList API (90 req/min):**
- Automatic rate limiting included
- More reliable for large fetches

### Missing Data

Some anime may lack:
- Synopsis → Skip embedding generation
- Characters → Use Jikan instead of AniList
- Recommendations → Manual addition needed

```python
# Filter anime without synopsis before ingestion
anime_list = [a for a in anime_list if a.get("synopsis")]
```

### Memory Issues

```bash
# Reduce batch size
python cli.py fetch-anime --count 50

# Skip embeddings
python cli.py ingest-anime --no-embeddings

# Increase Neo4j heap memory
# Neo4j Desktop → Manage → Settings
# dbms.memory.heap.max_size=4G
```

---

## 📚 Tech Stack

### Core Technologies

- **Graph Database**: Neo4j 5.15+ (with APOC & GDS plugins)
- **Vector Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **APIs**: Jikan REST API, AniList GraphQL API
- **Framework**: LangChain for RAG
- **NLP**: spaCy for entity extraction
- **CLI**: Click + Rich (beautiful terminal output)
- **Web UI**: Streamlit (optional)

### Python Libraries

```
Core: neo4j, langchain, sentence-transformers
APIs: requests (Jikan), graphql (AniList)
NLP: spacy, tiktoken
Vector: faiss-cpu, scikit-learn
Utils: click, rich, pydantic, python-dotenv
```

---

## 📖 Documentation

- **[NEO4J_DESKTOP_SETUP.md](NEO4J_DESKTOP_SETUP.md)** - Complete Neo4j Desktop setup guide
- **[QUICK_START.md](QUICK_START.md)** - 5-minute getting started guide
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Navigation guide for all docs
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture deep-dive
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project overview

---

## 🎓 Learning Resources

### Neo4j
- [Neo4j Graph Academy](https://neo4j.com/graphacademy/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [APOC Documentation](https://neo4j.com/labs/apoc/)

### APIs
- [Jikan API Docs](https://docs.api.jikan.moe/)
- [AniList GraphQL](https://anilist.gitbook.io/anilist-apiv2-docs/)
- [MyAnimeList](https://myanimelist.net/)

### RAG & Embeddings
- [LangChain Docs](https://python.langchain.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [Vector Search Guide](https://www.pinecone.io/learn/vector-embeddings/)

---

## 🌐 Example Visualizations

### 1. Similarity Network
![Similarity Network](docs/images/similarity_network.png)
*Anime clustered by synopsis similarity (embedding-based)*

### 2. Studio Networks
![Studio Network](docs/images/studio_network.png)
*Kyoto Animation's complete anime portfolio*

### 3. Genre Distribution
![Genre Distribution](docs/images/genre_distribution.png)
*Action genre with top-rated anime*

### 4. Recommendation Graph
![Recommendation Graph](docs/images/recommendation_graph.png)
*User-recommended anime connections*

**To create these visualizations:**
1. Run queries from "Graph Visualization Commands" section
2. Customize styling in Neo4j Browser
3. Export as PNG/SVG using download button

---

## 🆚 Comparison: Document vs Anime RAG

| Feature | Document RAG | Anime RAG |
|---------|--------------|-----------|
| **Data Source** | PDF, TXT, MD, DOCX files | Jikan/AniList APIs |
| **Node Types** | Document, Chunk, Entity | Anime, Genre, Studio, Character, VoiceActor |
| **Text Content** | Full documents split into chunks | Anime synopsis, descriptions |
| **Embeddings** | Text chunks (500 chars) | Synopsis (full text) |
| **Relationships** | HAS_CHUNK, NEXT, SIMILAR_TO | HAS_GENRE, PRODUCED_BY, FEATURES, SIMILAR_TO, RECOMMENDED |
| **Query Type** | "What does this document say about X?" | "Find anime similar to X" |
| **Use Case** | Information retrieval, Q&A | Recommendation, discovery |
| **LLM Integration** | Answer generation with context | Semantic search (no LLM needed) |
| **Visualization** | Document hierarchy | Network graph of relationships |

---

## 🤝 Contributing

This is a personal project, but feel free to:
- Fork and customize for your use case
- Add new data sources (Kitsu, AniDB)
- Improve embedding models
- Build a web UI for recommendations
- Share interesting Cypher queries!

---

## 📝 License

MIT License - Feel free to use for personal or commercial projects.

---

## 🙏 Acknowledgments

- **Neo4j** for the amazing graph database
- **Jikan** for free MyAnimeList API access
- **AniList** for comprehensive anime data
- **Sentence Transformers** for embeddings
- **LangChain** for RAG framework

---

## 🎉 Next Steps

1. ✅ **Test connection**: `python cli.py stats`
2. ✅ **Fetch anime data**: `python cli.py fetch-anime --count 100`
3. ✅ **Build graph**: `python cli.py ingest-anime --clear`
4. ✅ **Visualize**: Open http://localhost:7474
5. ✅ **Query**: `python cli.py query-anime "your query"`
6. 🎯 **Explore**: Try advanced Cypher queries
7. 🚀 **Customize**: Add your own data sources and relationships

---

**Happy anime hunting! 🎌**

Questions? Explore your graph at `http://localhost:7474` or check the [documentation](DOCUMENTATION_INDEX.md).
