# API Reference

Complete reference for Semantic Memory MCP API endpoints and MCP tools.

## Table of Contents

- [MCP Tools](#mcp-tools)
- [HTTP API Endpoints](#http-api-endpoints)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Rate Limits](#rate-limits)
- [Examples](#examples)

## MCP Tools

These tools are available when connected via MCP protocol to Claude.ai or other MCP clients.

### `search_neural_memory`

Search through stored notes using semantic similarity.

**Parameters:**
- `query` (string, required): Search query text
- `limit` (integer, optional): Maximum results to return (default: 5, max: 20)

**Response:**
- `results`: Array of matching notes with similarity scores
- `total_found`: Total number of matches above threshold
- `search_time`: Query execution time in milliseconds

**Example:**
```json
{
  "query": "machine learning projects",
  "limit": 3,
  "results": [
    {
      "id": 42,
      "content": "Started working on neural network for image classification...",
      "category": "projects",
      "similarity": 0.8234,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_found": 7,
  "search_time": 45
}
```

### `add_note`

Store a new note with automatic embedding generation.

**Parameters:**
- `content` (string, required): Note content (max 10,000 characters)
- `category` (string, optional): Note category (default: "general")

**Response:**
- `id`: Generated note ID
- `embedding_dimensions`: Number of dimensions in generated embedding
- `status`: Success confirmation

**Example:**
```json
{
  "content": "Learned about transformer architecture today. Key insight: attention mechanism allows parallel processing.",
  "category": "learning",
  "response": {
    "id": 43,
    "embedding_dimensions": 384,
    "status": "Note added successfully"
  }
}
```

### `update_note`

Modify existing note content. Automatically regenerates embedding.

**Parameters:**
- `note_id` (integer, required): ID of note to update
- `content` (string, required): New content (max 10,000 characters)
- `category` (string, optional): New category

**Response:**
- `id`: Note ID
- `updated`: Confirmation message
- `embedding_updated`: Whether new embedding was generated

**Example:**
```json
{
  "note_id": 43,
  "content": "Updated: Learned about transformer architecture. Key insights: attention mechanism + positional encoding.",
  "response": {
    "id": 43,
    "updated": "Note updated successfully",
    "embedding_updated": true
  }
}
```

### `delete_note`

Remove a note from memory.

**Parameters:**
- `note_id` (integer, required): ID of note to delete

**Response:**
- `deleted`: Note ID that was removed
- `status`: Confirmation message

**Example:**
```json
{
  "note_id": 43,
  "response": {
    "deleted": 43,
    "status": "Note deleted successfully"
  }
}
```

### `neural_stats`

Get statistics about the memory system.

**Parameters:** None

**Response:**
- `total_notes`: Number of stored notes
- `categories`: Breakdown by category
- `embedding_info`: Model and dimensions
- `database_size`: Storage usage
- `oldest_note`: Timestamp of first note
- `newest_note`: Timestamp of latest note

**Example:**
```json
{
  "response": {
    "total_notes": 127,
    "categories": {
      "general": 45,
      "projects": 32,
      "learning": 28,
      "ideas": 22
    },
    "embedding_info": {
      "model": "all-MiniLM-L6-v2",
      "dimensions": 384,
      "consistency_check": "passed"
    },
    "database_size": "2.4 MB",
    "oldest_note": "2024-01-01T00:00:00Z",
    "newest_note": "2024-01-21T15:30:00Z"
  }
}
```

## HTTP API Endpoints

Direct HTTP access to the memory system (used internally by MCP server).

### Base URL
```
http://localhost:5000
```

### Authentication
All endpoints require API key authentication via:
- URL parameter: `?api_key=YOUR_API_KEY`
- Header: `Authorization: Bearer YOUR_API_KEY`

### `POST /api/search`

Semantic search endpoint.

**Request Body:**
```json
{
  "query": "machine learning",
  "limit": 5
}
```

**Response:**
```json
{
  "results": [...],
  "total_found": 12,
  "search_time_ms": 45,
  "status": "success"
}
```

### `POST /api/add`

Add new note endpoint.

**Request Body:**
```json
{
  "content": "Note content here",
  "category": "projects"
}
```

**Response:**
```json
{
  "id": 44,
  "status": "success",
  "embedding_generated": true
}
```

### `PUT /api/update/{note_id}`

Update existing note.

**Request Body:**
```json
{
  "content": "Updated content",
  "category": "learning"
}
```

**Response:**
```json
{
  "id": 44,
  "status": "updated",
  "embedding_regenerated": true
}
```

### `DELETE /api/delete/{note_id}`

Delete note.

**Response:**
```json
{
  "deleted_id": 44,
  "status": "success"
}
```

### `GET /api/stats`

Get system statistics.

**Response:**
```json
{
  "total_notes": 127,
  "categories": {...},
  "embedding_info": {...},
  "status": "success"
}
```

### `GET /api/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "embedding_model": "loaded",
  "uptime_seconds": 3600
}
```

## Authentication

### API Key Setup
1. Set in environment: `NEURAL_MEMORY_API_KEY=your_secure_key`
2. Include in requests via URL parameter or Authorization header
3. Minimum 16 characters recommended

### Security Notes
- API key transmitted in plain text over HTTP
- Use HTTPS in production
- Rotate keys periodically
- Store keys securely (not in code)

## Error Handling

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (missing/invalid API key)
- `404` - Not Found (note doesn't exist)
- `500` - Internal Server Error

### Error Response Format
```json
{
  "error": "Note not found",
  "code": "NOTE_NOT_FOUND",
  "status": "error"
}
```

### Common Errors

#### Authentication Errors
```json
{
  "error": "API key required",
  "code": "MISSING_API_KEY",
  "status": "error"
}
```

#### Validation Errors
```json
{
  "error": "Content too long (max 10,000 characters)",
  "code": "CONTENT_TOO_LONG", 
  "status": "error"
}
```

#### System Errors
```json
{
  "error": "Embedding model not loaded",
  "code": "EMBEDDING_ERROR",
  "status": "error"
}
```

## Rate Limits

### Default Limits
- **Search requests**: 30 per minute
- **Write operations** (add/update/delete): 10 per minute
- **Stats/health checks**: 60 per minute

### Rate Limit Headers
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 29
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded
```json
{
  "error": "Rate limit exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60,
  "status": "error"
}
```

## Examples

### Complete MCP Session Example

```python
# Connect to Claude.ai with MCP server configured
# Then use these tools:

# 1. Add some notes
add_note("Working on semantic search project. Using transformers for embeddings.", "projects")
add_note("Read paper on attention mechanisms. Key insight: query-key-value paradigm.", "learning")
add_note("Idea: combine semantic search with graph database for knowledge mapping.", "ideas")

# 2. Search by meaning
search_result = search_neural_memory("transformer embeddings", limit=3)
# Returns notes about transformers, embeddings, attention mechanisms

# 3. Get system overview
stats = neural_stats()
# Shows 3 notes across 3 categories

# 4. Update a note
update_note(1, "Updated: Semantic search project using all-MiniLM-L6-v2 model for embeddings.")

# 5. Clean up
delete_note(3)
```

### Direct HTTP API Example

```bash
# Set API key
export API_KEY="your_secure_api_key_here"

# Add a note
curl -X POST "http://localhost:5000/api/add?api_key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"content": "Learning about neural embeddings", "category": "research"}'

# Search for notes
curl -X POST "http://localhost:5000/api/search?api_key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "neural networks", "limit": 5}'

# Get statistics
curl "http://localhost:5000/api/stats?api_key=$API_KEY"

# Health check
curl "http://localhost:5000/api/health?api_key=$API_KEY"
```

### JavaScript Client Example

```javascript
class SemanticMemoryClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async search(query, limit = 5) {
    const response = await fetch(`${this.baseUrl}/api/search?api_key=${this.apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit })
    });
    return response.json();
  }

  async addNote(content, category = 'general') {
    const response = await fetch(`${this.baseUrl}/api/add?api_key=${this.apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, category })
    });
    return response.json();
  }
}

