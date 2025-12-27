# Anime Graph RAG - Quick Start Guide

Build a knowledge graph from anime data (AniList/Jikan APIs) and query it with natural language!

---

## 🎯 What This Does

Instead of ingesting documents, this system:
1. **Fetches anime data** from AniList or Jikan (MyAnimeList) API
2. **Stores as JSON** for caching and inspection
3. **Builds a knowledge graph** in Neo4j with:
   - Anime nodes (with synopsis embeddings)
   - Genre, Studio, Character, Voice Actor nodes
   - Rich relationships (HAS_GENRE, PRODUCED_BY, FEATURES, SIMILAR_TO, etc.)
4. **Enables semantic search** - Ask questions like "Show me dark fantasy anime" or "Anime similar to Attack on Titan"

---

## 🚀 Quick Start (3 Steps)

### Step 1: Fetch Anime Data

```bash
# Fetch top 100 anime from Jikan API (MyAnimeList data)
python cli.py fetch-anime --source jikan --count 100 --min-score 7.0

# Or fetch from AniList
python cli.py fetch-anime --source anilist --count 100 --min-score 70
```

This creates `data/anime/anime_data.json`

**What you get:**
- Anime metadata (title, synopsis, score, episodes, year)
- Genres and themes
- Studios
- Characters and voice actors (Jikan only)
- Recommendations
- Related anime (sequels, prequels, etc.)

### Step 2: Ingest into Neo4j

```bash
# Ingest anime data and build knowledge graph
python cli.py ingest-anime --clear

# This will:
# 1. Load data from data/anime/anime_data.json
# 2. Generate embeddings from anime synopsis
# 3. Create nodes: Anime, Genre, Studio, Character, VoiceActor
# 4. Create relationships between them
# 5. Compute similarity between anime
```

### Step 3: Query!

```bash
# Semantic search
python cli.py query-anime "dark fantasy anime with great animation"

# Find similar anime
python cli.py query-anime "anime similar to Steins Gate"

# By genre/theme
python cli.py query-anime "psychological thriller anime"
```

---

## 📊 Graph Structure

### Nodes Created

```
(:Anime)
  - id, title, title_english, title_japanese
  - synopsis (text)
  - embedding (384D vector from synopsis)
  - score, popularity, episodes
  - type, status, year, season
  - image_url, url

(:Genre)
  - name

(:Studio)
  - name

(:Character)
  - id, name, role, image_url

(:VoiceActor)
  - id, name
```

### Relationships

```
(Anime)-[:HAS_GENRE]->(Genre)
(Anime)-[:PRODUCED_BY]->(Studio)
(Anime)-[:FEATURES {role: "MAIN"}]->(Character)
(Character)-[:VOICED_BY {language: "Japanese"}]->(VoiceActor)
(Anime)-[:RECOMMENDED {votes: 150}]->(Anime)
(Anime)-[:SEQUEL_OF]->(Anime)
(Anime)-[:PREQUEL_OF]->(Anime)
(Anime)-[:SIMILAR_TO {similarity: 0.85}]->(Anime)
```

---

## 🎨 Visual Example

After ingestion, your graph looks like:

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

## 🔍 Advanced Queries

### Using Cypher in Neo4j Browser

**Find anime by genre:**
```cypher
MATCH (a:Anime)-[:HAS_GENRE]->(g:Genre {name: "Action"})
WHERE a.score >= 8.0
RETURN a.title, a.score
ORDER BY a.score DESC
LIMIT 10
```

**Find anime from specific studio:**
```cypher
MATCH (a:Anime)-[:PRODUCED_BY]->(s:Studio {name: "Kyoto Animation"})
RETURN a.title, a.year, a.score
ORDER BY a.year DESC
```

**Find voice actor's anime:**
```cypher
MATCH (va:VoiceActor {name: "Kana Hanazawa"})<-[:VOICED_BY]-(c:Character)<-[:FEATURES]-(a:Anime)
RETURN DISTINCT a.title, c.name as character
ORDER BY a.score DESC
```

