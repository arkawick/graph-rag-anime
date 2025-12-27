# Visualization Images

This directory contains screenshots of the anime knowledge graph visualizations.

## Required Images

After you build and visualize your anime graph in Neo4j Browser, take screenshots and save them here:

### 1. `visualization.png`
**Main visualization** - Overview of your anime knowledge graph
- Open: http://localhost:7474
- Run query:
  ```cypher
  MATCH (a:Anime)-[r]->(n)
  WHERE a.score >= 8.5
  RETURN a, r, n
  LIMIT 200
  ```
- Style the graph (click node types, set captions, colors)
- Take screenshot and save as `visualization.png`

### 2. `schema.png`
**Graph schema** - Shows node types and relationships
- Run query:
  ```cypher
  CALL db.schema.visualization()
  ```
- Take screenshot and save as `schema.png`

### 3. `browser.png`
**Neo4j Browser interface** - Shows the UI
- Screenshot of Neo4j Browser with query results
- Save as `browser.png`

### 4. `similarity_network.png`
**Similarity network** - Anime clustered by embeddings
- Run query:
  ```cypher
  MATCH (a1:Anime)-[r:SIMILAR_TO]->(a2:Anime)
  WHERE r.similarity >= 0.75
  RETURN a1, r, a2
  LIMIT 100
  ```
- Take screenshot and save as `similarity_network.png`

### 5. `studio_network.png`
**Studio network** - A studio's portfolio
- Run query:
  ```cypher
  MATCH (s:Studio {name: "Kyoto Animation"})<-[r1:PRODUCED_BY]-(a:Anime)-[r2]->(n)
  RETURN s, r1, a, r2, n
  LIMIT 200
  ```
- Take screenshot and save as `studio_network.png`

### 6. `genre_distribution.png`
**Genre view** - Anime in a genre
- Run query:
  ```cypher
  MATCH (g:Genre {name: "Action"})<-[r1:HAS_GENRE]-(a:Anime)-[r2]->(n)
  WHERE a.score >= 7.0
  RETURN g, r1, a, r2, n
  LIMIT 150
  ```
- Take screenshot and save as `genre_distribution.png`

### 7. `recommendation_graph.png`
**Recommendation network** - User recommendations
- Run query:
  ```cypher
  MATCH (a1:Anime)-[r:RECOMMENDED]->(a2:Anime)
  WHERE r.votes >= 50
  RETURN a1, r, a2
  LIMIT 100
  ```
- Take screenshot and save as `recommendation_graph.png`

### 8. `styled_graph.png`
**Custom styled graph** - Shows styling capabilities
- Take any query result
- Customize extensively:
  - Size anime nodes by `score`
  - Color by node type
  - Set captions to show `title` and `score`
- Take screenshot and save as `styled_graph.png`

## How to Take Screenshots

### In Neo4j Browser:

1. **Full screen**: Click expand icon in top-right
2. **Adjust view**: Zoom and pan to show interesting clusters
3. **Style nodes**: Click node types at top, customize appearance
4. **Take screenshot**: Use OS screenshot tool
   - Windows: `Win + Shift + S`
   - Mac: `Cmd + Shift + 4`
   - Linux: `Print Screen` or `gnome-screenshot`

### Export from Neo4j Browser:

1. **Click download icon** in query result area
2. **Select PNG or SVG**
3. **Save to this directory**

## Image Specifications

- **Format**: PNG (preferred) or SVG
- **Resolution**: At least 1920x1080 for clarity
- **File size**: Keep under 5MB each
- **Background**: Use Neo4j's default dark theme for consistency

## Example Styling

**For the best-looking visualizations:**

1. **Anime nodes**:
   - Caption: `{title} ({score})`
   - Size: By `score` property
   - Color: Blue/Purple

2. **Genre nodes**:
   - Caption: `{name}`
   - Size: Medium (fixed)
   - Color: Green

3. **Studio nodes**:
   - Caption: `{name}`
   - Size: Medium (fixed)
   - Color: Orange

4. **Character nodes**:
   - Caption: `{name}`
   - Size: Small (fixed)
   - Color: Pink

5. **VoiceActor nodes**:
   - Caption: `{name}`
   - Size: Small (fixed)
   - Color: Yellow

## Placeholder Images

Until you create actual screenshots, the README.md references will show as broken images. This is expected! Create your visualizations and add the images here.

---

**Note**: These images are for documentation purposes. They help users understand what the anime knowledge graph looks like before they build their own.
