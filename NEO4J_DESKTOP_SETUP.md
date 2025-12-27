# Using Existing Neo4j Desktop Installation

This guide explains how to use your existing Neo4j Desktop installation instead of Docker.

---

## Prerequisites

- ✅ Neo4j Desktop installed and running
- ✅ A Neo4j database created (any version 4.x or 5.x)
- ✅ APOC plugin installed (recommended)
- ✅ Graph Data Science plugin installed (recommended)

---

## Step-by-Step Setup

### 1. Start Your Neo4j Database

1. Open **Neo4j Desktop**
2. Select your database (or create a new one)
3. Click **Start** to start the database
4. Note the connection details:
   - **Bolt URL**: Usually `bolt://localhost:7687`
   - **Username**: Usually `neo4j`
   - **Password**: Your database password

---

### 2. Install Required Plugins

In **Neo4j Desktop**:

1. Select your database
2. Go to **Plugins** tab
3. Install the following:
   - ✅ **APOC** (Awesome Procedures on Cypher)
   - ✅ **Graph Data Science** (for similarity functions)
4. **Restart** your database after installing plugins

**Why these plugins?**
- `APOC`: Provides graph traversal functions
- `GDS`: Provides cosine similarity for vector search

---

### 3. Configure Connection

Create/edit `.env` file in project root:

```env
# ============================================
# NEO4J DESKTOP CONNECTION
# ============================================
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-actual-password

# If using a specific database (Neo4j 4.x+)
# NEO4J_DATABASE=neo4j

# ============================================
# EMBEDDINGS (Local - No API Key Needed)
# ============================================
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# ============================================
# LLM OPTIONS
# ============================================
# Option 1: OpenAI (Best quality, requires API key)
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your-api-key-here

# Option 2: Ollama (Free, local)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama2
OLLAMA_BASE_URL=http://localhost:11434

# ============================================
# CHUNKING CONFIGURATION
# ============================================
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# ============================================
# SEARCH CONFIGURATION
# ============================================
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.7
```

---

### 4. Find Your Connection Details

#### In Neo4j Desktop:

1. Select your database
2. Click on **Manage** or **Details**
3. Look for:
   ```
   Bolt URL: bolt://localhost:7687
   Username: neo4j
   Password: [your password]
   ```

#### Common Connection Settings:

| Setting | Default Value | How to Find |
|---------|--------------|-------------|
| URI | `bolt://localhost:7687` | Neo4j Desktop → Database Details |
| User | `neo4j` | Default username |
| Password | Your chosen password | Set when creating database |
| Port | `7687` | Neo4j Desktop → Settings |

#### If Using Different Port:

Some installations use different ports. Check in Neo4j Desktop settings:

```env
NEO4J_URI=bolt://localhost:7688  # or your custom port
```

---

### 5. Verify Connection

Test the connection before proceeding:

```bash
# Test Python connection
python -c "from src.graph import Neo4jClient; client = Neo4jClient(); print('✓ Connected successfully!'); client.close()"
```

**Expected output:**
```
✓ Connected to Neo4j at bolt://localhost:7687
✓ Connected successfully!
Neo4j connection closed
```

**If it fails:**
- ❌ Check database is STARTED in Neo4j Desktop
- ❌ Verify password in `.env` matches Neo4j Desktop
- ❌ Check Bolt port is correct
- ❌ Ensure firewall isn't blocking port 7687

---

### 6. Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm
```

---

### 7. Check Database Statistics

```bash
python cli.py stats
```

**Expected output (empty database):**
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

### 8. Test with Sample Data

```bash
# Create test document
mkdir -p data/documents
echo "Artificial Intelligence is transforming modern technology through machine learning and deep learning techniques." > data/documents/test.txt

# Ingest
python cli.py ingest --source data/documents

# Check stats again
python cli.py stats

# Should now show 1 document and some chunks!
```

---

### 9. Query the System

```bash
# Ask a question
python cli.py query "What is AI?"

# More detailed query
python cli.py query "Explain machine learning" --top-k 10
```

---

## Docker vs Neo4j Desktop Comparison

| Feature | Docker | Neo4j Desktop |
|---------|--------|---------------|
| **Setup** | `docker-compose up` | Already installed ✅ |
| **GUI** | Browser only | Full Desktop GUI ✅ |
| **Plugins** | Pre-configured | Manual install |
| **Port** | 7474, 7687 | 7474, 7687 |
| **Data Persistence** | Docker volumes | Desktop storage ✅ |
| **Visual Browser** | Yes | Yes ✅ |
| **Cypher Editor** | Yes | Better UI ✅ |
| **Multiple DBs** | Harder | Easy ✅ |

**Recommendation**: Use Neo4j Desktop if you already have it! ✅

---

## Neo4j Desktop Advantages

### 1. Visual Graph Browser
- View your knowledge graph visually
- Explore relationships
- Run Cypher queries with auto-complete

### 2. Database Management
- Easy start/stop
- Multiple databases
- Backup and restore
- Performance monitoring

### 3. Plugin Management
- One-click plugin installation
- Plugin updates
- Enable/disable easily

### 4. Query Editor
- Syntax highlighting
- Auto-completion
- Query history
- Export results

---

## Accessing Neo4j Browser

After starting your database in Neo4j Desktop:

1. Click **Open** button next to your database
2. This opens Neo4j Browser at `http://localhost:7474`
3. Login with your credentials

### Useful Cypher Queries