**Find anime similar to a specific one:**
```cypher
MATCH (a1:Anime {title: "Steins;Gate"})-[s:SIMILAR_TO]->(a2:Anime)
RETURN a2.title, s.similarity, a2.score
ORDER BY s.similarity DESC
LIMIT 5
```

**Shortest path between two anime:**
```cypher
MATCH path = shortestPath(
  (a1:Anime {title: "Death Note"})-[*]-(a2:Anime {title: "Code Geass"})
)
RETURN path
```

---

## 🎨 Graph Visualization Commands

These commands are specifically designed for the **Neo4j Browser** to visualize your anime knowledge graph.

### View All Nodes and Relationships

**⚠️ Warning:** Only use this on small datasets (<100 nodes) or Neo4j Browser may freeze!

```cypher
// View entire graph (use with caution!)
MATCH (n)-[r]->(m)
RETURN n, r, m
```

### View Limited Nodes (Recommended)

**View 50 nodes and their relationships:**
```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 50
```

**View 100 nodes and relationships:**
```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 100
```

**View 200 nodes and relationships:**
```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 200
```

### View Specific Node Types

**View all Anime nodes with their Genre relationships:**
```cypher
MATCH (a:Anime)-[r:HAS_GENRE]->(g:Genre)
RETURN a, r, g
LIMIT 100
```

**View Anime and Studio relationships:**
```cypher
MATCH (a:Anime)-[r:PRODUCED_BY]->(s:Studio)
RETURN a, r, s
LIMIT 100
```

**View complete anime ecosystem (Anime + Genres + Studios):**
```cypher
MATCH (a:Anime)-[r1:HAS_GENRE]->(g:Genre)
OPTIONAL MATCH (a)-[r2:PRODUCED_BY]->(s:Studio)
RETURN a, r1, g, r2, s
LIMIT 50
```

**View anime similarity network:**
```cypher
MATCH (a1:Anime)-[r:SIMILAR_TO]->(a2:Anime)
WHERE r.similarity >= 0.75
RETURN a1, r, a2
LIMIT 100
```

**View recommendation network:**
```cypher
MATCH (a1:Anime)-[r:RECOMMENDED]->(a2:Anime)
WHERE r.votes >= 50
RETURN a1, r, a2
LIMIT 100
```

**View character network:**
```cypher
MATCH (a:Anime)-[r1:FEATURES]->(c:Character)-[r2:VOICED_BY]->(va:VoiceActor)
RETURN a, r1, c, r2, va
LIMIT 100
```

### View High-Rated Anime Network

**Top anime and their connections (great for visualization!):**
```cypher
MATCH (a:Anime)-[r]->(n)
WHERE a.score >= 8.5
RETURN a, r, n
LIMIT 200
```

**Popular anime with all relationships:**
```cypher
MATCH (a:Anime)-[r]->(n)
WHERE a.popularity <= 100
RETURN a, r, n
LIMIT 200
```

### View Specific Anime Neighborhood

**Explore everything connected to a specific anime:**
```cypher
// Replace "Attack on Titan" with your anime
MATCH (a:Anime {title: "Attack on Titan"})-[r]-(n)
RETURN a, r, n
```

**Two-hop neighborhood (anime + similar + their genres):**
```cypher
MATCH (a:Anime {title: "Death Note"})-[r1]-(n1)-[r2]-(n2)
RETURN a, r1, n1, r2, n2
LIMIT 200
```

### Studio-Centric View

**View a studio's complete network:**
```cypher
MATCH (s:Studio {name: "Kyoto Animation"})<-[r1:PRODUCED_BY]-(a:Anime)-[r2]->(n)
RETURN s, r1, a, r2, n
LIMIT 200
```

### Genre-Centric View

**View anime in a specific genre:**
```cypher
MATCH (g:Genre {name: "Action"})<-[r1:HAS_GENRE]-(a:Anime)-[r2]->(n)
WHERE a.score >= 7.0
RETURN g, r1, a, r2, n
LIMIT 150
```

### Graph Schema Visualization

