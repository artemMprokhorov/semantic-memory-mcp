# Architecture Overview

## System Design

Neural Memory MCP is designed as a self-contained, portable semantic memory system.

### Core Components

#### 1. MCP Protocol Handler (`mcp_sse_handler.py`)

Implements the Model Context Protocol using Server-Sent Events (SSE):

- Handles `initialize`, `tools/list`, and `tools/call` methods
- Manages tool routing for CRUD operations
- API key authentication via URL parameter

#### 2. Embedding Model (`stable_embeddings.py`)

Wraps HuggingFace Transformers for stable embedding generation:

- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Output: 384-dimensional vectors
- Direct transformers usage (avoids sentence-transformers ARM64 issues)

#### 3. Consistency Check (`embedding_check.py`)

Protects against embedding drift:

- Stores calibration vectors on first run
- Compares on every startup
- Threshold: 0.99 cosine similarity

#### 4. SQLite Database

Simple, portable storage:

```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    timestamp TEXT,
    embedding_vector BLOB  -- 384 * 4 bytes = 1536 bytes
);
```

### Data Flow

```
User Query → Claude.ai → ngrok → MCP Server
                                     │
                                     ▼
                              Parse MCP Request
                                     │
                                     ▼
                              Route to Tool
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
               add_note         search_notes     delete_note
                    │                │                │
                    ▼                ▼                ▼
              Generate         Query Embedding   Direct DB
              Embedding              │           Operation
                    │                ▼
                    │         Cosine Similarity
                    │         Against All Notes
                    │                │
                    ▼                ▼
              Store in DB      Return Ranked
                              Results (sim > 0.4)
```

### Search Algorithm

1. Encode query text → 384D vector
2. Load all note embeddings from SQLite
3. Compute cosine similarity for each
4. Filter by threshold (default 0.4)
5. Sort by similarity descending
6. Return top N results

### Why These Choices?

| Decision | Reasoning |
|----------|-----------|
| SQLite over Postgres | Portability, zero config, sufficient for 10K+ notes |
| Direct transformers over sentence-transformers | ARM64 stability (Mac M-series) |
| BLOB storage for embeddings | Simple, no vector DB dependency |
| SSE over WebSocket | MCP protocol standard, simpler implementation |
| Flask over FastAPI | Lighter weight, sufficient for single-user |

### Scaling Considerations

Current design optimized for:
- Single user
- Up to ~10,000 notes
- Response time < 500ms

For larger scale:
- Add FAISS index for faster search
- Batch embedding generation
- PostgreSQL with pgvector