**View all nodes:**
```cypher
MATCH (n)
RETURN n
LIMIT 25
```

**View graph schema:**
```cypher
CALL db.schema.visualization()
```

**Count nodes by type:**
```cypher
MATCH (n)
RETURN labels(n) AS type, count(n) AS count
ORDER BY count DESC
```

**View sample chunks:**
```cypher
MATCH (c:Chunk)
RETURN c.id, c.text[0..100] + '...' AS preview
LIMIT 5
```

**View document-chunk relationships:**
```cypher
MATCH (d:Document)-[r:HAS_CHUNK]->(c:Chunk)
RETURN d.filename, count(c) AS chunk_count
```

**Find similar chunks:**
```cypher
MATCH (c1:Chunk)-[r:SIMILAR_TO]->(c2:Chunk)
RETURN c1.text[0..50] AS chunk1,
       c2.text[0..50] AS chunk2,
       r.similarity AS similarity
ORDER BY r.similarity DESC
LIMIT 10
```

---

## Troubleshooting

### Issue: "Connection refused"

**Cause**: Database not running

**Solution**:
1. Open Neo4j Desktop
2. Make sure database shows **Started** (green)
3. If not, click **Start**

---

### Issue: "Authentication failed"

**Cause**: Wrong password in `.env`

**Solution**:
1. Check password in Neo4j Desktop
2. Update `.env` file:
   ```env
   NEO4J_PASSWORD=correct-password-here
   ```
3. Or reset password in Neo4j Desktop:
   - Stop database
   - Click **Manage** → **Administration**
   - Reset password

---

### Issue: "Plugin not found: apoc"

**Cause**: APOC plugin not installed

**Solution**:
1. In Neo4j Desktop, select database
2. Go to **Plugins** tab
3. Click **Install** on APOC
4. **Restart** database
5. Verify: Run in Neo4j Browser:
   ```cypher
   RETURN apoc.version()
   ```

---

### Issue: "Plugin not found: gds"

**Cause**: Graph Data Science plugin not installed

**Solution**:
1. In Neo4j Desktop, select database
2. Go to **Plugins** tab
3. Click **Install** on Graph Data Science
4. **Restart** database
5. Verify: Run in Neo4j Browser:
   ```cypher
   RETURN gds.version()
   ```

---

### Issue: Different port being used

**Cause**: Custom port configuration

**Solution**:
1. Check Neo4j Desktop → Database → **Manage**
2. Look for Bolt connector settings
3. Update `.env`:
   ```env
   NEO4J_URI=bolt://localhost:YOUR_PORT
   ```

---

### Issue: "Database 'neo4j' not found"

**Cause**: Using wrong database name (Neo4j 4.x+)

**Solution**:
1. Check database name in Neo4j Desktop
2. Update `.env`:
   ```env
   NEO4J_DATABASE=your-database-name
   ```
3. Or use default:
   ```env
   NEO4J_DATABASE=neo4j
   ```

---

## Performance Tuning for Desktop

### Memory Settings

Edit your database configuration in Neo4j Desktop:

1. Select database → **Manage** → **Settings**
2. Add/modify:

```properties
# Heap memory (adjust based on your RAM)
dbms.memory.heap.initial_size=512m
dbms.memory.heap.max_size=2G

# Page cache (for better read performance)
dbms.memory.pagecache.size=1G

# Transaction log
dbms.tx_log.rotation.retention_policy=2 days
```

### Recommended Settings by System

| RAM | Heap Max | Page Cache |
|-----|----------|------------|
| 8 GB | 1G | 1G |
| 16 GB | 2G | 2G |
| 32 GB+ | 4G | 4G |

---

## Switching Between Desktop and Docker

If you want to switch back to Docker later:

### To Docker:
```bash
# Stop Neo4j Desktop database
# Start Docker
docker-compose up -d

# Update .env
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=password123
```

### Back to Desktop:
```bash
# Stop Docker
docker-compose down

# Start Neo4j Desktop database
# Update .env with Desktop credentials
```

---

## Best Practices

### 1. Backup Your Data

In Neo4j Desktop:
1. Select database
2. Click **Manage** → **Dump**
3. Save backup file

### 2. Monitor Performance

- Check **Monitoring** tab in Neo4j Desktop
- Watch query performance
- Monitor memory usage

### 3. Keep Plugins Updated

- Regularly check for plugin updates
- Update APOC and GDS when available

### 4. Use Separate Databases

For different projects:
1. Create new database in Neo4j Desktop
2. Update `.env` with new database name
3. Keep data isolated

---

## Quick Reference

### Start Using Neo4j Desktop

```bash
# 1. Start database in Neo4j Desktop (click Start button)

# 2. Configure .env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# 3. Test connection
python cli.py stats

# 4. Ingest documents
python cli.py ingest --source data/documents

# 5. Query
python cli.py query "Your question?"
```

---

## Summary

✅ **No Docker needed** - Use your existing Neo4j Desktop
✅ **Better GUI** - Visual graph browser and management
✅ **Easy setup** - Just configure connection in `.env`
✅ **Same features** - All RAG functionality works identically
✅ **Better debugging** - Cypher query editor with syntax highlighting

**You're all set to use Neo4j Desktop with this RAG system!** 🚀

---

## Need Help?

- Check Neo4j Desktop logs: **Manage** → **Logs**
- Test Cypher queries in Neo4j Browser
- Run: `python cli.py stats` to verify connection
- Check `.env` file has correct credentials