**View the structure of your graph:**
```cypher
CALL db.schema.visualization()
```

**See all node labels and counts:**
```cypher
MATCH (n)
RETURN DISTINCT labels(n) AS NodeType, count(n) AS Count
ORDER BY Count DESC
```

**See all relationship types and counts:**
```cypher
MATCH ()-[r]->()
RETURN DISTINCT type(r) AS RelationshipType, count(r) AS Count
ORDER BY Count DESC
```

### Interactive Visualization Tips

**In Neo4j Browser:**

1. **Expand on Click**: Click any node to see its immediate connections
2. **Zoom**: Use mouse wheel to zoom in/out
3. **Pan**: Click and drag background to move around
4. **Node Colors**: Different node types have different colors
5. **Relationship Labels**: Hover over edges to see relationship types
6. **Full Screen**: Click expand icon for better view
7. **Download**: Export visualization as PNG or SVG

**Styling Tips:**

```cypher
// After running a query, click the node type at the top
// Then customize:
// - Size (by property like score)
// - Color
// - Caption (what to display on node)
```

**Recommended Caption Settings:**
- **Anime**: Display `title` and `score`
- **Genre**: Display `name`
- **Studio**: Display `name`
- **Character**: Display `name`

---

## 🛠️ CLI Commands Reference

### Fetch Commands

```bash
# Fetch from Jikan (MyAnimeList)
python cli.py fetch-anime --source jikan --count 200 --min-score 8.0

# Fetch from AniList
python cli.py fetch-anime --source anilist --count 200 --min-score 80

# Save to custom file
python cli.py fetch-anime --output my_anime.json
```

### Ingest Commands

```bash
# Ingest with embeddings (default)
python cli.py ingest-anime

# Ingest without embeddings (faster, no similarity search)
python cli.py ingest-anime --no-embeddings

# Ingest from custom JSON file
python cli.py ingest-anime --json-file data/anime/my_anime.json

# Clear database first
python cli.py ingest-anime --clear
```

### Query Commands

```bash
# Basic query
python cli.py query-anime "mecha anime"

# Get more results
python cli.py query-anime "slice of life" --top-k 10

# View database stats
python cli.py stats
```

---

## 💡 Example Workflows

### Workflow 1: Build Complete Anime Database

```bash
# 1. Fetch comprehensive data (takes ~5 minutes for 500 anime)
python cli.py fetch-anime --source jikan --count 500 --min-score 6.0

# 2. Ingest into graph
python cli.py ingest-anime --clear

# 3. Explore in Neo4j Browser
# Open: http://localhost:7474
# Run: MATCH (n) RETURN n LIMIT 100

# 4. Query
python cli.py query-anime "epic battle shonen anime"
```

### Workflow 2: Seasonal Anime Update

```bash
# Fetch recent high-rated anime
python cli.py fetch-anime --count 50 --min-score 8.0 --output seasonal_2024.json

# Ingest without clearing (adds to existing graph)
python cli.py ingest-anime --json-file data/anime/seasonal_2024.json

# Find similar to your favorites
python cli.py query-anime "anime like Frieren"
```

### Workflow 3: Genre-Specific Collection

```bash
# Fetch and filter in code (modify anime_fetcher.py)
# Or use Jikan genre filter

# Example: Romance anime
python cli.py fetch-anime --count 100

# Then filter in Neo4j:
# MATCH (a:Anime)-[:HAS_GENRE]->(g:Genre {name: "Romance"})
# DETACH DELETE a WHERE NOT (a)-[:HAS_GENRE]->(:Genre {name: "Romance"})
```

---

## 🎯 Use Cases

### 1. **Recommendation System**
```bash
python cli.py query-anime "anime similar to Your Name with romance"
```

### 2. **Discover Hidden Gems**
```cypher
MATCH (a:Anime)
WHERE a.score >= 8.0 AND a.popularity < 10000
RETURN a.title, a.score, a.synopsis
LIMIT 10
```