// Usage
const client = new SemanticMemoryClient('http://localhost:5000', 'your_api_key');

// Add note
await client.addNote('Studying graph neural networks for knowledge representation');

// Search
const results = await client.search('graph neural networks');
console.log(results);
```

## Embedding Model Details

### Model: all-MiniLM-L6-v2
- **Dimensions**: 384
- **Max sequence length**: 256 tokens
- **Languages**: English (optimized), multilingual support
- **Performance**: ~14ms per embedding on Apple Silicon M3

### Similarity Threshold
- **Default threshold**: 0.3
- **High relevance**: 0.7+
- **Medium relevance**: 0.5-0.7
- **Low relevance**: 0.3-0.5

### Consistency Check
System verifies embedding consistency on startup:
- Calibration phrases embedded and stored
- On restart, same phrases re-embedded
- Cosine similarity compared to stored values
- Warning if drift detected (>5% change)

## Database Schema

### Notes Table
```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    embedding BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Calibration Table
```sql  
CREATE TABLE calibration_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phrase TEXT NOT NULL,
    embedding BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Need Help?

- **Issues**: [GitHub Issues](https://github.com/artemMprokhorov/semantic-memory-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/artemMprokhorov/semantic-memory-mcp/discussions)
- **Documentation**: Check other files in `/docs/`
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