### 3. **Studio Analysis**
```cypher
MATCH (s:Studio)<-[:PRODUCED_BY]-(a:Anime)
RETURN s.name, count(a) as anime_count, avg(a.score) as avg_score
ORDER BY anime_count DESC
```

### 4. **Character Network**
```cypher
MATCH (c:Character)<-[:FEATURES]-(a:Anime)-[:FEATURES]->(c2:Character)
WHERE c.name CONTAINS "Luffy"
RETURN c2.name, count(a) as shared_anime
ORDER BY shared_anime DESC
```

---

## 🔧 Customization

### Modify Graph Schema

Edit `src/graph/anime_graph_builder.py`:

```python
# Add custom relationships
def _link_anime_to_theme(self, anime_id: str, theme: str):
    query = """
    MATCH (a:Anime {id: $anime_id})
    MERGE (t:Theme {name: $theme})
    MERGE (a)-[:HAS_THEME]->(t)
    """
    self.client.execute_query(query, {"anime_id": anime_id, "theme": theme})
```

### Add More Data Sources

Edit `src/ingestion/anime_fetcher.py`:

```python
def fetch_from_kitsu(self):
    # Implement Kitsu API fetching
    pass
```

---

## 📈 Performance Tips

### 1. **Create Indexes** (automatically done)
```cypher
CREATE INDEX anime_id FOR (a:Anime) ON (a.id);
CREATE INDEX genre_name FOR (g:Genre) ON (g.name);
CREATE INDEX studio_name FOR (s:Studio) ON (s.name);
```

### 2. **Limit Embedding Generation**
```bash
# Skip embeddings for faster ingestion
python cli.py ingest-anime --no-embeddings
```

### 3. **Batch Processing**
```bash
# Process in chunks
python cli.py fetch-anime --count 100 --output batch1.json
python cli.py ingest-anime --json-file data/anime/batch1.json

python cli.py fetch-anime --count 100 --output batch2.json
python cli.py ingest-anime --json-file data/anime/batch2.json
```

---

## 🐛 Troubleshooting

### API Rate Limits

**Jikan:** 3 requests/second, 60/minute
- Add delays in `anime_fetcher.py` (already implemented)

**AniList:** 90 requests/minute
- Automatic rate limiting included

### Missing Data

Some anime might not have:
- Characters (use Jikan for this)
- Recommendations (add manually)
- Synopsis (skip embedding)

```python
# Filter out anime without synopsis
anime_list = [a for a in anime_list if a.get("synopsis")]
```

### Connection Issues

```bash
# Test Neo4j connection
python cli.py stats

# Check if database is running
# Neo4j Desktop → Start database
```

---

## 🎓 Next Steps

1. **Explore the graph visually** in Neo4j Browser
2. **Build a Streamlit UI** for anime recommendations
3. **Add user ratings** and personalization
4. **Implement RAG** for answering questions about anime lore
5. **Create visualization** similar to your anime map!

---

## 🆚 Comparison: Documents vs Anime

| Feature | Document RAG | Anime RAG |
|---------|-------------|-----------|
| **Data Source** | PDF, TXT, MD files | Jikan/AniList API |
| **Main Nodes** | Document, Chunk | Anime, Genre, Studio |
| **Text Content** | Full documents | Synopsis, descriptions |
| **Embeddings** | Text chunks | Anime synopsis |
| **Relationships** | HAS_CHUNK, NEXT | HAS_GENRE, SIMILAR_TO, RECOMMENDED |
| **Queries** | "What does this say?" | "Show me anime like X" |
| **Use Case** | Information retrieval | Recommendation, discovery |

---

## 📚 API Documentation

### Jikan API
- Docs: https://docs.api.jikan.moe/
- Endpoints: `/anime`, `/characters`, `/recommendations`
- Rate limit: 3 req/s, 60 req/min

### AniList API
- Docs: https://anilist.gitbook.io/anilist-apiv2-docs/
- Type: GraphQL
- Rate limit: 90 req/min
- More data: Relations, recommendations, staff

---

**Happy anime hunting! 🎌**

Questions? Check Neo4j Browser at `http://localhost:7474` to explore your anime graph!
